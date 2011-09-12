import json
import re
from urllib import quote

from django.db import models

#
# database models
#

class TwitterSearch(models.Model):
    class Meta:
        db_table = 'twitter_search'

    search_term = models.TextField()
    response_json = models.TextField()


class FlickrSearch(models.Model):
    class Meta:
        db_table = 'flickr_search'

    search_term = models.TextField(blank=True, null=True)
    response_json = models.TextField(blank=True, null=True)


class TwitflickSearch(models.Model):
    class Meta:
        db_table = 'twitflick_search'

    twitter_search = models.ForeignKey('TwitterSearch')
    flickr_search = models.ForeignKey('FlickrSearch')
    logwhen = models.DateTimeField(auto_now_add=True)

#
# object models
#

class Tweet:
    def __init__(self, search_response_json):
        self.data = json.loads(search_response_json)
        self.text = self.data['results'][0]['text']
        self.user = self.data['results'][0]['from_user']
        self.profile_image_url = self.data['results'][0]['profile_image_url']

    def get_user_url(self):
        url = 'http://twitter.com/#!/'
        encoded_username = quote(self.user)
        return url + encoded_username

    _url = re.compile(r"\bhttps?://[^\s]+")
    _s_contraction = re.compile(r"(\w)'([Ss])\b")
    _nt_contraction = re.compile(r"([Nn])'([Tt])\b")
    _im_contraction = re.compile(r"\b([Ii])'([Mm])\b")
    _apostrophe = r"AAAAPOSTROPHEEEE"
    _apostrophe_decode = re.compile(_apostrophe)
    _tokenizer = re.compile(r'\W+')
    def tokenize(self):
        """
        Return all the words in the tweet text, preserving apostrophes so that
        contractions and possessives don't get interpreted as separate words.
        (I.e., so "can't" doesn't get interepreted as "can" and "t".)
        Also strip out urls so that they don't get tokenized into "words".
        """
        text = self._url.sub(r'', self.text)
        text = self._s_contraction.sub(r'\1%s\2' % self._apostrophe, text)
        text = self._nt_contraction.sub(r'\1%s\2' % self._apostrophe, text)
        text = self._im_contraction.sub(r'\1%s\2' % self._apostrophe, text)
        words = self._tokenizer.split(text)
        words = [self._apostrophe_decode.sub("'", w) for w in words if w]
        return words

    _forbidden_terms = ("the", "a", "an", "that", "i", "you")
    def extract_flickr_search_term(self):
        """
        Extract the flickr search term from the tweet text.
        It must be the 4th word in the tweet, and it must not be in the list
        of forbidden words.
        If no word matches these conditions, return None.
        """
        term = None
        for word in self.tokenize()[3:]:
            if word.lower() not in self._forbidden_terms:
                term = word
                break
        return term

    def save_twitter_search(self):
        """
        Save the search response to the database.
        """
        twitter_search = TwitterSearch(
                            search_term=self.data['query'],
                            response_json=json.dumps(self.data)
                         )
        twitter_search.save()
        return twitter_search


class FlickrPhoto:
    def __init__(self, search_response_json, search_term):
        self.data = json.loads(search_response_json)
        self.id = self.data['photo']['id']
        self.farm = self.data['photo']['farm']
        self.server = self.data['photo']['server']
        self.secret = self.data['photo']['secret']
        self.search_term = search_term

    def get_img_src_url(self):
        d = {'farm':self.farm,
             'server':self.server,
             'photo_id':self.id,
             'secret':self.secret,
            }
        src_url = ('http://farm%(farm)s.static.flickr.com/%(server)s/'
                   '%(photo_id)s_%(secret)s_z.jpg') % d
        return src_url

    _flickr_url_clean = re.compile(r'\\')
    def get_page_url(self):
        return self._flickr_url_clean.sub('',
                               self.data['photo']['urls']['url'][0]['_content'])

    def save_flickr_search(self):
        """
        Save the search response to the database.
        """
        flickr_search = FlickrSearch(
                            search_term=self.search_term,
                            response_json=json.dumps(self.data)
                         )
        flickr_search.save()
        return flickr_search

