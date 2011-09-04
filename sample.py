""" Sample code for Dillamond usage
    Settings
    root:
        root of the APPLICATION, used to generate view_paths
    view_paths:
        set up where you want to place your mako templates.
        array of paths relative to root
"""
import sys
from os.path import abspath, dirname
from dillamond import Dillamond




# Create the APPLICATION
APP = Dillamond({'root': abspath(dirname(__file__)), 'view_paths': ['views/']})

#################################################
# actions
#################################################

# use the APP.route decorator to associate uris to functions
#   route(path, req = [], generate = False, **kwargs)
#       path: url matcher
#       req: array of functions accepting environ and returning a bool
#       generate: whether or not to generate a static file for that action
#       **kwargs: additional arguments you want to used within your action


@APP.route('/', generate=True)
@APP.route('/fire/?', generate=True)
def index(res):
    """ Matches / and /fire
    returns the Mako template index found the in view_paths
    """
    return res.view('index')

@APP.get('/c1/action1')
def action1(res):
    """
    return a mako template, passing viewdata into the mako template
    """
    return res.view('view1', viewdata=1234)

@APP.post('/json/action/?')
def multiaction(res):
    """ Matches a POST on /json/action and /json/action/
    return json
    """
    return res.json('{"status":"waffles!"}')

@APP.route('/json/control1/{action}/?')
def jsonaction(res, action):
    """ Matches /json/.*/ and /json/.*
    Anything matching this pattern will put the part
    matching {action} into the kwarg action
    """
    return res.json('{"status":"' + action + '"}')

@APP.error
@APP.route('{err}')
def error(res, err=''):
    """ Catchall for errors
    
    """
    return res.json('{"status":"error","error":' + err + '}')

#################################################
# wsgi APP
#################################################

# point your wsgi entry point here
#   ex: the variable 'APPLICATION' is now a wsgi APP
APPLICATION = APP.wsgiapp()

# you can run this file from commandline to invoke
# the static file generator or simple wsgi server
# see dillamond.Dillamond.main() for more details
if __name__ == '__main__':
    APP.main(sys.argv[1:])