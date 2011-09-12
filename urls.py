from django.conf.urls.defaults import patterns, include, url

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'twitflick.views.home', name='home'),
    # url(r'^twitflick/', include('twitflick.foo.urls')),

    (r'^/?$', 'twitflick.views.index'),

    (r'^static/css/(?P<theme>[^/]+)/images/(?P<filename>[^.]+).png$',
        'twitflick.views.jquery_ui_images'),
    (r'^static/css/(?P<filename>.+)$', 'twitflick.views.css'),
    (r'^static/js/(?P<filename>.+)$', 'twitflick.views.js'),
    (r'^static/img/(?P<filename>[^.]+)\.gif$', 'twitflick.views.gif'),
    (r'^static/img/(?P<filename>[^.]+)\.png$', 'twitflick.views.png'),
    (r'^static/img/(?P<filename>[^.]+)\.(?P<extension>jpe?g)$',
        'twitflick.views.jpeg'),

    (r'app/', include('twitflick.app.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    # url(r'^admin/', include(admin.site.urls)),
)
