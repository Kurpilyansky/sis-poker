from server import models

import json
import random
import time

from server import deuces

PREFLOP = 'PREFLOP'
FLOP = 'FLOP'
TURN = 'TURN'
RIVER = 'RIVER'
SHOWDOWN = 'SHOWDOWN'
END_ROUND = 'END_ROUND'

START = 'START'
FOLD = 'FOLD'
OPEN = 'OPEN'
CHECK = 'CHECK'
CALL = 'CALL'
BET = 'BET'
RAISE = 'RAISE'
ALL_IN = 'ALL_IN'


class Player:
  def __init__(self, player_id, name, chips):
    self.id = player_id
    self.name = name
    self.chips = chips
    self.bet = 0
    self.any_moved = False
    self.is_fault = False
    self.opened_cards = False
    self.place = None
    self.hand = []
    self.win_probs = []

  @property
  def in_game(self):
    return not self.place and not self.is_fault

  def fold(self):
    self.is_fault = True
    self.any_moved = True

  def open_cards(self):
    self.opened_cards = True
    self.any_moved = True

  def make_bet(self, bet, blind=False):
    delta = min(self.chips, bet - self.bet)
    self.bet += delta
    self.chips -= delta
    self.any_moved = not blind

  def clear_street_info(self):
    self.any_moved = False
    self.win_probs = []

  def clear_round_info(self):
    self.clear_street_info()
    self.is_fault = False
    self.opened_cards = False
    self.hand = []

  def evaluate_hand(self, evaluator, board):
    if not self.hand:
      return None
    hand = list(map(deuces.Card.new, self.hand))
    if not board:
      if deuces.Card.get_rank_int(hand[0]) == deuces.Card.get_rank_int(hand[1]):
        return deuces.LookupTable.MAX_PAIR
      else:
        return deuces.LookupTable.MAX_HIGH_CARD
    board = list(map(deuces.Card.new, board))
    return evaluator.evaluate(board, hand)

  def as_dict(self, evaluator, board, is_current):
    rank = self.evaluate_hand(evaluator, board)
    if rank:
      rank_class = evaluator.get_rank_class(rank)
      class_string = evaluator.class_to_string(rank_class)
    else:
      class_string = None
    return {'name': self.name,
            'win_probs': self.win_probs,
            'hand': self.hand,
            'chips': self.chips,
            'bet': self.bet,
            'is_fault': self.is_fault,
            'is_current': is_current,
            'place': self.place,
            'combination': class_string}
  
  def __str__(self):
    return '%s %s+%s' % (self.name, self.chips, self.bet)


class CardDeck:
  def __init__(self):
    self.offset = 0
    #self.cards = model.cards.split()
    self.cards = [val+suit for val in '23456789TJQKA' for suit in 'hdsc']
    random.shuffle(self.cards)

  def draw(self, count):
    res = self.cards[self.offset:self.offset + count]
    self.offset += count
    return res


class Pot:
  def __init__(self):
    self.chips = 0
    self.players = []
    self.winners = []

  def add_player_bet(self, player, bet):
    bet = min(bet, player.bet)
    self.chips += bet
    player.bet -= bet
    if player.in_game:
      self.players.append(player)

  def add_winner(self, player):
    self.winners.append(player)

  def move_to_winners(self):
    MIN_CHIP = 5
    n = len(self.winners)
    x = self.chips // MIN_CHIP
    y = x // n
    z = x % n
    for i in range(n):
      player = self.winners[i]
      if i < z:
        player.chips += (y + 1) * MIN_CHIP
      else:
        player.chips += y * MIN_CHIP


class GameState:

  def __init__(self, players):
    self.state = None
    self.deck = None
    self.pots = []
    self.cur_bet = 0
    self.board = []
    self.players = players
    self.button_pos = len(players) - 1
    self.cur_player = 0
    self.blinds = (5, 10)
    self.evaluator = deuces.Evaluator()

  @classmethod
  def create_new(cls, table):
    players = [Player(p.id, p.name, table.start_chips) for p in sorted(table.players, key=lambda p: p.table_place)]
    return cls(players)

  def _move_bets_to_pot(self):
    if not self.pots:
      self.pots = [Pot()]
    first = True
    while True:
      bets = [p.bet for p in self.iter_players() if p.in_game and p.bet > 0]
      if not bets:
        break
      if not first:
        self.pots.append(Pot())
      else:
        self.pots[-1].players = []
      first = False
      min_bet = min(bets)
      for p in self.iter_players():
        if p.bet > 0:
          self.pots[-1].add_player_bet(p, min_bet)

  def _start_new_street(self, new_state):
    if self.state:
      self._move_bets_to_pot()
    self.state = new_state
    self.cur_bet = 0
    for p in self.iter_players():
      p.clear_street_info()
    self.cur_player = self.button_pos
    self._find_next_player()
  
  def _find_next_player(self):
    iters = 0
    n = len(self.players)
    i = self.cur_player
    while True:
      iters += 1
      i = (i + 1) % n
      if self.players[i].in_game and self.players[i].chips > 0:
        break
      # fix infinite loop for all in all-in
      if iters > 2 * n:
        return False
    self.cur_player = i
    return True

  def iter_players(self):
    n = len(self.players)
    for i in range(n):
      j = (i + self.button_pos + 1) % n
      if not self.players[j].place:
        yield self.players[j]

  def _deal_cards(self):
    if self.state == None:
      self.deck = CardDeck()
      self._start_new_street(PREFLOP)
      self.deck.draw(1)
      for i in range(2):
        for p in self.iter_players():
          p.hand += self.deck.draw(1)
      for i in range(2):
        self.players[self.cur_player].make_bet(self.blinds[i], blind=True)
        self._find_next_player()
      self.cur_bet = self.blinds[1]
    elif self.state == PREFLOP:
      self._start_new_street(FLOP)
      self.deck.draw(1)
      self.board = self.deck.draw(3)
    elif self.state == FLOP:
      self._start_new_street(TURN)
      self.deck.draw(1)
      self.board += self.deck.draw(1)
    elif self.state == TURN:
      self._start_new_street(RIVER)
      self.deck.draw(1)
      self.board += self.deck.draw(1)
    elif self.state == RIVER:
      self._start_new_street(SHOWDOWN)
    elif self.state == SHOWDOWN:
      self._detect_winner()
    else:
      raise ValueError('unknown self.state ' + self.state)

  def _detect_winner(self):
    self._move_bets_to_pot()
    self.state = END_ROUND
    for player in self.players:
      player.win_probs = []
    for pot in self.pots:
      players = [p for p in pot.players if p.in_game]
      vals = []
      if len(players) == 1:
        vals = [-1]
      else:
        for player in players:
          vals.append(player.evaluate_hand(self.evaluator, self.board))
      best_val = min(vals)
      for player, val in zip(players, vals):
        if val == best_val:
          player.win_probs.append(100.0)
          pot.add_winner(player)
        else:
          player.win_probs.append(0.0)

  def _end_round(self):
    for pot in self.pots:
      pot.move_to_winners()
    self.state = None
    self.board = []
    self.pots = []
    for p in self.iter_players():
      p.clear_round_info()
    self.cur_player = self.button_pos
    self._find_next_player()
    self.button_pos = self.cur_player

  def _all_in_all_in(self):
    while self.state != END_ROUND:
      self._deal_cards()

  def _check_one_player_in_game(self):
    count = 0
    for p in self.iter_players():
      if p.in_game:
        count += 1
    return count == 1

  def make_action(self, action_type, **kwargs):
    if action_type == START:
      self._deal_cards()
      return
    elif action_type == END_ROUND:
      self._end_round()
      return
    elif action_type == FOLD:
      self.players[self.cur_player].fold()
      if self._check_one_player_in_game():
        self._detect_winner()
        return
    elif action_type == CALL or action_type == CHECK:
      self.players[self.cur_player].make_bet(self.cur_bet)
    elif action_type == RAISE or action_type == BET:
      raise_bet = int(kwargs.get('raise_bet'))
      self.cur_bet += raise_bet
      self.players[self.cur_player].make_bet(self.cur_bet)
    elif action_type == ALL_IN:
      p = self.players[self.cur_player]
      self.cur_bet = max(self.cur_bet, p.chips + p.bet)
      p.make_bet(p.chips + p.bet)
    elif action_type == OPEN:
      self.players[self.cur_player].open_cards()
    else:
      return
    if not self._find_next_player():
      self._all_in_all_in()
      return
    player = self.players[self.cur_player]
    if player.bet == self.cur_bet and player.any_moved:
      self._deal_cards()

  @classmethod
  def _build_action(cls, action_type, action_text=None, args=None):
    return {'type': action_type,
            'text': action_text or action_type,
            'args': args or []}

  def _get_actions(self):
    if self.state == None:
      return [self._build_action(START, 'Новая раздача')]
    if self.state == END_ROUND:
      return [self._build_action(END_ROUND, 'Закончить раздачу')]
    if self.state == SHOWDOWN:
      return [self._build_action(FOLD),
              self._build_action(OPEN)]
    actions = []
    player = self.players[self.cur_player]
    actions.append(self._build_action(FOLD))
    actions.append(self._build_action(CHECK if self.cur_bet == player.bet else CALL))
    actions.append(self._build_action(BET if self.cur_bet == 0 else RAISE, args=['raise_bet']))
    actions.append(self._build_action(ALL_IN))
    return actions

  def as_dict(self):
    return {'state': self.state,
            'board': self.board,
            'pots': [pot.chips for pot in self.pots],
            'cur_bet': self.cur_bet,
            'players': [p.as_dict(self.evaluator,
                                  self.board,
                                  p.id == self.players[self.cur_player].id)
                        for p in self.iter_players()],
            'actions': self._get_actions()}

