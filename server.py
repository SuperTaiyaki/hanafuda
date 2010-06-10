import cherrypy
from mako.template import Template
from mako.runtime import Context
from StringIO import StringIO
import game
import cards
import json
import threading
import time

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
				print("Game ", i, " Players ", g.active_players)
				if g.active_players < 2:
					cherrypy.session['player'] = 1
					cherrypy.session['game'] = i
					player = 1
					gr = g
					g.active_players = 2
					print("Joined game ", i)
					return (gr, player)

			# start a new game
			g = game.Game(cards.create_deck(), 0)
			self.games.append(g)
			g.active_players = 1
			player = 0
			cherrypy.session['player'] = 0
			cherrypy.session['game'] = len(self.games) - 1 # is this
			# why things break?
			self.init_update()
			print("Created new game", cherrypy.session['game'])
		else:
			g = self.games[cherrypy.session['game']]
			player = cherrypy.session['player']

		return (g, player)
	def reset_game(self):
		g = game.Game(cards.create_deck(), 0)
		g.active_players = 2
		print g.get_hand(0)
		self.games[cherrypy.session['game']] = g


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

			if g.get_player() == player:
				ret['active'] = True

			ret['gameid'] = cherrypy.session['game']

			return json.dumps(ret)
		elif arg == "koikoi":
			g.koikoi()
			# Trip a mostly empty update to make the turns switch
			# Should also show the opponent what happened
			alert  = "Opponent did not koikoi.<br />"
			alert += "Multiplier is now %ix" % g.multiplier

			self.set_update({'active': True, 'alert': alert})
			return json.dumps({})
		elif arg == "endgame":
			g.end(player)
			# Save the results and delete the game to save memory
			ret = {'results': self.score(g, player)}
			p2 = 1 if player == 0 else 0
			oupd = {'results': self.score(g, p2)}
			self.reset_game()
			self.set_update(oupd)
			return json.dumps(ret)


	def update_card(self,card):
		ret = {}
		if (card == None):
			ret['img'] = "img/empty.gif"
			ret['suit'] = "empty"
			ret['rank'] = -1
		else:
			ret['img'] = "img/" + card.image
			ret['suit'] = "mon" + str(card.suit)
			ret['rank'] = card.rank
		return ret

	@cherrypy.expose
	def place(self, hand, field):
		(g, player) = self.getsession()
		p2 = 0 if player == 1 else 1
		# sanity checks
		try:
			upd = g.play(player, int(hand), int(field))
		except game.GameError as e:
			return json.dumps({'error': e.__repr__()})
		# Player update will be hand, field, maybe deck, captures
		# Opponent update will be opponent, field, opponent captures

		# Take the state changes from the game and form the AJAX request
		
		upd['type'] = "play"

		upd['handcard'] = self.update_card(upd['handcard'])
		upd['deckcard'] = self.update_card(upd['deckcard'])
		upd['gameid'] = cherrypy.session['game']
	
		# updates to both sides

		ret = upd # are these linked or copied? hrm... 
		oupd = upd.copy()

		ret['player'] = True
		oupd['player'] = False

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

#			a message

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
	def update(self):
		# Polling method, let the client know if anything can be updated
		upd = self.watch_update()
		return json.dumps(upd)

	@cherrypy.expose
	def board(self):
		# Initiate the session if necessary
		(g, player) = self.getsession()
		deck = cards.create_deck()
		deck = map(lambda x: "img/" + x.image, deck)
		tmpl = Template(filename="board.html")
		return tmpl.render(images = deck)


	@cherrypy.expose
	def debug(self, args):
		(g, player) = self.getsession()
		if args == "win":
			g.winner = player
		elif args == "koikoi":
			c = cards.Card("jan1.gif", 1)
			c.attrs['bright'] = True
			c.rank = 20
			g.captures[player].extend([c] * 5)


	# Summary screen after the game is over
	@cherrypy.expose
	def scores(self):
		(g, player) = self.getsession()
		tmpl = Template(filename="scores.html")
		won = False
		if g.winner == player:
			won = True

#		return tmpl.render(

root = Server()

cherrypy.quickstart(root, '/', 'cpconfig')


