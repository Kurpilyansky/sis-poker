from django.contrib import admin

from reversion.admin import VersionAdmin

from . import models


class TableAdmin(VersionAdmin):
    list_display = (
        'id',
        'start_chips',
    )

    list_filter = (
    )

    search_fields = (
        '=id',
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


admin.site.register(models.Table, TableAdmin)
admin.site.register(models.Player, PlayerAdmin)
