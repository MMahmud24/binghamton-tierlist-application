import os
import json
from flask import Flask, render_template, request, jsonify, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL", "sqlite:///tierlists.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "a7f3c9e2b8d4f1a6e9c2b7d4f3a8e1c9")

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


def _build_preview_data(tierlists):
    preview_data = []
    for tl in tierlists:
        mini_tiers = []
        try:
            tiers = json.loads(tl.data)
            for tier_label in ["S", "A", "B", "C", "D", "F"]:
                items = tiers.get(tier_label, [])
                row = []
                for item in items:
                    if isinstance(item, dict):
                        row.append({
                            "name": item.get("name") or "",
                            "image": item.get("image")
                        })
                    else:
                        row.append({"name": str(item), "image": None})
                mini_tiers.append({"label": tier_label, "items": row})
        except Exception:
            tiers = {}
            mini_tiers = []

        preview_data.append({
            "id": tl.id,
            "title": tl.title,
            "mini_tiers": mini_tiers,
        })
    return preview_data


@app.route("/")
def index():
    tierlists = TierList.query.order_by(TierList.id.desc()).all()
    preview_data = _build_preview_data(tierlists)
    return render_template("index.html", tierlists=preview_data)


@app.route("/create")
def create():
    return render_template("create.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        if not username or not password:
            flash('Please enter both username and password', 'error')
            return render_template("login.html")
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            session['user_id'] = user.id
            session['username'] = user.username
            flash('Login successful!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password', 'error')
            return render_template("login.html")

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    flash('You have been logged out', 'success')
    return redirect(url_for('index'))


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

        existing_user = User.query.filter((User.username == username) | (User.email == email)).first()
        if existing_user:
            return render_template("signup.html", error="Username or email already exists.")

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


@app.route("/view/<int:id>")
def view_tierlist(id):
    tierlist = TierList.query.get_or_404(id)
    tiers = json.loads(tierlist.data)

    return render_template(
        "view.html",
        title=tierlist.title,
        tiers=tiers
    )


@app.route("/debug/db")
def debug_db():
    """Temporary debug route to inspect all users and tier lists."""
    tierlists = TierList.query.order_by(TierList.id).all()
    users = User.query.order_by(User.id).all()
    return render_template("debug_db.html", tierlists=tierlists, users=users)


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
