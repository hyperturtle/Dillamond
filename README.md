#Dillamond

##Features

- Simple WSGI framework built on top of webob and mako
- Less than 500 lines of code
- Includes a development WSGI server using wsgiref
- Decorator based uri to function mappings
- Static generation of files

##Dependancies

- [Mako](http://www.makotemplates.org/) -- `easy_install Mako`
- [WebOb](http://webob.org/) -- `easy_install webob`


##Installation
    cp dillamond.py /your_website_path/

##Usage

    #Create the application
    app = Dillamond({'root': abspath(dirname(__file__)), 'view_paths': ['views/']})
    
    #Decorate functions to accept on uri matchers
    #app.route(path, req = [], generate = False, **kwargs)
    
    @app.route('/') #path matching '' and '/'
    def index(res):
        return res.view('index') #return the template 'index.mako' in view_paths
    
    @app.route('/action/?') #matches '/action' and '/action/'
    def jsonaction(res,action):
        return res.json('{"status":"okay"}')

###Start development server on port 8080
    python sample.py -s -p 8080

###List files in the static generation list
    python sample.py -l

###Generating static files
    python sample.py -g

