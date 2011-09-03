#Sophisticated route lookup and URL generation
#Named routes
#Redirect routes
#Wildcard paths before and after static parts
#Sub-domain support built-in
#Conditional matching based on domain, cookies, HTTP method (RESTful), and more
#Easily extensible utilizing custom condition functions and route generation functions

import re
import time
import json
from os.path import join
from webob import Request,Response

#Template/Views: Mako
from mako.template import Template
from mako.lookup import TemplateLookup
from mako.runtime import Context
from mako import exceptions

from urllib import quote

def secondsToStr(t):
    return "%d:%02d:%02d.%03d" % \
        reduce(lambda ll,b : divmod(ll[0],b) + ll[1:],
            [(t*1000,),1000,60,60])

#FILTERS

def filter_method(methods):
    def wrapped(request):
        if request.method in methods:
            return True
        else:
            return False
        pass
    return wrapped


def filter_domain(name):
    def wrapped(request):
        if request.environ.get('HTTP_HOST'):
            url = request.environ['HTTP_HOST']
        else:
            url = request.environ['SERVER_NAME']
        if url == name:
            return True

        return False
    return wrapped


def filter_ssl(request):
    if request.scheme == 'https':
        return True
    else:
        return False

def filter_nossl(request):
    if request.scheme == 'http':
        return True
    else:
        return False

#RESPONDER

class Responder(object):
    def __init__( self, start_res, environ, mylookup, start_time):
        self.start_response = start_res
        self.mylookup = mylookup
        self.req = Request(environ)
        self.environ = environ
        self.start_time = start_time
        self.res = Response()
    
    @property
    def post(self):
        return self.req.str_POST
        
    def cookie(self, name, value = None, max_age=60*60*3, **kwargs):
        if value == None:
            if name in self.req.cookies:
                return self.req.cookies[name]
        else:
            self.res.set_cookie(name,value, max_age= max_age, **kwargs)

    def view(self, viewname, **data):
    
        view = self.mylookup.get_template(viewname + '.html').render(**data)
        
        self.res.status = 202
        self.res.content_type = 'text/html'
        self.res.content_length = len(view)
        
        self.start_response(self.res.status, self.res.headerlist)
        
        return view
    
    def json( self, data ):
        self.res.status = 202
        self.res.content_type = 'application/json'
        self.res.charset = None
        self.res.content_length = None
        self.start_response(self.res.status, self.res.headerlist)
        print(secondsToStr(time.clock()-self.start_time))
        return str(data)

    def text( self, data ):
        self.res.content_type = 'text/plain'
        self.res.status = 202
        self.res.body = data
        return self.res(self.environ, self.start_response)
    
    def redirect( self, url, code = 303, cookies = None):
        self.res.status = code
        self.res.location = url
        self.res.content_type = 'text/html'
        self.res.content_length = None
        self.start_response(self.res.status, self.res.headerlist)
        return ['']

#MAIN APP

class Dillamond:
    def __init__(self, settings = {}):
        self.mylookup = TemplateLookup(
            directories = [join(settings['root'],rpath) for rpath in settings['view_paths']],
            #filesystem_checks = True,
            #module_directory = join(settings['root'],settings['viewcache_path']),
            #imports = ['import json'],
            output_encoding='utf-8')
        
        #self.static_path = join(settings['root'],settings['static_path'])
        #self.static_asset_path = join(settings['root'],settings['static_asset_path'])
        #self.asset_path = join(settings['root'],settings['asset_path'])
        self.routes = []
        self.genlist = []
        self._part_matcher = re.compile(r'{.*?}')
        
    def _partspath(self, path):
        parts = re.findall(self._part_matcher,path)
        d = []
        for part in xrange(len(parts)):
            a = parts[part][1:-1].split('=')
            d.append(a)
        return d
        
    def _regexpath(self, path):
        return '^' + re.sub(self._part_matcher,'(.*?)',path) + '$'
    
    def error(self, fn):
        self.error_handler = fn
        return fn

    def route(self, path, req = [], **kwargs):
        def wrapped(fn):
            self.routes.append((path,{
                'regex': self._regexpath(path),
                'name':fn.__name__,
                'function':fn,
                'reqs':req,
                'kwargs':kwargs,
                'parts':self._partspath(path)
                }))

            return fn
        return wrapped
    
    def generate(self,path):
        def wrapped(fn):
            self.genlist.append( (path,fn) )
            return fn
        return wrapped
    
    def post(self ,path, req = [], **kwargs):
        return self.route(path, req=req+filter_method(['POST']), **kwargs)
    
    def get(self,path, req = [], **kwargs):
        return self.route(path, req=req+filter_method(['GET']), **kwargs)
    
    def getpost(self,path, req = [], **kwargs):
        return self.route(path, req=req+filter_method(['GET','POST']), **kwargs)
    
    def _meetsreqs(self, requirement, reqs):
        for requirements in reqs:
            if requirements(requirement) == False:
                return False
        return True
    
    def parse(self, req):
        m = None
        for reg,route in self.routes:
            m = re.match(route['regex'],req.path)
            if m and self._meetsreqs(req,route['reqs']):
                break
                
        else:
            return False
        bindings = route['kwargs']
        for part in route['parts']:
            if len(part) == 2:
                bindings[part[0]] = part[1]
        for part in xrange(len(m.groups())):
            if m.group(part+1):
                bindings[route['parts'][part][0]] = m.group(part+1)
        return bindings,route

    def execute(self, res, req):
        m = None
        for reg,route in self.routes:
            m = re.match(route['regex'],req.path)
            if m and self._meetsreqs(req,route['reqs']):
                break
                
        else:
            return False
        bindings = route['kwargs']
        for part in route['parts']:
            if len(part) == 2:
                bindings[part[0]] = part[1]
        for part in xrange(len(m.groups())):
            if m.group(part+1):
                bindings[route['parts'][part][0]] = m.group(part+1)

        return route['function'](res, **dict(bindings))
    
    def wsgiapp(self):
        def wrapped(environ, start_response):
            start_time = time.clock()
            req = Request(environ)
            res = Responder(start_response, environ, self.mylookup, start_time)
            return str(self.execute(res, req))
        return wrapped
    
    def generatehtml(self, genfunc):
        def rawview(viewname, **data):
            view = self.mylookup.get_template(viewname + '.html').render
            return view(**data)
        return genfunc(rawview)
