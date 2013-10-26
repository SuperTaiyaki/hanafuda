//jquery should be loaded


var dragging = false;
var deck_select = false;
var cometactive = false;

function log(msg) {
    //opera-specific JS debugging
    window.opera.postError(msg);
}
// {{{ Animation/graphical stuff
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

//set a field card to an empty space
function blank_card(card) {
    card.attr('src', "/img/empty.gif");
    clear_suit(card);
    card.data('rank', -1);
    card.data('suit', 'empty');
    card.addClass("empty");
}

/* enter deck selection mode, where there are multiple options from the field to
 * match a card from the deck. The player can only take the deck card and match
 * it to field cards of the same suit.
 */
function deckselect_enable(card) {
    $("#deckCard").draggable("option", "disabled", false);
    $("#deckCard").addClass("cardHighlight");
    unmark_field();
    var month = card.suit;
    mark_field(month, false);
    //should disable highlight and dragging for the main cards
    $(".fieldCard:not(." + month + ")").droppable("option", "disabled", true);
    $(".fieldCard." + month).droppable("option", "disabled", false)
    $(".handCard").draggable("option", "disabled", true);
    deck_select = true;
}

function deckselect_disable(card) {
    //restore the old state
    $("#deckCard").attr('src', "/img/back.gif")
    $("#deckCard").removeClass("cardHighlight");
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

/* Find the correct slot for a captured card */
function capture_dest(rank, path) {
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

/* Make field cards of the matching suit into drop targets */
function drag_targets(suit, blank) {
    if (deck_select)
        return; //don't bother it
    $(".fieldCard").droppable("option", "disabled", true);
    if (suit == "")
        return;
    var droptgts = $(".fieldCard." + suit);
    if (droptgts.length > 0)
        droptgts.droppable("option", "disabled", false);
    else
        $(".fieldCard.empty").droppable("option", "disabled", false);
}

/* Highlight field cards of the matching suit */
function mark_field(month, blank) {
    if (dragging || deck_select)
        return;
    var tgts = $("#fieldCards ." + month);
    if (tgts.length > 0)
        tgts.addClass('cardHighlight');
    else if (blank)
        $(".fieldCard.empty").addClass('cardHighlight');
}
/* Clear field highlights */
function unmark_field() {
    if (!dragging && !deck_select) {
        $(".fieldCard.cardHighlight").removeClass('cardHighlight');
        drag_targets("", false);
    }
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
    var clone = el.clone(true).appendTo('body');
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
// }}}

opponent_play_order = [];

function opponent_place_card(field, card) {
    // TODO: Randomly pick a card from opponent's hand
    var hand = opponent_play_order.pop();
    var el = extract_card(get_opphand(hand));
    set_card(el, card);
    el.attr('id', 'flyingCard');
    var dest = get_field(field);

    var tgt = dest.offset();
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
    move_card(el, tgt, cb);
}

function opponent_fly_card(location, card) {
    var hand = opponent_play_order.pop();
    var el = extract_card(get_opphand(hand));
    set_card(el, card);
    el.attr('id', 'flyingCard');
    var dest = get_field(location);

    var tgt = dest.offset();
    tgt.top += 25;
    tgt.left += 25;

    move_card(el, tgt);
}

function capture_cards(locations, player) {
    //function to make a class sit in the captures pile
    function settle_card(container, card) {
        container.append(card);
        card.css('position', 'static');
        card.attr('id', '');
        card.removeClass().addClass("card capCard");
        //card.draggable("option", "disabled", true);
    }
    //get around annoying JS not-really-closures
    function make_settlecard(container, card) {
        return function() {
            settle_card(container, card);};
    }

    //move flyingCard and field[data.field1[]] to captures
    var caps = player === playerid ? $("#playerCaptures") : $("#opponentCaptures");
    var i;
    for (i = 0;i < locations.length;i++) {
        var fc = get_field(locations[i]);
        var fcc = lift_card(fc);
        blank_card(fc);

        var tgti = capture_dest(fcc.data('rank'), caps);

        move_card(fcc, tgti.offset(), make_settlecard(tgti, fcc, i));
    }
    var fc = $("#flyingCard2");
    var tgt = capture_dest(fc.data('rank'), caps);
    move_card(fc, tgt.offset(), make_settlecard(tgt, fc));
}

function self_place_card(field) {
    var dest = get_field(field);
    if (dest.data('suit') != "empty") {
        // A capture, nothing to do
        return;
    }
    var fc = $("#flyingCard");
    //card has attributes and junk, so manually copy over
    //the important stuff
    var c = {img: fc.attr('src'),
        suit: fc.data("suit"),
        rank: fc.data("rank")};
    clear_suit(dest);
    set_card(dest, c);
    dest.data('id', field); // TODO: Maybe strip these out? They don't seem useful
    dest.attr('id', "field_" + field);
    dest.removeClass("handCard").addClass("fieldCard");
    fc.remove();
}

function draw_card(card) {
    // Draw the card
    set_card(get_deckcard(), card);
}

// Lift the card off the top of the deck, blank the card underneath, return the new
// handle (as flyingCard2)
// Not useful if the deck card isn't flipped up
function deck_lift() {
    var dc = get_deckcard();
    var dcc = lift_card(dc);
    blank_card(dc);
    dc.attr('src', '/img/back.gif');
    // set_card(dcc, data.deckcard);

    //change the name just in case the animations overlap
    dcc.attr('id', 'flyingCard2');
    return dcc;
}

function deck_place(location, card) {
    var dcc = deck_lift();
    var tgt = get_field(location);
    var tgtpos = tgt.offset();
    var cb;
    //leaving it on the field somewhere
    cb = function() {
        clear_suit(tgt);
        set_card(tgt, card);
        dcc.remove();
    }
    setTimeout(function() {move_card(dcc, tgtpos, cb)}, 200);

}

function deck_capture(locations, player) {
    // Fly the card to the temporary location on top of a captured card
    var dcc = deck_lift();
    var target = get_field(locations[0]);
    var tgt_pos = target.offset();
    tgt_pos.top += 25;
    tgt_pos.left += 25;

    setTimeout(function() {move_card(dcc, tgt_pos)}, 200);

    // Take all the captures
    capture_cards(locations, player);
    return;
}

function update_animate(data) {
    //format of data is
    //hand: [hand id, field id]
    //  hand id is -1 for the deck card
    //field1: [field id]* cards moving from the field to the captures pile
    //deck: field id
    //  the id of the field location the deck card will move to (-1 if
    //  it's not moving)
    //field2: [field id]*
    //  ids of the cards moving from the field to captures due to the
    //  deck match (only if deck isn't -1)
    
    var el = 0;
    var caps = data.player ? $("#playerCaptures") : $("#opponentCaptures");
    var time = 0;

    if (!data.player) {
        if (data.deck == -2) {
            el = $("#flyingCard");
            blank_card(get_deckcard());
            get_deckcard().attr('src', 'img/back.gif');
        } else {
            el = extract_card(get_opphand(data.hand[0]));
            set_card(el, data.handcard);
            el.attr('id', 'flyingCard');
        }

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

    //function to make a class sit in the captures pile
    function settle_card(container, card) {
        container.append(card);
        card.css('position', 'static');
        card.attr('id', '');
        card.removeClass().addClass("card capCard");
        card.draggable("option", "disabled", true);
    }
    //get around annoying JS not-really-closures
    function make_settlecard(container, card) {
        return function() {
            settle_card(container, card);};
    }

    // Fly all the field cards of one suit to the captures pile
    function field_caps1() {
        //move flyingCard and field[data.field1[]] to captures
        var i;
        for (i = 0;i < data.field1.length;i++) {
            var fc =  get_field(data.field1[i]);
            var fcc = lift_card(fc);
            blank_card(fc);

            var tgti = capture_dest(fcc.data('rank'), caps);

            move_card(fcc, tgti.offset(), make_settlecard(tgti, fcc, i));
        }
        var fc = $("#flyingCard");
        var tgt = capture_dest(fc.data('rank'), caps);
        move_card(fc, tgt.offset(), make_settlecard(tgt, fc));
    }

    function move_decktop() {
        if (data.deck == -1) {
            set_card(get_deckcard(), data.deckcard);
            clear_suit(get_deckcard());
            
            if (data.player)
                deckselect_enable(data.deckcard);
            else {
                var dc = get_deckcard();
                var c = lift_card(dc);
                c.attr('id', 'flyingCard');
            }
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
            var tgti = capture_dest(fcc.data('rank'), caps);
            move_card(fcc, tgti.offset(), make_settlecard(tgti, fcc));
        }
        var fc = $("#flyingCard2");
        var tgt = capture_dest(fc.data('rank'), caps);
        move_card(fc, tgt.offset(), make_settlecard(tgt, fc));
    }

    if (data.field1.length > 0) {
        setTimeout(function() {field_caps1();}, time);
        time += 800;
    }

    if (data.deck == -2) {
        return; //half update, just the player selection
    }

    setTimeout(function() {move_decktop();}, time);
    if (data.deck != -1)
        time += 800;

    if (data.field2.length > 0) {
        setTimeout(function() {deck_capture();}, time);
    }
}

/*
function update(json) {
    if (!json) {
        alert("Connection to server lost.");
        return;
    }

    if (json.error) {
        alert(json.error);
        return;
    }
    if (json.start_game) {
        start_game();
    }

    //small things that could be slipped into any update
    if (json.score) {
        $("#txtScore").text(json.score);
    } else if (json.opp_score) {
        $("#txtOppScore").text(json.opp_score);
    }

    if (json.multiplier) {
        $("#txtMultiplier").text(json.multiplier);
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
    if (json.alert) {
        $("#txtAlert").html(json.alert);
        $("#alert").slideDown('fast', function() {
                setTimeout(function() {$("#alert").slideUp('fast');}, 1000);
                });
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
*/

function showLink() {
    prompt("Give this link to your opponent:", gamelink);
    return false;
}

function start_game() {
    $("#alert").slideUp('fast');
    $("#screen").fadeOut(100);
    return;
}

function run_event(data) {
    console.log(data.type);
    console.log(data);
    switch(data.type) {
        case 'init':
            board_init(data);
            break;
        case 'game_start':
            start_game();
            break;
        // Hand -> Field
        case 'play_card':
            if (data.player != playerid) {
                opponent_place_card(data.location, data.card);
            } else {
                // Plant the card
                self_place_card(data.location);
            }
            break;
        case 'take_card':
            /*if (data.player != playerid) {
                opponent_fly_card(data.location, data.card);
            }*/
            capture_cards(data.location, data.player);
            break;
        case 'draw_card':
            draw_card(data.card);
            break;
        case 'draw_place':
            deck_place(data.location, data.card);
            break;
        case 'draw_capture':
            deck_capture(data.location, data.player);
            break;
        case 'turn_end':
            disable_hand();
            break;
        case 'start_turn':
            enable_hand();
            break;

        default:
            alert("Unknown message: " + data.type);
    }

}

function ws_init() {
    wsock = new WebSocket('ws://localhost:8080/play_ws');
    wsock.onopen = function() {
        var data = new Object;
        data.type = 'client_connect';
        data.game_id = gameid;
        data.player = playerid;
        wsock.send(JSON.stringify(data));
    };
    wsock.onmessage = function(evt) {
        var data = JSON.parse(evt.data);
        for (var i = 0;i < data.length;i++) {
            run_event(data[i]);
        }
    };
}

function board_init(state) {
    var i;
    gamelink = state.gamelink;
    $("#txtGameId").html(gameid);
    //hand
    for (i = 0;i < 8;i++) {
        var cn = "#player_" + i;
        if (state.hand[i].rank == -1) {
            $(cn).css('display', 'none');
        } else {
            set_card($(cn), state.hand[i]);
            $(cn).data('id', i);
        }
    }

    //field
    for (i = 0;i < 12;i++) {
        var cn = "#field_" + i;
        set_card($(cn), state.field[i]);
        $(cn).data('id', i);
    }

    for (i = 0;i < state.captures_player.length;i++) {
        var tgt = capture_dest(state.captures_player[i].rank, $("#playerCaptures"));
        tgt.append("<img src=\"" + state.captures_player[i].img + "\" />");
    }
    for (i = 0;i < state.captures_opp.length;i++) {
        var tgt = capture_dest(state.captures_opp[i].rank, $("#opponentCaptures"));
        tgt.append("<img src=\"" + state.captures_opp[i].img + "\" />");
    }
    for (i = 0;i < state.opp_hand.length;i++) {
        get_opphand(state.opp_hand[i]).css('display', 'none');
    opponent_play_order.push(i);
    // TODO: shuffle play_order
    }

    $("#screen").css('display', 'block');
    $("#alert").css('display', 'block');
    disable_hand();

    if (!state.game_started) {
        $("#screen").css('display', 'block');
        $("#alert").css('display', 'block');
    }
    if (!state.active) {
        disable_hand();
    } else {
        enable_hand();
    }
}

/* Set up the initial board. Easier to do this via AJAX than to populate the inital HTML */
function init() {
    ws_init()

    $("#deckCard").data('id', -1);

    $(".fieldCard").droppable({drop: function(event, ui) {
            place(ui.draggable.data("id"), $(this).data("id"),
            ui.draggable, ui.position);
            },
            'disabled': true});

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
}


/* User took one of their cards and placed it, either on a matched card on an
 * empty space. 
 * handID: ID of the card taken (-1 if it's from the deck, special case)
 * fieldID: ID of the card matched
 */
function place(handID, fieldID, el, tgt) {
    if (deck_select) {
        el = lift_card(el);
    } else {
        extract_card(el);
    }
    el.css('top', tgt.top);
    el.css('left', tgt.left);
    el.css('opacity', 1.0);
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

    var data = {};
    data['type'] = 'place';
    data['hand'] = handID;
    data['field'] = fieldID;
    wsock.send(JSON.stringify(data));

    return;
}

function koikoi() {
    $.getJSON('koikoi', function(json) {
            update(json);
            //processYaku(json);
    });
    screen_off();
    $("#koikoiPrompt").css('display', 'none');
}

function endGame() {
    $.getJSON('endgame', function(json) {
            $("#koikoiPrompt").css('display', 'none');
            update(json);
    });
    
}

$(document).ready(function() {
        init();
        });

