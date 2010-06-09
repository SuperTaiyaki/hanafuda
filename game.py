import cards
import random

class GameError(Exception):
	pass

class Game:
	FIELD_SIZE = 12 # maximum possible
	# Dealer should be 0 or 1
	def __init__(self, deck, dealer = -1):
		# "the total number of permutations of x is larger than the
		# period of most random number generators; this implies that
		# most permutations of a long sequence can never be generated."
		# but I don't think there's much to do about it
		random.shuffle(deck)
		self.cards = deck
		# take the first 3 slices of 8 cards to make the hands and field
		self.hands = (self.cards[0:8], self.cards[8:16])
		self.captures = ([], [])
		self.scores = (cards.Scoring(), cards.Scoring())
		self.field = self.cards[16:24]
		# Pad up to FIELD_SIZE with Nones
		self.field.extend([None] * (self.FIELD_SIZE - len(self.field)))

		self.cards = self.cards[24:]

		self.deck_top = None

		if (dealer == -1):
			dealer = random.randint(0, 1)
		self.dealer = dealer
		self.player = dealer
		self.active_players = 0
		
		self.multiplier = 1
		self.winner = None

	def get_player(self):
		return self.player
	
	def get_hand(self, player):
		return self.hands[player]

	def get_captures(self, player):
		return self.captures[player]

	def get_field(self):
		return self.field
	def get_deck_top(self):
		return self.deck_top

	def end(self, player):
		self.winner = player

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
		print("Player: ", player, " Hand: ", hand, " Field: ", field)
		if player != self.player:
			raise GameError("Wrong player's turn")
		if hand != -1 and self.hands[player][hand] == None:
			raise GameError("Invalid card")
		if hand != -1 and self.field[field] != None and self.field[field].suit != self.hands[player][hand].suit:
			print self.field[field]
			print self.hands[player][hand]
			raise GameError("Suits don't match")
		if hand == -1 and self.deck_top.suit != self.field[field].suit:
			raise GameError("Deck card must match field card")
			# exception, trying to match the deck suit to
			# something random
		# Player trying to not match when matches exist
		if self.field[field] == None and \
				len(self._search_field(self.hands[player][hand].suit)) > 0:
			raise GameError("Card must match field card")

		# prepare the return stuff
		# caps is going to be weird
		changes = {'caps': [], 'field': [], 'hand': [], 'deck': False,
			'koikoi': False}
		#caps = []
		#ret_field = []
		#deck = None

		# Match the existing card
		if self.field[field] == None:
			self.field[field] = self.hands[player][hand]
			changes['field'].append(field)
			self.hands[player][hand] = None
			changes['hand'].append(hand)
		else:
			# Actually matching something
			# Check for 3 matching cards
			matches = self._search_field(self.hands[player][hand].suit)
			if (len(matches) == 3):
				cap_cards = map(lambda x: self.field[x], matches)
				cap_cards.append(self.hands[player][hand])
				self.captures[player].extend(cap_cards)
				changes['caps'].extend(cap_cards)
				for x in matches:
					self.field[x] = None
					changes['field'].append(x)
			else:
				self.captures[player].extend([self.field[field], self.hands[player][hand]])
				changes['caps'].extend([self.field[field], self.hands[player][hand]])
				self.field[field] = None
				changes['field'].append(field)

			self.hands[player][hand] = None
			changes['hand'].append(hand)
			if hand == -1: # Special case, matching from the deck to
				# the field. Don't need to draw
				# But still do need to change player
				self.player = 1 if self.player == 0 else 0
				return changes

		# Draw a card, etc.
		card = self.cards.pop()
		matches = self._search_field(card.suit)
		if len(matches) == 0:
			# Nothing matches, put it into the field
			idx = self.field.index(None)
			self.field[idx] = card
			changes['field'].append(idx)
		elif len(matches) == 1:
			# Only one match, take both cards
			match = matches[0]
			self.captures[player].extend([self.field[match], card])
			changes['caps'].extend([self.field[match], card])
			self.field[match] = None
			changes['field'].append(match)
		elif len(matches) == 3: # Special rule, 3 matches -> take them all
			# If not for this the other 2 cards would be stuck on the field
			cap_cards = map(lambda x: self.field[x], matches)
			self.captures[player].extend(cap_cards)
			changes['caps'].extend(cap_cards)
			for x in matches:
				self.field[x] = None
				changes['field'].append(x)
		else:
			# More than one match, need the player to choose
			self.deck_top = card
			changes['deck'] = True
		# if deck is set the player needs to force a match, turn isn't
		# over
		# TODO: This will also need to check for fresh yakus
		newyaku = self.scores[player].update(self.captures[player])
		changes['koikoi'] = newyaku

		if len(self.hands[player]) == 0 and self.player != self.dealer:
			# Ran out of cards, the game is over


		if not changes['deck'] and not newyaku:
			self.player = 1 if self.player == 0 else 0
		return changes

	def koikoi(self):
		self.multiplier *= 2
		self.player = 1 if self.player == 0 else 0
	
	def get_score(self, player):
		return self.scores[player]
		
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

