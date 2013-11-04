
opponent_play_order = []
dragging = false

log = (msg) ->
    console.log(msg)

animation_queue = []
animation_frame = []
animating = false; # Really don't like trying to block this way...

animate_next = () ->
    if (animation_queue.length == 0)
        animating = false
        return
    animating = true

    events = animation_queue.shift()
    ev() for ev in events

    setTimeout(() ->
            animate_next()
        , 1000)

animate_gate = () ->
    if (animation_frame.length == 0)
        return

    run = (animation_queue.length == 0)
    animation_queue.push(animation_frame)
    # console.log("Animation push:");
    # console.log(animation_frame);
    animation_frame = []
    if (run && !animating)
        animate_next()

# Fly el to a new location, then
# call the callback.
move_card = (el, target, callback) ->
    animation_frame.push(() ->
        el.animate(target, 'fast', 'swing', callback)
    )


# Raise a screen onto the playing area to block interaction. Used for dialogs.
screen_on = () ->
    $("#screen").css('display', 'block')

screen_off = () ->
    $("#screen").css('display', 'none')

# Set the player's hand as active or inactive. This currently involves a grey
# shade behind the disabled player and dragging is disabled.
enable_hand = () ->
    $("#playerHand").removeClass("handDisabled")
    $("#opponentHand").addClass("handDisabled")
    $("#playerHand > .handCard").draggable("option", "disabled", false)

disable_hand = () ->
    $("#opponentHand").removeClass("handDisabled")
    $("#playerHand").addClass("handDisabled")
    $("#playerHand > .handCard").draggable("option", "disabled", true)


# Strip all suits off a card
clear_suit = (el) ->
    for i in [0...12]
        el.removeClass("mon" + i)
    el.removeClass("empty")
    el.data('suit', "empty")

# apply attributes to a card
set_card = (card, data) ->
    card.attr('src', data.img)
    card.addClass(data.suit)
    card.data('suit', data.suit)
    card.data('rank', data.rank)

# set a field card to an empty space
blank_card = (card) ->
    card.attr('src', "/img/empty.gif")
    clear_suit(card)
    card.data('rank', -1)
    card.data('suit', 'empty')
    card.addClass("empty")

# Find the correct slot for a captured card
capture_dest = (rank, path) ->
    group = "Dregs"
    switch rank
        when 20
            group = "Brights"
        when 10
            group = "Animals"
        when 5
            group = "Slips"
    path.children(".captures" + group).children().last()

# Clone an element but overlay it onto the original
lift_card = (el) ->
    pos = el.offset()
    clone = el.clone(true).appendTo('body')
    clone.data('rank', el.data('rank'))
    clone.css('top', pos.top)
    clone.css('left', pos.left)
    clone.css('position', 'absolute')
    # uhh... it's chainable, so the return should be clone?

# Pull a card out of the layout (the real card) 
extract_card = (el) ->
    pos = el.offset()
    el.appendTo('body')
    el.css('top', pos.top)
    el.css('left', pos.left)
    el.css('position', 'absolute')

get_hand = (id) ->
    $("#player_" + id)
get_field = (id) ->
    $("#field_" + id)
get_opphand = (id) ->
    $("#opponent_" + id)
get_deckcard = () ->
    $("#deckCard")


# enter deck selection mode, where there are multiple options from the field to
# match a card from the deck. The player can only take the deck card and match
# it to field cards of the same suit.
#
deck_select = false
deckselect_enable = (card) ->
    $("#deckCard").draggable("option", "disabled", false)
    $("#deckCard").addClass("cardHighlight")
    unmark_field()
    month = card.suit
    mark_field(month, false)
    # should disable highlight and dragging for the main cards
    $(".fieldCard:not(." + month + ")").droppable("option", "disabled", true)
    $(".fieldCard." + month).droppable("option", "disabled", false)
    $(".handCard").draggable("option", "disabled", true)
    deck_select = true

deckselect_disable = (card) ->
    # restore the old state
    $("#deckCard").attr('src', "/img/back.gif")
    $("#deckCard").removeClass("cardHighlight")
    $("#deckCard").draggable("option", "disabled", true)
    $(".fieldCard").droppable("option", "disabled", false)
    $(".handCard").draggable("option", "disabled", false)
    deck_select = false
    unmark_field()


# Make field cards of the matching suit into drop targets
drag_targets = (suit, blank) ->
    if (deck_select)
        return; # don't bother it
    $(".fieldCard").droppable("option", "disabled", true)
    if (suit == "")
        return
    droptgts = $(".fieldCard." + suit)
    if (droptgts.length > 0)
        droptgts.droppable("option", "disabled", false)
    else
        $(".fieldCard.empty").droppable("option", "disabled", false)

# Highlight field cards of the matching suit
mark_field = (month, blank) ->
    if (dragging || deck_select)
        return
    tgts = $("#fieldCards ." + month)
    if (tgts.length > 0)
        tgts.addClass('cardHighlight')
    else if (blank)
        $(".fieldCard.empty").addClass('cardHighlight')

# Clear field highlights
unmark_field = () ->
    if (!dragging && !deck_select)
        $(".fieldCard.cardHighlight").removeClass('cardHighlight')
        drag_targets("", false)

# Plant the player's dragged card if necessary
self_place_card = (field) ->
    dest = get_field(field)
    if (dest.data('suit') != "empty")
        # A capture, nothing to do
        return
    fc = $("#flyingCard")
    # card has attributes and junk, so manually copy over
    # the important stuff
    c =
        'img': fc.attr('src'),
        'suit': fc.data("suit"),
        'rank': fc.data("rank")
    clear_suit(dest)
    set_card(dest, c)
    dest.data('id', field); #  TODO: Maybe strip these out? They don't seem useful
    dest.attr('id', "field_" + field)
    dest.removeClass("handCard").addClass("fieldCard")
    fc.remove()

opponent_place_card = (field, card) ->
    hand = opponent_play_order.pop()
    el = extract_card(get_opphand(hand))
    set_card(el, card)
    el.attr('id', 'flyingCard')

    dest = get_field(field)
    tgt = dest.offset()

    if (dest.data('suit') == 'empty')
        cb = () ->
            #don't actually replace the element, that kills
            #the attributes
            c =
                'img': el.attr('src'),
                'suit': el.data("suit")
                'rank': el.data("rank")
            clear_suit(dest)
            set_card(dest, c)
            el.remove()
    else
        tgt.top += 25
        tgt.left += 25
        cb = "void()" # TODO: What's the CoffeeScript way to do this?
    move_card(el, tgt, cb)

opponent_fly_card = (location, card) ->
    hand = opponent_play_order.pop()
    el = extract_card(get_opphand(hand))
    set_card(el, card)
    el.attr('id', 'flyingCard')
    dest = get_field(location)

    tgt = dest.offset()
    tgt.top += 25
    tgt.left += 25

    move_card(el, tgt)

# function to make a class sit in the captures pile
settle_card = (container, card) ->
    container.append(card)
    card.css('position', 'static')
    card.attr('id', '')
    card.removeClass().addClass("card capCard")
    #card.draggable("option", "disabled", true)

#get around annoying JS not-really-closures
#TODO: Figure out how this works with CoffeeScript
make_settlecard = (container, card) ->
    () ->
        settle_card(container, card)

capture_cards = (locations, player) ->
    #move flyingCard and field[data.field1[]] to captures
    caps = if player == playerid then $("#playerCaptures") else $("#opponentCaptures")

    for loc in locations
        fc = get_field(loc)
        fcc = lift_card(fc)
        blank_card(fc)

        tgti = capture_dest(fcc.data('rank'), caps)

        move_card(fcc, tgti.offset(), make_settlecard(tgti, fcc))

capture_single = (card, player) ->
    # TODO: playerid probably isn't available in this scope
    caps = if player == playerid then $("#playerCaptures") else $("#opponentCaptures")
    tgt = capture_dest(card.data('rank'), caps)
    move_card(card, tgt.offset(), make_settlecard(tgt, card))


# Lift the card off the top of the deck, blank the card underneath, return the new
# handle (as flyingCard2)
# Not useful if the deck card isn't flipped up
deck_lift = () ->
    dc = get_deckcard()
    dcc = lift_card(dc)
    blank_card(dc)
    dc.attr('src', '/img/back.gif')
    # set_card(dcc, data.deckcard)

    # change the name just in case the animations overlap
    dcc.attr('id', 'flyingCard2')
    # return dcc;

deck_place = (location, card) ->
    dcc = deck_lift()
    tgt = get_field(location)
    tgtpos = tgt.offset()
    # leaving it on the field somewhere
    cb = () ->
        clear_suit(tgt)
        set_card(tgt, card)
        dcc.remove()
    move_card(dcc, tgtpos, cb)

deck_capture = (locations, player) ->
    # Fly the card to the temporary location on top of a captured card
    dcc = $("#flyingDeckCard")
    # flyingCard won't be null in case of a :deck_match
    if (dcc.length == 0)
        dcc = deck_lift()
        target = get_field(locations[0])
        tgt_pos = target.offset()
        tgt_pos.top += 25
        tgt_pos.left += 25
    #    dcc.attr('id', 'flyingCard');

        move_card(dcc, tgt_pos)
        animate_gate()

    capture_single(dcc, player)

    # Take all the captures
    capture_cards(locations, player)

draw_card = (card) ->
    set_card(get_deckcard(), card)

start_game = () ->
    $("#alert").slideUp('fast')
    $("#screen").fadeOut(100)

koikoi_prompt = (yaku) ->
    text = ""
    for y in yaku
        text += y + "<br />"
    $("#txtHands").html(text)
    $("#koikoiPrompt").css('display', 'block')
    screen_on()


run_event = (data) ->
    console.log(data.type)
    console.log(data)
    switch data.type
        when 'init'
            board_init(data)
        when 'game_start'
            start_game()
        # Hand -> Field
        when 'play_card'
            if (data.player != playerid)
                opponent_place_card(data.location, data.card)
            else
                # Plant the card
                self_place_card(data.location)
        when 'take_card'
            #if (data.player != playerid) {
            #    opponent_fly_card(data.location, data.card)
            #}
            capture_cards(data.location, data.player)
            capture_single($("#flyingCard"), data.player)
        when 'draw_card'
            draw_card(data.card)
            # Not symmetrical with play_card/take_card
        when ':draw_match'
            deckselect_enable(data.card)
        when 'draw_place'
            deck_place(data.location, data.card)
        when 'draw_capture'
            deck_capture(data.location, data.player)
        when ':koikoi'
            koikoi_prompt(data.yaku)
        when 'turn_end'
            disable_hand()
        when 'start_turn'
            enable_hand()
        when 'alert'
            $("#txtAlert").html(data.text)
            # slideUp chained onto a slideDown
            $("#alert").slideDown('fast', () ->
                setTimeout(() ->
                    $("#alert").slideUp('fast')
                , 1000))
        when 'results'
            $("#results").html(data.data)
            $("#results").css('display', 'block')
            $("#results").draggable(); #if the user wants to see stuff
            screen_on()
        else
            alert("Unknown message: " + data.type)
    animate_gate()


board_init = (state) ->
    gamelink = state.gamelink
    $("#txtGameId").html(gameid)
    # hand
    for i in [0...8]
        cn = "#player_" + i
        # TODO: This is a bit awkward... is it really -1 in the hand data? 
        # Can't I just iterate over state.hand like a sane loop?
        if (state.hand[i].rank == -1)
            $(cn).css('display', 'none')
        else
            set_card($(cn), state.hand[i])
            $(cn).data('id', i)
    # field
    for i in [0...12]
        cn = "#field_" + i
        set_card($(cn), state.field[i])
        $(cn).data('id', i)

    for cap in state.captures_player
        tgt = capture_dest(cap.rank, $("#playerCaptures"))
        tgt.append("<img src=\"" + cap.img + "\" />")
    
    for cap in state.captures_opp
        tgt = capture_dest(cap.rank, $("#opponentCaptures"))
        tgt.append("<img src=\"" + cap.img + "\" />")

    # TODO: More global nastiness
    for i, idx in state.opp_hand
        get_opphand(i).css('display', 'none')
        opponent_play_order.push(idx)

    $("#screen").css('display', 'block')
    $("#alert").css('display', 'block')
    disable_hand()

    if (!state.game_started)
        $("#screen").css('display', 'block')
        $("#alert").css('display', 'block')

    if (!state.active)
        disable_hand()
    else
        enable_hand()

# User took one of their cards and placed it, either on a matched card on an
# empty space. 
# handID: ID of the card taken (-1 if it's from the deck, special case)
# fieldID: ID of the card matched
# Called from the field card droppable handler
place = (handID, fieldID, el, tgt) ->
    # This isn't cancelling right elsewhere
    dragging = false
    unmark_field() # May have to forcefully cancel the dragging global
    if (deck_select)
        el = lift_card(el)
    else
        extract_card(el)

    el.css('top', tgt.top)
    el.css('left', tgt.left)
    el.css('opacity', 1.0)
    # clear_suit(el); // this data is still useful
    if (handID == -1)
        el.attr('id', 'flyingDeckCard')
    else
        el.attr('id', 'flyingCard')

    # special case, match deck to field
    if (handID == -1)
        # should set this up so it can be bounced, but meh
        deckselect_disable()

    data =
        'type': 'place'
        'hand': handID
        'field': fieldID
    wsock.send(JSON.stringify(data))

ws_init = () ->
    wsock = new WebSocket('ws://localhost:8080/play_ws')
    wsock.onopen = () ->
        data =
            'type': 'client_connect'
            'game_id': gameid
            'player': playerid
        wsock.send(JSON.stringify(data))

    wsock.onmessage = (evt) ->
        data = JSON.parse(evt.data)
        run_event evt for evt in data
    window.wsock = wsock

init = ->
    log("In init function")
    ws_init()
    $("#deckCard").data('id', -1)

    $(".fieldCard").droppable({drop: (event, ui) ->
            place(ui.draggable.data("id"), $(this).data("id"),
                ui.draggable, ui.position)
        , 'disabled': true})

    # handle dragging and hovering cards
    # On hover highlight the cards that match the highlighted card
    # On drag lock the highlight
    # On drag release or unhover remove the highlight
    draggingthing = 0 # Better than having it be global... hopefully this means the 
    # references inside the two lambdas will point here
    $("#playerHand > .handCard").draggable(
            helper: 'clone'
            # TODO: Clean up nasty global window.dragging business
            # So in here, 'this' is apparently the base object while ui.helper is the flying bit
            start: (event, ui) ->
                dragging = true; #need to mark the original somehow
                month = $(this).data('suit')
                draggingthing = ui.helper # $(this)
                draggingthing.css('opacity', 0.2)
                drag_targets(month, true)
            stop: () ->
                console.log("Drag stop")
                dragging = false
                draggingthing.css('opacity', 1.0)
                )
    $("#playerHand > .handCard").hover(() ->
        # start hover handler, mark the suit
            suit = $(this).data('suit')
            mark_field(suit, true)
        ,() ->
            # stop hover handler
            unmark_field()
            )
    $("#deckCard").draggable(
        helper: 'clone',
        disabled: true)
    log("Finished init")



$(document).ready(() ->
    init()
)

# Stuff to export globals out of the namespace function
root = exports ? this

root.showLink = () ->
    prompt("Give this link to your opponent:", gamelink)
    false


root.koikoi = () ->
    wsock.send(JSON.stringify(
        'type': 'koikoi'))
    screen_off()
    $("#koikoiPrompt").css('display', 'none')

root.endGame = () ->
    wsock.send(JSON.stringify(
        'type': 'end_game'))
    $("#koikoiPrompt").css('display', 'none')

