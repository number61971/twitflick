from django.conf.urls.defaults import *

urlpatterns = patterns(
    'app.views',

    (r'^/?$', 'index'),
    (r'^twitflick_search_post', 'twitflick_search_post'),
    (r'^twitflick_search_ajax', 'twitflick_search_ajax'),
)
