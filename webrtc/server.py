from flask import Flask, render_template, request, session
from flask_socketio import SocketIO, emit, join_room
import platform

app = Flask(__name__)
app.config['SECRET_KEY'] = "wubba lubba dub dub"

socketio = SocketIO(app)

users_in_room = {}
rooms_sid = {}
names_sid = {}

@app.route("/join", methods=["GET"])
def join():
    display_name = request.args.get('display_name', 'Anonymous')
    mute_audio = request.args.get('mute_audio', '0')  # Default to unmuted
    mute_video = request.args.get('mute_video', '0')  # Default to unmuted
    room_id = request.args.get('room_id', 'default_room')  # Default room

    # Store the session data
    session[room_id] = {
        "name": display_name,
        "mute_audio": mute_audio,
        "mute_video": mute_video
    }

    return render_template(
        "join.html",
        room_id=room_id,
        display_name=session[room_id]["name"],
        mute_audio=session[room_id]["mute_audio"],
        mute_video=session[room_id]["mute_video"]
    )

@socketio.on("connect")
def on_connect():
    sid = request.sid
    print("New socket connected", sid)

@socketio.on("join-room")
def on_join_room(data):
    sid = request.sid
    room_id = data.get("room_id", "default_room")
    display_name = session.get(room_id, {}).get("name", "Anonymous")

    # Register sid to the room
    join_room(room_id)
    rooms_sid[sid] = room_id
    names_sid[sid] = display_name

    # Broadcast to others in the room
    print(f"[{room_id}] New member joined: {display_name}<{sid}>")
    emit("user-connect", {"sid": sid, "name": display_name},
         broadcast=True, include_self=False, room=room_id)

    # Add to user list maintained on server
    if room_id not in users_in_room:
        users_in_room[room_id] = [sid]
        emit("user-list", {"my_id": sid})  # Send own id only
    else:
        usrlist = {u_id: names_sid[u_id]
                   for u_id in users_in_room[room_id]}
        # Send list of existing users to the new member
        emit("user-list", {"list": usrlist, "my_id": sid})
        # Add new member to user list maintained on server
        users_in_room[room_id].append(sid)

    print("\nusers:", users_in_room, "\n")

@socketio.on("disconnect")
def on_disconnect():
    sid = request.sid
    room_id = rooms_sid.get(sid)
    display_name = names_sid.get(sid, "Unknown")

    if room_id:
        print(f"[{room_id}] Member left: {display_name}<{sid}>")
        emit("user-disconnect", {"sid": sid},
             broadcast=True, include_self=False, room=room_id)

        users_in_room[room_id].remove(sid)
        if len(users_in_room[room_id]) == 0:
            users_in_room.pop(room_id)

        rooms_sid.pop(sid, None)
        names_sid.pop(sid, None)

    print("\nusers:", users_in_room, "\n")

@socketio.on("data")
def on_data(data):
    sender_sid = data['sender_id']
    target_sid = data['target_id']
    if sender_sid != request.sid:
        print("[Not supposed to happen!] request.sid and sender_id don't match!!!")

    if data["type"] != "new-ice-candidate":
        print(f'{data["type"]} message from {sender_sid} to {target_sid}')
    socketio.emit('data', data, room=target_sid)

if __name__ == "__main__":
    if platform.system() == "Windows":
        socketio.run(app, debug=True)
    else:
        socketio.run(app)
