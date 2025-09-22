# models.py
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.dialects.sqlite import JSON

db = SQLAlchemy()

class Child(db.Model):
    __tablename__ = "children"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    date_of_birth = db.Column(db.Date, nullable=False)
    sex = db.Column(db.String(10), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "date_of_birth": self.date_of_birth.isoformat(),
            "sex": self.sex,
            "created_at": self.created_at.isoformat()
        }

class DailyIntake(db.Model):
    __tablename__ = "daily_intakes"
    id = db.Column(db.Integer, primary_key=True)
    child_id = db.Column(db.Integer, db.ForeignKey("children.id"), nullable=False)
    date = db.Column(db.Date, nullable=False)
    meal_items = db.Column(JSON, nullable=False)
    total_calories = db.Column(db.Float, nullable=False)
    total_protein = db.Column(db.Float, nullable=False)
    recorded_at = db.Column(db.DateTime, default=datetime.utcnow)

    child = db.relationship("Child", backref="intakes")

    def to_dict(self):
        return {
            "id": self.id,
            "child_id": self.child_id,
            "date": self.date.isoformat(),
            "meal_items": self.meal_items,
            "total_calories": self.total_calories,
            "total_protein": self.total_protein,
            "recorded_at": self.recorded_at.isoformat()
        }

class OPDReport(db.Model):
    __tablename__ = "opd_reports"
    id = db.Column(db.Integer, primary_key=True)
    child_id = db.Column(db.Integer, db.ForeignKey("children.id"), nullable=False)
    date = db.Column(db.Date, nullable=False)
    weight_kg = db.Column(db.Float, nullable=False)
    height_cm = db.Column(db.Float, nullable=False)
    muac_cm = db.Column(db.Float, nullable=True)
    notes = db.Column(db.Text, nullable=True)
    recorded_at = db.Column(db.DateTime, default=datetime.utcnow)

    child = db.relationship("Child", backref="opd_reports")

    def to_dict(self):
        return {
            "id": self.id,
            "child_id": self.child_id,
            "date": self.date.isoformat(),
            "weight_kg": self.weight_kg,
            "height_cm": self.height_cm,
            "muac_cm": self.muac_cm,
            "notes": self.notes,
            "recorded_at": self.recorded_at.isoformat()
        }
