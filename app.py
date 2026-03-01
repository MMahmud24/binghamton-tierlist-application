import os
import json
from flask import Flask, render_template, request, jsonify, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.sql import func
from sqlalchemy import UniqueConstraint

app = Flask(__name__)

app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL", "sqlite:///tierlists.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "a7f3c9e2b8d4f1a6e9c2b7d4f3a8e1c9")

db = SQLAlchemy(app)


class TierList(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100))
    data = db.Column(db.Text)
    cover_image = db.Column(db.Text, nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)
    user = db.relationship("User", backref="tierlists")
    comments = db.relationship("Comment", backref="tierlist", cascade="all, delete-orphan")
    votes = db.relationship("TierListVote", backref="tierlist", cascade="all, delete-orphan")


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=func.now())
    updated_at = db.Column(db.DateTime, nullable=False, default=func.now(), onupdate=func.now())
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    tierlist_id = db.Column(db.Integer, db.ForeignKey("tier_list.id"), nullable=False)
    user = db.relationship("User", backref="comments")


class TierListVote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    value = db.Column(db.Integer, nullable=False)  # 1 = upvote, -1 = downvote
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    tierlist_id = db.Column(db.Integer, db.ForeignKey("tier_list.id"), nullable=False)
    user = db.relationship("User", backref="tierlist_votes")
    __table_args__ = (UniqueConstraint("user_id", "tierlist_id", name="uq_vote_user_tierlist"),)


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
            "cover_image": tl.cover_image,
            "username": tl.user.username if tl.user else None,
            "user_id": tl.user_id,
            "upvotes": sum(1 for vote in tl.votes if vote.value == 1),
            "downvotes": sum(1 for vote in tl.votes if vote.value == -1),
            "score": sum(vote.value for vote in tl.votes),
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


@app.route("/edit/<int:id>")
def edit_tierlist(id):
    tierlist = TierList.query.get_or_404(id)
    if session.get("user_id") != tierlist.user_id:
        flash("You don't have permission to edit this tier list.", "error")
        return redirect(url_for("index"))
    tiers = json.loads(tierlist.data)
    return render_template(
        "create.html",
        edit_mode=True,
        edit_id=tierlist.id,
        edit_title=tierlist.title,
        edit_cover=tierlist.cover_image,
        edit_tiers=tiers,
    )


@app.route("/update/<int:id>", methods=["POST"])
def update_tierlist(id):
    tierlist = TierList.query.get_or_404(id)
    if session.get("user_id") != tierlist.user_id:
        return jsonify({"error": "Unauthorized"}), 403

    payload = request.get_json()
    if not payload or "tiers" not in payload:
        return jsonify({"error": "Invalid data"}), 400

    tierlist.title = payload.get("title", tierlist.title)
    tierlist.data = json.dumps(payload["tiers"])
    if "cover_image" in payload:
        tierlist.cover_image = payload["cover_image"] or None

    db.session.commit()
    return jsonify({"id": tierlist.id})


@app.route("/save", methods=["POST"])
def save():
    payload = request.get_json()

    if not payload or "tiers" not in payload:
        return jsonify({"error": "Invalid data"}), 400

    tierlist = TierList(
        title=payload.get("title", "Untitled Tier List"),
        data=json.dumps(payload["tiers"]),
        cover_image=payload.get("cover_image") or None,
        user_id=session.get("user_id") or None,
    )

    db.session.add(tierlist)
    db.session.commit()

    return jsonify({"id": tierlist.id})


@app.route("/view/<int:id>")
def view_tierlist(id):
    tierlist = TierList.query.get_or_404(id)
    tiers = json.loads(tierlist.data)
    comments = Comment.query.filter_by(tierlist_id=tierlist.id).order_by(Comment.created_at.desc()).all()
    upvotes = TierListVote.query.filter_by(tierlist_id=tierlist.id, value=1).count()
    downvotes = TierListVote.query.filter_by(tierlist_id=tierlist.id, value=-1).count()
    score = upvotes - downvotes
    current_user_vote = None
    if session.get("user_id"):
        existing_vote = TierListVote.query.filter_by(
            tierlist_id=tierlist.id,
            user_id=session["user_id"]
        ).first()
        if existing_vote:
            current_user_vote = existing_vote.value

    return render_template(
        "view.html",
        title=tierlist.title,
        tiers=tiers,
        cover_image=tierlist.cover_image,
        username=tierlist.user.username if tierlist.user else None,
        is_owner=(session.get("user_id") == tierlist.user_id and tierlist.user_id is not None),
        tierlist_id=tierlist.id,
        comments=comments,
        current_user_id=session.get("user_id"),
        upvotes=upvotes,
        downvotes=downvotes,
        score=score,
        current_user_vote=current_user_vote,
    )


@app.route("/view/<int:id>/vote", methods=["POST"])
def vote_tierlist(id):
    tierlist = TierList.query.get_or_404(id)
    if not session.get("user_id"):
        flash("Please log in to vote.", "error")
        return redirect(url_for("login"))

    vote_raw = request.form.get("vote", "").strip().lower()
    if vote_raw not in {"up", "down"}:
        flash("Invalid vote.", "error")
        return redirect(url_for("view_tierlist", id=tierlist.id))

    vote_value = 1 if vote_raw == "up" else -1
    existing_vote = TierListVote.query.filter_by(
        tierlist_id=tierlist.id,
        user_id=session["user_id"]
    ).first()

    if existing_vote is None:
        db.session.add(TierListVote(
            value=vote_value,
            user_id=session["user_id"],
            tierlist_id=tierlist.id,
        ))
        flash("Vote recorded.", "success")
    elif existing_vote.value == vote_value:
        flash("You already cast this vote.", "error")
    else:
        existing_vote.value = vote_value
        flash("Vote updated.", "success")

    db.session.commit()
    return redirect(url_for("view_tierlist", id=tierlist.id))


@app.route("/view/<int:id>/comments", methods=["POST"])
def add_comment(id):
    tierlist = TierList.query.get_or_404(id)
    if not session.get("user_id"):
        flash("Please log in to leave a comment.", "error")
        return redirect(url_for("login"))

    content = request.form.get("content", "").strip()
    if not content:
        flash("Comment cannot be empty.", "error")
        return redirect(url_for("view_tierlist", id=tierlist.id))
    if len(content) > 1000:
        flash("Comment is too long (max 1000 characters).", "error")
        return redirect(url_for("view_tierlist", id=tierlist.id))

    comment = Comment(
        content=content,
        user_id=session["user_id"],
        tierlist_id=tierlist.id,
    )
    db.session.add(comment)
    db.session.commit()
    flash("Comment posted.", "success")
    return redirect(url_for("view_tierlist", id=tierlist.id))


@app.route("/view/<int:tierlist_id>/comments/<int:comment_id>/edit", methods=["POST"])
def edit_comment(tierlist_id, comment_id):
    tierlist = TierList.query.get_or_404(tierlist_id)
    comment = Comment.query.filter_by(id=comment_id, tierlist_id=tierlist.id).first_or_404()

    if session.get("user_id") != comment.user_id:
        flash("You can only edit your own comments.", "error")
        return redirect(url_for("view_tierlist", id=tierlist.id))

    content = request.form.get("content", "").strip()
    if not content:
        flash("Comment cannot be empty.", "error")
        return redirect(url_for("view_tierlist", id=tierlist.id))
    if len(content) > 1000:
        flash("Comment is too long (max 1000 characters).", "error")
        return redirect(url_for("view_tierlist", id=tierlist.id))

    comment.content = content
    db.session.commit()
    flash("Comment updated.", "success")
    return redirect(url_for("view_tierlist", id=tierlist.id))


@app.route("/view/<int:tierlist_id>/comments/<int:comment_id>/delete", methods=["POST"])
def delete_comment(tierlist_id, comment_id):
    tierlist = TierList.query.get_or_404(tierlist_id)
    comment = Comment.query.filter_by(id=comment_id, tierlist_id=tierlist.id).first_or_404()

    if session.get("user_id") != comment.user_id:
        flash("You can only delete your own comments.", "error")
        return redirect(url_for("view_tierlist", id=tierlist.id))

    db.session.delete(comment)
    db.session.commit()
    flash("Comment deleted.", "success")
    return redirect(url_for("view_tierlist", id=tierlist.id))


@app.route("/delete/<int:id>", methods=["POST"])
def delete_tierlist(id):
    tierlist = TierList.query.get_or_404(id)
    if session.get("user_id") != tierlist.user_id:
        return jsonify({"error": "Unauthorized"}), 403
    TierListVote.query.filter_by(tierlist_id=tierlist.id).delete()
    Comment.query.filter_by(tierlist_id=tierlist.id).delete()
    db.session.delete(tierlist)
    db.session.commit()
    return jsonify({"success": True})


@app.route("/debug/db")
def debug_db():
    """Temporary debug route to inspect all users and tier lists."""
    tierlists = TierList.query.order_by(TierList.id).all()
    users = User.query.order_by(User.id).all()
    return render_template("debug_db.html", tierlists=tierlists, users=users)


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        from sqlalchemy import text, inspect
        inspector = inspect(db.engine)
        cols = [c["name"] for c in inspector.get_columns("tier_list")]
        tables = inspector.get_table_names()
        with db.engine.connect() as conn:
            if "cover_image" not in cols:
                conn.execute(text("ALTER TABLE tier_list ADD COLUMN cover_image TEXT"))
                print("[migration] Added cover_image column")
            if "user_id" not in cols:
                conn.execute(text("ALTER TABLE tier_list ADD COLUMN user_id INTEGER REFERENCES user(id)"))
                print("[migration] Added user_id column")
            if "comment" not in tables:
                conn.execute(text("""
                    CREATE TABLE comment (
                        id INTEGER NOT NULL PRIMARY KEY,
                        content TEXT NOT NULL,
                        created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                        updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                        user_id INTEGER NOT NULL REFERENCES user(id),
                        tierlist_id INTEGER NOT NULL REFERENCES tier_list(id)
                    )
                """))
                print("[migration] Added comment table")
            if "tier_list_vote" not in tables:
                conn.execute(text("""
                    CREATE TABLE tier_list_vote (
                        id INTEGER NOT NULL PRIMARY KEY,
                        value INTEGER NOT NULL,
                        user_id INTEGER NOT NULL REFERENCES user(id),
                        tierlist_id INTEGER NOT NULL REFERENCES tier_list(id),
                        CONSTRAINT uq_vote_user_tierlist UNIQUE (user_id, tierlist_id)
                    )
                """))
                print("[migration] Added tier_list_vote table")
            conn.commit()
    app.run(debug=True)
