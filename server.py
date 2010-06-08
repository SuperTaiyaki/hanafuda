import cherrypy
from mako.template import Template
import game
import cards
import json

class Server:

	def __init__(self):
		deck = cards.create_deck()
		self.game = game.Game(deck, 0)
		self.games = {}
		self.updates = []

	# Test function that spits out a list of images
	@cherrypy.expose
	def showcards(self):
		deck = cards.create_deck()
		buf = ""
		for card in deck:
			buf += "<img src=\"img/%s\" />Suit: %i Rank: %i<br />\n" % (card.image, card.suit, card.rank)
		return buf

	# Bunch of AJAX functions

	@cherrypy.expose
	def ajax(self, arg):
		if arg == "init":
			ret = {}
			ret['hand'] = []
			for c in self.game.get_hand(0):
				# oh no my python is looking like JS
				if c == None:
					ret['hand'].append({
						'img': "img/clear.gif",
						'suit': None})
				else:
					ret['hand'].append({
						'img': "img/" + c.image,
						'suit': "mon" +	str(c.suit)})

			ret['field'] = []
			for c in self.game.get_field():
				if c:
					ret['field'].append({
						'img':"img/" + c.image,
						'suit': "mon"+str(c.suit)})
				else:
					ret['field'].append("")
			
			return json.dumps(ret)

	def update_card(self, idx, card):
		ret = {'id': idx}
		if (card == None):
			ret['img'] = "img/empty.gif"
			ret['suit'] = None
		else:
			ret['img'] = "img/" + card.image
			ret['suit'] = "mon" + str(card.suit)
		return ret


	@cherrypy.expose
	def place(self, hand, field):
		# sanity checks
		upd = self.game.play(0, int(hand), int(field))
		# Player update will be hand, field, maybe deck, captures
		# Opponent update will be opponent, field, opponent captures
		self.reg_update(['field', 'opp', 'caps_opp'])
		# return the updates required for this turn (the actual data,
		# not just flags)

		ret = {}
		if len(upd['field']) > 0:
			ret['field'] = []
			for c in upd['field']:
				ret['field'].append(self.update_card(c,
					self.game.get_hand(0)[c]))
		if len(upd['hand']) > 0:
			ret['hand'] = []
			for c in upd['hand']:
				ret['hand'].append(c)
		if len(upd['caps']) > 0:
			ret['caps_self'] = []
			for c in upd['caps']:
				ret['caps_self'].append({'img':"img/"+c.image})

		return json.dumps(ret)


	# *** These update functions are not session-ized and will need to be
	# fixed later
	@cherrypy.expose
	def update(self):
		# Polling method, let the client know if anything can be updated
		ret = json.dumps(self.updates)
		self.updates = []
		return ret

	def reg_update(self, type):
		self.updates.append(type)

	@cherrypy.expose
	def board(self):
		tmpl = Template(filename="board.html")
		return tmpl.render()

root = Server()

cherrypy.quickstart(root, '/', 'cpconfig')


