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
board = [['' for _ in range(3)] for _ in range(3)]
turn = 'X'                 # whose turn it is now

def check_winner(b):
    # rows, cols, diags
    lines = b + list(map(list, zip(*b))) + [[b[i][i] for i in range(3)]] + [[b[i][2-i] for i in range(3)]]
    for line in lines:
        if line[0] and line.count(line[0]) == 3:
            return line[0]
    return None

@app.route('/', methods=['GET', 'POST'])
def index():
    global turn
    ip = request.remote_addr

    # assign player if new
    if ip not in players and len(players) < 2:
        players[ip] = 'X' if 'X' not in players.values() else 'O'
        logging.info(f"Assigned {ip} as {players[ip]}")

    if request.method == 'POST':
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
            winner = check_winner(board)
            if winner:
                flash(f"Player {winner} wins!")
            elif all(all(cell for cell in row) for row in board):
                flash("Draw!")
            else:
                turn = 'O' if turn == 'X' else 'X'
        return redirect(url_for('index'))

    return render_template('index.html',
                           board=board,
                           players=players,
                           your_symbol=players.get(ip),
                           turn=turn)

@app.route('/reset')
def reset():
    global board, turn, players
    board = [['' for _ in range(3)] for _ in range(3)]
    turn = 'X'
    players.clear()
    logging.info("Game reset")
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
