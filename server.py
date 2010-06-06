import cherrypy
from mako.template import Template
import game
import cards
import json

class Server:

	def __init__(self):
		deck = cards.create_deck()
		self.game = game.Game(deck, 0)

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
			for c in self.game.hand(0):
				ret['hand'].append("img/" + c.image)

			ret['field'] = []
			for c in self.game.get_field():
				if c:
					ret['field'].append("img/" + c.image)
				else:
					ret['field'].append("")
			
			ret['matches'] = self.game.hand_match(0)

			return json.dumps(ret)

	@cherrypy.expose
	def board(self):
		tmpl = Template(filename="board.html")
		return tmpl.render()

root = Server()

cherrypy.quickstart(root, '/', 'cpconfig')


