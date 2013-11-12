#!/usr/bin/python2

import random
import json

from mako.template import Template

import cherrypy
from ws4py.server.cherrypyserver import WebSocketPlugin, WebSocketTool
from ws4py.websocket import WebSocket

import server
import cards


class GameManager(object):
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


class SessionManager(object):
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

class Lobby(object):
    board_tmpl = Template(filename="board.html")
    tmpl = Template(filename="lobby.html")
    list_tpl = Template(filename="gamelist.tpl")

    def __init__(self):
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

    def gamelist_render(self):
        games = []
        for id,name in self.waiting.iteritems():
            games.append({
                'name': name,
                'link': "/join_game?id=%i" % id})
        return self.list_tpl.render(gamelist = games)

    def game_alert(self):
        gamelist = self.gamelist_render()
        for l in listeners:
            l.send(gamelist) if l else '' # Might have become None

    @cherrypy.expose
    def default(self):
        sess = self.getsession()
        data = {'name': sess['name']}
        data['gamelist'] = self.gamelist_render()
        return self.tmpl.render(data = data)

    def create_game(self):
        id1 = self.create_id()
        id2 = self.create_id()

        g = server.Server(self, (id1, id2))
        self.games[id1] = (g, 0)
        self.games[id2] = (g, 1)

        return (id1, id2, g)

    @cherrypy.expose
    def new_game(self, id = None, lobby = True):

        (id1, id2, g) = self.create_game()

        cherrypy.session['game'] = g
        cherrypy.session['player'] = 0
        cherrypy.session['game_id'] = id1

        if lobby and 'name' in cherrypy.session:
            self.waiting[id2] = cherrypy.session['name']
            self.game_alert()

        raise cherrypy.HTTPRedirect("/board")

    def end_game(self, id):
        del self.games[id[0]]
        del self.games[id[1]]

    @cherrypy.expose
    def join_game(self, id):
        id = int(id)
        if id in self.waiting:
            del self.waiting[id]
            self.game_alert()
        if id not in self.games:
            raise cherrypy.HTTPRedirect("/")
        game, player = self.games[id]
        cherrypy.session['game'] = game
        cherrypy.session['game_id'] = id
        raise cherrypy.HTTPRedirect("/board")

    def connect_client(self, pipe, id):
        if id not in self.games:
            return None
        game = self.games[id][0]
        game.connect(self.games[id][1], pipe)
        return self.games[id]

    @cherrypy.expose
    def ws(self):
        pass
        # handler = cherrypy.request.ws_handler

    @cherrypy.expose
    def play_ws(self):
        pass
    
    # Return the link to join the game
    def join_link(self, gameid):
        return cherrypy.request.base + "/join_game?id=%i" % gameid

    def create_id(self):
        ti = 0
        while True:
            ti = random.randrange(11111111, 99999999)
            if ti not in self.games:
                break
        return ti

    @cherrypy.expose
    def board(self):
        if 'game' not in cherrypy.session:
            return 'Error: No active game'
        deck = ['/img/' + x.image for x in cards.DECK]
        return self.board_tmpl.render(images = deck, gameid = cherrypy.session['game_id'])

listeners = []

class EWS(WebSocket):
    def received_message(self, message):
        print("Received message")
        self.send(message.data, message.is_binary)
    def opened(self):
        print("WS Connection opened")
        listeners.append(self)
    def notify(self, data):
        self.send(json.dumps(data), False)
        print("Added listener")
    def closed(self, code, reason = None):
        listeners.remove(self)
        print("Removed listener")


class GameWS(WebSocket):
    def __init__(self, *args, **kwargs):
        super(GameWS, self).__init__(*args, **kwargs)
        self.game = None
    def received_message(self, message):
        print("MESSAGE: " + message.data)
        data = json.loads(message.data)
        if self.game is None:
            # Get a hold of the dispatcher
            self.game, self.player = get_lobby().connect_client(self, data['game_id'])
        else:
            self.game.message(self.player, data)
    def opened(self):
        pass
    def closed(self, code, reason = None):
        pass


root = Lobby()

WebSocketPlugin(cherrypy.engine).subscribe()
cherrypy.tools.websocket = WebSocketTool() 

# This doesn't work for some reason - 
#wsconfig = {'/': {'tools.websocket.on': True,
#        'tools.websocket.handler_cls': EWS}}
#cherrypy.tree.mount(root, '/ws', wsconfig)

cherrypy.server.shutdown_timeout = 0
#cherrypy.quickstart(root, '/', 'cpconfig')

cherrypy.config.update({'tools.sessions.on': True,
    'tool.staticdir.root': '/home/rek/code/hanafuda'})
cherrypy.quickstart(root, '/', {
    '/ws': {
        'tools.websocket.on': True,
        'tools.websocket.handler_cls': EWS},
    '/play_ws': {
        'tools.websocket.on': True,
        'tools.websocket.handler_cls': GameWS},

    '/scripts': {
        'tools.staticdir.on': True,
        'tools.staticdir.dir': '/home/rek/code/hanafuda/scripts'},
    '/img': {
        'tools.staticdir.on': True,
        'tools.staticdir.dir': '/home/rek/code/hanafuda/img'}})
# Websocket weirdness... reassemble this correctly later
