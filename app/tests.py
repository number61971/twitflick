"""
These tests will pass when you run "python manage.py test app".
"""
import json

from django.test.client import Client
from django.utils import unittest

from app.models import *
from app.views import *


class PublicAPIFunctionTests(unittest.TestCase):
    """
    Behavioral testing. I.e.,
    Test that URLs generate the expected responses, call the correct views, etc.
    """
    def test_index_redirect(self):
        c = Client()
        response = c.get('/', follow=True)
        redirect_chain = [('http://testserver/app', 302),
                          ('http://testserver/app/', 301)]
        self.assertEqual(response.redirect_chain, redirect_chain)

    def test_index(self):
        c = Client()
        response = c.get('/app/')

        status_code = 200
        self.assertEqual(response.status_code, status_code)

        stat = 'ok'
        self.assertEqual(response.context['stat'], stat)

        templates = ['index.html']
        response_templates = [t.name for t in response.templates]
        self.assertEqual(response_templates, templates)

    def test_twitflick_search_ajax(self):
        c = Client()
        response = c.get('/app/twitflick_search_ajax/')

        stat = 'ok'
        response_data = json.loads(response.content)
        self.assertEqual(response_data['stat'], stat)


class ViewHelperFunctionTests(unittest.TestCase):
    def test_search_twitter(self):
        """
        Test that querying twitter returns the expected response. 
        """
        tweet, twitter_search = search_twitter()

        # test tweet object
        self.failIf(tweet.data.has_key('error'))
        self.assert_(tweet.data.has_key('completed_in'))
        self.assert_(tweet.data.has_key('query'))
        self.assertEqual(tweet.data['results_per_page'], 1)
        self.assert_(tweet.data['results'])

        # test twitter_search database object
        self.assert_(twitter_search.id)

        # ensure that tweet and twitter_search represent the same data
        self.assertEqual(tweet.data, json.loads(twitter_search.response_json))

    def test_search_flickr(self):
        """
        Test that querying flickr returns the expected response.
        This is very much a behavioral test because flickr produces
        unpredictable output.
        """
        term = 'getty'
        flickr_photo, flickr_search = search_flickr(term)

        # test flickr_photo_object ... which may be None!
        self.assert_((flickr_photo is None
                        or flickr_photo.data['stat'] == 'ok'))

        if flickr_photo:
            self.assert_((flickr_photo.data.has_key('photo')
                            or flickr_photo.data.has_key('photos')))

            # test flickr_search database object
            self.assert_(flickr_search.id)

            # ensure that flickr_photo and flickr_search represent the same data
            if flickr_photo and flickr_photo.data.has_key('photo'):
                self.assertEqual(flickr_photo.data,
                                    json.loads(flickr_search.response_json))



class TweetTests(unittest.TestCase):
    def setUp(self):
        sample_twitter_json = r"""{"completed_in":0.136, "max_id":112333943902175232, "max_id_str":"112333943902175232", "next_page":"?page=2&max_id=112333943902175232&q=getty&rpp=1", "page":1, "query":"getty", "refresh_url":"?since_id=112333943902175232&q=getty", "results":[{"created_at":"Sat, 10 Sep 2011 01:17:53 +0000", "from_user":"Flylife_Mangu", "from_user_id":288892814, "from_user_id_str":"288892814", "geo":null, "id":112333943902175232, "id_str":"112333943902175232", "iso_language_code":"en", "metadata":{"result_type":"recent"}, "profile_image_url":"http://a0.twimg.com/profile_images/1530354129/manguu_normal.jpg", "source":"&lt;a href=&quot;http://levelupstudio.com&quot; rel=&quot;nofollow&quot;&gt;Plume\u00A0\u00A0&lt;/a&gt;", "text":"Somone cop cuz I know.sebbys Getty.isn't ganna be all that nut its something", "to_user_id":null, "to_user_id_str":null}], "results_per_page":1, "since_id":0, "since_id_str":"0"}"""
        self.tweet = Tweet(sample_twitter_json)

    def test_text(self):
        text = "Somone cop cuz I know.sebbys Getty.isn't ganna be all that nut its something"
        self.assertEqual(self.tweet.text, text)

    def test_user(self):
        user = 'Flylife_Mangu'
        self.assertEqual(self.tweet.user, user)

    def test_profile_image_url(self):
        url = 'http://a0.twimg.com/profile_images/1530354129/manguu_normal.jpg'
        self.assertEqual(self.tweet.profile_image_url, url)

    def test_get_user_url(self):
        url = 'http://twitter.com/#!/Flylife_Mangu'
        self.assertEqual(self.tweet.get_user_url(), url)

    def test_tokenize(self):
        """
        Ensure that all words are extracted from a tweet.
        """
        words = ['Somone', 'cop', 'cuz', 'I', 'know', 'sebbys', 'Getty',
                 "isn't", 'ganna', 'be', 'all', 'that', 'nut', 'its',
                 'something']
        self.assertEqual(self.tweet.tokenize(), words)

        #
        # ad hoc tests
        #

        # no empty words
        data = {
            'results':[
                {'text':('@Rafiki58 the song been playing randomly in my mind.'
                         ' Got play other songs to Getty it off my mind.'),
                 'from_user':'Rafiki58',
                 'profile_image_url':'http://somewhere.com',},
                ],
            }
        tweet = Tweet(json.dumps(data))
        words = ['Rafiki58', 'the', 'song', 'been', 'playing', 'randomly', 'in',
                 'my', 'mind', 'Got', 'play', 'other', 'songs', 'to', 'Getty',
                 'it', 'off', 'my', 'mind']
        self.assertEqual(tweet.tokenize(), words)

        # preserve 's contractions and possessives
        data = {
            'results':[
                {'text':("Watching Sarah Silverman hold Selma Blair's baby in "
                         'the Getty portrait studio.'),
                 'from_user':'Rafiki58',
                 'profile_image_url':'http://somewhere.com',},
                ],
            }
        tweet = Tweet(json.dumps(data))
        words = ['Watching', 'Sarah', 'Silverman', 'hold', 'Selma', "Blair's",
                 'baby', 'in', 'the', 'Getty', 'portrait', 'studio']
        self.assertEqual(tweet.tokenize(), words)

        # "I'm" preserved
        data = {
            'results':[
                {'text':"@Mr_desire saturday,I'm having a getty,slideeee",
                 'from_user':'jeaaanty',
                 'profile_image_url':'http://somewhere.com',},
                ],
            }
        tweet = Tweet(json.dumps(data))
        words = ['Mr_desire', 'saturday', "I'm", 'having', 'a', 'getty',
                 'slideeee']
        self.assertEqual(tweet.tokenize(), words)

        # no URLs
        data = {
            'results':[
                {'text':('http://t.co/uH6QEvG Warren Gatland takes in his '
                         "Wales team's 17-16 defeat by South Africa in "
                         'Wellington. Photograph: Stu Forster/Getty Im'),
                 'from_user':'Rafiki58',
                 'profile_image_url':'http://somewhere.com',},
                ],
            }
        tweet = Tweet(json.dumps(data))
        words = ['Warren', 'Gatland', 'takes', 'in', 'his', 'Wales', "team's",
                 '17', '16', 'defeat', 'by', 'South', 'Africa', 'in',
                 'Wellington', 'Photograph', 'Stu', 'Forster', 'Getty', 'Im']
        self.assertEqual(tweet.tokenize(), words)

    def test_extract_flickr_search_term(self):
        term = 'know'
        self.assertEqual(self.tweet.extract_flickr_search_term(), term)

        #
        # ad hoc tests
        #

        # no empty words so expected term gets pulled out
        data = {
            'results':[
                {'text':('@Rafiki58 the song been playing randomly in my mind.'
                         ' Got play other songs to Getty it off my mind.'),
                 'from_user':'Rafiki58',
                 'profile_image_url':'http://somewhere.com'},
                ],
            }
        tweet = Tweet(json.dumps(data))
        term = 'been'
        self.assertEqual(tweet.extract_flickr_search_term(), term)

        # no URLs so expected term gets pulled out
        data = {
            'results':[
                {'text':('http://t.co/uH6QEvG Warren Gatland takes in his '
                         "Wales team's 17-16 defeat by South Africa in "
                         'Wellington. Photograph: Stu Forster/Getty Im'),
                 'from_user':'Rafiki58',
                 'profile_image_url':'http://somewhere.com',},
                ],
            }
        tweet = Tweet(json.dumps(data))
        term = 'in'
        self.assertEqual(tweet.extract_flickr_search_term(), term)

        data = {
            'results':[
                {'text':'can use the fourth word here',
                 'from_user':'unittest',
                 'profile_image_url':'http://somewhere.com',},
                ],
            }
        tweet = Tweet(json.dumps(data))
        term = 'fourth'
        self.assertEqual(tweet.extract_flickr_search_term(), term)

        data = {
            'results':[
                {'text':'too few words',
                 'from_user':'unittest',
                 'profile_image_url':'http://somewhwere.com',},
                ],
            }
        tweet = Tweet(json.dumps(data))
        term = None
        self.assertEqual(tweet.extract_flickr_search_term(), term)

        data = {
            'results':[
                {'text':("can't use any that you an the a i That YOU "
                         "An THE A I"),
                 'from_user':'unittest',
                 'profile_image_url':'http://somewhere.com',},
                ],
            }
        tweet = Tweet(json.dumps(data))
        term = None
        self.assertEqual(tweet.extract_flickr_search_term(), term)


class FlickrPhotoTests(unittest.TestCase):
    def setUp(self):
        sample_search_term = 'summer'
        sample_flickr_json = r"""{"photo":{"id":"6132014232", "secret":"18a28c1c65", "server":"6181", "farm":7, "dateuploaded":"1315623756", "isfavorite":0, "license":"0", "safety_level":"0", "rotation":0, "owner":{"nsid":"24085411@N08", "username":"elidanang", "realname":"ELI DANANG", "location":"DANANG, VIETNAM", "iconserver":"0", "iconfarm":0}, "title":{"_content":"eli_summer_farewell_party_sept_2011_112"}, "description":{"_content":""}, "visibility":{"ispublic":1, "isfriend":0, "isfamily":0}, "dates":{"posted":"1315623756", "taken":"2011-09-09 18:32:40", "takengranularity":"0", "lastupdate":"1315623801"}, "views":"1", "editability":{"cancomment":0, "canaddmeta":0}, "publiceditability":{"cancomment":1, "canaddmeta":0}, "usage":{"candownload":1, "canblog":0, "canprint":0, "canshare":1}, "comments":{"_content":"0"}, "notes":{"note":[]}, "people":{"haspeople":0}, "tags":{"tag":[{"id":"23992598-6132014232-3763", "author":"24085411@N08", "raw":"ELI", "_content":"eli", "machine_tag":0}, {"id":"23992598-6132014232-245", "author":"24085411@N08", "raw":"Summer", "_content":"summer", "machine_tag":0}, {"id":"23992598-6132014232-14330", "author":"24085411@N08", "raw":"Farewell", "_content":"farewell", "machine_tag":0}, {"id":"23992598-6132014232-239", "author":"24085411@N08", "raw":"Party", "_content":"party", "machine_tag":0}, {"id":"23992598-6132014232-676190", "author":"24085411@N08", "raw":"2011", "_content":"2011", "machine_tag":0}]}, "urls":{"url":[{"type":"photopage", "_content":"http:\/\/www.flickr.com\/photos\/elidanang\/6132014232\/"}]}, "media":"photo"}, "stat":"ok"}"""
        self.flickr_photo = FlickrPhoto(sample_flickr_json, sample_search_term)

    def test_id(self):
        id = '6132014232'
        self.assertEqual(self.flickr_photo.id, id)

    def test_farm(self):
        farm = 7
        self.assertEqual(self.flickr_photo.farm, farm)

    def test_server(self):
        server = '6181'
        self.assertEqual(self.flickr_photo.server, server)

    def test_secret(self):
        secret = '18a28c1c65'
        self.assertEqual(self.flickr_photo.secret, secret)

    def test_get_img_src_url(self):
        """
        Test that a valid imr src url is constructed from raw flickr data.
        """
        url = 'http://farm7.static.flickr.com/6181/6132014232_18a28c1c65_z.jpg'
        self.assertEqual(self.flickr_photo.get_img_src_url(), url)

    def test_get_page_url(self):
        """
        Test that the flickr page url for a photo is ready for use
        on a web page.
        """
        url = 'http://www.flickr.com/photos/elidanang/6132014232/'
        self.assertEqual(self.flickr_photo.get_page_url(), url)

