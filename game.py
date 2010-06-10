import cards
import random

class GameError(Exception):
	pass

class Game:
	FIELD_SIZE = 12 # maximum possible
	# Dealer should be 0 or 1
	def __init__(self, deck, dealer = -1):
		# Actually not an ideal shuffle according to the docs
		# take the first 3 slices of 8 cards to make the hands and field
		self.cards = deck[:]
		def draw():
			random.shuffle(self.cards)
			self.hands = (self.cards[0:8], self.cards[8:16])
			self.captures = ([], [])
			self.scores = (cards.Scoring(), cards.Scoring())
			self.field = self.cards[16:24]

		draw()
		while (cards.win_hand(self.hands[0])[0] or
			cards.win_hand(self.hands[1])[0] or
			cards.bad_field(self.field)[0]):
			draw()

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

	def play(self, player, hand, field):
		if player != self.player:
			raise GameError("Wrong player's turn")
		if hand != -1 and self.hands[player][hand] == None:
			print ("Error Hand: ", self.hands[player][hand])
			raise GameError("Invalid card")
		if hand != -1 and self.field[field] != None and self.field[field].suit != self.hands[player][hand].suit:
			raise GameError("Suits don't match")
		if hand == -1 and self.deck_top.suit != self.field[field].suit:
			raise GameError("Deck card must match field card")
			# exception, trying to match the deck suit to
			# something random
		# Player trying to not match when matches exist
		if self.field[field] == None and \
				len(self._search_field(self.hands[player][hand].suit)) > 0:
			raise GameError("Card must match field card")

		changes = {'hand': [-1, -1], # hand id, field id
				'handcard': None, # Card
				'field1': [], # field ids
				'deck': -1, # field id
				'deckcard': None, # Card
				'field2': [], # field ids
				'koikoi': False} 

		# playing hand card

		changes['hand'] = [hand, field]
		changes['handcard'] = self.hands[player][hand]
		if self.field[field] == None:
			# Placing it onto the field
			self.field[field] = self.hands[player][hand]
			self.hands[player][hand] = None
			# field1 doesn't change
		else:
			# Actually matching something
			# Check for 3 matching cards
			matches = (self._search_field(self.hands[player][hand].suit) if
					hand != -1 else [])
			if (len(matches) == 3):
				cap_cards = map(lambda x: self.field[x], matches)
				cap_cards.append(self.hands[player][hand])
				self.captures[player].extend(cap_cards)
				changes['field1'] = matches
				for x in matches:
					self.field[x] = None
			else:
				self.captures[player].extend([self.field[field], self.hands[player][hand]])
				self.field[field] = None
				changes['field1'] = [field]


			self.hands[player][hand] = None
			if hand == -1: # Special case, matching from the deck to
				# the field. Don't need to draw
				# But still do need to change player
				self.player = 1 if self.player == 0 else 0
				return changes

		# Draw a card, etc.
		card = self.cards.pop()
		changes['deckcard'] = card
		matches = self._search_field(card.suit)
		if len(matches) == 0:
			# Nothing matches, put it into the field
			idx = self.field.index(None)
			self.field[idx] = card
			changes['deck'] = idx
		elif len(matches) == 1:
			# Only one match, take both cards
			match = matches[0]
			self.captures[player].extend([self.field[match], card])
			self.field[match] = None
			changes['deck'] = matches[0]
			changes['field2'] = [match]
		elif len(matches) == 3: # Special rule, 3 matches -> take them all
			# If not for this the other 2 cards would be stuck on the field
			cap_cards = map(lambda x: self.field[x], matches)
			self.captures[player].extend(cap_cards)
			for x in matches:
				self.field[x] = None
			changes['field2'] = matches
		else:
			# More than one match, need the player to choose
			self.deck_top = card
			# field2 left empty, deck left as -1
		# if deck is set the player needs to force a match, turn isn't
		# over
		newyaku = self.scores[player].update(self.captures[player])
		changes['koikoi'] = newyaku

		if len(self.hands[player]) == 0 and self.player != self.dealer:
			if newyaku:
				self.winner = player
			else:
				self.winner = 3; # nobody

		if changes['deck'] != -1 and not newyaku:
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

