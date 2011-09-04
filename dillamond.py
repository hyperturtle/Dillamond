"""Dillamond

Copyright (C) 2011 by Linh-Nam Vu

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.

"""


import re
import time

from os.path import join, dirname
from os import makedirs
from webob import Request, Response

#Template/Views: Mako
from mako.lookup import TemplateLookup

#import json
#from mako.template import Template
#from mako.runtime import Context
#from mako import exceptions
#from urllib import quote

#HELPERS

def seconds_to_str(time_in_seconds):
    """Pretty print time"""
    return "%d:%02d:%02d.%03d" % \
        reduce(lambda ll,b : divmod(ll[0],b) + ll[1:],
            [(time_in_seconds*1000,),1000,60,60])

def meetsreqs(request, requirements):
    """used to test an array of requirements
    """
    for requirement in requirements:
        if requirement(request) == False:
            return False
    return True

#FILTERS

def filter_method(methods):
    """Creates a filter for requests by method
    
    Arguments
    method: array of 'POST','GET',etc...
    """
    def wrapped(request):
        """ Function used to filter request
        """
        if request.method in methods:
            return True
        else:
            return False
    return wrapped


def filter_domain(name):
    """Creates a filter for requests by domain name
    name: string to use to match domain name.
    """
    def wrapped(request):
        """ Function used to filter request
        """
        if request.environ.get('HTTP_HOST'):
            url = request.environ['HTTP_HOST']
        else:
            url = request.environ['SERVER_NAME']
        if url.lower() == name.lower():
            return True

        return False
    return wrapped


def filter_ssl(request):
    """ Function used to filter request
    passes if request is https:
    """
    if request.scheme == 'https':
        return True
    else:
        return False

def filter_nossl(request):
    """ Function used to filter request
    passes if request is http:
    """
    if request.scheme == 'http':
        return True
    else:
        return False

def noop(*args, **kwargs):
    """ NO-OP function.
    Does nothing!
    """
    pass

#RESPONDER

class Responder(object):
    """Responder object
    This is passed to the functions.
    Main interface that functions use to interact with
    the Dillamond framework
    """
    
    def __init__(self, start_res, environ, mylookup, start_time):
        """ initialization
        
        Arguments:
        start_res: the wsgi "start response" function
        environ: the wsgi environ object
        mylookup: Mako lookup object used to find templates
        start_time: the when the request was recieved
        """
        self.start_response = start_res
        self.mylookup = mylookup
        self.req = Request(environ)
        self.environ = environ
        self.start_time = start_time
        self.res = Response()
    
    @property
    def post(self):
        """
        allows access to the POST variables
        """
        return self.req.str_POST
        
    def cookie(self, name, value = None, max_age=60*60*3, **kwargs):
        """cookie modifification
        
        Arguments:
        name: name of cookie
        value: value of the cookie
        max_age: max_age of cookie
        kwargs: additional argueents to the WebOb set_cookie function
        """
        if value == None:
            if name in self.req.cookies:
                return self.req.cookies[name]
        else:
            self.res.set_cookie(name, value, max_age=max_age, **kwargs)

    def view(self, viewname, **data):
        """Generate html response through a Mako template
        
        Arguments:
        viewname: name of the template to use
        data: data to be passed to the template
        """
        view = self.mylookup.get_template(viewname + '.mako').render(**data)
        
        self.res.status = 202
        self.res.content_type = 'text/html'
        self.res.content_length = len(view)
        
        self.start_response(self.res.status, self.res.headerlist)
        print(seconds_to_str(time.clock()-self.start_time))
        return view
    
    def json( self, data ):
        """Generate a JSON response
        
        Arguments:
        data: already jsonified string
        """
        self.res.status = 202
        self.res.content_type = 'application/json'
        self.res.charset = None
        self.res.content_length = None
        self.start_response(self.res.status, self.res.headerlist)
        print(seconds_to_str(time.clock()-self.start_time))
        return str(data)

    def text( self, data ):
        """Generate a text response
        
        Arguments:
        data: string
        """
        self.res.content_type = 'text/plain'
        self.res.status = 202
        self.res.body = data
        return self.res(self.environ, self.start_response)
    
    def redirect( self, url, code = 303):
        """Generate a redirect response
        
        Arguments
        url: url to redirect to
        code: http code to send
        """
        self.res.status = code
        self.res.location = url
        self.res.content_type = 'text/html'
        self.res.content_length = None
        self.start_response(self.res.status, self.res.headerlist)
        return ['']


def static_view_finder(viewname, **other):
    """Used to find the template used inside a function"""
    return viewname

#MAIN APP

class Dillamond:
    """Main Dillamond framework app"""
    def __init__(self, settings):
        """inialize app with settings"""
        self.mylookup = TemplateLookup(
            directories = [join(settings['root'],rpath) \
                for rpath in settings['view_paths']],
            output_encoding='utf-8')
        
        self.routes = []
        self._part_matcher = re.compile(r'{.*?}')
        self.error_handler = noop
    
    
    ###########################################################################
    # Decorators
    ###########################################################################
    
    def error(self, func):
        """specify the error handler"""
        self.error_handler = func
        return func

    def route(self, path, req = None, generate = False, **kwargs):
        """associate uris to functions
        
        Arguments:
        path: url matcher
        req: array of functions accepting environ and returning a bool
        generate: whether or not to generate a static file for that action
        **kwargs: additional arguments you want to used within your action
        """
        req = req or []
        
        parts = re.findall(self._part_matcher, path)
        parts_info = []
        for part in xrange(len(parts)):
            part_pair = parts[part][1:-1].split('=')
            parts_info.append(part_pair)
        
        
        def wrapped(func):
            """decorate the function and bind the route to it"""
            self.routes.append((path, {
                'regex': '^' + re.sub(self._part_matcher,'(.*?)',path) + '$',
                'function':func,
                'reqs':req,
                'kwargs':kwargs,
                'parts':parts_info,
                'generate':generate
                }))

            return func
        return wrapped
    
    def post(self, path, req = None, **kwargs):
        """wrapper around route to simplify specifying a POST method"""
        req = req or []
        return self.route(path,
        req=req+[filter_method(['POST'])],
        **kwargs)
    
    def get(self, path, req = None, **kwargs):
        """wrapper around route to simplify specifying a GET method"""
        req = req or []
        return self.route(path,
        req=req+[filter_method(['GET'])],
        **kwargs)

    ###########################################################################
    # Decorators
    ###########################################################################

    def wsgiapp(self):
        """generate wsgi application function"""
        def wrapped(environ, start_response):
            """wsgi application function"""
            start_time = time.clock()
            req = Request(environ)
            res = Responder(start_response, environ, self.mylookup, start_time)
            
            
            found_matches = None
            route = {}
            for reg, route in self.routes:
                found_matches = re.match(route['regex'], req.path)
                if found_matches and meetsreqs(req, route['reqs']):
                    break
            else:
                return ''
            bindings = route['kwargs']
            for part in route['parts']:
                if len(part) == 2:
                    bindings[part[0]] = part[1]
            for part in xrange(len(found_matches.groups())):
                if found_matches.group(part+1):
                    partname = route['parts'][part][0]
                    bindings[partname] = found_matches.group(part+1)

            return str(route['function'](res, **dict(bindings)))

        return wrapped
    
    def generatehtml(self, path):
        """generates static content based on path
        returns the generated string
        """
        for path, route in self.routes:
            if path == path:
                res = Responder(noop, {}, self.mylookup, 0)
                return route['function'](res)

    def genlist(self):
        """generates the list of generatable content"""
        out = []
        def responder():
            """empty responder object used to find the template name"""
            pass
        responder.view = static_view_finder
        for path, route in self.routes:
            if route['generate']:
                mako_template = route['function'](responder)+'.mako'
                filename = self.mylookup.get_template(mako_template).filename
                out.append((path, filename))
        return out

    def main(self, options):
        """commandline use
        used to generate files
        start a simple server
        """
        import sys
        import getopt
        import errno

        try:
            opts, args = getopt.getopt(options,
                "lt:gsp:", [
                    "port=",
                    "view=",
                    "list",
                    "static=",
                    "generate",
                    "server"])
        except getopt.GetoptError, err:
            print str(err)
            sys.exit(2)
        
        generate = False
        serve = False
        listfiles = False
        statichtml = 'static'
        view = False
        port = 8080
        
        for option, arg in opts:
            if option in ("-g","--generate"):
                generate = True
            elif option in ("-t","--static"):
                statichtml = arg
            elif option in ("--view"):
                view = arg
            elif option in ("-s","--serve"):
                serve = True
            elif option in ("-l","--list"):
                listfiles = True
            elif option in ("-p","--port"):
                port = int(arg)
            else:
                assert False, "unhandle option"
        
        if generate or listfiles:
            for path, filename in self.genlist():
                
                path = path.replace('?','')
                
                if view and view != path:
                    continue
                    
                if listfiles:
                    print path + " <= " + \
                        join(path[1:],'index.html') + ' <= ' + \
                        filename
                
                if generate:
                    path = join(statichtml , path[1:], 'index.html')
                    try:
                        makedirs(dirname(path))
                    except OSError as exc:
                        if exc.errno == errno.EEXIST:
                            pass
                        else: raise
                    print "Generating " + path
                    static_file = open(path,'w')
                    static_file.write(self.generatehtml(path))
                    static_file.close()
                
        if serve:
            print "Starting wsgi web server on port " + str(port)
            from wsgiref.simple_server import make_server
            server = make_server('', port, self.wsgiapp())
            server.serve_forever()