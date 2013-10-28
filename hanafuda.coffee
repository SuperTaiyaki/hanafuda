
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
        when 'draw_match'
            deckselect_enable(data.card)
        when 'draw_place'
            deck_place(data.location, data.card)
        when 'draw_capture'
            deck_capture(data.location, data.player)
        when 'turn_end'
            disable_hand()
        when 'start_turn'
            enable_hand()
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
    window.opponent_play_order = []
    for i, idx in state.opp_hand
        get_opphand(i).css('display', 'none')
        window.opponent_play_order.push(idx)

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
                window.dragging = true; #need to mark the original somehow
                month = $(this).data('suit')
                draggingthing = ui.helper # $(this)
                draggingthing.css('opacity', 0.2)
                drag_targets(month, true)
            stop: () ->
                console.log("Drag stop")
                window.dragging = false
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


