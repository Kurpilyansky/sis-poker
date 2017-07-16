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
                                        deck_id__gt=last_deck_id) \
                                .order_by('deck_id').first()
    return card_deck

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

