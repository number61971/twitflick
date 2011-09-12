import json
import re
import sys
import time
import traceback
from urllib import urlencode
from urllib2 import urlopen, HTTPError, URLError

from django.contrib.humanize.templatetags import humanize
from django.http import HttpResponse
from django.shortcuts import redirect, render_to_response
from django.template import RequestContext

from app.models import *

TWITTER_DEFAULT_SEARCH_TERM = 'getty'

#
# public API
#
DATA_KEY = 'twitflick_search_results'
def index(req):
    data = req.session.get(DATA_KEY)
    if data:
        # clear the session so that page refreshes will result in new search
        req.session[DATA_KEY] = None
    else:
        # no data, so initiate a search
        data = twitflick_search(req)
    return render_to_response('index.html', data,
            context_instance=RequestContext(req))

def twitflick_search_post(req):
    """
    Query for twitflick data, then reload the website page.
    Normally won't be called because jQuery is overriding POST form
    submission.
    """
    data = twitflick_search(req)
    req.session[DATA_KEY] = data
    return redirect('/app')

def twitflick_search_ajax(req):
    try:
        data = twitflick_search(req)
    except:
        # most exceptions will be HTTP timeouts
        # so ensure those are formatted most clearly
        # all other -- unforseen -- exceptions will just poop on out!
        tb_type, tb_value, tb = sys.exc_info()
        exc_value = traceback.format_exception_only(tb_type, tb_value)[0]
        data = {'stat':'failure',
                'msg':exc_value.replace('Exception: HTTP', 'HTTP'),
               }
    return HttpResponse(json.dumps(data), 'application/json')

#
# private helpers
#

def twitflick_search(req):
    """
    Main program logic.

    1. Search twitter for latest tweet containing the default search term
       (e.g., 'getty')
    2. Extract 4th word in tweet as flicker search term
       a. UNLESS 4th word is among:
            "the", "a", "an", "that", "I", "you"
          in which case take the next word should be chosen
          UNLESS it's also a forbidden word,
          etc., etc.
       b. If no suitable word available, don't search flickr

    Return the data in a form suitable for direct output to web page.
    """
    tweet, twitter_search = search_twitter()
    term = tweet.extract_flickr_search_term()
    if term:
        flickr_search_term_display = (
            'Searched flickr with <span id="flickr_search_term">%s</span>:'
            ) % term
        flickr_photo, flickr_search = search_flickr(term)
        if flickr_photo:
            flickr_display = '<a href="%s"><img src="%s"/></a>' % (
                                 flickr_photo.get_page_url(),
                                 flickr_photo.get_img_src_url())
        else:
            flickr_display = 'No flickr image found!'

    else:
        # NOTE: I would normally insert NULLs into the database to represent
        # the empty flickr search. However, django's sqlite3 database wrapper
        # makes doing this difficult. So I'm using the string 'NULL' to
        # represent NULLs. This does have the beneficial side effect of making
        # querying against NULL values a bit easier, however! See:
        # http://www.sqlite.org/nulls.html
        #flickr_search = FlickrSearch(search_term=None, response_json=None)
        flickr_search = FlickrSearch(search_term='NULL', response_json='NULL')
        flickr_search.save()
        flickr_search_term_display = (
            'No suitable search term from the tweet could be extracted.'
            )
        flickr_display = ''
    
    # associate the twitter and flickr searches together as a single
    # twitflick search event and store in database
    twitflick_search = TwitflickSearch(
                            twitter_search=twitter_search,
                            flickr_search=flickr_search
                            )
    twitflick_search.save()

    # finalize data for page display
    search_count = TwitflickSearch.objects.count()
    data = {'stat': 'ok',
            'twitter_search_term': TWITTER_DEFAULT_SEARCH_TERM,
            'twitter_user_profile_image_url': tweet.profile_image_url,
            'twitter_user_url': tweet.get_user_url(),
            'twitter_user': tweet.user,
            'tweet': tweet.text,
            'flickr_search_term_display': flickr_search_term_display,
            'flickr_display': flickr_display,
            'search_count': humanize.intcomma(search_count),
            'search_count_plural': 's' if search_count != 1 else '',
           }
    return data

def search_twitter():
    """
    Query twitter for most recent tweet containing the default search term
    and return a Tweet instance.
    """
    url = 'http://search.twitter.com/search.json'
    params = urlencode([
                ('q',TWITTER_DEFAULT_SEARCH_TERM),
                ('result_type','recent'),
                ('rpp','1'),
            ])
    response_text = GET('%s?%s' % (url, params)).read()
    tweet = Tweet(response_text)
    twitter_search = tweet.save_twitter_search()
    return (tweet, twitter_search)

_twitflick_api_key = '66ece251b8a5443c56195555d8182514'
_jsonFlickrApi = re.compile(r'^jsonFlickrApi\(\{(.+)\}\)$')
def search_flickr(term):
    """
    Search flickr with the supplied search term
    and return a FlickrPhoto instance ...
    ... unless no photo is found, in which case return None.
    flickr returns no results a surprising number of times! Why?
    """
    url = 'http://api.flickr.com/services/rest/'
    params = urlencode([
                ('method','flickr.photos.search'),
                ('api_key',_twitflick_api_key),
                ('text',term),
                ('content_type','1'),
                ('per_page','1'),
                ('format','json'),
            ])
    response_text = GET('%s?%s' % (url, params)).read()
    response_json = _jsonFlickrApi.sub(r'{\1}', response_text)
    response_data = json.loads(response_json)

    # Must also query for full photo info to obtain the photo's flickr page url
    # in order to comply with flickr's community guidelines and terms of use
    # for displaying photos outside of flickr.
    # See: http://www.flickr.com/guidelines.gne, http://www.flickr.com/terms.gne
    if response_data['photos']['photo']:
        photo_id = response_data['photos']['photo'][0]['id']
        params = urlencode([
                    ('method','flickr.photos.getInfo'),
                    ('api_key',_twitflick_api_key),
                    ('photo_id', photo_id),
                    ('format','json'),
                ])
        response_text = GET('%s?%s' % (url, params)).read()
        response_json = _jsonFlickrApi.sub(r'{\1}', response_text)
        flickr_photo = FlickrPhoto(response_json, term)
        flickr_search = flickr_photo.save_flickr_search()
    else:
        # if the initial flickr search returned no results, e.g.:
        # {u'photos': {u'total': u'0', u'photo': [], u'perpage': 1, u'page': 1, u'pages': 0}, u'stat': u'ok'}
        # there will be no photo data from which an ID may be extracted.
        flickr_photo = None
        flickr_search = FlickrSearch(
                                  search_term=term, response_json=response_json)
        flickr_search.save()
    return (flickr_photo, flickr_search)

def GET(url):
    """
    HTTP 503 timeout errors are common when accessing flickr
    (at least at home where I put this together).
    Retry for up to a minute, then give up for good.
    """
    i = 0
    while i < 6:
        try:
            i += 1
            response = urlopen(url)
        except (HTTPError, URLError):
            # try again in 10 seconds
            time.sleep(10)
        else:
            # success!
            return response
    raise Exception('HTTP ERROR 503: Timeout accessing %s' % url)

