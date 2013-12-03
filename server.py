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

import config

from ws4py.server.cherrypyserver import WebSocketPlugin, WebSocketTool
from ws4py.websocket import WebSocket

class GameFullException(Exception):
    pass

# Probably not an appropriate name any more...
# Layer between the Game instance and the frontend JS side
class Server(object):
    results_tmpl = Template(filename="results.html")

    def __init__(self, dispatcher, dealer = -1, options = None):
        self.game = game.Game()
        self.game.new_game(dealer)
        self.channels = [None, None] # WebSocket instances
        self.joined = [False, False]
        self.started = False
        self.dispatcher = dispatcher

    def send_messages(self, player, own, other):
        self.channels[player].send(own)
        self.channels[player^1].send(other)

    # Build the initial state to the JS, to build the board
    # Also used on reconnect
    @cherrypy.expose
    def render_state(self, player):

        scores = self.dispatcher.get_scores()
        ret = {'player': player, 'own_score': scores[player], 'opp_score': scores[player^1]}

        ret['hand'] = [self.update_card(c) for c in self.game.get_hand(player)]

        ret['field'] = [self.update_card(c) for c in self.game.get_field()]

        ret['captures_player'] = [self.update_card(c) for c in self.game.get_captures(player)]
        for c in self.game.get_captures(player):
            ret['captures_player'].append(self.update_card(c))

        ret['captures_opp'] = [self.update_card(c) for c in self.game.get_captures(player^1)]

        ret['opp_hand'] = [None for c in self.game.get_hand(player^1)]

        if self.game.get_player() == player:
            ret['active'] = True

        ret['game_started'] = self.started

        # self.joined[player] = True
        return ret
        # This should set up deckselect or koikoi too. maybe.

    def koikoi(self, player, state):

        # Check to make sure this is legal

        if self.game.state != game.States.KOIKOI:
            return # Empty return may crash the client, but it
            # shouldn't be doing this anyway

        self.game.koikoi(player, state)

        # Trip a mostly empty update to make the turns switch
        # Should also show the opponent what happened
        # alert  = "Opponent did not koikoi.<br />"
        # alert += "Multiplier is now %ix" % g.multiplier

        events_self = []
        events_other = []
        if self.game.state == game.States.FINISHED:
            (evs, evo) = self.end_game(player)
            events_self.extend(evs)
            events_other.extend(evo)
        else:
            events_self.append({'type': 'turn_end'})
            events_other.append({'type': 'start_turn'})
            events_other.append({'type': 'alert', 'text': 'Koi'})
        self.send_messages(player, json.dumps(events_self), json.dumps(events_other))
        self.game.clear_events() # Uhh... without reading them. 

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

    def end_game(self, player):
        events_self = []
        events_other = []

        score = 0 if self.game.winner == -1 else self.game.get_score(self.game.winner).get_score() * self.game.multiplier[self.game.winner]
        # Pull out the numerical score, don't need the rest of the data
        self.dispatcher.end_round(self.game.winner, score)
        next_ids = self.dispatcher.next_round()

        results_1 = self.score(self.game, player, next_ids[player])
        results_2 = self.score(self.game, player^1, next_ids[player^1])
        events_self.append({'type': 'results', 'data': results_1})
        events_other.append({'type': 'results', 'data': results_2})

        event = {'type': 'game_end'}
        events_self.append(event)
        events_other.append(event)

        return (events_self, events_other)

    @cherrypy.expose
    def place(self, player, hand, field):

        p2 = player ^ 1
        # sanity checks
        try:
            if hand == -1:
                upd = self.game.draw_match(player, field)
            else:
                upd = self.game.play_card(player, hand, field)
        except game.GameError as e:
            print("Game exception...")
            print(e.__repr__())
            raise

        events_self = []
        events_other = []

        print("Player: %s" % player)
        for event in self.game.get_events():
            print(event)
            if event['card'] is not None:
                event['card'] = self.update_card(event['card'])
            events_self.append((event))
            if event['type'][0] != ":": # or player == event['player']:
                events_other.append((event))
            else:
                print("Excluding message from player %s" % player)

        self.game.clear_events()

        if self.game.state == game.States.DRAW_MATCH:
            events_self.append({'type': 'alert','text': "Deck card matches multiple cards on the field. Select one."})
        elif self.game.state == game.States.KOIKOI:
            events_self.append({'type': ':koikoi', 'yaku': self.game.get_yaku(player)})
        elif self.game.state == game.States.FINISHED:
            (evs, evo) = self.end_game(player)
            events_self.extend(evs)
            events_other.extend(evo)
        else: # Other player, state is PLAY
            events_self.append({'type': 'turn_end'})
            events_other.append({'type': 'start_turn'})

        self.send_messages(player, json.dumps(events_self), json.dumps(events_other))

    @cherrypy.expose # testing only
    def score(self, g, player, next_game):
        ctx = {}
        if g.winner == -1:
            ctx['result'] = "Draw"
            ctx['score'] = 0
            ctx['multiplier'] = 0
            ctx['finalScore'] = 0
            ctx['hands'] = ''
        else:
            ctx['result'] = "Win" if g.winner == player else "Lose"
            scores = g.get_score(g.winner)
            ctx['score'] = scores.get_score()
            ctx['multiplier'] = g.get_multiplier(g.winner)
            ctx['finalScore'] = g.multiplier[g.winner] * ctx['score']
            ctx['hands'] = scores.get_names()

        if next_game:
            ctx['next_game'] = next_game
        # print ctx
        return self.results_tmpl.render(c = ctx)


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

    def connect(self, player, client):
        self.channels[player] = client
        board_state = self.render_state(player)
        print(board_state)
        board_state['type'] = 'init'
        client.send(json.dumps([board_state]))

        # Both players connected, get started
        if all(self.channels) and not self.started:
            data = json.dumps([{'type': 'game_start'}])
            self.send_messages(0, data, data)
            self.started = True

    def disconnect(self, player, client):
        print("Client disconnected")
        # TODO: This will happen at the end of a game too
        self.channels[player] = None
        if not any(self.channels) and self.game.state != game.States.FINISHED:
            self.dispatcher.abort_game()

    def message(self, player, data):
        try:
            if data['type'] == 'place':
                self.place(player, int(data['hand']), int(data['field']))
            elif data['type'] == 'koikoi':
                self.koikoi(player, True)
            elif data['type'] == 'end_game':
                self.koikoi(player, False)

            if not config.DEBUG:
                return
            # Debugging only!
            elif data['type'] == 'win':
                # Instant hanamizake
                self.game.captures[player].extend([8, 32])
            elif data['type'] == 'draw':
                # Doesn't work so well... probably need to do this every turn
                del self.game.captures[player][:]
                self.game.scores[player].update([])
        except game.GameError as e:
            # Should probably try to HTML escape this...
            message = json.dumps([{'type': 'error', 'text': 
"""
An error has occurred. You may be able to continue this game by refreshing the page.<br />
Error: %s
""" % str(e)}])
            self.channels[player].send(message)
            # Might have to disconnect the socket here... error recovery basically doesn't work
