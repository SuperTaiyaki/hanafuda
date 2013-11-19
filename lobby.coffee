$(document).ready = ->
    if (!'WebSocket' in window)
        alert("No websocket support. Not going to work.")

wsconn = new WebSocket(socket)

wsconn.onopen = ->
    "" # What's the 'pass' equivalent?

wsconn.onmessage = (data) ->
    json = JSON.parse(data.data)
    # alert("WS Message: " + data.data);
    if json.type == 'name'
        $("#namebox").val(json.name)
    else if json.type == 'games'
        $("#gamelist").html(json.games)

wsconn.onclose = ->
    $("#update_block").html("Connection lost")
#    alert("Server connection lost.")

wsconn.onerror = ->
    $("#update_block").html("WebSocket error")
    #alert("WebSocket error")

root = exports ? this
root.new_name = () ->
    wsconn.send(JSON.stringify({type: 'new_name'}))
    false

root.set_name = () ->
    name = $("#namebox").val()
    $.ajax('/set_name', data: {name: name})

