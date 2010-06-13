from mako.template import Template
import random
import cherrypy
import server

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

def get_lobby():
	return root

class Lobby:
	def __init__(self):
		self.tmpl = Template(filename="lobby.html")
		self.waiting = {}

	def initsession(self):
		cherrypy.session['name'] = generate_name()

	def getsession(self):
		if 'name' not in cherrypy.session:
			self.initsession()
		return {'name': cherrypy.session['name']}

	@cherrypy.expose
	def setname(self, name, **blah):
		if 'random' in blah:
			cherrypy.session['name'] = generate_name()
		else:
			cherrypy.session['name'] = name
		raise cherrypy.HTTPRedirect("/")

	@cherrypy.expose
	def default(self):
		sess = self.getsession()
		data = {'name': sess['name'], 'games': []}
		for id,name in self.waiting.iteritems():
			data['games'].append({
				'name': name,
				'link': "/play/board?id=%i" % id})
		return self.tmpl.render(data = data)

	@cherrypy.expose
	def newgame(self):
		raise cherrypy.HTTPRedirect("/play/board?lobby=1")

	# For the game itself to report back
	def alert_create(self, id):
		# don't add players who go straight to the game screen
		if 'name' in cherrypy.session:
			self.waiting[id] = cherrypy.session['name']
	def alert_join(self, id):
		if id in self.waiting:
			del self.waiting[id]

root = Lobby()
server = server.Server(root)

root.play = server

cherrypy.quickstart(root, '/', 'cpconfig')


