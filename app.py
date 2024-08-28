from flask import Flask, render_template, request, redirect, url_for
from flask_socketio import SocketIO, join_room, leave_room, emit

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)

# Route to serve the index page
@app.route('/')
def index():
    return render_template('index.html')

# Route to handle room joining
@app.route('/join', methods=['POST'])
def join():
    room_name = request.form.get('room_name')
    username = request.form.get('username')
    return redirect(url_for('room', room_name=room_name, username=username))

# Route to serve the room page
@app.route('/room/<room_name>')
def room(room_name):
    return render_template('room.html', room_name=room_name)

# SocketIO events (unchanged)
@socketio.on('join')
def on_join(data):
    username = data['username']
    room = data['room']
    join_room(room)
    emit('message', {'msg': f'{username} has joined the room.'}, room=room)

@socketio.on('leave')
def on_leave(data):
    username = data['username']
    room = data['room']
    leave_room(room)
    emit('message', {'msg': f'{username} has left the room.'}, room=room)

@socketio.on('offer')
def handle_offer(data):
    room = data['room']
    emit('offer', data['offer'], room=room)

@socketio.on('answer')
def handle_answer(data):
    room = data['room']
    emit('answer', data['answer'], room=room)

@socketio.on('candidate')
def handle_candidate(data):
    room = data['room']
    emit('candidate', data['candidate'], room=room)

if __name__ == '__main__':
    socketio.run(app, debug=True)
