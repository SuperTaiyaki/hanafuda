
opponent_play_order = []
dragging = false
playerid = -1

log = (msg) ->
    console.log(msg)

animation_queue = []
animation_frame = []
animating = false # Really don't like trying to block this way...
field_locked = false

animate_next = () ->
    if (animation_queue.length == 0)
        animating = false
        return
    animating = true
    
    loop
        events = animation_queue.shift()
        break if events or animation_queue.length == 0
    if not events
        animating = false
        return

    ev() for ev in events

    setTimeout(() ->
            animate_next()
        , 750)

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
move_now = (el, target, callback) ->
    el.animate(target, 'fast', 'swing', callback)

animate_queue = (fn) ->
    animation_frame.push(fn)

# Insert at the end of the queue, rather than into the next block
animate_inject = (fn) ->
    if not animating
        fn()
    else
        animation_queue[-1].push(fn)

# Raise a screen onto the playing area to block interaction. Used for dialogs.
screen_on = () ->
    $("#screen").css('display', 'block')

screen_off = () ->
    $("#screen").css('display', 'none')

# Set the player's hand as active or inactive. This currently involves a grey
# shade behind the disabled player and dragging is disabled.
enable_hand = () ->
    # Delay until the animation is over, to match the actual enabled/disabled state
    animate_queue( () ->
        $("#playerHand").removeClass("handDisabled")
        $("#opponentHand").addClass("handDisabled")
        field_locked = false
    )

disable_hand = () ->
    $("#opponentHand").removeClass("handDisabled")
    $("#playerHand").addClass("handDisabled")
    field_locked = true


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
    if (clone.data('rank') == -1)
        alert("Trying to lift an empty card")
        console.log(el)
    clone.data('rank', el.data('rank'))
    clone.css('top', pos.top)
    clone.css('left', pos.left)
    clone.css('position', 'absolute')
    # uhh... it's chainable, so the return should be clone?

# Pull a card out of the layout (the real card) 
extract_card = (el) ->
    #pos = el.offset()
    #clone = el.clone(true).appendTo('body')
    #el.appendTo('body')
    #clone.css('top', pos.top)
    #clone.css('left', pos.left)
    #clone.css('position', 'absolute')
    clone = lift_card(el)
    # Blank out the old card
    el.attr('src', '/img/blank.gif')
    el.removeClass("selected card")
    el.off()
    return clone

get_hand = (id) ->
    $("#player_" + id)
get_field = (id) ->
    $("#field_" + id)
get_opphand = (id) ->
    $("#opponent_" + id)
get_deckcard = () ->
    $("#deckCard")


get_hand_id = (card) ->
    card.attr('id').slice(7, 9)
get_field_id = (field) ->
    field.attr('id').slice(6, 8)

get_suit = (suit) ->
    return $("#fieldCards ." + suit)

# Highlight field cards of the matching suit
mark_field = (month, blank, mode) ->
    if (dragging || deck_select)
        return
    tgts = get_suit(month)
    if (tgts.length > 0)
        tgts.addClass(mode)
    else if (blank)
        $(".fieldCard.empty").addClass(mode)

# Clear field highlights
unmark_field = (mode) ->
    if (!dragging && !deck_select)
        $(".fieldCard." + mode).removeClass(mode)

# ANIMATION UTILITY FUNCTIONS. NOT DELAYED. WRAP IN AN ANIMATE_QUEUE

# Take el and dump it to field location
# It will be left as flyingCard if the location is filled
place_card = (el, field) ->
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
        cb = () -> undefined
        el.attr('id', 'flyingCard')
    move_now(el, tgt, cb)

# function to return a function to make a class sit in the captures pile
settle_card = (container, card) ->
    # Extra layer of wrapping to bind container and card _now_
    # Without this multiple captures go funny, because tgti keeps changing or something
    () ->
        container.append(card)
        card.css('position', 'static')
        card.attr('id', '')
        card.removeClass().addClass("card capCard")


# Move all cards from [locations] to player's discards
capture_cards = (locations, player) ->
    #move flyingCard and field[data.field1[]] to captures
    caps = if player == playerid then $("#playerCaptures") else $("#opponentCaptures")

    for loc in locations
        # Here we go again... this is going to be executed later, so bind loc now
        do (loc) ->
            #animate_queue( () ->
                fc = get_field(loc)
                fcc = lift_card(fc)
                blank_card(fc)
                tgti = capture_dest(fcc.data('rank'), caps)

                move_now(fcc, tgti.offset(), settle_card(tgti, fcc))
            #)

# Move card (element, not location) to player's discards
capture_single = (card, player) ->
    caps = if player == playerid then $("#playerCaptures") else $("#opponentCaptures")
    tgt = capture_dest(card.data('rank'), caps)
    card.attr('id', '')
    move_now(card, tgt.offset(), settle_card(tgt, card))


################################################################################################
# Handlers for server events

# Plant the player's dragged card if necessary
self_plant_card = (field) ->
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
    # TODO: blank rather than remove (well, the original, not the flying ver)
    fc.remove()

opponent_place_card = (field, card) ->
    animate_queue( () ->
        hand = opponent_play_order.pop()
        el = extract_card(get_opphand(hand))
        set_card(el, card)

        place_card(el, field)
    )

capture_play = (location, player) ->
    animate_queue( () ->
        capture_cards(location, player)
        capture_single($("#flyingCard"), player)
    )

# Lift the card off the top of the deck, blank the card underneath, return the new
# handle
# Not useful if the deck card isn't flipped up
deck_lift = () ->
    dc = get_deckcard()
    dcc = lift_card(dc)
    blank_card(dc)
    dc.attr('src', '/img/back.gif')
    dcc

deck_place = (location) ->
    animate_queue( () ->
        if $("#flyingCard").length > 0
            return
        dcc = deck_lift()
        place_card(dcc, location)
    )

deck_capture = (locations, player) ->
    animate_queue( () ->
        dcc = $("#flyingCard")
        # flyingCard won't be null in case of a :deck_match
        capture_single(dcc, player)
        # Take all the captures
        capture_cards(locations, player)
    )

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
            if data.player != playerid
                opponent_place_card(data.location, data.card)
            else
                # Plant the card
                self_plant_card(data.location)
        when 'take_card'
            capture_play(data.location, data.player)
        when 'draw_card'
            draw_card(data.card)
            # Not symmetrical with play_card/take_card
        when ':draw_match'
            deckselect_enable(data.card)
        when 'draw_place'
            deck_place(data.location)
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
        when 'error'
            screen_on()
            $("#txtAlert").html(data.text)
            # slideUp chained onto a slideDown
            $("#alert").slideDown('fast')
        when 'game_end'
            wsock.close()
        when 'results'
            $("#results").html(data.data)
            $("#results").css('display', 'block')
            # $("#results").draggable(); #if the user wants to see stuff
            screen_on()
        else
            alert("Unknown message: " + data.type)
    animate_gate()


board_init = (state) ->
    # gamelink = state.gamelink
    playerid = state.player
    $("#txtGameId").html(gameid)
    $("#txtScore").html(state.own_score)
    $("#txtOppScore").html(state.opp_score)
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


selectedCard = null
click_hand = (card) ->
    if deck_select
        return null
    $("img.selected").removeClass("selected")
    unmark_field('cardTarget')
    if (selectedCard == card)
        selectedCard = null
    else
        selectedCard = card
        selectedCard.addClass("selected")
        month = card.data("suit")
        mark_field(month, true, 'cardTarget')

click_field = (field) ->
    if selectedCard == null || field_locked
        return

    # Place on empty iff there are no possible matches
    if field.data("suit") != "empty" && selectedCard.data("suit") != field.data("suit") ||
            field.data("suit") == "empty" && get_suit(selectedCard.data("suit")).length > 0
        return null

    unmark_field('cardTarget')
    if deck_select
        handID = -1
        card = deck_lift()
        deckselect_disable()
    else
        handID = get_hand_id(selectedCard)
        card = extract_card(selectedCard)
    fieldID = get_field_id(field)
    animate_queue(() ->
        place_card(card, fieldID))
    selectedCard = null
    data =
        'type': 'place'
        'hand': handID
        'field': fieldID
    wsock.send(JSON.stringify(data))
    animate_gate()

# enter deck selection mode, where there are multiple options from the field to
# match a card from the deck. The player can only take the deck card and match
# it to field cards of the same suit.

deck_select = false
deckselect_enable = (card) ->
    $("#deckCard").addClass("cardHighlight")
    unmark_field('cardHighlight')
    month = card.suit
    $("#deckCard").data("suit", month)
    mark_field(month, false, 'cardTarget')
    # should disable highlight and dragging for the main cards
    selectedCard = $("#deckCard")
    deck_select = true

deckselect_disable = (card) ->
    # restore the old state
    $("#deckCard").attr('src', "/img/back.gif")
    $("#deckCard").removeClass("cardHighlight cardTarget")
    deck_select = false
    unmark_field('cardHighlight')
    unmark_field('cardTarget')

ws_init = () ->
    wsock = new WebSocket(socket_url)
    wsock.onopen = () ->
        data =
            'type': 'client_connect'
            'game_id': gameid
        wsock.send(JSON.stringify(data))

    wsock.onmessage = (evt) ->
        data = JSON.parse(evt.data)
        run_event evt for evt in data
    wsock.onerror = (evt) ->
        alert("Websocket error: " + evt.data)
    window.wsock = wsock

init = ->
    log("In init function")
    ws_init()
    $("#deckCard").data('id', -1)

    $(".fieldCard").click(() ->
        click_field($(this)))
    $("#playerHand > .handCard").click(() ->
        click_hand($(this)))

    $("#playerHand > .handCard").hover(() ->
        # start hover handler, mark the suit
            suit = $(this).data('suit')
            mark_field(suit, true, 'cardHighlight')
        ,() ->
            # stop hover handler
            unmark_field('cardHighlight')
            )
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

root.win = () ->
    wsock.send(JSON.stringify(
        'type': 'win'))
root.draw = () ->
    wsock.send(JSON.stringify(
        'type': 'draw'))

