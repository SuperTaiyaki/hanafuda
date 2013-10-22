from mako.template import Template
import random
import cherrypy
import server


class GameManager:
    """Handles a single set of rounds """
    # Options:
    # rounds: 3, 6, 12
    # custom rules to be specified later
    def __init__(self, options):
        if 'rounds' in options:
            self.rounds = options['rounds']
        else:
            self.rounds = 12
        self.scores = [0, 0]
        # Randomize the dealer
        # Spawn the current game
    
    def addScore(self, player, score):
        self.scores[player] += score
        # Spawn the new game with the correct dealer


class SessionManager:
    """ Handles individual users and games, times them out due to
    inactivity.
    """
    def __init__(self):
        self.sessions = []
        cherrypy.session['manager'] = self # The only part clients
        # should touch


    def new(self, name = None):
        if name == None:
            name = self.generate_name()
        sess = {'game': None,
                'lastupdate': 0}
        self.sessions.append(sess)
    
    def create_game(self, options):
        g = GameManager(options)
        cherrypy.session['game'] = g

    def get_session(self, id = -1):
        # Error checking, whatever else...
        # Delay the culling
        return cherrypy.session['game'], cherrypy.session['player']

def get_lobby():
    return root

class Lobby:
    def __init__(self):
        self.tmpl = Template(filename="lobby.html")
        self.waiting = {} # Need to make sure this doesn't build up...
        self.games = {}
        f = open("namelist")
        self.names = f.readlines()
        f.close()

    def generate_name(self):
        return random.choice(self.names)
    
    def initsession(self):
        cherrypy.session['name'] = self.generate_name()

    def getsession(self):
        if 'name' not in cherrypy.session:
            self.initsession()
        return {'name': cherrypy.session['name']}

    def get_game(self):
        return cherrypy.session['game']
    
    def get_player(self):
        return cherrypy.session['player']

    @cherrypy.expose
    def setname(self, name, **blah):
        if 'random' in blah:
            cherrypy.session['name'] = self.generate_name()
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
                'link': "/join_game?id=%i" % id})
        return self.tmpl.render(data = data)

    @cherrypy.expose
    def new_game(self, id = None, lobby = True):
        g = server.create_game() # global var
        cherrypy.session['game'] = g
        cherrypy.session['player'] = 0
        if id == None or id in self.games:
            id = self.create_id()
        else:
            id = int(id)
        cherrypy.session['game_id'] = id
        if lobby and 'name' in cherrypy.session:
            self.waiting[id] = cherrypy.session['name']
        self.games[id] = g
        raise cherrypy.HTTPRedirect("/play/board")

    @cherrypy.expose
    def join_game(self, id):
        id = int(id)
        if id in self.waiting:
            del self.waiting[id]
        if id not in self.games:
            raise cherrypy.HTTPRedirect("/")
        cherrypy.session['game'] = self.games[id]
        cherrypy.session['player'] = 1
        # should be checking g.active_players
        # in case of a new round both players will join
        cherrypy.session['game_id'] = id
        raise cherrypy.HTTPRedirect("/play/board")
    
    # Return the link to join the game
    def join_link(self):
        return cherrypy.request.base + "/join_game?id=%i" % cherrypy.session['game_id']

    def create_id(self):
        ti = 0
        while True:
            ti = random.randrange(11111111, 99999999)
            if ti not in self.games:
                break
        return ti

root = Lobby()
server = server.Server(root)

root.play = server

cherrypy.server.shutdown_timeout = 10
cherrypy.quickstart(root, '/', 'cpconfig')


