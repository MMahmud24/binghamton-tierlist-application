from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
import json

app = Flask(__name__)

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///tierlists.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

class TierList(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100))
    data = db.Column(db.Text)



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

@app.route("/signup")
def signup():
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
