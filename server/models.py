from django.db import models


class Table(models.Model):
  name = models.CharField(max_length=500)
  start_chips = models.IntegerField()

  @property
  def players(self):
    return list(Player.objects.filter(table_id=self.id).order_by('table_place').all())

  def get_new_deck_id(self):
    card_deck = CardDeck.objects.filter(table_id=self.id).order_by('-deck_id').first()
    if card_deck:
      return card_deck.deck_id + 1
    return 0

  def get_next_deck(self, last_deck_id=-1):
    card_deck = CardDeck.objects.filter(table_id=self.id,
                                        deck_id__gt=last_deck_id,
                                        is_canceled=False) \
                                .order_by('deck_id').first()
    return card_deck

  def get_last_event(self):
    return GameEvent.objects.filter(table_id=self.id,
                                    is_canceled=False) \
                            .order_by('-event_id').first()

  def get_new_event_id(self):
    event = GameEvent.objects.filter(table_id=self.id).order_by('-event_id').first()
    if event:
      return event.event_id + 1
    return 0

  def __str__(self):
    return self.name


class Player(models.Model):
  name = models.CharField(max_length=100)
  table = models.ForeignKey(Table)
  table_place = models.IntegerField()


class CardDeck(models.Model):
  table = models.ForeignKey(Table, null=True)
  deck_id = models.IntegerField()
  cards = models.CharField(max_length=500)
  dealer_error = models.IntegerField(help_text='маска ошибок дилера', default=0)
  
  is_canceled = models.BooleanField(default=False)


class GameEvent(models.Model):
  table = models.ForeignKey(Table)
  deck_id = models.IntegerField()
  player_id = models.IntegerField(null=True, blank=True)
  player_name = models.CharField(max_length=100, null=True, blank=True)

  event_id = models.IntegerField()
  event_type = models.CharField(max_length=500)
  args = models.CharField(max_length=2000)

  is_canceled = models.BooleanField(default=False)

  def __str__(self):
    return '#%d %s' % (self.id, self.get_text())

  def get_text(self):
    return '%s %s %s' % (self.player_name, self.event_type, self.args)

  @classmethod
  def get_prev_event(cls, table_id, event_id):
    return cls.objects.filter(table_id=table_id,
                              is_canceled=False,
                              event_id__lt=event_id
                              ).order_by('-event_id').first()
    
  @classmethod
  def get_next_event(cls, table_id, event_id):
    return cls.objects.filter(table_id=table_id,
                              is_canceled=False,
                              event_id__gt=event_id
                              ).order_by('event_id').first()
