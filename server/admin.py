from django.contrib import admin

from reversion.admin import VersionAdmin

from . import models


class TableAdmin(VersionAdmin):
    list_display = (
        'id',
        'name',
        'start_chips',
    )

    list_filter = (
    )

    search_fields = (
        '=id',
        'name',
    )


class PlayerAdmin(VersionAdmin):
    list_display = (
        'id',
        'name',
        'table',
    )

    list_filter = (
    )

    search_fields = (
        '=id',
        'name',
    )


class CardDeckAdmin(VersionAdmin):
    list_display = (
        'id',
        'deck_id',
        'table',
    )

    list_filter = (
        'table',
    )

    search_fields = (
        '=deck_id',
    )


admin.site.register(models.Table, TableAdmin)
admin.site.register(models.Player, PlayerAdmin)
admin.site.register(models.CardDeck, CardDeckAdmin)
