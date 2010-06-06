# Main hanafuda game handling class
import yaml

# abstract card
class Card:
	image = ""
	suit = -1 # [0,12]
	rank = -1 # [0,1,2,3]
	id = -1 # [0,48] (unique)

	def __init__(self, image, suit):
		self.image = image
		self.suit = suit
	
 	# class function, return a complete deck
	def deck(yaml):

		# Helpers for all the special attributes...
		# brights
		def bright(card):
			card.rank = 20
			card.bright = True
		def moon(card):
			bright(card)
			card.moon = True
		def curtain(card):
			bright(card)
			card.moon = True
		def rainman(card):
			bright(card)
			card.rainmain = True

		def animal(card):
			card.rank = 10
			card.animal = True
		def isc(card):
			animal(card)
			card.isc = True
		def cup(card):
			animal(card)
			card.cup = True

		def slip(card):
			card.slip = True
			card.rank = 5
		def blueslip(card):
			card.blueslip = True
			slip(card)
		def redslip(card):
			slip(card)

		# yaml is a YAML object containing the deck specification
		cards = []
		suit = 0
		for month in yaml:
			for card in month['month']:
				c = Card(card['img'], suit)
				# attributes are the names of functions defined above
				if 'attribute' in card:
					locals()[card['attribute']](c)
				cards.append(c)

			suit += 1
		return cards

f = open('cards.yaml')
y = yaml.load(f)
deck = Card.deck(y)

for card in deck:
	print(card)
