from django.db import models


class Table(models.Model):
  start_chips = models.IntegerField()

  @property
  def players(self):
    return list(Player.objects.filter(table_id=self.id).order_by('table_place').all())


class Player(models.Model):
  name = models.CharField(max_length=100)
  table = models.ForeignKey(Table)
  table_place = models.IntegerField()


class CardDeck(models.Model):
  cards = models.CharField(max_length=500)


