from flask import Flask, render_template
from flask_socketio import send, emit
from flask_socketio import SocketIO

from server import models
from server.game_state import GameState

import json
import random
import time

app = Flask(__name__)
#app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)
game_state = None

def send_full_game_state():
  global game_state
  emit('full_state', game_state.as_dict(), json=True)

def broadcast_full_game_state():
  global game_state
  emit('full_state', game_state.as_dict(), json=True, broadcast=True)

@socketio.on('get_full_state')
def handle_get_full_state():
  send_full_game_state()

@socketio.on('make_action')
def handle_make_action(*args):
  global game_state
  game_state.make_action(**(args[0]))
  broadcast_full_game_state()

def run_game_server(table_id):
  global game_state
  game_state = GameState.create_new(models.Table.objects.get(id=table_id))
  socketio.run(app)

