# Main hanafuda game handling class
import yaml

# abstract card
class Card:
	image = ""
	suit = -1 # [0,12]
	rank = 1 # [20, 5, 10, 1]
	id = -1 # [0,48] (unique)
	
	# attributes
	attrs = {}

	def __init__(self, image, suit):
		self.image = image
		self.suit = suit
		self.attrs = {}
		self.rank = 1

	def __repr__(self):
		out = "\nCARD Suit: %i Rank: %i Attrs: %s" % (self.suit, self.rank,
				self.attrs)
		return out

f = open('cards.yaml')
y = yaml.load(f)
# Create a complete deck
def create_deck():
	yaml = y

	# Helpers for all the special attributes...
	# brights
	def bright(card):
		card.rank = 20
		card.attrs['bright'] = True
	def moon(card):
		bright(card)
		card.attrs['moon'] = True
	def curtain(card):
		bright(card)
		card.attrs['curtain'] = True
	def rainman(card):
		bright(card)
		card.attrs['rainmain'] = True
	# animals
	def animal(card):
		card.rank = 10
		card.attrs['animal'] = True
	def isc(card): # ino shika chou / boar deer butterfly
		animal(card)
		card.attrs['isc'] = True
	def cup(card):
		animal(card)
		card.attrs['cup'] = True
	# slips
	def slip(card):
		card.attrs['slip'] = True
		card.rank = 5
	def blueslip(card):
		card.attrs['blueslip'] = True
		slip(card)
	def redslip(card):
		slip(card)
		card.attrs['redslip'] = True

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

def score_brights(hand):
	brights = filter(lambda c: c.attrs.has_key('bright'), hand)
	# 5 brights
	if len(brights) == 5:
		return (10, "Five Lights")
	rainmain = len(filter(lambda c: c.attrs.has_key('rainmain'), brights)) > 0
	if len(brights) == 4:
		# rainy four
		if rainmain:
			return (7, "Four Lights")
		else: # dry four
			return (8, "Dry Four Lights")
	if not rainmain and len(brights) == 3:
		return (6, "Three Lights")
	return (0, "")

scoring = [
		# red slips
		{'filter': lambda c: c.attrs.has_key('redslip'), 'count': 3, 'score': (lambda x: 6, "Red Poems")},
		# blue slips
		{'filter': lambda c: c.attrs.has_key('blueslip'), 'count': 3, 'score': (lambda x: 6, "Blue Poems")},
		# all slips
		{'filter': lambda c: c.attrs.has_key('slip'), 'count': 5, 'score': (lambda x: x - 4,
			"Poems")},
		# ISC (may require fiddling for extra animal points
		{'filter': lambda c: c.attrs.has_key('isc'), 'count': 3, 'score': (lambda x: 6,
		"Boar Deer Butterfly")},
		# plain animals
		{'filter': lambda c: c.attrs.has_key('animal'), 'count': 5, 'score': (lambda x: x
			- 4, "Animals")},
		{'filter': lambda c: c.attrs.has_key('cup') or c.attrs.has_key('moon'), 'count': 2, 'score':
			(lambda x: 5, "Moon viewing")},
		{'filter': lambda c: c.attrs.has_key('cup') or c.attrs.has_key('curtain'), 'count': 2, 'score':
			(lambda x: 5, "Flower viewing")},
		# dregs
		{'filter': lambda c: c.rank == 1, 'count': 10, 'score':
			(lambda x: x - 9, "Basic")}]

def score_hand(hand):
	score = 0
	yaku = []
	(score, comment) = score_brights(hand)
	if score > 0:
		yaku.append(comment)
	
	for y in scoring:
		f = filter(y['filter'], hand)
		if len(f) >= y['count']:
			score += y['score'][0](len(f))
			yaku.append(y['score'][1])
	return (score, yaku)


#
#for yaku in scoring:
#	f = filter(yaku['filter'], deck)
#	if len(f) >= yaku['count']:
#		score = yaku['score'][0](len(f))
#		desc = yaku['score'][1]
#		print(score, desc)
#
#print(score_brights(deck))
#
