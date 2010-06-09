
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
	el.removeClass("empty");
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

function captureDest(rank, path) {
	var group = "Dregs";
	switch(rank) {
		case 20:
			group = "Brights";
			break;
		case 10:
			group = "Animals";
			break;
		case 5:
			group = "Slips";
	}
	var target = path.children(".captures" + group).children().last();
	return target;
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

/* Update cards in the field */
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

/* Set the player's hand as active or inactive. This currently involves a grey
 * shade behind the disabled player and dragging is disabled.
 */
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

/* Fly el to a new location, then
 * call the callback.
 */
function move_card(el, target, callback) {
	el.animate(target, 600, 'swing', callback);
}
/* Clone an element but overlay it onto the original */
function lift_card(el) {
	var pos = el.offset();
	var clone = el.clone().appendTo('body');
	clone.css('top', pos.top);
	clone.css('left', pos.left);
	clone.css('position', 'absolute');
	return clone;
//	clone.draggable();
}

/* Pull a card out of the layout (the real card) */
function extract_card(el) {
	var pos = el.offset();
	el.appendTo('body');
	el.css('top', pos.top);
	el.css('left', pos.left);
	el.css('position', 'absolute');
	return el;
//	clone.draggable();
}

//set a field card to an empty space
function blank_card(card) {
	card.attr('src', "img/empty.gif");
	clear_suit(card);
	card.data('rank', -1);
	card.data('suit', 'empty');
	card.addClass("empty");
}

function get_hand(id) {
	return $("#player_" + id);
}
function get_field(id) {
	return $("#field_" + id);
}
function get_opphand(id) {
	return $("#opponent_" + id);
}
function get_deckcard() {
	return $("#deckCard");
}

function update_animate(data) {
	//format of data is
	//hand: id of card moved from hand to field (-1 if active player)
	//	Note this is an index into the opponent's hand
	//field: field id(s) of card matched to hand
	//deck: field id(s) of card matched to deck
	//field2: id of card moved from deck to field
	//player: whether this is for the player or the opponent
	//only one of deck or field2 should be used
	
	// Before entering this function:
	// -Set the field card the player put down (if it didn't match)
	// -Expose the card the opponent played
	// -Expose the card on the deck
	
	var el = 0;
	var caps = data.player ? $("#playerCaptures") : $("#opponentCaptures");
	var do_caps1; //anything to capture in the first round?
	if (!data.player && data.field) {
		//move hand[data.hand] to field[0]
		el = extract_card(get_opphand(data.hand));
		el.attr('id', 'flyingCard');
		var dest = get_field(data.field[0]);
		var tgt;
		var cb;
		// if field[data.field] is empty, plant this card there
		if (dest.data('suit') != "empty") {
			tgt = dest.offset();
			tgt.top += 25;
			tgt.left += 25;
			cb = "void()";
			do_caps1 = true;
		} else {
			tgt = dest.offset();
			do_caps1 = false;
			cb = function() {
				//copy the attributes down and delete
				//TODO
			}
		}

		move_card(el, tgt, cb);
	}
	
	//if the card was just laid down there's nothing to do

	//time = 1 slide, speed is 600ms (maybe)

	//function to make a class sit in the captures pile
	function settle_card(card) {
		card.css('position', 'static');
		card.attr('id', '');
		card.removeClass().addClass("card capCard");
	}


	function field_caps1() {
		//move flyingCard and field[data.field[]] to captures
		var i;
		for (i = 0;i < data.field.length;i++) {
			var fc =  get_field(data.field[i]);
			var fcc = lift_card(fc);
			blank_card(fc);
			var tgt = captureDest(fcc.data('rank'), caps);
			move_card(fcc, tgt.offset(), function() {
					tgt.append(fcc);
					settle_card(fcc);});
		}
		var fc = $("#flyingCard");
		var tgt = captureDest(fc.data('rank'), caps);
		//ewwww
		move_card(fc, tgt.offset(), function() {
				tgt.append(fc);
				settle_card(fc);
				});
	}

	function move_decktop() {
		var dc = get_deckcard();
		var dcc = lift_card(dc);
		//change the name just in case the animations overlap
		dcc.attr('id', 'flyingCard2');
		var tgtpos;

		var cb;
		if (data.field2) {
			//leaving it on the field somewhere
			var tgt = get_field(data.field2);
			tgtpos = tgt.offset();

			cb = function() {
				var imgname = dcc.attr('src');
				tgt.attr('src', imgname);
				//all attributes of the card should be set in
				//the background
				dcc.remove();
			}
		} else {
			var tgt = get_field(data.deck[0]);
			tgtpos = tgt.offset();

			tgtpos.top += 25;
			tgtpos.left += 25;
			cb = "void()";
		}
		move_card(dcc, tgtpos, cb);
	}

	function deck_capture() {
		//take the card(s) from the deck and put them into captures
		var i;
		for (i = 0;i < data.deck.length;i++) {
			var fc =  get_field(data.deck);
			var fcc = lift_card(fc);
			blank_card(fc);
			var tgt = captureDest(fcc.data('rank'), caps);
			move_card(fcc, tgt.offset(), function() {
					tgt.append(fcc);
					settle_card(fcc);});
		}
		var fc = $("#flyingCard2");
		var tgt = captureDest(fc.data('rank'), caps);
		//ewwww
		move_card(fc, tgt.offset(), function() {
				tgt.append(fc);
				settle_card(fc);
				});
	}
	if (do_caps1)
		setTimeout(function() {field_caps1();}, 1000);

	setTimeout(function() {move_decktop();}, 1500);
	if (data.deck) {
		setTimeout(function() {deck_capture();}, 2400);
	}

}
function update2(json) {
	if (json.error) {
		alert(json.error);
		return;
	}
	var i;
	anim = {hand: -1};

/*	if (json.field) {
		updateField(json.field)
	}*/
	/* rephrase the 'sources' data into animation data*/
	if (json.hand) {
		// hide cards from the player's own hand
		for (i = 0;i < json.hand.length;i++) {
			var idx = json.hand[i];
			var cn = "#player_" + idx;
			$(cn).css('display', 'none');
		}
	}

	if (json.caps_opp) {
		// flip the card, store the index
		// same format as updateField
		var oc = $("#opponent_" + json.caps_opp[0].id);
		oc.attr('src', json.caps_opp[0].img);
		anim.hand = json.inputs.hand;

		//nasty hacky logic
		//Basically, check the first card taken from the field is the
		//same as the card the user selected. If it is, it was a
		//capture. Otherwise they planted it.
		if (json.inputs.field != json.field[0].idx) {
			anim.field = json.field[0].idx;
		} else {
			anim.field = json.sources[1];
		}
		//suit and rank won't be needed, it's getting pushed to caps
		
	}

	/* Sources contains most of the important information.
	 * hand: pull from json.input
	 * field: basically sources[1], though if nothing was captured in the
	 *   first round it needs to be pulled from elsewhere
	 * deck: sources[2]
	 * field2: if sources[2] is empty field2 will be the last json.field entry
	 */

	// *** Animation work was done up to here ***

	if (json.caps_self) {
		//update own captures
		addCaptures(json.caps_self, $("#playerCaptures"));
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
/* General update worker function, take an update from the backend and process
 * the fields.
 */
function update(json) {
	if (json.error) {
		alert(json.error);
		return;
	}
	var i;

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
					place(ui.draggable.data("id"), $(this).data("id"), $(ui.draggable));
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
				var month = $(this).data('suit');
				draggingthing = $(this);
				draggingthing.css('opacity', 0.2);
				drag_targets(month, true);
				},
			stop: function() {
				dragging = false;
				draggingthing.css('opacity', 1.0);
				unmark_field();
				}});
	$("#playerHand > .handCard").hover(function() {
			//start hover handler, mark the suit
			var suit = $(this).data('suit');
			mark_field(suit, true);
			}, function() {
			//stop hover handler
			unmark_field();
			});

	setTimeout(function() {update_animate({hand: 2, field: [2], deck: [1]});}, 500);
/*	setTimeout(function() {later();}, 1000);
	function later() {
		alert("Later?");
	}*/
/*	clone = extract_card($("#deckCard"));
	move_card(clone, {left: 0, top: 0}, function() {alert("Callback!");});*/
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
 * fieldID: ID of the card matched
 */
function place(handID, fieldID, el) {
	if (!get_field(fieldID).hasClass("empty")) {
		extract_card(el);
		clear_suit(el);
		el.attr('id', 'flyingCard');
	}
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

