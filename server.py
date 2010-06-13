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

class Server:

	def __init__(self, lobby):
		self.lobby = lobby
		self.games = {}
		self.updates = {}

	# Test function that spits out a list of images
	@cherrypy.expose
	def showcards(self):
		deck = cards.create_deck()
		buf = ""
		for card in deck:
			buf += "<img src=\"/img/%s\" />Suit: %i Rank: %i<br />\n" % (card.image, card.suit, card.rank)
		return buf

	def create_id(self):
		ti = 0
		while True:
			ti = random.randrange(11111111, 99999999)
			if ti not in self.games:
				break
		return ti

	# id, active game: join
	# no id active session: reuse
	# id, inactive game: create
	# no id, no session: create
	
	def getsession(self, id = -1):
		# time.sleep(1.4)
		id = int(id)

		if 'game' in cherrypy.session and (id == -1 or id == cherrypy.session['game']):
			g = self.games[cherrypy.session['game']]
			player = cherrypy.session['player']
			return (g, player)

		if id == -1:
			if 'game' in cherrypy.session:
				id = cherrypy.session['game']
			else:
				id = self.create_id()

		if id not in self.games:
			# start a new game
			g = game.Game(cards.create_deck(), 0)
			self.games[id] = (g)
			g.active_players = 1
			player = 0
			cherrypy.session['player'] = 0
			cherrypy.session['game'] = id
			self.init_update()
			self.lobby.alert_create(id)
			print("Created new game", id)
			return (g, player)
		# Try to join the game #id
		if self.games[id] and self.games[id].active_players < 2:
			player = self.games[id].active_players
			cherrypy.session['player'] = player
			cherrypy.session['game'] = id 
			self.games[id].active_players = player + 1
			gr = self.games[id]
			print("Joined game ", id)
			self.lobby.alert_join(id)
			return (gr, player)

		raise GameFullException("Game is full")

	def reset_game(self):
		g = game.Game(cards.create_deck(), 0)
		g.active_players = 0
		self.games[cherrypy.session['game']] = g


	# Threaded functions for moving updates between players
	# Note that watch and update operate on alternate players

	def init_update(self):
		if 'game' not in cherrypy.session:
			raise Exception("Trying initialize get updates with no game")
		id = cherrypy.session['game']
		self.updates[id] = [Queue.Queue(3), Queue.Queue(3)]

	def watch_update(self):
		if 'game' not in cherrypy.session:
			raise Exception("Trying to get updates with no game")
		id = cherrypy.session['game']
		player = cherrypy.session['player']
		q = self.updates[id][player]

		# The timeout here should be _shorter_ than the one from the
		# client. Better for this to time out (and leave the data) than
		# for the data to be lost
		upd = None
		try:
			upd = q.get(True, 240.0)
			# FF has a short-ish timeout, this is under
		except Queue.Empty as e:
			return {'timeout': True}
		q.task_done()
		# If the connection is gone this message will be lost

		# Anything else in there?
		# Unfortunately exceptions are the only option here
		while True:
			try:
				data = q.get(False)
				upd.update(data)
				q.task_done()
			except Queue.Empty as e:
				break
		return upd

	def set_update(self, upd):
		if 'game' not in cherrypy.session:
			raise Exception("Trying to get updates with no game")
		p = 0 if cherrypy.session['player'] else 1
		id = cherrypy.session['game']

		q = self.updates[id][p]
		q.put_nowait(upd) # Ignore the exception - if it hits, something broke

		return

	@cherrypy.expose
	def init(self):
		(g, player) = self.getsession()
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

		if g.get_player() == player:
			ret['active'] = True

		ret['gameid'] = cherrypy.session['game']
		ret['gamelink'] = cherrypy.request.base + "/board?id=" + str(ret['gameid'])

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

		self.set_update({'active': True, 'alert': alert})
		return json.dumps({})

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
			ret['img'] = "/img/" + card.image
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
			print("Game exception...")
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
			oupd['alert'] = "Opponent deciding whether to koikoi"
			oupd['multiplier'] = ret['multiplier'] = g.multiplier
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
	def board(self, id = -1, lobby = False):
		# Initiate the session if necessary
		try:
			(g, player) = self.getsession(id)
		except GameFullException as e:
			return "Error: Game is full"
		deck = cards.create_deck()
		deck = map(lambda x: "/img/" + x.image, deck)
		tmpl = Template(filename="board.html")
		return tmpl.render(images = deck)


	@cherrypy.expose
	def debug(self, args):
		(g, player) = self.getsession()
		if args == "win":
			g.winner = player
			return "Set winner"
		elif args == "koikoi":
			c = cards.Card("jan1.gif", 1)
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
			g.field[0] = cards.Card("jan1.gif", 1)
			g.field[1] = cards.Card("jan2.gif", 1)
			g.field[2] = cards.Card("jan3.gif", 1)
			g.hands[player][0] = cards.Card("jan4.gif", 1)
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

#		return tmpl.render(

#root = Server()

#cherrypy.quickstart(root, '/', 'cpconfig')


