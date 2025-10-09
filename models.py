# models.py
from flask_sqlalchemy import SQLAlchemy
from datetime import date, datetime

db = SQLAlchemy()

class Child(db.Model):
    __tablename__ = 'children'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    date_of_birth = db.Column(db.Date, nullable=False)
    sex = db.Column(db.String(10), default='unknown')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    intakes = db.relationship('DailyIntake', backref='child', lazy=True, cascade='all, delete-orphan')
    opd_reports = db.relationship('OPDReport', backref='child', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        age = (date.today() - self.date_of_birth).days / 365.25
        return {
            'id': self.id,
            'name': self.name,
            'date_of_birth': self.date_of_birth.isoformat(),
            'sex': self.sex,
            'age_years': round(age, 1),
            'age_months': round(age * 12, 1)
        }


class DailyIntake(db.Model):
    __tablename__ = 'daily_intakes'
    
    id = db.Column(db.Integer, primary_key=True)
    child_id = db.Column(db.Integer, db.ForeignKey('children.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    meal_items = db.Column(db.JSON)  # List of meal item names
    total_calories = db.Column(db.Float, default=0.0)
    total_protein = db.Column(db.Float, default=0.0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'child_id': self.child_id,
            'date': self.date.isoformat(),
            'meal_items': self.meal_items or [],
            'total_calories': self.total_calories,
            'total_protein': self.total_protein
        }


class OPDReport(db.Model):
    __tablename__ = 'opd_reports'
    
    id = db.Column(db.Integer, primary_key=True)
    child_id = db.Column(db.Integer, db.ForeignKey('children.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    weight_kg = db.Column(db.Float, nullable=False)
    height_cm = db.Column(db.Float, nullable=False)
    muac_cm = db.Column(db.Float, nullable=True)  # Mid-Upper Arm Circumference
    notes = db.Column(db.Text, default='')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'child_id': self.child_id,
            'date': self.date.isoformat(),
            'weight_kg': self.weight_kg,
            'height_cm': self.height_cm,
            'muac_cm': self.muac_cm,
            'notes': self.notes
        }