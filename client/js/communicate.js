/**
 * Created by shhdup on 16/07/2017.
 */

//var socket = io.connect('http://localhost:' + 5000);
var socket = io.connect('http://10.0.1.144:' + 5000);

socket.on('full_state', function(data) {
    console.log(data);

    var state = data['state'];
    var stateDict = {
        'PREFLOP': 'Pre-Flop',
        'FLOP': 'Flop',
        'TURN': 'Turn',
        'RIVER': 'River',
        'SHOWDOWN': 'Showdown',
        'END_ROUND': ''

    };
    state = stateDict[state];
    $('#state').html(state);

    var pots = data['pots'];

    var $pots = $('#pots');
    $pots.empty();
    if (pots.length === 1) {
        $pots.html('Текущий банк: <span class="num">' + pots[0] + '</span>');
    } else if (pots.length > 1) {
        pots.forEach(function (elem, ind) {
            $pots.append('Банк #' + (ind + 1) + ': <span class="num">' + elem + "</span><br/>");
        });
    }

    var table_name = data['table_name'];
    $('#table-name').html(table_name);

    var cards = data['board'];

    while (cards.length < 5) {
        cards.push('xx');
    }

    cards.forEach(function (card, ind) {
        $card = $($('#cards .card')[ind]);
        $card.removeClass('red');
        $card.removeClass('black');
        $card.removeClass('closed');
        if (card === 'xx') {
            $card.addClass('closed');
            $card.html('<i>&nbsp;</i>');
        } else {
            $card.html('<span>&nbsp;</span><span>&nbsp;</span><i>&nbsp;</i>');
            if (card[1] === 's' || card[1] === 'c') {
                $card.addClass('black');
            } else {
                $card.addClass('red');
            }
            var suit = {
                'c': '&clubs;',
                's': '&spades;',
                'h': '&hearts;',
                'd': '&diams;'
            }[card[1]];
            $card.find('i').html(suit);
            $card.find('span').html(card[0].toUpperCase());
        }
    });

    var players = data['players'];

    while ($('.player-row').length > players.length) {
        $('.player-row').last().remove();
    }

    while ($('.player-row').length < players.length) {
        $('.glob').last().before('<div class="player-row"></div>');
        $('.player-row').last().html($('.player-row-prototype').html());
    }


    players.forEach(function(player, ind) {
        var suit = {
            'c': '&clubs;',
            's': '&spades;',
            'h': '&hearts;',
            'd': '&diams;'
        };
        var color = {
            'c': 'black',
            's': 'black',
            'd': 'red',
            'h': 'red'
        };
        $player = $($('.player-row')[ind]);

        $player.removeClass('fault');
        if (player.is_fault) {
            $player.addClass('fault');
        }
        $player.removeClass('active');
        if (player.is_current) {
            $player.addClass('active');
        }

        $player.find('.name').html(player.name);

        $player.find('.cards .card span').html('&nbsp;');
        $player.find('.cards .card i').html('&nbsp;');

        $player.find('.cards .card').removeClass('red');
        $player.find('.cards .card').removeClass('black');
        $player.find('.cards .card').removeClass('closed');

        if (player.hand.length) {
            $player.find('.cards .card:nth-child(1) span').html(player.hand[0][0]);
            $player.find('.cards .card:nth-child(1) i').html(suit[player.hand[0][1]]);
            $player.find('.cards .card:nth-child(1)').addClass(color[player.hand[0][1]]);
            $player.find('.cards .card:nth-child(2) span').html(player.hand[1][0]);
            $player.find('.cards .card:nth-child(2) i').html(suit[player.hand[1][1]]);
            $player.find('.cards .card:nth-child(2)').addClass(color[player.hand[1][1]]);
        } else {
            $player.find('.cards .card').addClass('closed');
        }

        $player.find('.stack').html('&nbsp;');
        $player.find('.stack').html(player.chips);

        $player.find('.bet').html('&nbsp;');
        if (player.bet) {
            $player.find('.bet').html(player.bet);
        }
        if (player.win_chips) {
            $player.find('.bet').html('+' + player.win_chips);
        }

        if (player.place) {
            $player.find('.stack').text('#' + player.place);
        }

        $player.find('.combination').html('&nbsp;');
        $player.find('.combination').html(player.combination);

        $player.find('.status').html('&nbsp;');
        if (player.status) {
            $player.find('.status').html(player.status);
        }

    });

});
