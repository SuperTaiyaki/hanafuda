#!/usr/bin/python2

import random
import json

from mako.template import Template
import cherrypy
from ws4py.server.cherrypyserver import WebSocketPlugin, WebSocketTool
from ws4py.websocket import WebSocket
from ws4py.exc import WebSocketException, StreamClosed

import server
import cards
import config
import storage

INITIAL_POINTS = 1000

root = None

class Player(object):
    def __init__(self):
        self.id = ""
        self.name = generate_name()
        self.points = INITIAL_POINTS

    def get_name(self):
        return self.name

    def set_name(self, name):
        self.name = name

    def get_id(self):
        return self.id

    def set_id(self, id):
        self.id = id

    def get_score(self):
        return self.points

    def add_score(self, points):
        # Minimise dodginess
        if self.id:
            self.load(self.id)
        self.points += points
        if self.id:
            self.save()
        return self.points

    def save(self):
        storage.save_user(self)

    def load(self, key):
        self.id, self.name, self.points = storage.load_user(key)

class Match(object):
    template = Template(filename="settlement.html")
    def __init__(self, dispatcher):
        self.rounds = 3
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
            # Winner will be 0 or 1
            self.scores.append(((winner^1)*score, winner*score))
            self.next_dealer = winner

    def abort_game(self):
        self.dispatcher.delete(*self.ids)
        # Should this be in here or in the dispatcher? Really, neither should have to know about the lobby
        get_lobby().cancel(self.ids)
        # Does deleting self.game deallocate?
        # And does this result in this object being deleted?
        # This should hopefully get swept up in the near future too
        del self.game # Circular reference

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

            # Do the settlement stuff
            scores = self.get_scores()
            diff = scores[0] - scores[1]
            self.players[0].add_score(diff*self.rate)
            self.players[1].add_score(diff*self.rate*-1)
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

        return self.template.render(player = self.players[player].get_name(),
                opp = self.players[player^1].get_name(),
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
        if id1 in self.games:
            del self.games[id1]
        if id2 in self.games:
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
        self.dispatcher = Dispatcher()
        self.listeners = []

    def get_game(self):
        return cherrypy.session['game']

    @cherrypy.expose
    def set_name(self, name):
        cherrypy.session['player'].set_name(name)

    def add_listener(self, socket):
        self.listeners.append(socket)

    def remove_listener(self, socket):
        self.listeners.remove(socket)
    def init_client(self, socket):
        gamelist = self.gamelist_render()
        data = json.dumps({'type': 'games', 'games': gamelist})
        socket.send(data)

    def get_player(self):
        return cherrypy.session['player']

    def gamelist_render(self):
        games = []
        for id,name in self.waiting.iteritems():
            games.append({
                'name': name,
                'link': "/join_game?id=%i" % id})
        ret = self.list_tpl.render(gamelist = games)
        return ret

    def game_alert(self):
        gamelist = self.gamelist_render()
        data = json.dumps({'type': 'games', 'games': gamelist})
        for l in self.listeners:
            try:
                l.send(data) if l else '' # Might have become None
            except Exception as e:
                self.listeners.remove(l)

    def cancel(self, ids):
        deleted = False
        for id in ids:
            # Yay thread-unsafety
            if id in self.waiting:
                del self.waiting[id]
                deleted = True
        if deleted:
            self.game_alert()

    @cherrypy.expose
    def default(self):
        if 'player' not in cherrypy.session:
            p = Player()
            cherrypy.session['player'] = p
        player = cherrypy.session['player']

        data = {'name': player.get_name(),
                'score': player.get_score(),
                'id': player.get_id()}

        return self.tmpl.render(data = data, socket = config.WEBSOCKET_URL)

    @cherrypy.expose
    def user(self, **args):
        if 'create' in args:
            cherrypy.session['player'].save()
            pass
        elif 'load' in args and args['user_id']:
            cherrypy.session['player'].load(args['user_id'])
            pass

        raise cherrypy.HTTPRedirect("/")

    @cherrypy.expose
    def new_game(self, id = None, lobby = True):
        if 'player' not in cherrypy.session:
            raise cherrypy.HTTPRedirect("/")

        # Match isn't stored. The game instances will hold references, and eventually it should get GCed.
        # Hopefully after recording a result to persistent storage
        match = Match(self.dispatcher)
        match.set_player(0, cherrypy.session['player'])
        (id1, id2) = match.get_ids()

        cherrypy.session['slot'] = 0
        cherrypy.session['game_id'] = id1
        cherrypy.session['game'] = match.get_game()
        cherrypy.session['match'] = match

        if lobby:
            self.waiting[id2] = cherrypy.session['player'].get_name()
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

        match.set_player(player, cherrypy.session['player'])
        cherrypy.session['match'] = match
        cherrypy.session['game'] = match.get_game()
        cherrypy.session['game_id'] = id
        cherrypy.session['slot'] = player
        # TODO: This needs to load match into the session too
        raise cherrypy.HTTPRedirect("/board")

    def connect_client(self, pipe, id):
        match, player = self.dispatcher.find(id)
        if match is None:
            return (None, None)
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
        return self.board_tmpl.render(images = deck, gameid = cherrypy.session['game_id'], socket =
                config.WEBSOCKET_URL, DEBUG = config.DEBUG)

    @cherrypy.expose
    def results(self):
        if 'match' not in cherrypy.session:
            raise cherrypy.HTTPRedirect("/")
        return cherrypy.session['match'].show_results(cherrypy.session['slot'])

class EWS(WebSocket):
    def received_message(self, message):
        data = json.loads(message.data)
        if data['type'] == 'new_name':
            name = generate_name()
            self.send(json.dumps({'type': 'name', 'name': name}))
        elif data['type'] == 'init':
            get_lobby().init_client(self)

    def opened(self):
        get_lobby().add_listener(self)
    def notify(self, data):
        self.send(json.dumps(data), False)
    def closed(self, code, reason = None):
        get_lobby().remove_listener(self)


class GameWS(WebSocket):
    def __init__(self, *args, **kwargs):
        super(GameWS, self).__init__(*args, **kwargs)
        self.game = None
    def received_message(self, message):
        print("MESSAGE: " + message.data)
        try:
            data = json.loads(message.data)
            if self.game is None:
                # Get a hold of the dispatcher
                self.game, self.player = get_lobby().connect_client(self, data['game_id'])
                print("Connected player %s" % self.player)
            else:
                self.game.message(self.player, data)
        except WebSocketException as e:
            pass
        except StreamClosed as e:
            self.closed(0)

    def opened(self):
        pass
    def closed(self, code, reason = None):
        if self.game is not None:
            self.game.disconnect(self.player, self)
            del self.game

class app2(object):
    tpl = Template(filename="gamelist.tpl")
    @cherrypy.expose
    def default(self, **crap):
        print("About to do test template render")
        print(Template("aaaaaaaaaaaaaaaaaaaa inside templaet").render())
        #ret = self.tpl.render(gamelist = [])
        #print(ret)
        return "Nothing to see here"


#root = app2()

def run():
    global root
    root = Lobby()
    WebSocketPlugin(cherrypy.engine).subscribe()
    cherrypy.tools.websocket = WebSocketTool() 

    # This doesn't work for some reason - 
    #wsconfig = {'/': {'tools.websocket.on': True,
    #        'tools.websocket.handler_cls': EWS}}
    #cherrypy.tree.mount(root, '/ws', wsconfig)

    cherrypy.server.shutdown_timeout = 0
    #cherrypy.quickstart(root, '/', 'cpconfig')

    cherrypy.server.socket_port = config.SERVER_PORT
    cherrypy.server.socket_host = config.SERVER_IP

    cherrypy.config.update({'tools.sessions.on': True,
        'tools.staticdir.root': config.ASSETS_PATH})
    cherrypy.quickstart(root, '/', {
        '/ws': {
            'tools.websocket.on': True,
            'tools.websocket.handler_cls': EWS},
        '/play_ws': {
            'tools.websocket.on': True,
            'tools.websocket.handler_cls': GameWS},

        '/scripts': {
            'tools.staticdir.on': True,
            'tools.staticdir.dir': 'scripts'},
        '/img': {
            'tools.staticdir.on': True,
            'tools.staticdir.dir': 'img'}})

if __name__ == "__main__":
    run()

