import cards
import random

class Game:
	FIELD_SIZE = 10
	# Dealer should be 0 or 1
	def __init__(self, cards, dealer = -1):
		# "the total number of permutations of x is larger than the
		# period of most random number generators; this implies that
		# most permutations of a long sequence can never be generated."
		# but I don't think there's much to do about it
		random.shuffle(cards)
		self.cards = cards
		# take the first 3 slices of 8 cards to make the hands and field
		self.hands = (self.cards[0:8], self.cards[8:16])
		self.captures = ([], [])
		self.field = self.cards[16:24]
		# Pad up to FIELD_SIZE with Nones
		self.field.extend([None] * (self.FIELD_SIZE - len(self.field)))

		self.cards = self.cards[24:]

		self.deck_top = None

		if (dealer == -1):
			dealer = random.randint(0, 1)
		self.dealer = dealer
		self.player = dealer
		
		self.multiplier = 1

	def player(self):
		return self.player
	
	def hand(self, player):
		return self.hands[player]

	def captures(self, player):
		return self.captures[player]

	def get_field(self):
		return self.field

	def hand_match(self, player):
		# For each item in the hand make a list of matching items in the
		# field
		ret = [None] * self.FIELD_SIZE
		for i, el in enumerate(self.hands[player]):
			if el:
				ret[i] = self._search_field(el.suit)
			else:
				ret[i] = None
		return ret

	def play(self, player, hand, field):
		if player != self.player:
			return -1 # exception, wrong player
		if hand != -1 and field != -1 and self.field[field].suit != self.hands[player][hand].suit:
			return -1 # exception, suits don't match
		if hand == -1 and self.deck_top.suit != self.field[field].suit:
			return -1 # exception, trying to match the deck suit to
					# something random

		# No error, so flip the player now

		# prepare the return stuff
		caps = []
		ret_field = []
		deck = None

		# Match the existing card
		if field == -1:
			# Just sending it to the field
			# Grab the first available slot
			idx = self.field.index(None)
			# that will bug out if the field ever fills...
			self.field[idx] = self.hands[player][hand]
			ret_field.append(self.hands[player][hand])
			self.hands[player][hand] = None
		else:
			# Actually matching something
			self.captures[player].extend([self.field[field], self.hands[player][hand]])
			caps.extend([self.field[field], self.hands[player][hand]])
			self.field[field] = None
			self.hands[player][hand] = None
			if hand == -1: # Special case, matching from the deck to
				# the field. Don't need to draw
				return {'captures': caps, 'deck': None}

		# Draw a card, etc.
		card = self.cards.pop()
		matches = self._search_field(card.suit)
		if len(matches) == 0:
			# Nothing matches, put it into the field
			idx = self.field.index(None)
			self.field[idx] = card
			ret_field.append(card)
		elif len(matches) == 1:
			# Only one match, take both cards
			match = matches[0]
			self.captures[player].extend([self.field[match], card])
			caps.extend([self.field[match], card])
			self.field[match] = None
		else:
			# More than one match, need the player to choose
			self.deck_top = card
			deck = card
		# if deck is set the player needs to force a match, turn isn't
		# over
		# TODO: This will also need to check for fresh yakus
		if not deck:
			self.player = 1 if self.player == 0 else 0
		return {'captures': caps, 'field': ret_field, 'deck': deck}
	
	def score(self, player):
		return cards.score_hand(self.captures[player])
		
	def _search_field(self, suit):
		res = []
		for idx, val in enumerate(self.field):
			if not val:
				continue
			if val.suit == suit:
				res.append(idx)
		return res

def test():
	g = Game(cards.create_deck())
	print("Hand 0:")
	print g.hand(0)
	print("Hand 1:")
	print g.hand(1)
	print ("Field:")
	print g.get_field()
	
def itest():
	return Game(cards.create_deck(), 0)

#test()

