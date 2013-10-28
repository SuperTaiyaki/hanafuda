$(document).ready = ->
    if (!'WebSocket' in window)
        alert("No websocket support. Not going to work.")

wsconn = new WebSocket("ws://localhost:8080/ws")

wsconn.onopen = ->
    "" # What's the 'pass' equivalent?

wsconn.onmessage = (data) ->
    # alert("WS Message: " + data.data);
    $("#gamelist").html(data.data)

wsconn.onclose = ->
    alert("Server connection lost.")

wsconn.onerror = ->
    alert("WebSocket error")

