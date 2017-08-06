SIS Holdem Poker
=======

SIS Holdem Poker

## Install

    $ git clone git@github.com:Kurpilyansky/sis-poker.git
    $ cd sis-poker/
    $ virtualenv -p python3 venv
    $ source ./venv/bin/activate
    $ pip install -Ur src/requirements.txt

Чтобы сделать дамп базы данных:

    $ python manage.py dumpdata > db.json

Чтобы импортировать базу данных:

    $ python manage.py migrate
    $ python manage.py sqlflush | sqlite3 db.sqlite3
    $ python manage.py loaddata db.json

Запустить веб-админку для редактирования базы данных:

    $ python manage.py createsuperuser  # только в первый раз (для создания веб-логина)
    $ python manage.py runserver
    Open http://localhost:8000/admin in browser
    
Чтобы сконфигурировать новый стол:

    Создать объект в таблице Table
    Создать объекты в таблице Player (со ссылкой на Table)
 
Чтобы запустить GameServer (в режиме игры):

    Прописать свой IP в client/js/config.js (и server/index.html) (только для доступа с других устройств)
    $ python manage.py run_game_server --table-id=<table_id>
    Страница для дилера/его помощника (вбивать ходы участников) --- server/index.html (TODO move this to client)
    Страница для <<вбивателя>> колод --- client/deck_builder.html
    Страница для зрителей --- client/index.html (or client/board.html + client/players.html)
   
Чтобы запустить GameServer (в режиме реплея игры):
    $ python manage.py run_game_server --table-id=<table_id> --replay
    Страница для зрителей --- client/index.html (or client/board.html + client/players.html)

