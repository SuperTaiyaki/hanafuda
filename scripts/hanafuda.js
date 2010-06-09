
// the list of matchable cards
//jquery should be loaded


var dragging = false;
var deck_select = false;
var cometactive = false;
var gameid;

function log(msg) {
	//opera-specific JS debugging
	window.opera.postError(msg);
}

// Strip all suits off a card
function clear_suit(el) {
	var i;
	for (i=0;i < 12;i++) {
		el.removeClass("mon" + i);
	}
}

/* enter deck selection mode, where there are multiple options from the field to
 * match a card from the deck. The player can only take the deck card and match
 * it to field cards of the same suit.
 */
function deckselect_enable(card) {
	$("#deckCard").draggable({helper: 'clone'});
	unmark_field();
	var month = card.suit
	mark_field(month, false);
	//should disable highlight and dragging for the main cards
	$(".fieldCard:not(." + month + ")").droppable("option", "disabled", true);
	$(".handCard").draggable("option", "disabled", true);
	deck_select = true;
}

function deckselect_disable(card) {
	//restore the old state
	$("#deckCard").attr('src', "img/back.gif");
	$(".fieldCard").droppable("option", "disabled", false);
	$(".handCard").draggable("option", "disabled", false);
	deck_select = false;
	unmark_field();
}

/* Raise a screen onto the playing area to block interaction. Used for dialogs.
 */
function screen_on() {
	$("#screen").css('display', 'block');
}

function screen_off() {
	$("#screen").css('display', 'none');
}

/* Take a list of captures and insert it into the captures box given. The main
 * work of this is to group them correctly.
 */
function addCaptures(caps, path) {
	var i;
	for (i = 0;i < caps.length;i++) {
		var group = "Dregs";
		switch(caps[i].rank) {
			case 20:
				group = "Brights";
				break;
			case 10:
				group = "Animals";
				break;
			case 5:
				group = "Slips";
		}
		var img = "<img src=\"" + caps[i].img + "\" class=\"capCard\" />";
		var target = path.children(".captures" + group).children().last();
		target.after(img);
	}
}


function updateField(cards) {
	for (i = 0;i < cards.length;i++) {
		var el = cards[i];
		var cn = "#field_" + el.id;
		var card = $(cn);
		card.attr('src', el.img);
		clear_suit(card);
		card.addClass(el.suit);
		card.data('suit', el.suit);
	}
}

function enable_hand() {
	$("#playerHand").removeClass("handDisabled");
	$("#opponentHand").addClass("handDisabled");
	$("#playerHand > .handCard").draggable("option", "disabled", false);
}

function disable_hand() {
	$("#opponentHand").removeClass("handDisabled")
	$("#playerHand").addClass("handDisabled");
	$("#playerHand > .handCard").draggable("option", "disabled", true);
}

function drag_targets(suit, blank) {
	if (deck_select)
		return; //don't bother it
	$(".fieldCard").droppable("option", "disabled", true);
	if (suit == "")
		return;
	var droptgts = $(".fieldcard." + suit);
	if (droptgts.length > 0)
		droptgts.droppable("option", "disabled", false);
	else
		$(".fieldCard.empty").droppable("option", "disabled", false);
}

/* General update worker function, take an update from the backend and process
 * the fields.
 */
function update(json) {
	if (json.error) {
		alert(json.error);
		return;
	}
	var i;
	/*if (json.gameid != gameid) {
		alert("Game IDs don't match: own " + gameid + " new " + json.gameid);
	}*/
	if (json.field) {
		updateField(json.field)
	}
	if (json.hand) {
		// hide cards from the player's own hand
		for (i = 0;i < json.hand.length;i++) {
			var idx = json.hand[i];
			var cn = "#player_" + idx;
			$(cn).css('display', 'none');
		}
	}
	if (json.opp_hand) {
		//update opponent's hand
		$("#opponent_" + json.opp_hand[0]).css('display', 'none');
	}
	if (json.caps_self) {
		//update own captures
		addCaptures(json.caps_self, $("#playerCaptures"));
	}
	if (json.caps_opp) {
		//update opponent's captures
		addCaptures(json.caps_opp, $("#opponentCaptures"));
	}

	if (json.deck) {
		//let the player match the deck card to a field card
		//inactive player gets to watch, but not to act
		$("#deckCard").attr('src', json.deck.img);
		if (json.active) {
			deckselect_enable(json.deck);
		}
	}
	if (json.deck_clear) {
		$("#deckCard").attr('src', "img/back.gif");
	}

	if (json.koikoi) {
		var yakus = ""
		for (i = 0;i < json.yaku.length;i++) {
			yakus += json.yaku[i] + "<br />";
		}
		$("#txtHands").html(yakus);
		$("#koikoiPrompt").css('display', 'block');
		screen_on();
	}

	if (json.score) {
		$("#txtScore").text(json.score);
	} else if (json.opp_score) {
		$("#txtOppScore").text(json.opp_score);
	}
	
	//Results display
	if (json.results) {
		$("#results").html(json.results);
		$("#results").css('display', 'block');
		$("#results").draggable(); //if the user wants to see stuff
		screen_on();
		return; //don't let the comet restart
	}


	if (!json.active) {
		disable_hand();
		setTimeout("comet()", 500);
	} else {
		enable_hand();
	}
}

function comet() {
	cometactive = true; //because it will block other ajax requests
	$.getJSON('update', function(json) {
			cometactive = false;
			update(json);
		});
	return;
}

function init() {
	$.getJSON('ajax/init', function(json) {
/*			var i;
			gameid = json.gameid;
			$("#txtGameId").html(gameid); */
			//hand
			for (i = 0;i < 8;i++) {
				var cn = "#player_" + i;
				if (json.hand[i].suit == -1) {
					$(cn).css('display', 'none');
				} else {
					$(cn).get(0).src = json.hand[i].img;
					$(cn).addClass(json.hand[i].suit)
					$(cn).data('suit', json.hand[i].suit)
					$(cn).data('id', i);
				}
			}

			//field
			for (i = 0;i < 12;i++) {
				var cn = "#field_" + i;
				$(cn).get(0).src = json.field[i].img;
				$(cn).addClass(json.field[i].suit);
				$(cn).data('suit', json.field[i].suit);
				$(cn).data('id', i);
			}

			$("#deckCard").data('id', -1);

			$(".fieldCard").droppable({drop: function(event, ui) {
					place(ui.draggable.data("id"), $(this).data("id"));
					},
					'disabled': true});

			//dealer?
			if (!json.active) {
				disable_hand();
				setTimeout('comet()', 500); //start the comet process going
			}
	});

	
	/* handle dragging and hovering cards
	 * On hover highlight the cards that match the highlighted card
	 * On drag lock the highlight
	 * On drag release or unhover remove the highlight
	 */
	$("#playerHand > .handCard").draggable({helper: 'clone',
			start: function(event, ui) {
				dragging = true; //need to mark the original somehow
				$(this).css('opacity', 0.2);
				draggingthing = $(this);
				var month = $(this).data('suit');
				drag_targets(month, true);
				},
			stop: function() {
				dragging = false;
				unmark_field();
				draggingthing.css('opacity', 1.0);
				}});
	$("#playerHand > .handCard").hover(function() {
			//start hover handler, mark the suit
			var suit = $(this).data('suit');
			mark_field(suit, true);
			}, function() {
			//stop hover handler
			unmark_field();
			});

}

function mark_field(month, blank) {
	var tgts = $(".fieldCard." + month);
	if (tgts.length > 0)
		tgts.addClass('cardHighlight');
	else if (blank)
		$(".fieldcard.empty").addClass('cardHighlight');
}
function unmark_field() {
	if (!dragging && !deck_select) {
		$(".fieldcard.cardHighlight").removeClass('cardHighlight');
		drag_targets("", false);
	}
}

/* User took one of their cards and placed it, either on a matched card on an
 * empty space. 
 * handID: ID of the card taken (-1 if it's from the deck, special case)
 * fieldID: ID of the card matched (-1 for empty)
 */
function place(handID, fieldID) {
	if (cometactive) {
		alert("Error, it's probably not your turn");
		return;
	}
	 //special case, match deck to field
	if (handID == -1) {
		//should set this up so it can be bounced, but meh
		deckselect_disable();
	}

	$.getJSON('place', {hand: handID, field: fieldID}, function(json) {
			update(json);

	});
	return;
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
			update(json);
			//processYaku(json);
	});
	screen_off();
	$("#koikoiPrompt").css('display', 'none');
}

function endGame() {
	$.getJSON('ajax/endgame', function(json) {
			$("#koikoiPrompt").css('display', 'none');
			update(json);
	});
	
}

$(document).ready(function() {
		init();
		});

