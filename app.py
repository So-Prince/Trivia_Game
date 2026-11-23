
from flask import (
    Flask, render_template, request, session, jsonify, redirect, url_for
)
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask_migrate import Migrate
from werkzeug.security import generate_password_hash, check_password_hash
import random
import os
from functools import wraps


app = Flask(__name__)

# Application configuration
app.secret_key = "change-this-development-secret"

# Create a location for our database
os.makedirs(app.instance_path, exist_ok=True)

database_path = os.path.join(app.instance_path, "rock_paper_scissors.db")

app.config["SQLALCHEMY_DATABASE_URI"] = (
    "sqlite:///" + database_path
)

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)
migrate = Migrate(app, db)

game_options = ["rock", "paper", "scissor"]


# ---------------------------------
# DATABASE MODELS
# ---------------------------------

class Player(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    nickname = db.Column(
        db.String(50),
        nullable=False,
        default="Guest"
    )

    email = db.Column(
        db.String(120),
        unique=True,
        nullable=True
    )

    password_hash = db.Column(
        db.String(255),
        nullable=True
    )

    wins = db.Column(db.Integer, default=0, nullable=False)
    losses = db.Column(db.Integer, default=0, nullable=False)
    draws = db.Column(db.Integer, default=0, nullable=False)

    games = db.relationship(
        "Game",
        backref="player",
        lazy=True,
        cascade="all, delete-orphan"
    )


class Game(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    player_id = db.Column(
        db.Integer,
        db.ForeignKey("player.id"),
        nullable=False
    )

    player_choice = db.Column(db.String(20), nullable=False)
    computer_choice = db.Column(db.String(20), nullable=False)

    outcome = db.Column(db.String(10), nullable=False)

    played_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        nullable=False
    )


# ---------------------------------
# AUTHENTICATION DECORATOR
# ---------------------------------

def login_required(view):

    @wraps(view)
    def wrapped_view(*args, **kwargs):

        player_id = session.get("player_id")

        player = (
            db.session.get(Player, player_id)
            if player_id else None
        )

        # Require a real registered account
        if player is None or not player.email:
            session.clear()

            if request.is_json:
                return jsonify({
                    "error": "Please log in to continue."
                }), 401

            return redirect(url_for("login"))

        return view(*args, **kwargs)

    return wrapped_view


# ---------------------------------
# DATABASE HELPER FUNCTIONS
# ---------------------------------

def get_current_player():

    player_id = session.get("player_id")

    player = db.session.get(Player, player_id) if player_id else None

    if player is None:

        player = Player(nickname="Guest")

        db.session.add(player)
        db.session.commit()

        session["player_id"] = player.id

    return player


def play_game(user):

    computer = random.choice(game_options)

    if user == computer:
        outcome = "draw"

    elif (
        (user == "rock" and computer == "scissor")
        or (user == "scissor" and computer == "paper")
        or (user == "paper" and computer == "rock")
    ):
        outcome = "win"

    else:
        outcome = "lose"

    return computer, outcome


def get_recent_history(player):

    recent_games = (
        Game.query
        .filter_by(player_id=player.id)
        .order_by(Game.played_at.desc(), Game.id.desc())
        .limit(10)
        .all()
    )

    return [
        {
            "user": game.player_choice,
            "computer": game.computer_choice,
            "result": {
                "win": "You win!",
                "lose": "You lose!",
                "draw": "It's a draw!"
            }[game.outcome],
            "outcome": game.outcome
        }
        for game in recent_games
    ]


# ---------------------------------
# PLAYER REGISTRATION
# ---------------------------------

@app.route("/register", methods=["GET", "POST"])
def register():

    error = None

    if request.method == "POST":

        nickname = request.form.get("nickname", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        if not nickname or not email or not password:
            error = "All fields are required."

        elif len(nickname) > 50:
            error = "Nickname must not exceed 50 characters."

        elif len(password) < 8:
            error = "Password must contain at least 8 characters."

        elif Player.query.filter_by(email=email).first():
            error = "This email is already registered."

        else:

            new_player = Player(
                nickname=nickname,
                email=email,
                password_hash=generate_password_hash(password)
            )

            db.session.add(new_player)
            db.session.commit()

            # Start a fresh authenticated session
            session.clear()
            session["player_id"] = new_player.id

            return redirect(url_for("home"))

    return render_template("register.html", error=error)


# ---------------------------------
# PLAYER LOGIN
# ---------------------------------

@app.route("/login", methods=["GET", "POST"])
def login():

    error = None

    if request.method == "POST":

        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        player = Player.query.filter_by(email=email).first()

        if player and player.password_hash and check_password_hash(
            player.password_hash, password
        ):

            session.clear()
            session["player_id"] = player.id

            return redirect(url_for("home"))

        error = "Invalid email or password."

    return render_template("login.html", error=error)


# ---------------------------------
# PLAYER LOGOUT
# ---------------------------------

@app.route("/logout")
def logout():

    session.clear()

    return redirect(url_for("login"))

# ---------------------------------
# HOME PAGE
# ---------------------------------

@app.route("/")
@login_required
def home():

    player = db.session.get(
    Player,
    session["player_id"]
)

    return render_template(
        "index.html",
        player_score=player.wins,
        computer_score=player.losses,
        draw_score=player.draws,
        history=get_recent_history(player),
        nickname=player.nickname,
        logged_in=bool(player.email)
    )


# ---------------------------------
# PLAYER DASHBOARD
# ---------------------------------

@app.route("/dashboard")
@login_required
def dashboard():

    player = db.session.get(
        Player,
        session["player_id"]
    )

    total_games = (
        player.wins +
        player.losses +
        player.draws
    )

    win_rate = (
        (player.wins / total_games) * 100
        if total_games > 0 else 0
    )

    return render_template(
        "dashboard.html",
        player=player,
        total_games=total_games,
        win_rate=round(win_rate, 1)
    )


# ---------------------------------
# PLAY GAME
# ---------------------------------

@app.route("/play", methods=["POST"])
@login_required
def play():

    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({"error": "Invalid request"}), 400

    user = data.get("choice")

    if user not in game_options:
        return jsonify({"error": "Invalid choice"}), 400

    player = db.session.get(
    Player,
    session["player_id"]
)

    computer, outcome = play_game(user)

    # Update player statistics
    if outcome == "win":
        player.wins += 1

    elif outcome == "lose":
        player.losses += 1

    else:
        player.draws += 1

    # Save this round in the database
    new_game = Game(
        player_id=player.id,
        player_choice=user,
        computer_choice=computer,
        outcome=outcome
    )

    db.session.add(new_game)
    db.session.commit()

    result = {
        "win": "You win!",
        "lose": "You lose!",
        "draw": "It's a draw!"
    }[outcome]

    return jsonify({
        "user": user,
        "computer": computer,
        "result": result,
        "outcome": outcome,
        "player_score": player.wins,
        "computer_score": player.losses,
        "draw_score": player.draws,
        "history": get_recent_history(player)
    })


# ---------------------------------
# RESET GAME
# ---------------------------------

@app.route("/reset", methods=["POST"])
@login_required
def reset():

    player = db.session.get(
    Player,
    session["player_id"]
)

    # Delete saved game records for this player
    Game.query.filter_by(player_id=player.id).delete()

    player.wins = 0
    player.losses = 0
    player.draws = 0

    db.session.commit()

    return jsonify({
        "player_score": 0,
        "computer_score": 0,
        "draw_score": 0,
        "history": []
    })


# ---------------------------------
# CREATE DATABASE TABLES
# ---------------------------------

with app.app_context():
    db.create_all()


# ---------------------------------
# START APPLICATION
# ---------------------------------

if __name__ == "__main__":
    app.run(debug=True)
