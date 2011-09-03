import sys
from os.path import abspath, dirname
from dillamond import Dillamond, filter_domain, filter_ssl, filter_nossl

#Settings
#   root:
#       root of the application, used to generate view_paths
#   view_paths:
#       set up where you want to place your mako templates.
#       array of paths relative to root
settings = {}
settings['root'] = abspath(dirname(__file__))
settings['view_paths'] = ['views/']

app = Dillamond(settings)

#################################################
# actions
#################################################

#specify the url path you want your action to run on.
# ex: mydomain.com/p/action1/

@app.route('/', generate=True)
@app.route('/fire', generate=True)
def index(res):
    return res.view('index')

@app.route('/c1/action1')
def action1(res):
    #return a mako template
    return res.view('view1')

@app.route('/json/action/?')
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

if __name__ == '__main__':
    app.main(sys.argv[1:])
