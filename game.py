import cards
import random
import cPickle

# This thing is genius
def enum(*sequential, **named):
    enums = dict(zip(sequential, range(len(sequential))), **named)
    return type('Enum', (), enums)

class GameError(Exception):
    pass

States = enum(
    'PLAY', # Regular, expecting play()
    'DRAW_MATCH', # Drew a card -> multiple on-field matches, expecting ___()
    'KOIKOI', # Completed a yaku, expecting koikoi() or end()
    'FINISHED')

class Game(object):
    """ Class used to operate a game.
    Initialize to a new game state with new_game().

    Check active player with get_player()
    Check state with get_state()
    If state is PLAY:
        -respond with play_card.
        -> Extra draw will take place automatically. 
            -> If player must choose which field card to match with the draw,
                state will become DRAW_MATCH on return
            -> If not, koikoi check will occur. State either goes to PLAY (other player)
                or KOIKOI
        -> Player changes, state is back to PLAY.

    If state is DRAW_MATCH:
        -respond with draw_match
        -> Koikoi check will occur. State either goes back to PLAY or KOIKOI.
    If state is KOIKOI:
        -respond with koikoi
        -> If yes, state becomes PLAY player changes.
        -> If no, game ends.

    """
    FIELD_SIZE = 12 # maximum possible
    # Dealer should be 0 or 1
    def __init__(self):
        pass

    def new_game(self, dealer = -1):
        # Actually not an ideal shuffle according to the docs
        # take the first 3 slices of 8 cards to make the hands and field
        self.cards = range(48)
        self.captures = ([], [])
        def draw():
            random.shuffle(self.cards)
            self.hands = (self.cards[0:8], self.cards[8:16])
            self.field = self.cards[16:24]

        draw()
        while (cards.win_hand(self.hands[0])[0] or
            cards.win_hand(self.hands[1])[0] or
            cards.bad_field(self.field)[0]):
            draw()

        # Pad up to FIELD_SIZE with Nones
        self.field.extend([None] * (self.FIELD_SIZE - len(self.field)))

        self.cards = self.cards[24:]

        # Fuck with the deck a bit to make the draw_match come up
        #for i, c in enumerate(self.field):
        #    if c is not None and c < 4:
        #        self.field[i] += 10
        #self.field[0:1] = [0, 1]
        #self.cards[-1] = 3

        # Same thing for the triple select
        #for i, c in enumerate(self.field):
        #    if c is not None and c < 4:
        #        self.field[i] += 10
        #self.field[0:2] = [0, 1, 2]
        #self.hands[0][0] = 3
        #self.hands[1][0] = 3

        self.deck_top = None

        self.state = States.PLAY

        if (dealer == -1):
            dealer = random.randint(0, 1)
        self.player = dealer

        self.koikoi_count = [0, 0]
        # Needed to check if there's a koikoi option, hence the full tracking
        self.scores = (cards.Scoring(), cards.Scoring())
        self.multiplier = [1, 1]
        self.winner = None

        # Write-only.
        self.events = []

    def event(self, type, player = None, card = None, location = None):
        #self.events.append((type, player, card, location))
        self.events.append({'type': type, 'player': player, 'card': card, 'location': location})

    @classmethod
    def load(state):
        self.hands = state['hands']
        self.field = state['field']
        self.captures = state['captures']
        self.deck = state['deck']
        self.koikoi_count = state['koikoi']
        self.player = state['player']
        self.state = state['state']
        self.deck_top = state['deck_top']
        self.scoring = (cards.Scoring(), cards.Scoring())
        self.scoring[0].update(self.captures[0])
        self.scoring[1].update(self.captures[1])
        # Calculate scores

    def dump():
        ret = {}
        # Only the important parts of the game state
        ret['hands'] = self.hands
        ret['field'] = self.field
        ret['captures'] = self.captures
        ret['deck'] = self.deck
        ret['koikoi'] = self.koikoi_count
        ret['player'] = self.player
        ret['state'] = self.state
        ret['deck_top'] = self.deck_top
        # Should store a version key in here or something...
        return ret

    def get_player(self):
        return self.player

    def get_state(self):
        return self.state

    def get_hand(self, player):
        return self.hands[player]

    def get_captures(self, player):
        return self.captures[player]

    def get_field(self):
        return self.field
    def get_deck_top(self):
        return self.deck_top

    def get_events(self):
        return self.events

    def clear_events(self):
        del self.events[0:]

    def get_yaku(self, player):
        return self.scores[player].get_names()

    def get_score(self, player):
        return self.scores[player].get_score()

    def get_multiplier(self, player):
        return self.multiplier[player]

    def _take_card(self, player, hand, field):
        if self.field[field] is None:
            raise GameError("Tried to place card on something; broken!")
        if self.hands[player][hand] / 4 != self.field[field] / 4:
            raise GameError("Suits don't match (inconsistent state, try refreshing)")

        # Special case: if there are 3 cards of the same suit on the field, take them all
        matches = self._search_field(self.hands[player][hand])
        captures = [field]
        if (len(matches) == 3):
            # Could just as easily compute this is card/4+0, +1, +2, +3
            cap_cards = [self.field[x] for x in matches]
            self.captures[player].extend(cap_cards)
            for card in matches:
                self.field[card] = None
            captures = matches
        else:
            self.captures[player].append(self.hands[player][hand])
            self.captures[player].append(self.field[field])
            self.field[field] = None
        self.event("take_card", player, None, captures)

        #cap_cards.append(self.hands[player][hand])
        self.hands[player][hand] = None

    def _place_card(self, player, hand, field):
        if self.field[field] != None:
            raise GameError("Tried to place card on something; broken!")
        self.field[field] = self.hands[player][hand]
        self.hands[player][hand] = None

    def play_card(self, player, hand, field):
        """ Player has dealt something.
        player is the player index (1 or 0, should match self.player)
        hand is the index of the card in the hand
        field is the index of the field space. If there's a card there,
            it's a capture. If not, the card is being placed.
        """

        # TODO: validation goes in here
        
        if len(self._search_field(self.hands[player][hand])) == 0 and\
                self.field[field] is not None:
                    raise GameError("Card placed when match is available")
        # TESTING!!!
        #if self.field[field] is not None and self.field[field] / 4 == 0:
        #    raise GameError("January off limits.")

        print(self.hands[player])
        self.event("play_card", player, self.hands[player][hand], field)

        if self.field[field] is None:
            self._place_card(player, hand, field)
        else:
            self._take_card(player, hand, field)

        self.deck_draw(player)

        return

    def deck_draw(self, player):
        card = self.cards.pop()
        self.event("draw_card", player, card, [])
        matches = self._search_field(card)

        if len(matches) == 0:
            # Nothing matches, put it into the field
            # Hrmmmmm, if the field is full this will explode
            # TODO: Would be nice to use rindex instead of index, but doesn't exist on lists
            idx = self.field.index(None)
            self.field[idx] = card
            self.event("draw_place", player, card, idx)
        elif len(matches) == 1:
            # Only one match, take both cards
            match = matches[0]
            self.captures[player].extend([self.field[match], card])
            self.event("draw_place", player, None, matches[0:1])
            self.event("draw_capture", player, self.field[match], matches)
            self.field[match] = None
        elif len(matches) == 3: # Special rule, 3 matches -> take them all
            # If not for this the other 2 cards would be stuck on the field
            cap_cards = [self.field[x] for x in matches]
            self.event("draw_place", player, None, matches[0:1])
            self.event("draw_capture", player, None, matches) # cards aren't actually useful here
            self.captures[player].extend(cap_cards)
            self.captures[player].append(card)
            for x in matches:
                self.field[x] = None
        else:
            # Two matches, need the player to choose
            self.deck_top = card
            self.state = States.DRAW_MATCH
            self.event(":draw_match", player, card, None)
            return # Not ending the turn yet!
            # Will be joined back in draw_match

        self.end_turn(player)

    def validate_input(self, player, field):
        if player != self.player:
            raise GameError("Incorrect player. Not your turn.")
        if field < 0 or field > 11:
            raise GameError("Invalid field location (wtf did you do?)")

    # Drawn card has multiple matches on-field -> player has selected one
    def draw_match(self, player, field):
        """ Indicate the card that the player will match against the card
        from the top of the deck."""
        if self.state != States.DRAW_MATCH:
            raise GameError("Not currently a valid move.")
        if self.deck_top / 4 != self.field[field] / 4:
            raise GameError("Suits don't match (inconsistent state, try refreshing)")

        self.captures[player].extend([self.field[field],self.deck_top])
        self.deck_top = None
        self.event("draw_place", player, None, [field])
        self.event("draw_capture", player, self.field[field], [field])
        self.field[field] = None
        self.end_turn(player)

    def koikoi(self, player, koikoi):
        """ Indicate whether the player will koikoi. True/False. """
        if self.state != States.KOIKOI:
            raise GameError("Unable to koikoi at this point.")
        if player != self.player:
            raise GameError("Wrong player.")

        if koikoi:
            self.koikoi_count[self.player] += 1
            self.event("koikoi", player, [], [])
            self.end_turn(player)
            return False
        else:
            self.winner = player
            self.state = States.FINISHED
            self.event("end", player, [], [])
            return True

    def get_score(self, player):
        return self.scores[player]

    def end_turn(self, player):
        if self.scores[player].update(self.captures[player]):
            print("Koikoi option")
            print self.hands
            #self.event(":koikoi", player, [], [])
            if any(self.hands[player]):
                self.state = States.KOIKOI
            else:
                # Out of cards
                self.state = States.FINISHED
                self.winner = player
        else:
            if not any((any(x) for x in self.hands)):
                self.state = States.FINISHED
                self.winner = -1 # Draw
            else:
                self.player ^= 1
                self.state = States.PLAY

        if self.scores[player].get_score() > 7:
            self.multiplier[player] = 2
            print("Multiplier at 2 for player %s" % player)
        # self.event("end_turn", player, None, [])

    def _search_field(self, suit):
        res = []
        for idx, card in enumerate(self.field):
            if card is not None and self._same_suit(suit, card):
                res.append(idx)
        return res

    @staticmethod
    def _same_suit(c1, c2):
        return c1 / 4 == c2 / 4

def test():
    g = Game()
    print("Hand 0:")
    print g.hands[0]
    print("Hand 1:")
    print g.hands[1]
    print ("Field:")
    print g.get_field()

    print cPickle.dumps(g)

def itest():
    return Game(cards.create_deck(), 0)

# Formal unit tests for this live elsewhere
if __name__ == '__main__':
    test()

