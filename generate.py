import argparse
import wsgi

if __name__ == "__main__":
	parser = argparse.ArgumentParser(description='Generate some files.')
	parser.add_argument('type', action='store',
						nargs='*',
						default=['all'],
						help='Type of files to generate. css,html,js,all,rest')
	args = vars(parser.parse_args())['type']
	for arg in args:
		if arg not in ['all','css','js','html','rest']:
			print('wrong arguments!(css|html|js|all|rest)*')
			break
		if arg == 'all':
			args = ['all']
	else:
		print args
		for arg in args:
			if arg == 'all':
				wsgi.app.generateall()
			elif arg == 'css':
				wsgi.app.generateall(r'.*^\.scss$', False)
			elif arg == 'html':
				wsgi.app.generateall('a^', True)
			elif arg == 'js':
				wsgi.app.generateall(r'^.*\.(js|coffee)$', False)
			elif arg == 'rest':
				wsgi.app.generateall(r'^.*\.(?!(js|coffee|scss)$)', False)
		#wsgi.app.generateall()
