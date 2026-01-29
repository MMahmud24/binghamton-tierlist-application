from flask import Flask, render_template, request, jsonify, redirect, url_for, session, flash
import os
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import json

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev_secret_key")

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///tierlists.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

class TierList(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100))
    data = db.Column(db.Text)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)



@app.route("/")
def index():
    tierlists = TierList.query.order_by(TierList.id.desc()).all()
    
    return render_template("index.html", tierlists=tierlists)

@app.route("/create")
def create():
    return render_template("create.html")

@app.route("/login")
def login():
    return render_template("login.html")

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        email = request.form.get("email", "").strip()
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        password2 = request.form.get("password2", "")

        if not email or not username or not password:
            return render_template("signup.html", error="Please fill out all fields.")

        if password != password2:
            return render_template("signup.html", error="Passwords do not match.")

        # Check for existing user
        existing_user = User.query.filter((User.username == username) | (User.email == email)).first()
        if existing_user:
            return render_template("signup.html", error="Username or email already exists.")

        # Create user
        new_user = User(email=email, username=username)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()

        session['user_id'] = new_user.id
        session['username'] = new_user.username

        return render_template('signup.html', success=True, redirect_url=url_for('login'), username=new_user.username)

    return render_template("signup.html")



@app.route("/save", methods=["POST"])
def save():
    payload = request.get_json()

    if not payload or "tiers" not in payload:
        return jsonify({"error": "Invalid data"}), 400

    tierlist = TierList(
        title=payload.get("title", "Untitled Tier List"),
        data=json.dumps(payload["tiers"])
    )

    db.session.add(tierlist)
    db.session.commit()

    return jsonify({"id": tierlist.id})


# @app.route("/view/<int:id>", methods=["POST"])

@app.route("/view/<int:id>")
def view_tierlist(id):
    tierlist = TierList.query.get_or_404(id)
    tiers = json.loads(tierlist.data)

    return render_template(
        "view.html",
        title=tierlist.title,
        tiers=tiers
    )


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
