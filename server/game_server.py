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

@socketio.on('connect')
def handle_get_full_state():
  send_full_game_state()

@socketio.on('make_action')
def handle_make_action(*args):
  global game_state
  game_state.make_action(**(args[0]))
  broadcast_full_game_state()

@socketio.on('add_deck')
def handle_add_deck(kwargs = None):
  kwargs = kwargs or dict()
  deck_id = kwargs.get('deck_id')
  cards = kwargs.get('cards')
  response_text = None
  success = False
  if deck_id and cards:
    table = game_state.table
    if table.get_new_deck_id() == deck_id:
      deck = models.CardDeck(deck_id=deck_id,
                             cards=cards,
                             table=game_state.table)
      deck.save()
      success = True
    else:
      response_text = 'Неправильный deck_id'

  players_count = game_state.get_players_count()
  emit('new_deck_info',
       {'new_deck_id': game_state.table.get_new_deck_id(),
        'need_cards': 1 + 2 * players_count + 4 + 2 + 2,
        'response_text': response_text,
        'success': success},
       json=True)

def run_game_server(table_id):
  global game_state
  game_state = GameState.create_new(models.Table.objects.get(id=table_id))
  socketio.run(app)

