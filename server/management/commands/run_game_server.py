
from django.core.management import base as management_base

from server import game_server


class Command(management_base.BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('--table-id', type=str, help='table id')

    def handle(self, *args, **options):
        table_id = options['table_id']
        game_server.run_game_server(table_id)
