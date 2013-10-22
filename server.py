import cherrypy
from mako.template import Template
from mako.runtime import Context
from StringIO import StringIO
import game
import cards
import json
import threading
import time
import random
import Queue

class GameFullException(Exception):
    pass

class SyncQueue():
    def __init__(self, timeout = 240.0):
        self.queue = []
        self.ready = threading.Event()
        self.q_lock = threading.Lock()
        self.queue_id = 100
        self.timeout = timeout
    def _lock(self):
        self.q_lock.acquire()
    def _unlock(self):
        # Should make sure the lock is held...
        self.q_lock.release()
    def ack(self, id):
        self._lock()
        if len(self.queue) and self.queue[0]['queue_id'] == int(id):
            del self.queue[0]
        if len(self.queue) == 0:
            self.ready.clear()
        self._unlock()
    def add(self, data):
        self._lock()
        data['queue_id'] = self.queue_id
        self.queue_id += 1
        self.queue.append(data)
        self.ready.set()
        self._unlock()
    def get(self):
        # Not strictly correct, the queue could empty between the time
        # the event triggers and the lock is acquired. If the wait
        # succeeds the lock should be acquired automatically to prevent
        # this... requires a different sort of event mechanism.

        # The correct mechanism will have a timeout and the ability to
        # wake multiple listeners at once. multiprocessing.lock() and
        # multiprocessing.semaphore() do have timeouts.

        # the lock releases and 
        self.ready.wait(self.timeout)
        self._lock()
        if len(self.queue) > 0:
            ret = self.queue[0]
            self._unlock()
            return self.queue[0]
        else:
            self._unlock()
            return {'timeout': True} # Don't want to use exceptions

class Server:

    def __init__(self, lobby):
        self.lobby = lobby
        self.updates = {}

    def create_game(self, options = None):
        # Err, no options for now...
        g = game.Game()
        g.new_game()
        return {'game': g, 'locks': self.init_queue()}

    # id, active game: join
    # no id active session: reuse
    # id, inactive game: create
    # no id, no session: create
    
    def getsession(self):
        # time.sleep(1.4)

        return (self.lobby.get_game()['game'], self.lobby.get_player())
#       id = int(id)
#
#       if 'game' in cherrypy.session and (id == -1 or id == cherrypy.session['game']):
#           g = self.games[cherrypy.session['game']]
#           player = cherrypy.session['player']
#           return (g, player)
#
#       if id == -1:
#           if 'game' in cherrypy.session:
#               id = cherrypy.session['game']
#           else:
#               id = self.create_id()
#
#       if id not in self.games:
#           # start a new game
#           g = game.Game(cards.create_deck(), 0)
#           self.games[id] = g
#           g.active_players = 1
#           player = 0
#           cherrypy.session['player'] = 0
#           cherrypy.session['game'] = id
#           self.init_update()
#           self.lobby.alert_create(id)
#           print("Created new game", id)
#           return (g, player)
#       # Try to join the game #id
#       if self.games[id] and self.games[id].active_players < 2:
#           player = self.games[id].active_players
#           cherrypy.session['player'] = player
#           cherrypy.session['game'] = id 
#           self.games[id].active_players = player + 1
#           gr = self.games[id]
#           print("Joined game ", id)
#           self.lobby.alert_join(id)
#
#           upd = {'start_game': True}
#           if gr.get_player() != player:
#               upd['active'] = True
#           self.set_update(upd)
#           return (gr, player)
#
#       raise GameFullException("Game is full")
    
    def init_queue(self):
        return [SyncQueue(), SyncQueue()]

    def get_queue(self, own = True):
        sess = self.lobby.get_game()
        player = self.lobby.get_player()

        if not own:
            player = (player + 1) % 2
        return sess['locks'][player]

    def watch_update(self):
        q = self.get_queue(True)
        return q.get()
    def set_update(self, upd):
        q = self.get_queue(False)
        q.add(upd)
    def ack_update(self, key):
        q = self.get_queue(True)
        q.ack(key)

    @cherrypy.expose
    def init(self):
        (g, player) = self.getsession()

        if player == 1:
            upd = {'start_game': True}
            if g.get_player() != player:
                upd['active'] = True
            self.set_update(upd)

        ret = {}
        ret['hand'] = []
        for i, c in enumerate(g.get_hand(player)):
            ret['hand'].append(self.update_card(c))

        ret['field'] = []
        for c in g.get_field():
            ret['field'].append(self.update_card(c))
        
        ret['captures_player'] = []
        for c in g.get_captures(player):
            ret['captures_player'].append(self.update_card(c))

        ret['captures_opp'] = []
        for c in g.get_captures((player + 1) % 2):
            ret['captures_opp'].append(self.update_card(c))

        ret['opp_hand'] = []
        for c in g.get_hand((player + 1) % 2):
            if c == None:
                ret['opp_hand'].append(i)

        ret['gamelink'] = self.lobby.join_link()

        if g.get_player() == player:
            ret['active'] = True
        if player == 1:
            ret['start_game'] = True

        # This should set up deckselect or koikoi too. maybe.

        return json.dumps(ret)

    @cherrypy.expose
    def koikoi(self):
        (g, player) = self.getsession()

        # Check to make sure this is legal

        if not g.koikoi():
            return # Empty return may crash the client, but it
            # shouldn't be doing this anyway

        # Trip a mostly empty update to make the turns switch
        # Should also show the opponent what happened
        alert  = "Opponent did not koikoi.<br />"
        alert += "Multiplier is now %ix" % g.multiplier

        self.set_update({'active': True, 'alert': alert,
            'multiplier': g.multiplier})
        return json.dumps({'multiplier': g.multiplier})

    @cherrypy.expose
    def endgame(self, arg):
        (g, player) = self.getsession()
        
        # Check to make sure this is legal

        if not g.end(player):
            return

        # Save the results and delete the game to save memory
        ret = {'results': self.score(g, player)}
        p2 = 1 if player == 0 else 0
        oupd = {'results': self.score(g, p2)}
        self.reset_game()
        self.set_update(oupd)
        return json.dumps(ret)


    # Create a card representation the client can use
    def update_card(self,card):
        ret = {}
        if (card == None):
            ret['img'] = "/img/empty.gif"
            ret['suit'] = "empty"
            ret['rank'] = -1
        else:
            data = cards.DECK[card]
            ret['img'] = "/img/" + data.image
            ret['suit'] = "mon" + str(data.suit)
            ret['rank'] = data.rank
        return ret

    @cherrypy.expose
    def place(self, hand, field):
        (g, player) = self.getsession()
        p2 = 0 if player == 1 else 1
        # sanity checks
        try:
            upd = g.play(player, int(hand), int(field))
        except game.GameError as e:
            print("Game exception...")
            return json.dumps({'error': e.__repr__()})
    
        events_self = []
        events_other = []

        events_self.append(('capture', g.self_captures))
        events_self.append(('draw', g.deck_draw))

        events_other.append(('play', 0)) # Need to pull out the card value somehow...
        events_other.append(('capture', g.self_captures))
        events_other.append(('draw', g.deck_draw))

        if g.state == game.States.DRAW_MATCH:
            events_self.append(('draw_match',))
            events_self.append(('alert',"Deck card matches multiple cards on the field. Select one."))
            events_other.append(('draw_match',))
        elif g.state == game.States.KOIKOI:
            events_self.append(('koikoi'))
        elif g.state == game.States.FINISHED:
            pass # Uhh...
        else: # Other player
            events_self.append(('turn_end',))
            events_other.append(('turn_start',))

        self.set_update(events_other)
        return json.dumps(events_self)


        # Player update will be hand, field, maybe deck, captures
        # Opponent update will be opponent, field, opponent captures

        # Take the state changes from the game and form the AJAX request
        
        upd['type'] = "play"

        upd['handcard'] = self.update_card(upd['handcard'])
        upd['deckcard'] = self.update_card(upd['deckcard'])
        upd['gameid'] = cherrypy.session['game_id']
    
        # updates to both sides

        ret = upd # are these linked or copied? hrm... 
        oupd = upd.copy()

        ret['player'] = True
        oupd['player'] = False

        if upd['deck'] == -1: # Deck select
            ret['alert'] = "Deck card matches multiple cards on the field. Select one."

        # This is actually to indicate whether to unlock the field - the
        # update data is for the other player
        if g.get_player() != player:
            oupd['active'] = True
        else:
            ret['active'] = True

        if upd['koikoi']:
            ret['koikoi'] = True
            scores = g.get_score(player)
            ret['yaku'] = scores.get_names()
            ret['score'] = scores.get_score()
            oupd['opp_score'] = ret['score']
            oupd['koikoi'] = False # Later need to replace this with
            oupd['alert'] = "Opponent deciding whether to koikoi"
            oupd['multiplier'] = ret['multiplier'] = g.multiplier

        # If the game is over also bring up the results page
        if g.winner != None:
            ret['results'] = self.score(g, player)
            oupd['results'] = self.score(g, p2)
            self.reset_game();

        # Trigger the update for the other player
        print("Player: ", ret)
        print("Opponent: ", oupd)
        self.set_update(oupd)

        return json.dumps(ret)

    @cherrypy.expose # testing only
    def score(self, g, player):
        tmpl = Template(filename="results.html")
        ctx = {}
        ctx['result'] = "Win" if g.winner == player else "Lose"
        scores = g.get_score(g.winner)
        ctx['score'] = scores.get_score()
        ctx['multiplier'] = g.multiplier
        ctx['finalScore'] = g.multiplier * ctx['score']
        ctx['hands'] = scores.get_names()
        print ctx
        return tmpl.render(c = ctx)

    @cherrypy.expose
    def update(self, key):
        # Polling method, let the client know if anything can be updated
        self.ack_update(key)
        upd = self.watch_update()
        return json.dumps(upd)

    @cherrypy.expose
    def board(self, id = -1, lobby = False):
        # Initiate the session if necessary
        try:
            (g, player) = self.getsession()
        except GameFullException as e:
            return "Error: Game is full"
        deck = map(lambda x: "/img/" + x.image, cards.DECK)
        tmpl = Template(filename="board.html")
        return tmpl.render(images = deck)

    @cherrypy.expose
    def debug(self, args):
        (g, player) = self.getsession()
        if args == "win":
            g.winner = player
            return "Set winner"
        elif args == "koikoi":
            c = cards.Card("jan1.gif", 0)
            c.attrs['bright'] = True
            c.rank = 20
            l = len(filter(lambda x: 'bright' in x.attrs,
                g.captures[player]))
            g.captures[player].extend([c] * (5 - l))
            return "Next play will koikoi"
        elif args == "cardselect":
            g.field[0] = cards.Card("jan1.gif", 0)
            g.field[1] = cards.Card("jan2.gif", 0)
            g.cards.append(cards.Card("jan3.gif", 0))
            return "Next play will require card select (maybe)"
        elif args == "take3":
            g.field[0] = cards.Card("jan1.gif", 0)
            g.field[1] = cards.Card("jan2.gif", 0)
            g.field[2] = cards.Card("jan3.gif", 0)
            g.hands[player][0] = cards.Card("jan4.gif", 0)
            return "Next play will take 3 cards from the field"
        elif args == "status":
            output = "Field: "

            def img(card):
                if card:
                    return "<img src=\"/img/" + c.image + "\" />"
                else:
                    return "<img src=\"/img/empty.gif\" />"

            for c in g.field:
                output += img(c)
            output += "<br />P1 hand: "
            for c in g.hands[0]:
                output += img(c)
            output += "<br />P2 hand: "
            for c in g.hands[1]:
                output += img(c)
            return output
        elif args == "showcards":
            deck = cards.create_deck()
            buf = ""
            for card in deck:
                buf += "<img src=\"/img/%s\" />Suit: %i Rank: %i<br />\n" % (card.image, card.suit, card.rank)
            return buf
        else:
            return "Invalid argument"



    # Summary screen after the game is over
    @cherrypy.expose
    def scores(self):
        (g, player) = self.getsession()
        tmpl = Template(filename="scores.html")
        won = False
        if g.winner == player:
            won = True

#       return tmpl.render(

#root = Server()

#cherrypy.quickstart(root, '/', 'cpconfig')


