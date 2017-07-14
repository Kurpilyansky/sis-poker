from flask import Flask, render_template
from flask_socketio import send, emit
from flask_socketio import SocketIO

import json
import random
import time

PREFLOP = 'PREFLOP'
FLOP = 'FLOP'
TURN = 'TURN'
RIVER = 'RIVER'

FOLD = 'FOLD'
CALL = 'CALL'
RAISE = 'RAISE'
ALL_IN = 'ALL_IN'

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)

class Player:
  def __init__(self, name, pos, chips):
    self.name = name
    self.pos = pos
    self.chips = chips
    self.hand = []

  def as_dict(self):
    return {'name': self.name,
            'pos': self.pos,
            'hand': self.hand,
            'chips': self.chips}

class CardDeck:
  def __init__(self):
    self.cards = [val+suit for val in '23456789TJQKA' for suit in 'hdsc']
    random.shuffle(self.cards)

  def next_card(self):
    card = self.cards[0]
    self.cards = self.cards[1:]
    return card

class GameState:
  def __init__(self):
    self.state = None
    self.pot = None
    self.board = []
    CHIPS = 1000
    self.players = [Player('Евгений', 1, CHIPS),
                    Player('Сергей', 2, CHIPS),
                    Player('Анна', 3, CHIPS)]
    self.button_pos = 1
    self.next_phase()

  def _start_new(self):
    self.state = PREFLOP
    self.pot = 0
    for p in self.players:
      p.hand = []
    self.board = []
    self.deck = CardDeck()
    self.players.sort(key=lambda x: x.pos)
    if self.button_pos < self.players[-1].pos:
      while self.players[0].pos <= self.button_pos:
        self.players = self.players[1:] + self.players[:1]
    self.deck.next_card()  # burn card
    for i in range(2):
      for p in self.players:
        p.hand.append(self.deck.next_card())

  def next_phase(self):
    if self.state == PREFLOP:
      self.state = FLOP
      self.deck.next_card()
      for i in range(3):
        self.board.append(self.deck.next_card())
    elif self.state == FLOP:
      self.state = TURN
      self.deck.next_card()
      self.board.append(self.deck.next_card())
    elif self.state == TURN:
      self.state = RIVER
      self.deck.next_card()
      self.board.append(self.deck.next_card())
    else:
      if self.state == RIVER:
        self.button_pos = self.players[0].pos
      self._start_new()

  def make_move(self, pos, action, *args):
     pass 

  def as_dict(self):
    return {'state': self.state,
            'board': self.board,
            'players': [p.as_dict() for p in sorted(self.players, key=lambda p: p.pos)],
            'button_pos': self.button_pos}

game_state = GameState()

def send_full_game_state():
  emit('full_state', game_state.as_dict(), json=True)

def send_full_game_state():
  emit('full_state', game_state.as_dict(), json=True, broadcast=True)

@socketio.on('get_full_state')
def handle_get_full_state():
  send_full_game_state()

@socketio.on('make_move')
def handle_make_move(player_pos, action, *args):
  game_state.make_move(pos, action, *args)
  send_full_game_state()

@socketio.on('next_phase')
def handle_next_phase():
  game_state.next_phase()
  broadcast_full_game_state()

if __name__ == '__main__':
  socketio.run(app)

