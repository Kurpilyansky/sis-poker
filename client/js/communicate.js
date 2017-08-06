/**
 * Created by shhdup on 16/07/2017.
 */

var socket = io.connect('http://' + HOSTNAME + ':' + PORT);

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

    var value = {
        'A': 'A',
        'K': 'K',
        'Q': 'Q',
        'J': 'J',
        'T': '10',
        '9': '9',
        '8': '8',
        '7': '7',
        '6': '6',
        '5': '5',
        '4': '4',
        '3': '3',
        '2': '2'
    };
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

    $('.blinds .num').html(data['blinds'].join('/'));
    $('#state .round-num').html(data['round_num']);
    $('#state .phase-name').html(state ? ':' + state : '&nbsp;');

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
            $card.addClass(color[card[1]]);
            $card.find('i').html(suit[card[1]]);
            $card.find('span').html(value[card[0]]);
        }
    });

    var players = data['players'];

    while ($('.player-row').length > players.length) {
        $('.player-row').last().remove();
    }

    while ($('.player-row').length < players.length) {
        $('.player-row-prototype').last().before('<div class="player-row"></div>');
        $('.player-row').last().html($('.player-row-prototype').html());
    }


    players.forEach(function(player, ind) {
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
            $player.find('.cards .card:nth-child(1) span').html(value[player.hand[0][0]]);
            $player.find('.cards .card:nth-child(1) i').html(suit[player.hand[0][1]]);
            $player.find('.cards .card:nth-child(1)').addClass(color[player.hand[0][1]]);
            $player.find('.cards .card:nth-child(2) span').html(value[player.hand[1][0]]);
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
        $player.find('.win-probs').html('&nbsp;');
        if (player.win_probs) {
            win_probs = []
            for (var i = 0; i < player.win_probs.length; ++i) {
              win_probs.push('<span class="item">' + (player.win_probs[i] * 100).toFixed() + '<span class="percent-symbol">%</span></span>');
            }
            $player.find('.win-probs').html(win_probs.join('&nbsp;'));
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

    var controls = data['controls'];
    if (controls) {
      var $controls_div = $('#controls');
      $controls_div.html('');
      controls.forEach(function(control) {
          var $control = $("<input/>").attr('type', 'submit').attr('value', control.text);
          $controls_div.append($control);
          //$controls_div.append($('<br/>'));
          $control.click(function () {
              var data = {'action_type': control.type};
              socket.emit('control', data);
            });
        });
    }
});
