# server/app.py
#!/usr/bin/env python3

from models import db, Activity, Camper, Signup
from flask_migrate import Migrate
from flask import Flask, make_response, request
import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATABASE = os.environ.get(
    "DB_URI", f"sqlite:///{os.path.join(BASE_DIR, 'app.db')}"
)

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.json.compact = False

migrate = Migrate(app, db)
db.init_app(app)


@app.route("/")
def home():
    return ""


# ---------- CAMPERS ----------

@app.get("/campers")
def get_campers():
    campers = Camper.query.all()
    data = [c.to_dict(only=("id", "name", "age")) for c in campers]
    return make_response(data, 200)


@app.get("/campers/<int:id>")
def get_camper(id):
    camper = Camper.query.get(id)
    if not camper:
        return make_response({"error": "Camper not found"}, 404)

    # include signups with nested activities
    return make_response(camper.to_dict(), 200)


@app.patch("/campers/<int:id>")
def update_camper(id):
    camper = Camper.query.get(id)
    if not camper:
        return make_response({"error": "Camper not found"}, 404)

    data = request.get_json() or {}

    try:
        if "name" in data:
            camper.name = data["name"]
        if "age" in data:
            camper.age = data["age"]

        db.session.commit()
    except ValueError:
        db.session.rollback()
        return make_response({"errors": ["validation errors"]}, 400)

    return make_response(camper.to_dict(only=("id", "name", "age")), 202)


@app.post("/campers")
def create_camper():
    data = request.get_json() or {}

    try:
        camper = Camper(
            name=data.get("name"),
            age=data.get("age"),
        )
        db.session.add(camper)
        db.session.commit()
    except ValueError:
        db.session.rollback()
        return make_response({"errors": ["validation errors"]}, 400)

    return make_response(camper.to_dict(only=("id", "name", "age")), 201)


# ---------- ACTIVITIES ----------

@app.get("/activities")
def get_activities():
    activities = Activity.query.all()
    data = [a.to_dict(only=("id", "name", "difficulty")) for a in activities]
    return make_response(data, 200)


@app.delete("/activities/<int:id>")
def delete_activity(id):
    activity = Activity.query.get(id)
    if not activity:
        return make_response({"error": "Activity not found"}, 404)

    db.session.delete(activity)   # signups are deleted by cascade
    db.session.commit()
    return make_response("", 204)


# ---------- SIGNUPS ----------

@app.post("/signups")
def create_signup():
    data = request.get_json() or {}

    try:
        signup = Signup(
            camper_id=data.get("camper_id"),
            activity_id=data.get("activity_id"),
            time=data.get("time"),
        )
        db.session.add(signup)
        db.session.commit()
    except ValueError:
        db.session.rollback()
        return make_response({"errors": ["validation errors"]}, 400)

    # include nested camper and activity
    return make_response(signup.to_dict(), 201)


if __name__ == "__main__":
    app.run(port=5555, debug=True)