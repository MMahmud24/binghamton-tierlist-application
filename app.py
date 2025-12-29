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
    return render_template("index.html")

@app.route("/create")
def create():
    return render_template("create.html")

@app.route("/login")
def login():
    return render_template("login.html")

@app.route("/signup")
def signup():
    return render_template("signup.html")



# @app.route("/save", methods=["POST"])


@app.route("/view", methods=["GET"])
def view():
    tierlists = get_all_tierlists()
    return render_template("view.html", tierlists=tierlists)

def get_all_tierlists():
    return TierList.query.all()




if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
