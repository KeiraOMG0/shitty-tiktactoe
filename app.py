from flask import Flask, request, render_template, redirect, url_for, flash
import logging
import os

app = Flask(__name__)
app.secret_key = os.urandom(24)

# --- logging setup ---
logging.basicConfig(
    filename='game.log',
    level=logging.INFO,
    format='%(asctime)s %(message)s',
)

# --- game state ---
players = {}               # ip -> symbol ('X' or 'O')
player_order = []           # list of IPs, in order they joined
board = [['' for _ in range(3)] for _ in range(3)]
turn = 'X'
winner = None
game_over = False

def check_winner(b):
    lines = b + list(map(list, zip(*b))) + [[b[i][i] for i in range(3)]] + [[b[i][2-i] for i in range(3)]]
    for line in lines:
        if line[0] and line.count(line[0]) == 3:
            return line[0]
    return None

@app.route('/', methods=['GET', 'POST'])
def index():
    global turn, winner, game_over
    ip = request.headers.get('X-Forwarded-For', request.remote_addr).split(',')[0].strip()

    # assign player if new
    if ip not in players and len(players) < 2:
        if not player_order:
            players[ip] = 'X'
            player_order.append(ip)
            logging.info(f"Player 1 Joined: IP={ip} assigned X")
        elif len(player_order) == 1:
            players[ip] = 'O'
            player_order.append(ip)
            logging.info(f"Player 2 Joined: IP={ip} assigned O")

    if request.method == 'POST':
        if not game_over:
            r, c = map(int, request.form['cell'].split(','))
            if ip not in players:
                flash("Spectators cannot play.")
            elif players[ip] != turn:
                flash("Not your turn.")
            elif board[r][c]:
                flash("Cell already taken.")
            else:
                board[r][c] = turn
                logging.info(f"{ip} ({turn}) -> move at {r},{c}")
                winner_symbol = check_winner(board)
                if winner_symbol:
                    winner = winner_symbol
                    game_over = True
                    logging.info(f"Game Over: {winner} wins")
                    return redirect(url_for('winner_page'))
                elif all(all(cell for cell in row) for row in board):
                    winner = "Draw"
                    game_over = True
                    logging.info("Game Over: Draw")
                    return redirect(url_for('winner_page'))
                else:
                    turn = 'O' if turn == 'X' else 'X'
        return redirect(url_for('index'))

    if len(players) < 2:
        return render_template('waiting.html', players=players)

    return render_template('index.html',
                           board=board,
                           players=players,
                           your_symbol=players.get(ip),
                           turn=turn)

@app.route('/switch')
def switch_players():
    global players, player_order, turn
    if len(player_order) == 2:
        ip1, ip2 = player_order
        players[ip1], players[ip2] = players[ip2], players[ip1]
        logging.info(f"Players switched: {ip1} <--> {ip2}")
    return redirect(url_for('index'))

@app.route('/winner')
def winner_page():
    return render_template('winner.html', winner=winner)

@app.route('/reset')
def reset():
    global board, turn, players, player_order, winner, game_over
    board = [['' for _ in range(3)] for _ in range(3)]
    turn = 'X'
    winner = None
    game_over = False

    if len(player_order) == 2:
        # Swap players before resetting
        ip1, ip2 = player_order
        players[ip1], players[ip2] = players[ip2], players[ip1]
        logging.info(f"Players auto-switched after round: {ip1} <--> {ip2}")

    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
