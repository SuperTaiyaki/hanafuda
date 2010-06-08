import cherrypy
from mako.template import Template
import game
import cards
import json
import threading

class Server:

	def __init__(self):
		deck = cards.create_deck()
		self.game = game.Game(deck, 0)
		self.games = []
		self.updates = {}

	# Test function that spits out a list of images
	@cherrypy.expose
	def showcards(self):
		deck = cards.create_deck()
		buf = ""
		for card in deck:
			buf += "<img src=\"img/%s\" />Suit: %i Rank: %i<br />\n" % (card.image, card.suit, card.rank)
		return buf

	# Bunch of AJAX functions
	def getsession(self):
		if 'player' not in cherrypy.session:
			# find a game?
			for i,g in enumerate(self.games):
				if g.active_players < 2:
					cherrypy.session['player'] = 1
					cherrypy.session['game'] = i
					player = 1
					gr = g
					g.active_players = 2
					return (gr, player)

			# start a new game
			g = game.Game(cards.create_deck(), 0)
			self.games.append(g)
			g.active_players = 1
			player = 0
			cherrypy.session['player'] = 0
			cherrypy.session['game'] = len(self.games) - 1 # is this
			self.init_update()
			# breaking any assumptions?
		else:
			g = self.games[cherrypy.session['game']]
			player = cherrypy.session['player']

		return (g, player)

	# Threaded functions for moving updates between players
	# Note that watch and update operate on alternate players

	def init_update(self):
		if 'game' not in cherrypy.session:
			raise Exception("Trying initialize get updates with no game")
		id = cherrypy.session['game'] * 2
		self.updates[id] = {'lock': threading.Lock(), 'value': {}}
		self.updates[id+1] = {'lock': threading.Lock(), 'value': {}}
		self.updates[id]['lock'].acquire(False)
		self.updates[id+1]['lock'].acquire(False)

	def watch_update(self):
		if 'game' not in cherrypy.session:
			raise Exception("Trying to get updates with no game")
		print("Watching updates for player ",
				cherrypy.session['player'])
		id = cherrypy.session['game'] * 2 + cherrypy.session['player']
		self.updates[id]['lock'].acquire()
		# When that releases there's an update ready to go
		val = self.updates[id]['value']
		self.updates[id]['value'] = {}
		return val

	def set_update(self, upd):
		if 'game' not in cherrypy.session:
			raise Exception("Trying to get updates with no game")
		p = 0 if cherrypy.session['player'] else 1
		id = cherrypy.session['game'] * 2 + p

		self.updates[id]['value'].update(upd)
		if not self.updates[id]['lock'].acquire(False):
			self.updates[id]['lock'].release()
		else:
			print("Error: Tried to release lock, but not held")

		return

	@cherrypy.expose
	def ajax(self, arg):
		(g, player) = self.getsession()

		if arg == "init":
			ret = {}
			ret['hand'] = []
			for i, c in enumerate(g.get_hand(player)):
				ret['hand'].append(self.update_card(i, c))

			ret['field'] = []
			for c in g.get_field():
				ret['field'].append(self.update_card(i, c))
			
			if g.get_player() == player:
				ret['active'] = True

			ret['gameid'] = cherrypy.session['game']

			return json.dumps(ret)

	def update_card(self, idx, card):
		ret = {'id': idx}
		if (card == None):
			ret['img'] = "img/empty.gif"
			ret['suit'] = -1
		else:
			ret['img'] = "img/" + card.image
			ret['suit'] = "mon" + str(card.suit)
		return ret


	@cherrypy.expose
	def place(self, hand, field):
		(g, player) = self.getsession()
		# sanity checks
		try:
			upd = g.play(player, int(hand), int(field))
		except game.GameError as e:
			return json.dumps({'error': e.__repr__()})
		# Player update will be hand, field, maybe deck, captures
		# Opponent update will be opponent, field, opponent captures

		ret = {} # local update
		oupd = {} # other player's update
		if len(upd['field']) > 0:
			ret['field'] = []
			for c in upd['field']:
				ret['field'].append(self.update_card(c,
					g.get_field()[c]))
			oupd['field'] = ret['field']
		if len(upd['hand']) > 0:
			ret['hand'] = []
			for c in upd['hand']:
				ret['hand'].append(c)
				oupd['opp_hand'] = ret['hand']
		if len(upd['caps']) > 0:
			ret['caps_self'] = []
			for c in upd['caps']:
				ret['caps_self'].append({'img':"img/"+c.image})
			oupd['caps_opp'] = ret['caps_self']
		if upd['deck']:
			ret['deck'] = self.update_card(0, g.get_deck_top())
			oupd['deck'] = ret['deck']
			# Need to set up highlighting and other junk too


		if g.get_player() != player:
			oupd['active'] = True
		else:
			ret['active'] = True

		ret['gameid'] = oupd['gameid'] = cherrypy.session['game']

		# Trigger the update for the other player
		self.set_update(oupd)

		return json.dumps(ret)


	# *** These update functions are not session-ized and will need to be
	# fixed later
	@cherrypy.expose
	def update(self):
		# Polling method, let the client know if anything can be updated
		upd = self.watch_update()
		return json.dumps(upd)

	@cherrypy.expose
	def board(self):
		tmpl = Template(filename="board.html")
		return tmpl.render()

root = Server()

cherrypy.quickstart(root, '/', 'cpconfig')


