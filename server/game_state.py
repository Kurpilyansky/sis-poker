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
END_GAME = 'END_GAME'

START = 'START'
FOLD = 'FOLD'
OPEN = 'OPEN'
CHECK = 'CHECK'
CALL = 'CALL'
BET = 'BET'
RAISE = 'RAISE'
ALL_IN = 'ALL_IN'

CANCEL_ROUND = 'CANCEL_ROUND'
INCREASE_BLINDS = 'INCREASE_BLINDS'
HARDCORE_SET = 'HARDCORE_SET'
SET_DEALER_ERROR = 'SET_DEALER_ERROR'
CANCEL_LAST_ACTION = 'CANCEL_LAST_ACTION'


class Player:
  def __init__(self, player_id, player_pos, name, chips):
    self.id = player_id
    self.pos = player_pos
    self.name = name
    self.chips = chips
    self.chips_on_round_start = self.chips
    self.bet = 0
    self.any_moved = False
    self.is_fault = False
    self.opened_cards = False
    self.place = None
    self.hand = []
    self.win_probs = None
    self.win_chips = None
    self.status = ''

  @property
  def in_game(self):
    return not self.place and not self.is_fault

  def fold(self):
    self.is_fault = True
    self.any_moved = True
    self.status = 'Fold'

  def open_cards(self):
    self.opened_cards = True
    self.any_moved = True
    self.status = 'Open cards'

  def make_bet(self, bet, action_text, blind=False):
    delta = min(self.chips, bet - self.bet)
    self.bet += delta
    self.chips -= delta
    self.any_moved = not blind
    self.status = action_text

  def clear_street_info(self):
    self.any_moved = False
    self.win_probs = []
    if self.place:
      self.status = ''
    elif self.chips == 0:
      self.status = 'All-in'
    else:
      self.status = ''

  def clear_round_info(self):
    self.clear_street_info()
    self.is_fault = False
    self.opened_cards = False
    self.hand = []
    self.chips_on_round_start = self.chips
    self.win_chips = None

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
            'win_chips': self.win_chips,
            'hand': self.hand,
            'chips': self.chips,
            'bet': self.bet,
            'opened_cards': self.opened_cards,
            'is_fault': self.is_fault,
            'is_current': is_current,
            'status': self.status,
            'place': self.place,
            'combination': class_string}
  
  def __str__(self):
    return '%s %s+%s' % (self.name, self.chips, self.bet)


class CardDeck:
  def __init__(self, model):
    self._model = model
    self.offset = 0
    self.dealer_error = model.dealer_error
    self.cards = model.cards.split()
    #self.cards = [val+suit for val in '23456789TJQKA' for suit in 'hdsc']
    #random.shuffle(self.cards)

  def set_dealer_error(self, dealer_error):
    self._model.dealer_error = dealer_error
    self._model.save()

  def draw(self, count):
    res = self.cards[self.offset:self.offset + count]
    self.offset += count
    return res

  def burn_card(self):
    error = self.dealer_error & 1
    self.dealer_error >>= 1
    if error == 0:
      self.draw(1)
    else:
      print('skip burning card')


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

  def keep_players_in_game(self):
    self.players = list(filter(lambda p: p.in_game, self.players))

  def move_to_winners(self):
    MIN_CHIP = 5
    n = len(self.winners)
    x = self.chips // MIN_CHIP
    y = x // n
    z = x % n
    for i in range(n):
      player = self.winners[i]
      if i < z:
        player.win_chips += (y + 1) * MIN_CHIP
      else:
        player.win_chips += y * MIN_CHIP

  def __str__(self):
    return 'chips %d, players %s, winners %s' % (self.chips, str(list(map(str, self.players))), str(list(map(str, self.winners))))


class GameState:

  def __init__(self, table, players):
    self.table = table
    self.state = None
    self.cur_deck_id = -1
    self.deck = None
    self.pots = []
    self.cur_bet = 0
    self.board = []
    self.players = players
    self.button_pos = len(players) - 1
    self.blinds_pos = [0, 1]
    self.cur_player = None
    self.blinds = (5, 10)
    self.evaluator = deuces.Evaluator()
    self.all_in_players = []
    self.called_players = []

  @classmethod
  def create_new(cls, table):
    players = [Player(p.id, i, p.name, table.start_chips) for i, p in enumerate(sorted(table.players, key=lambda p: p.table_place))]
    game_state = cls(table, players)
    events = list(models.GameEvent.objects.filter(table_id=table.id).order_by('event_id').all())
    for ev in events:
      game_state._process_action(ev)
    return game_state

  def get_players_count(self):
    return len([p for p in self.players if not p.place])

  def _move_bets_to_pot(self):
    while True:
      bets = [p.bet for p in self.iter_players() if p.in_game and p.bet > 0]
      if not bets:
        break
      if not self.pots:
        self.pots.append(Pot())
      else:
        self.pots[-1].keep_players_in_game()
        if len(self.pots[-1].players) != len(bets):
          self.pots.append(Pot())
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
    if self.state == SHOWDOWN:
      self._find_next_player()  # TODO refactor
    else:
      self.called_players = []
      self.cur_player = self.players[self.blinds_pos[0]]
      if not self.cur_player.in_game or self.cur_player.chips == 0:
        self._find_next_player()
  
  def _find_next_player(self):
    if self.state == SHOWDOWN:
      if not self.showdown_players:
        return False
      self.cur_player = self.showdown_players.pop()
      return True
    iters = 0
    n = len(self.players)
    i = self.cur_player.pos
    while True:
      iters += 1
      i = (i + 1) % n
      if self.players[i].in_game and self.players[i].chips > 0:
        break
      if iters > 2 * n:
        return False
    self.cur_player = self.players[i]
    return True

  def iter_players(self, include_losers=False):
    n = len(self.players)
    for i in range(n):
      j = (i + self.blinds_pos[0]) % n
      if not self.players[j].place:
        yield self.players[j]
    if include_losers:
      player_by_places = {p.place: p for p in self.players if p.place}
      for place in range(len(self.players) + 1):
        player = player_by_places.get(place)
        if player:
          yield player

  def _deal_cards(self):
    print('deal cards in state ' + str(self.state))
    if self.state == None:
      deck_model = self.table.get_next_deck(self.cur_deck_id)
      if not deck_model:
        return False
      self.cur_deck_id = deck_model.deck_id
      self.deck = CardDeck(deck_model)
      self._start_new_street(PREFLOP)
      self.deck.burn_card()
      for i in range(2):
        for p in self.iter_players():
          p.hand += self.deck.draw(1)
      self.players[self.button_pos].status = 'Dealer'
      players_count = len([p for p in self.players if not p.place])
      print('button_pos %d, blinds_pos (%d, %d)' % (self.button_pos, self.blinds_pos[0], self.blinds_pos[1]))
      print(list(map(str, self.players)))
      #if players_count == 2:
      #  self._find_next_player()  #Head's up
      if self.blinds_pos[0] != self.blinds_pos[1]:
        self.players[self.blinds_pos[0]].make_bet(self.blinds[0], 'SB: %d' % self.blinds[0], blind=True)
        self._find_next_player()
      self.players[self.blinds_pos[1]].make_bet(self.blinds[1], 'BB: %d' % self.blinds[1], blind=True)
      self._find_next_player()
      self.cur_bet = self.blinds[1]
    elif self.state == PREFLOP:
      self._start_new_street(FLOP)
      self.deck.burn_card()
      self.board = self.deck.draw(3)
    elif self.state == FLOP:
      self._start_new_street(TURN)
      self.deck.burn_card()
      self.board += self.deck.draw(1)
    elif self.state == TURN:
      self._start_new_street(RIVER)
      self.deck.burn_card()
      self.board += self.deck.draw(1)
    elif self.state == RIVER:
      self.showdown_players = list((self.all_in_players + self.called_players)[::-1])
      print(list(map(str, self.showdown_players)))
      self._start_new_street(SHOWDOWN)
    elif self.state == SHOWDOWN:
      self._detect_winner()
    else:
      raise ValueError('unknown self.state ' + self.state)
    return True

  def _detect_winner(self):
    self._move_bets_to_pot()
    self.state = END_ROUND
    self.cur_player = None
    for player in self.players:
      if player.in_game:
        player.win_probs = []
        player.win_chips = 0
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
      print(pot)
      pot.move_to_winners()

  def _set_losers(self):
    last_place = len([p for p in self.players if not p.place])
    new_losers = [p for p in self.players if p.chips == 0 and not p.place]
    new_losers.sort(key=lambda p: p.chips_on_round_start)
    for p in new_losers:
      p.place = last_place
      last_place -= 1
      p.clear_round_info()
    if last_place == 1:
      winner = [p for p in self.players if not p.place][0]
      winner.place = 1
      self.state = END_GAME
      return True
    return False


  def _get_next_pos(self, pos):
    backup_val = self.cur_player  #TODO refactor
    self.cur_player = self.players[pos]
    self._find_next_player()
    pos = self.cur_player.pos
    self.cur_player = backup_val
    return pos


  def _end_round(self):
    for p in self.players:
      if p.in_game:
        p.chips += p.win_chips
        p.win_chips = None
        p.win_probs = None
    self.state = None
    self.deck = None
    self.board = []
    self.pots = []

    if self._set_losers():
      return

    for p in self.iter_players():
      p.clear_round_info()
    if self.button_pos != self.blinds_pos[0]:
      self.button_pos = self._get_next_pos(self.button_pos)
    if self.blinds_pos[0] != self.blinds_pos[1]:
      self.blinds_pos[0] = self._get_next_pos(self.blinds_pos[0])
    self.blinds_pos[1] = self._get_next_pos(self.blinds_pos[1])
    self.cur_player = None
    self.all_in_players = []

  def _all_in_all_in(self):
    for p in self.players:
      if p.in_game:
        p.open_cards()
    while self.state != END_ROUND:
      self._deal_cards()

  def _check_one_player_in_game(self):
    count = 0
    for p in self.iter_players():
      if p.in_game:
        count += 1
    return count == 1

  def _get_next_blinds(self):
    """
      5/10
      10/20
      15/30
      25/50
      *2...
    """
    if self.blinds[0] == 10:
      return (15, 30)
    elif self.blinds[0] == 15:
      return (25, 50)
    else:
      return (self.blinds[0] * 2, self.blinds[1] * 2)

  def make_action(self, action_type, **kwargs):
    new_event = models.GameEvent(table=self.table,
                          deck_id=self.cur_deck_id,
                          event_id=self.table.get_new_event_id(),
                          event_type=action_type,
                          args=json.dumps(kwargs))
    if action_type in [FOLD, OPEN, CALL, CHECK, RAISE, BET, ALL_IN]:
      new_event.player_id = self.cur_player.id
      new_event.player_name = self.cur_player.name
    new_event.save()
    return self._process_action(new_event)

  def _process_action(self, event):
    if event.is_canceled:
      return
    action_type = event.event_type
    kwargs = json.loads(event.args)
    print(self.cur_player, action_type, kwargs)
    if action_type == CANCEL_LAST_ACTION:
      event.is_canceled = True
      event.save()
      last_event = self.table.get_last_event()
      if last_event:
        last_event.is_canceled = True
        last_event.save()
      return True
    elif action_type == SET_DEALER_ERROR:
      dealer_error = kwargs.get('mask', None)
      if self.deck and dealer_error is not None:
        self.deck.set_dealer_error(dealer_error)
      event.is_canceled = True
      event.save()
      return True
    elif action_type == HARDCORE_SET:
      data = kwargs.get('data')
      try:
        arr = list(map(int, data.split()))
      except ValueError:
        arr = []
      if len(arr) != len(self.players) + 3 or self.state is not None:
        event.is_canceled = True
        event.save()
        return
      self.button_pos = arr[0]
      self.blinds_pos = list(arr[1:3])
      for kvp in zip(arr[3:], self.players):
        if kvp[0] > 0:
          kvp[1].chips = kvp[0]
        else:
          kvp[1].place = -kvp[0]
      self._set_losers()
      return True
    elif action_type == CANCEL_ROUND:
      models.GameEvent.objects.filter(table_id=self.table.id,
                               deck_id=self.cur_deck_id).update(is_canceled=True)
      models.CardDeck.objects.filter(deck_id=self.cur_deck_id).update(is_canceled=True)
      return True
    elif action_type == INCREASE_BLINDS:
      self.blinds = self._get_next_blinds()
      return
    if action_type == START:
      if self.state == None:
        if not self._deal_cards():
          event.is_canceled = True
          event.save()
          return
      return
    elif action_type == END_ROUND:
      self._end_round()
      return
    elif action_type == FOLD:
      self.cur_player.fold()
      if self._check_one_player_in_game():
        self._detect_winner()
        return
    elif action_type == OPEN:
      self.cur_player.open_cards()
    elif action_type in [CALL, CHECK, RAISE, BET, ALL_IN]:
      p = self.cur_player
      if action_type == RAISE or action_type == BET:
        try:
          raise_bet = int(kwargs.get('raise_bet'))
        except ValueError:
          event.is_canceled = True
          event.save()
          return
        new_bet = self.cur_bet + raise_bet
      elif action_type == ALL_IN:
        new_bet = p.chips + p.bet
      else:
        new_bet = self.cur_bet

      new_bet = min(new_bet, p.chips + p.bet)

      if p.bet == new_bet:
        action_type = CHECK
        action_text = 'Check'
      elif new_bet <= self.cur_bet:
        action_type = CALL
        action_text = 'Call'
      elif new_bet == p.chips + p.bet:
        action_type = ALL_IN
        action_text = 'All-in'
      else:
        self.called_players = []
        if self.cur_bet == 0:
          action_type = BET
          action_text = 'Bet: %d' % new_bet
        else:
          action_type = RAISE
          action_text = 'Raise: %d' % (new_bet - self.cur_bet)
      
      p.make_bet(new_bet, action_text)
      self.cur_bet = max(self.cur_bet, new_bet)
      if p.chips == 0:
        self.all_in_players.append(p)
      else:
        self.called_players.append(p)
      
    else:
      return
    if not self._find_next_player():
      self._all_in_all_in()
      return
    player = self.cur_player
    if player.bet == self.cur_bet and player.any_moved:
      self._deal_cards()

  @classmethod
  def _build_action(cls, action_type, action_text=None, args=None):
    return {'type': action_type,
            'text': action_text or action_type,
            'args': args or []}

  def _get_actions(self):
    if self.state == END_GAME:
      return []
    if self.state == None:
      return [self._build_action(START, 'Новая раздача')]
    if self.state == END_ROUND:
      return [self._build_action(END_ROUND, 'Закончить раздачу')]
    if self.state == SHOWDOWN:
      return [self._build_action(FOLD),
              self._build_action(OPEN)]
    actions = []
    player = self.cur_player
    actions.append(self._build_action(FOLD))
    actions.append(self._build_action(CHECK if self.cur_bet == player.bet else CALL))
    actions.append(self._build_action(BET if self.cur_bet == 0 else RAISE, args=['raise_bet']))
    actions.append(self._build_action(ALL_IN))
    return actions

  def _get_special_actions(self):
    last_event = self.table.get_last_event()
    actions = [self._build_action(INCREASE_BLINDS, 'Повысить блайнды до %s' % '/'.join(map(str, self._get_next_blinds()))),
               self._build_action(CANCEL_ROUND, 'Отменить текущую раздачу'),
               self._build_action(SET_DEALER_ERROR, 'Ошибка крупье', args=['mask']),
               self._build_action(HARDCORE_SET, 'Засетить по хардкору все-все-все', args=['data'])]
    if last_event:
      actions.append(self._build_action(CANCEL_LAST_ACTION, 'Отменить последнее действие: %s' % last_event.get_text()))
    return actions

  def as_dict(self):
    return {'table_name': self.table.name,
            'state': self.state,
            'board': self.board,
            'pots': [pot.chips for pot in self.pots],
            'cur_bet': self.cur_bet,
            'blinds': self.blinds,
            'players': [p.as_dict(self.evaluator,
                                  self.board,
                                  self.cur_player is not None and p.id == self.cur_player.id)
                        for p in self.iter_players(True)],
            'actions': self._get_actions(),
            'special_actions': self._get_special_actions()}

