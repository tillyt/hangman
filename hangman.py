from flask import (
        Flask,
        render_template,
        request,
        session,
        redirect,
        url_for
    )
import random
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

app.secret_key = '\x1f!=\x12\xe3"\xa0\x18\xb9\x96F\x12?\xe3\x8f\xffad\x13\xe1Z&F\xba'

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///hangman_game_local.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

 
class Player(db.Model):
    pk = db.Column(db.Integer, primary_key=True)
    # name = db.Column(db.String(64), index=True, unique=True)
    wins = db.Column(db.Integer)
    losses = db.Column(db.Integer)
    games = db.relationship('Game', backref='player', lazy='dynamic')

    def __init__(self):
        self.pk = random.randint(1e9, 1e10)


class Game(db.Model):
    pk = db.Column(db.Integer, primary_key=True)
    word = db.Column(db.String(50))
    tried = db.Column(db.String(50))
    player_id = db.Column(db.Integer, db.ForeignKey('player.pk'))
    
    def __init__(self, player_id, word=None):
        self.player_id = player_id
        if not word:
            self.word = self.get_random_word()
        else:
            self.word = word
        self.tried = ''
        self.pk = random.randint(1e9, 1e10)

    def get_random_word(self):
        with open("./wordlist.txt") as wordlist:
            words = wordlist.read().split()
        word = random.choice(words).upper()
        return word

    @property
    def wrong_letters(self):
        return ''.join(set(self.tried) - set(self.word)).upper()

    @property
    def errors(self):
        return str(len(self.wrong_letters))

    @property
    def current(self):
        return ''.join([c if c in self.tried else ' _ ' for c in self.word]).upper()

    @property
    def won(self):
        return self.current == self.word

    @property
    def lost(self):
        return self.errors == '6'

    @property
    def finished(self):
        return self.won or self.lost

    def guess_letter(self, letter):
        if not self.finished and letter not in self.tried:
            self.tried += letter
            db.session.commit()



@app.route('/')
def home():
    return render_template('index.html')

@app.route('/play')
def new_game():
    if 'player_id' not in session: 
        player = Player()
        session['player_id'] = player.pk
    player_id = session['player_id']
    previous_games = Game.query.filter_by(player_id=player_id)
    session['wins'] = 0
    session['losses'] = 0
    for game in previous_games:
        if game.won:
            session['wins'] += 1
        if game.lost:
            session['losses'] += 1
    game = Game(player_id)
    db.session.add(game)
    db.session.commit()
    return redirect(url_for('play', game_id=game.pk))

@app.route('/play/<game_id>', methods=['GET', 'POST'])
def play(game_id):
    current_game = Game.query.get_or_404(game_id)
    if request.method == 'POST':
        letter = request.form['letter'].upper()
        if len(letter) == 1 and letter.isalpha():
            current_game.guess_letter(letter)
    return render_template('play.html', game=current_game)


if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
