
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

function clear_suit(el) {
	var i;
	for (i=0;i < 12;i++) {
		el.removeClass("mon" + i);
	}
}

function deckselect_enable(card) {
	$("#deckCard").draggable({helper: 'clone'});
	unmark_field();
	var month = card.suit
	mark_field(month);
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

// Hide the playable area slightly
function screen_on() {
	$("#screen").css('display', 'block');
}

function screen_off() {
	$("#screen").css('display', 'none');
}

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
		var img = "<img src=\"" + caps[i].img + "\" />";
		var target = path.children(".captures" + group).children().last();
		target.after(img);
	}
}

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
		addCaptures(json.caps_self, $("#playerCaptures"));
/*		for (i = 0;i < json.caps_self.length;i++) {
			//create a new element and stick it in
			//may need to add IDs to these to make them sort... or
			//maybe not, just have groups for them
			var img = "<img src=\"" + json.caps_self[i].img + "\" />";
			$("#playerCaptures img:last-child").after(img);
		}*/
	}
	if (json.caps_opp) {
		//update opponent's captures
		addCaptures(json.caps_opp, $("#opponentCaptures"));
	}
	if (json.opp_hand) {
		//update opponent's hand
		$("#opponent_" + json.opp_hand[0]).css('display', 'none');
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
	}else if (json.opp_score) {
		$("#txtOppScore").text(json.opp_score);
	}
	
	//need to handle other stuff like koikoi prompt and card selection
	//
	
	//score prompt
	if (json.results) {
		$("#results").html(json.results);
		$("#results").css('display', 'block');
		$("#results").draggable(); //if the user wants to see the field
		screen_on();
		return; //don't let the comet restart
	}


	if (!json.active) {
		$("#playerHand").addClass("handDisabled");
		setTimeout("comet()", 500);
	} else {
		$("#playerHand").removeClass("handDisabled");
	}
}

function comet() {
	cometactive = true;
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
			for (i = 0;i < 8;i++) {

				var cn = "#field_" + i;
				$(cn).get(0).src = json.field[i].img;
				$(cn).addClass(json.field[i].suit);
				$(cn).data('suit', json.field[i].suit);
				$(cn).data('id', i);
			}
			//the other 4 are blank but droppable
			for (i = 8;i < 12;i++) {
				var cn = "#field_" + i;
				$(cn).data('id', i);
			}

			$("#deckCard").data('id', -1); // set this up now

			$(".fieldCard").droppable({drop: function(event, ui) {
					place(ui.draggable.data("id"), $(this).data("id"));
					}});


			//dealer?
			if (!json.active) {
				$("#playerHand").addClass("handDisabled");
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
	if (!dragging && !deck_select)
		$(".fieldcard.cardHighlight").removeClass('cardHighlight');
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

