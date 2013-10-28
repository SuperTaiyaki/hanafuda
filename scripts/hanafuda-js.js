//jquery should be loaded

// {{{ Animation/graphical stuff



// }}}




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


