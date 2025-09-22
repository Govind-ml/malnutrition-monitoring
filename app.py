# app.py
from flask import Flask, request, jsonify, render_template
from models import db, Child, DailyIntake, OPDReport
from recommender import evaluate_intake
from datetime import datetime, date
import os

app = Flask(__name__, template_folder="templates", static_folder="static")
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///malnutrition.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)

@app.before_request
def create_db():
    db.create_all()

# --- Child management (create one from UI if needed) ---
@app.route("/api/children", methods=["POST"])
def create_child():
    data = request.get_json()
    name = data["name"]
    dob = datetime.fromisoformat(data["date_of_birth"]).date()
    sex = data.get("sex", "unknown")
    child = Child(name=name, date_of_birth=dob, sex=sex)
    db.session.add(child)
    db.session.commit()
    return jsonify(child.to_dict()), 201

@app.route("/api/children", methods=["GET"])
def list_children():
    children = Child.query.all()
    return jsonify([c.to_dict() for c in children])

# --- Intake: create and immediately return updated recommendation ---
@app.route("/api/children/<int:child_id>/intake", methods=["POST"])
def add_intake_and_recommend(child_id):
    Child.query.get_or_404(child_id)
    data = request.get_json()
    # expected fields: date (ISO), meal_items (list), total_calories, total_protein
    dt = datetime.fromisoformat(data["date"]).date()
    meal_items = data.get("meal_items", [])
    total_calories = float(data.get("total_calories", 0.0))
    total_protein = float(data.get("total_protein", 0.0))

    intake = DailyIntake(child_id=child_id, date=dt, meal_items=meal_items,
                         total_calories=total_calories, total_protein=total_protein)
    db.session.add(intake)
    db.session.commit()

    # Fetch recent intakes and opd to run recommender synchronously
    intakes = DailyIntake.query.filter_by(child_id=child_id).order_by(DailyIntake.date.desc()).limit(14).all()
    intakes_list = [i.to_dict() for i in intakes]
    opds = OPDReport.query.filter_by(child_id=child_id).order_by(OPDReport.date.asc()).all()
    opds_list = [o.to_dict() for o in opds]
    child = Child.query.get(child_id).to_dict()
    # Pass last 7 days (or up to 7 records)
    result = evaluate_intake(child, intakes_list[:7], opds_list)
    return jsonify({"intake": intake.to_dict(), "recommendation": result}), 201

# --- OPD: create and immediately return updated recommendation ---
@app.route("/api/children/<int:child_id>/opd", methods=["POST"])
def add_opd_and_recommend(child_id):
    Child.query.get_or_404(child_id)
    data = request.get_json()
    dt = datetime.fromisoformat(data["date"]).date()
    weight = float(data["weight_kg"])
    height = float(data["height_cm"])
    muac = float(data["muac_cm"]) if data.get("muac_cm") is not None else None
    notes = data.get("notes", "")
    r = OPDReport(child_id=child_id, date=dt, weight_kg=weight, height_cm=height, muac_cm=muac, notes=notes)
    db.session.add(r)
    db.session.commit()

    intakes = DailyIntake.query.filter_by(child_id=child_id).order_by(DailyIntake.date.desc()).limit(14).all()
    intakes_list = [i.to_dict() for i in intakes]
    opds = OPDReport.query.filter_by(child_id=child_id).order_by(OPDReport.date.asc()).all()
    opds_list = [o.to_dict() for o in opds]
    child = Child.query.get(child_id).to_dict()
    result = evaluate_intake(child, intakes_list[:7], opds_list)
    return jsonify({"opd": r.to_dict(), "recommendation": result}), 201

# --- Fetch endpoints for dashboard ---
@app.route("/api/children/<int:child_id>/intake", methods=["GET"])
def get_intakes(child_id):
    Child.query.get_or_404(child_id)
    records = DailyIntake.query.filter_by(child_id=child_id).order_by(DailyIntake.date.asc()).all()
    return jsonify([r.to_dict() for r in records])

@app.route("/api/children/<int:child_id>/opd", methods=["GET"])
def get_opds(child_id):
    Child.query.get_or_404(child_id)
    records = OPDReport.query.filter_by(child_id=child_id).order_by(OPDReport.date.asc()).all()
    return jsonify([r.to_dict() for r in records])

# --- Synchronous recommendation-only endpoint (no create) ---
@app.route("/api/children/<int:child_id>/recommend", methods=["GET"])
def recommend(child_id):
    c = Child.query.get_or_404(child_id)
    intakes = DailyIntake.query.filter_by(child_id=child_id).order_by(DailyIntake.date.desc()).limit(14).all()
    opds = OPDReport.query.filter_by(child_id=child_id).order_by(OPDReport.date.asc()).all()
    result = evaluate_intake(c.to_dict(), [i.to_dict() for i in intakes][:7], [o.to_dict() for o in opds])
    return jsonify(result)

# --- UI ---
@app.route("/")
def index():
    return render_template("index.html")

if __name__ == "__main__":
    app.run(debug=True, port=5000)
