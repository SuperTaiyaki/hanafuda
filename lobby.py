#!/usr/bin/python2

import random
import json

from mako.template import Template

import cherrypy
from ws4py.server.cherrypyserver import WebSocketPlugin, WebSocketTool
from ws4py.websocket import WebSocket

import server
import cards

class Match(object):
    template = Template(filename="settlement.html")
    def __init__(self, dispatcher):
        self.rounds = 2
        self.current_round = 0
        self.rules = None
        self.rate = 1
        self.scores = [(0, 0)] # List of (player1, player2)

        self.dispatcher = dispatcher
        self.next_dealer = -1
        # Names for now, IDs later (maybe)
        self.players = [None, None]

        self.game = server.Server(self)
        self.ids = self.dispatcher.register(self)

    def set_player(self, player, id):
        self.players[player] = id

    def end_round(self, winner, score):
        if winner == -1:
            self.scores.append((0, 0))
            self.next_dealer ^= 1
        else:
            self.scores.append(((winner^1)*score, winner*score))
            self.next_dealer = winner

    def next_round(self):
        # This breaks refresh continuity a bit - if the player refreshes before they enter the new game they won't be
        # able to come back
        self.dispatcher.delete(*self.ids)

        self.current_round += 1
        if self.current_round < self.rounds:
            self.game = server.Server(self, self.next_dealer)
            # Ask dispatcher for new IDs, return
            self.ids = self.dispatcher.register(self)
        else:
            self.ids = None, None
        return self.ids

    def get_ids(self):
        return self.ids

    def get_game(self):
        return self.game

    def get_scores(self):
        return map(sum, zip(*self.scores))

    def get_names(self):
        return self.players

    def show_results(self, player):
        scores = self.get_scores()
        diff = scores[player] - scores[player^1]

        return self.template.render(player = self.players[player],
                opp = self.players[player^1],
                self_score = scores[player],
                opp_score = scores[player^1],
                difference = diff,
                rate = self.rate,
                settlement = diff * self.rate)

class Dispatcher(object):

    def __init__(self):
        self.games = {}
        # No session in websockets
        self.results = {}

    def create_id(self):
        ti = 0
        while True:
            ti = random.randrange(11111111, 99999999)
            if ti not in self.games:
                break
        return ti

    def register(self, game):
        id1 = self.create_id()
        id2 = self.create_id()
        self.games[id1] = (game, 0)
        self.games[id2] = (game, 1)
        return (id1, id2)

    def delete(self, id1, id2):
        del self.games[id1]
        del self.games[id2]

    def find(self, id):
        if id in self.games:
            return self.games[id]
        return None, None

    def register_results(self, match):
        pass

f = open("namelist")
names = f.readlines()
f.close()
def generate_name():
    return random.choice(names)



def get_lobby():
    return root

class Lobby(object):
    board_tmpl = Template(filename="board.html")
    tmpl = Template(filename="lobby.html")
    list_tpl = Template(filename="gamelist.tpl")

    def __init__(self):
        self.waiting = {} # Need to make sure this doesn't build up...
        self.games = {}
        self.dispatcher = Dispatcher()


    def initsession(self):
        cherrypy.session['name'] = generate_name()

    def getsession(self):
        if 'name' not in cherrypy.session:
            self.initsession()
        return {'name': cherrypy.session['name']}

    def get_game(self):
        return cherrypy.session['game']

    @cherrypy.expose
    def set_name(self, name):
        cherrypy.session['name'] = name

    def get_player(self):
        return cherrypy.session['player']

    def gamelist_render(self):
        games = []
        for id,name in self.waiting.iteritems():
            games.append({
                'name': name,
                'link': "/join_game?id=%i" % id})
        return self.list_tpl.render(gamelist = games)

    def game_alert(self):
        gamelist = self.gamelist_render()
        data = json.dumps({'type': 'games', 'games': gamelist})
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

        # Match isn't stored. The game instances will hold references, and eventually it should get GCed.
        # Hopefully after recording a result to persistent storage
        match = Match(self.dispatcher)
        match.set_player(0, cherrypy.session['name'])
        (id1, id2) = match.get_ids()

        cherrypy.session['player'] = 0
        cherrypy.session['game_id'] = id1
        cherrypy.session['game'] = match.get_game()
        cherrypy.session['match'] = match

        if lobby and 'name' in cherrypy.session:
            self.waiting[id2] = cherrypy.session['name']
            self.game_alert()

        raise cherrypy.HTTPRedirect("/board")

    @cherrypy.expose
    def join_game(self, id):
        id = int(id)
 
        if id in self.waiting:
            del self.waiting[id]
            self.game_alert()
       
        match, player = self.dispatcher.find(id)
        if match is None:
            raise cherrypy.HTTPRedirect("/")

        match.set_player(player, cherrypy.session['name'])
        cherrypy.session['match'] = match
        cherrypy.session['game'] = match.get_game()
        cherrypy.session['game_id'] = id
        cherrypy.session['player'] = player
        # TODO: This needs to load match into the session too
        raise cherrypy.HTTPRedirect("/board")

    def connect_client(self, pipe, id):
        match, player = self.dispatcher.find(id)
        if match is None:
            return None
        game = match.get_game()
        game.connect(player, pipe)
        return game, player

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

    @cherrypy.expose
    def board(self):
        if 'game' not in cherrypy.session:
            return 'Error: No active game'
        deck = ['/img/' + x.image for x in cards.DECK]
        return self.board_tmpl.render(images = deck, gameid = cherrypy.session['game_id'])

    @cherrypy.expose
    def results(self):
        if 'match' not in cherrypy.session:
            raise cherrypy.HTTPRedirect("/")
        return cherrypy.session['match'].show_results(cherrypy.session['player'])

listeners = []

class EWS(WebSocket):
    def received_message(self, message):
        print("Received message")
        data = json.loads(message.data)
        if data['type'] == 'new_name':
            name = generate_name()
            print("Sending new name")
            self.send(json.dumps({'type': 'name', 'name': name}))

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
            print("Connected player %s" % self.player)
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
