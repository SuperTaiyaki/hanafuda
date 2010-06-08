
// the list of matchable cards
//jquery should be loaded


var dragging = false;

function log(msg) {
	window.opera.postError(msg);
}

function clear_suit(el) {
	var i;
	for (i=0;i < 12;i++) {
		el.removeClass("mon" + i);
	}
}

function update(json) {
	var i;
	if (json.field) {
		for (i = 0;i < json.field.length;i++) {
			var el = json.field[i];
			var cn = "#field_" + el.id;
			var card = $(cn);
			card.attr('src', el.img);
			clear_suit(card);
			card.addClass(el.suit);
			card.data('suit', el.suit);
		}
		//update the field
	}
	if (json.hand) {
		//update player's hand
		//this is only going to be removing stuff
		for (i = 0;i < json.hand.length;i++) {
			var idx = json.hand[i];
			var cn = "#player_" + idx;
			$(cn).css('display', 'none');
		}
	}
	if (json.caps_self) {
		//update own captures
		for (i = 0;i < json.caps_self.length;i++) {
			//create a new element and stick it in
			//may need to add IDs to these to make them sort... or
			//maybe not, just have groups for them
			var img = "<img src=\"" + json.caps_self[i].img + "\" />";
			$("#playerCaptures img:last-child").after(img);
		}
	}
	if (json.caps_opp) {
		//update opponent's captures
	}
	if (json.opp) {
		//update opponent's hand
	}
}

function comet() {
	$.getJSON('update', function(json) {
			update(json)
			setTimeout("comet()", 500);
		});
	return;
}

function init() {
	$.getJSON('ajax/init', function(json) {
			var i;
			//hand
			for (i = 0;i < 8;i++) {
				var cn = "#player_" + i;
				$(cn).get(0).src = json.hand[i].img;
				$(cn).addClass(json.hand[i].suit)
				$(cn).data('suit', json.hand[i].suit)
				$(cn).data('id', i);
			}

			//field
			for (i = 0;i < 8;i++) {
				if (json.field[i] == "blank") {
					// need to blank it somehow...
				}
				var cn = "#field_" + i;
				$(cn).get(0).src = json.field[i].img;
				$(cn).addClass(json.field[i].suit);
				$(cn).data('suit', json.field[i].suit);
				$(cn).data('id', i);
			}
			$(".fieldCard").droppable({drop: function(event, ui) {
					place(ui.draggable.data("id"), $(this).data("id"));
					}});


			//dealer?
	});

	
	/* handle dragging and hovering cards
	 * On hover highlight the cards that match the highlighted card
	 * On drag lock the highlight
	 * On drag release or unhover remove the highlight
	 */
	$("#playerHand > .handCard").draggable({helper: 'clone',
			start: function(event, ui) {
				dragging = true; //need to mark the original somehow
				},
			stop: function() {dragging = false;unmark_field();}});
	$("#playerHand > .handCard").hover(function() {
			//start hover handler, mark the suit
			var suit = $(this).data('suit');
			mark_field(suit);
			}, function() {
			//stop hover handler
			unmark_field();
			});

}

function mark_field(month) {
	$(".fieldCard." + month).addClass('cardHighlight');
}
function unmark_field() {
	if (!dragging)
		$(".fieldcard.cardHighlight").removeClass('cardHighlight');
}

/* User took one of their cards and placed it, either on a matched card on an
 * empty space. 
 * handID: ID of the card taken
 * fieldID: ID of the card matched (-1 for empty)
 */
function place(handID, fieldID) {
	$.getJSON('place', {hand: handID, field: fieldID}, function(json) {
			update(json);
			//catch the usual update stuff
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


