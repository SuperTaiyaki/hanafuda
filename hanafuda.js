
// the list of matchable cards
//jquery should be loaded

var cardMatch = []

function updateMatch(hand, field) {
	cardMatch[hand] = field;
	return;
}

function getMatch(hand) {
	return cardMatch[hand];
}

function init() {
	// could insert a second argument here with... something useful?
	$.getJSON('ajax/init', function(json) {
			//hand
			//card matches
			var i;
			for (i = 0;i < 8;i++) {
				updateMatch(i, json.matches[i]);
			}
			//field
			//dealer?
	});
}

/* User took one of their cards and placed it, either on a matched card on an
 * empty space. 
 * handID: ID of the card taken
 * fieldID: ID of the card matched (-1 for empty)
 */
function select(handID, fieldID) {
	$.getJSON('ajax/place', {hand: handID, field: fieldID}, function(json) {
			//captures
			//field
			//deck
			//userselect?

			//koikoi?
	});
	return;
}

/* Card on top of the deck matches more than 1 card in the field. Make them
 * selectable and set up for the user to choose one
 */
function deckMatch(matches) {
	//go through matches, mark selectable cards
	//field card should already be set...
	//set state flag to deckMatchSelect or whatever
}

/* User chose a card from the field to match the top of the deck. Push to the
 * backend
 */
function deckMatchSelect(fieldID) {
	$.getJSON('ajax/fieldselect', {field: fieldID}, function(json) {
			//koikoi?

	});
}

/* After a hand has been processed update multipliers, yaku, and other stuff
 * Also allow the user to koikoi/end if appropriate
 */
function processYaku(yaku) {
	//multiplier
	//yaku
	//koikoi?
}

function koikoi() {
	$.getJSON('ajax/koikoi', function(json) {
			processYaku(json);
	});
}

function endGame() {
	$.getJSON('ajax/endgame', function(json) {
			//dunno
	});
}

