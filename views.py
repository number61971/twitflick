from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import redirect

def index(req):
    return redirect('/app')

#
# cheating static content handlers
# because I don't want to run a web server dedicated to serving static files
#
def css(req, filename):
    return HttpResponse(
            open('%scss/%s' % (settings.MEDIA_ROOT,filename), 'rb').read(),
            mimetype='text/css'
        )

def js(req, filename):
    return HttpResponse(
            open('%sjs/%s' % (settings.MEDIA_ROOT,filename), 'rb').read(),
            mimetype='application/x-javascript'
        )

def gif(req, filename):
    return HttpResponse(
            open('%simg/%s.gif' % (settings.MEDIA_ROOT,filename), 'rb').read(),
            mimetype='image/gif'
        )

def png(req, filename):
    return HttpResponse(
            open('%simg/%s.png' % (settings.MEDIA_ROOT,filename), 'rb').read(),
            mimetype='image/png'
        )

def jpeg(req, filename, extension):
    return HttpResponse(
            open('%simg/%s.%s' % (settings.MEDIA_ROOT,filename,extension), 'rb').read(),
            mimetype='image/jpeg'
        )

def jquery_ui_images(req, theme, filename):
    return HttpResponse(
            open('%scss/%s/images/%s.png' % (settings.MEDIA_ROOT,theme, filename), 'rb').read(),
            mimetype='image/png'
        )

