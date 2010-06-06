
// the list of matchable cards
//jquery should be loaded

var cardMatch = new Array(100); // safe value... stupid, but meh
var dragging = false;

function updateMatch(hand, field) {
	cardMatch[hand] = field;
	return;
}

function getMatch(hand) {
	return cardMatch[hand];
}

function markMatched(hand) {
	var matched = cardMatch[hand];
	var i;
	for (i = 0; i < matched.length;i++) {
		var el = $("#field_" + matched[i]);
		//el.effect("pulsate", {times:1}, 2000);
		el.addClass("cardHighlight");
	}
	return;
}
function unmark() {
	if (!dragging)
		$(".fieldCard").removeClass("cardHighlight");
}

function log(msg) {
	window.opera.postError(msg);
}

function init() {
	$.getJSON('ajax/init', function(json) {
			var i;
			//hand
			for (i = 0;i < 8;i++) {
				var cn = "#player_" + i;
				$(cn).get(0).src = json.hand[i];
			}
			//card matches
			for (i = 0;i < 8;i++) {
				updateMatch(i, json.matches[i]);
			}
			//field
			for (i = 0;i < 8;i++) {
				if (json.field[i] == "blank") {
					// need to blank it somehow...
				}
				var cn = "#field_" + i;
				$(cn).get(0).src = json.field[i];
			}
			//dealer?
	});

	//set up the dragging functionality
	//need to make the original disappear somehow...
	$("#playerHand > .handCard").draggable({helper: 'clone',
			start: function(event, ui) {
				dragging = true; //need to mark the original somehow
				},
			stop: function() {dragging = false;unmark();}});
	$("#playerHand > .handCard").hover(function() {
			//substr 7: is the start of the number after field_
			id = $(this).get(0).id.substr(7, 3);
			markMatched(id);
			}, function() {
			unmark();
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

$(document).ready(function() {
		init();
		});


