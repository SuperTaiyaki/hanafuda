# coding=utf8

# Main hanafuda game handling class
import yaml
import unittest

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


class Yaku:
	def __init__(self):
		self.filter = None
		self.count = 0
		self._name = None
		self.points = 0
	
	def check(self, caps):
		f = self._filter_attr(self.filter, caps)
		return len(f) >= self.count
	def score(self, caps = None):
		return self.points
	def name(self, caps = None): # actual name, if any
		return self._name
	def names(self): # all possible names
		return [self._name]

	# return caps with anything that doesn't have the attr removed
	def _filter_attr(self, attr, caps):
		return filter(lambda c: attr in c.attrs, caps)
	def _in_caps(self, attr, caps):
		return len(self._filter_attr(attr, caps)) > 0

# {{{ caps definitions 
all_hands = []
def define_hand(y):
	all_hands.append(y())
	return y
@define_hand
class Redslip(Yaku):
	def __init__(self):
		Yaku.__init__(self)
		self.filter = 'redslip'
		self.count = 3
		self._name = "Red Poems" # 赤タン
		self.points = 6
@define_hand
class Blueslip(Yaku):
	def __init__(self):
		Yaku.__init__(self)
		self.filter = 'blueslip'
		self.count = 3
		self._name = "Blue Poems" # 青タン
		self.points = 6
@define_hand
class Slip(Yaku):
	def __init__(self):
		Yaku.__init__(self)
		self.filter = 'slip'
		self.count = 5
		self._name = "Poems" # タン
	def score(self, caps):
		# 1 basic + 1 for each slip after
		f = self._filter_attr('slip', caps)
		return len(f) - 4
@define_hand
class Hanami(Yaku): # err, should be doing this in English, but 'moon viewing' is long
	def __init__(self):
		Yaku.__init__(self)
		self._name = "Flower viewing" # 花見(酒)
		self.points = 5
	def check(self, caps):
		return self._in_caps('cup', caps) and self._in_caps('curtain', caps)
@define_hand
class Tsukimi(Yaku):
	def __init__(self):
		Yaku.__init__(self)
		self._name = "Moon viewing" # 月見 (酒)
		self.points = 5
	def check(self, caps):
		return self._in_caps('cup', caps) and self._in_caps('moon', caps)
@define_hand
class ISC(Yaku):
	def __init__(self):
		Yaku.__init__(self)
		self.filter = 'isc'
		self.count = 3
		self._name = "D.B.D" # Ino Shika Chou
		self.points = 6
	def score(self, caps):
		# 6 basic + 3 for each animal afterwards
		f = self._filter_attr('animal', caps)
		return len(f) + 3
@define_hand
class Animal(Yaku):
	def __init__(self):
		Yaku.__init__(self)
		self.filter = 'animal'
		self.count = 5
		self._name = "Earth" # タネ
	def score(self, caps):
		# 1 basic + 1 for each animal after
		f = self._filter_attr('animal', caps)
		return len(f) - 4
@define_hand
class Dregs(Yaku):
	def __init__(self):
		Yaku.__init__(self)
		self._name = "Basic" # can't remember
		self.filter = lambda c: c.rank == 1
	def check(self, caps):
		f = filter(self.filter, caps)
		return len(f) >= 10
	def score(self, caps):
		# 1 basic + 1 for each animal after
		f = filter(self.filter, caps)
		return len(f) - 9
@define_hand
class Lights(Yaku):
	def __init__(self):
		Yaku.__init__(self)
		self.filter = 'bright'
		self.count = 3
	def check(self, caps):
		ret = Yaku.check(self, caps)
		# 3 brights including rainmain is not valid
		if ret and self._in_caps('rainmain', caps):
			return False
		return ret
	def score_brights(self, caps):
		brights = self._filter_attr('bright', caps)
		# 5 brights
		if len(brights) == 5:
			return (10, "Five Lights")
		rainmain = self._in_caps('rainmain', caps)
		if len(brights) == 4:
			# rainy four
			if rainmain:
				return (7, "Four Lights")
			else: # dry four
				return (8, "Dry Four Lights")
		if not rainmain and len(brights) == 3:
			return (6, "Three Lights")
		return (0, "")
	def score(self, caps):
		(sc, _) = self.score_brights(caps)
		return sc
	def name(self, caps):
		(_, name) = self.score_brights(caps)
		return name 
	def names(self):
		return ["Five Lights", "Four Lights", "Dry Four Lights",
			"Three Lights"]
# }}}
class Scoring:
	def __init__(self):
		self.hands = all_hands # generated with decorators above
		self.total = 0
		self.names = map(lambda x: x.names(), self.hands)
		# yeah, this makes my head hurt too
		self.names = [item for sublist in self.names
				for item in sublist]
		# Associate each hand with its name
		self.names = dict.fromkeys(self.names, None)
		self.yakus = {}
		for h in self.hands:
			self.yakus[h] = None

	def update(self, caps):
		score = 0
		new = False
		for y in self.hands:
			if y.check(caps):
				score += y.score(caps)
				n = y.name(caps)
				self.yakus[y] = n
				self.names[y.name] = True
		print("Old: ", self.total, "New: ", score)
		if score > self.total:
			new = True
		self.total = score
		return new

	def get_score(self):
		return self.total
	def get_names(self):
		ret = []
		for g in self.yakus:
			if self.yakus[g]:
				ret.append(self.yakus[g])
		return ret

# {{{ Tests

class TestScoring(unittest.TestCase):
	def setUp(self):
		self.deck = create_deck()
	def getCards(self, cards):
		return map(lambda c: self.deck[c], cards)

	def testJunk(self):
		short = self.getCards(range(0, 9))
		# The first couple of dregs cards
		long = self.getCards([2,3,6,7,10,11,14,15,18,19, 45, 46, 47])

		dregs = Dregs()
		self.assertFalse(dregs.check(short))
		self.assertTrue(dregs.check(long))
		self.assertTrue(dregs.name(long) in dregs.names())
		self.assertTrue(dregs.score(long) == 4)
	
if __name__ == '__main__':
    unittest.main()

# }}}

