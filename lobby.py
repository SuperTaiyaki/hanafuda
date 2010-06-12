from mako.template import Template
import random
import cherrypy

class Session:
	def __init__(self):
		self.dict = {}
	
	def setattr(self, name, val):
		self.dict['name'] = val

	def getattr(self, name):
		return self.dict['name']

	def delattr(self, name):
		del self.dict['name']

f = open("namelist")
names = f.readlines()

def generate_name():
	return random.choice(names)


class Lobby:
	def __init__(self):
		self.tmpl = Template(filename="lobby.html")

	def initsession(self):
		cherrypy.session['name'] = generate_name()

	def getsession(self):
		if 'name' not in cherrypy.session:
			self.initsession()
		return {'name': cherrypy.session['name']}

	@cherrypy.expose
	def setname(self, name, **blah):
		cherrypy.session['name'] = name
		raise cherrypy.HTTPRedirect("/")

	@cherrypy.expose
	def default(self):
		sess = self.getsession()
		data = {'name': sess['name'], 'games': []}
		return self.tmpl.render(data = data)

root = Lobby()

cherrypy.quickstart(root, '/', 'cpconfig')


