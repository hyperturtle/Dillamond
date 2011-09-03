import sys
from os.path import abspath, dirname
from dillamond import Dillamond


#Settings
#   root:
#       root of the application, used to generate view_paths
#   view_paths:
#       set up where you want to place your mako templates.
#       array of paths relative to root
settings = {}
settings['root'] = abspath(dirname(__file__))
settings['view_paths'] = ['views/']

#Create the application
app = Dillamond(settings)

#################################################
# actions
#################################################

#use the app.route decorator to associate uris to functions
#   route(path, req = [], generate = False, **kwargs)
#       path: url matcher
#       req: array of functions accepting environ and returning a bool
#       generate: whether or not to generate a static file for that action
#       **kwarhs: additional arguments you want to used within your action

#   post,get,getnpost(...)
#       helper decorators that wrap route()

@app.route('/', generate=True)
@app.route('/fire', generate=True)
def index(res):
    return res.view('index')

@app.get('/c1/action1')
def action1(res):
    #return a mako template
    return res.view('view1',viewdata=1234)

@app.post('/json/action/?')
def multiaction(res):
    #return a mako template
    return res.json('{"status":"waffles!"}')

@app.route('/json/{action}/?')
def jsonaction(res,action):
    #return a mako template
    return res.json('{"status":"' + action + '"}')

@app.error
@app.route('{error}')
def error(res, error=''):
    return res.json('{"status":"error"}')

#################################################
# wsgi app
#################################################

#point your wsgi entry point here
# ex: the variable 'application' is now a wsgi app
application = app.wsgiapp()

#you can run this file from commandline to invoke the static file generator or simple wsgi server
#see dillamond.Dillamond.main() for more details
if __name__ == '__main__':
    app.main(sys.argv[1:])