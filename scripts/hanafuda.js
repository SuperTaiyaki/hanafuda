
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
	el.data('suit', "empty");
}

//apply attributes to a card
function set_card(card, data) {
	card.attr('src', data.img);
	card.addClass(data.suit);
	card.data('suit', data.suit);
	card.data('rank', data.rank);
}

/* enter deck selection mode, where there are multiple options from the field to
 * match a card from the deck. The player can only take the deck card and match
 * it to field cards of the same suit.
 */
function deckselect_enable(card) {
	$("#deckCard").draggable("option", "disabled", false);
	unmark_field();
	var month = card.suit;
	mark_field(month, false);
	//should disable highlight and dragging for the main cards
	$(".fieldCard:not(." + month + ")").droppable("option", "disabled", true);
	$(".handCard").draggable("option", "disabled", true);
	deck_select = true;
}

function deckselect_disable(card) {
	//restore the old state
	$("#deckCard").attr('src', "img/back.gif");
	$("#deckCard").draggable("option", "disabled", true);
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
	el.animate(target, 'fast', 'swing', callback);
}
/* Clone an element but overlay it onto the original */
function lift_card(el) {
	var pos = el.offset();
	//could clone with 'true' to make sure all .data moves too
	//only need rank though
	var clone = el.clone().appendTo('body');
	clone.data('rank', el.data('rank'));
	clone.css('top', pos.top);
	clone.css('left', pos.left);
	clone.css('position', 'absolute');
	return clone;
}

/* Pull a card out of the layout (the real card) */
function extract_card(el) {
	var pos = el.offset();
	el.appendTo('body');
	el.css('top', pos.top);
	el.css('left', pos.left);
	el.css('position', 'absolute');
	return el;
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
	//hand: [hand id, field id]
	//	hand id is -1 for the deck card
	//field1: [field id]* cards moving from the field to the captures pile
	//deck: field id
	//	the id of the field location the deck card will move to (-1 if
	//	it's not moving)
	//field2: [field id]*
	//	ids of the cards moving from the field to captures due to the
	//	deck match (only if deck isn't -1)
	
	var el = 0;
	var caps = data.player ? $("#playerCaptures") : $("#opponentCaptures");
	var do_caps1; //anything to capture in the first round?
	var time = 0;
		
		//expose the card first
	if (!data.player) {
		el = extract_card(get_opphand(data.hand[0]));
		set_card(el, data.handcard);

		el.attr('id', 'flyingCard');
		var dest = get_field(data.hand[1]);
		var tgt;
		var cb;
		// if field[data.field] is empty, plant this card there
		if (dest.data('suit') != "empty") {
			tgt = dest.offset();
			tgt.top += 25;
			tgt.left += 25;
			cb = "void()";
		} else {
			tgt = dest.offset();
			cb = function() {
				//don't actually replace the element, that kills
				//the attributes
				var c = {img: el.attr('src'),
					suit: el.data("suit"),
					rank: el.data("rank")};
				clear_suit(dest);
				set_card(dest, c);
				el.remove();
			}
		}
		//let the card sit for a moment...
		setTimeout(function() {move_card(el, tgt, cb);}, 200);
		time += 800;
	} else {
		var dest = get_field(data.hand[1]);
		if (dest.data('suit') == "empty") {
			var fc = $("#flyingCard");
			//card has attributes and junk, so manually copy over
			//the important stuff
			var c = {img: fc.attr('src'),
				suit: fc.data("suit"),
				rank: fc.data("rank")};
			clear_suit(dest);
			set_card(dest, c);
			dest.data('id', data.hand[1]);
			dest.attr('id', "field_" + data.hand[1]);
			dest.removeClass("handCard").addClass("fieldCard");
			fc.remove();
		}
	}

	//time = 1 slide, speed is 600ms (maybe)

	//function to make a class sit in the captures pile
	function settle_card(card) {
		card.css('position', 'static');
		card.attr('id', '');
		card.removeClass().addClass("card capCard");
		card.draggable("option", "disabled", true);
	}


	function field_caps1() {
		//move flyingCard and field[data.field1[]] to captures
		var i;
		for (i = 0;i < data.field1.length;i++) {
			var fc =  get_field(data.field1[i]);
			var fcc = lift_card(fc);
			blank_card(fc);

			var tgti = captureDest(fcc.data('rank'), caps);
			move_card(fcc, tgti.offset(), function() {
					tgti.append(fcc);
					settle_card(fcc);});
		}
		var fc = $("#flyingCard");
		var tgt = captureDest(fc.data('rank'), caps);
		move_card(fc, tgt.offset(), function() {
				tgt.append(fc);
				settle_card(fc);
				});
	}

	function move_decktop() {
		if (data.deck == -1) {
			set_card(get_deckcard(), data.deckcard);
			
			if (data.player)
				deckselect_enable(data.deckcard);
			return;
		}

		var dc = get_deckcard();
		var dcc = lift_card(dc);

		//expose dcc
		set_card(dcc, data.deckcard);

		//change the name just in case the animations overlap
		dcc.attr('id', 'flyingCard2');
		var tgt = get_field(data.deck);
		var tgtpos = tgt.offset();
		var cb;
		if (tgt.data('suit') == "empty") {
			//leaving it on the field somewhere
			cb = function() {
				clear_suit(tgt);
				set_card(tgt, data.deckcard);
				dcc.remove();
			}
		} else {
			tgtpos.top += 25;
			tgtpos.left += 25;
			cb = "void()";
		}
		setTimeout(function() {move_card(dcc, tgtpos, cb)}, 200);
	}

	function deck_capture() {
		//take the card(s) from the deck and put them into captures
		var i;
		for (i = 0;i < data.field2.length;i++) {
			var fc =  get_field(data.field2[i]);
			var fcc = lift_card(fc);
			blank_card(fc);
			var tgti = captureDest(fcc.data('rank'), caps);
			move_card(fcc, tgti.offset(), function() {
					tgti.append(fcc);
					settle_card(fcc);});
		}
		var fc = $("#flyingCard2");
		var tgt = captureDest(fc.data('rank'), caps);
		move_card(fc, tgt.offset(), function() {
				tgt.append(fc);
				settle_card(fc);
				});
	}

	// 1 move in action by this point

	if (data.field1.length > 0) {
		setTimeout(function() {field_caps1();}, time);
		time += 800;
	}

	setTimeout(function() {move_decktop();}, time);
	if (data.deck != -1)
		time += 800;

	if (data.field2.length > 0) {
		setTimeout(function() {deck_capture();}, time);
	}
}
function update(json) {
	if (json.error) {
		alert(json.error);
		return;
	}

	//small things that could be slipped into any update
	if (json.score) {
		$("#txtScore").text(json.score);
	} else if (json.opp_score) {
		$("#txtOppScore").text(json.opp_score);
	}

	if (json.type == "play") {
		update_animate(json);

		if (json.koikoi) {
			var yakus = ""
			for (i = 0;i < json.yaku.length;i++) {
				yakus += json.yaku[i] + "<br />";
			}
			$("#txtHands").html(yakus);
			$("#koikoiPrompt").css('display', 'block');
			screen_on();
		}


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
function update_static(json) {
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
					set_card($(cn), json.hand[i]);
					$(cn).data('id', i);
				}
			}

			//field
			for (i = 0;i < 12;i++) {
				var cn = "#field_" + i;
				set_card($(cn), json.field[i]);
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
	$("#deckCard").draggable({helper: 'clone',
			disabled: true});

//	setTimeout(function() {update_animate({hand: 2, field: [2], deck: [1]});}, 500);
/*	setTimeout(function() {later();}, 1000);
	function later() {
		alert("Later?");
	}*/
/*	clone = extract_card($("#deckCard"));
	move_card(clone, {left: 0, top: 0}, function() {alert("Callback!");});*/
}

function mark_field(month, blank) {
	if (dragging || deck_select)
		return;
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
	extract_card(el);
	//clear_suit(el); // this data is still useful
	el.attr('id', 'flyingCard');
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

