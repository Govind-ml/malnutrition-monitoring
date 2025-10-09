# app.py
from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS
from models import db, Child, DailyIntake, OPDReport
from recommender import evaluate_intake
from datetime import datetime
import os

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend communication

# Configuration
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///malnutrition.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SECRET_KEY"] = "your-secret-key-here"

# Initialize database
db.init_app(app)

# Create tables
with app.app_context():
    db.create_all()

# ==================== API ENDPOINTS ====================

# --- Child Management ---
@app.route("/api/children", methods=["POST"])
def create_child():
    """Create a new child profile"""
    try:
        data = request.get_json()
        
        name = data.get("name")
        dob = datetime.fromisoformat(data.get("date_of_birth")).date()
        sex = data.get("sex", "unknown")
        
        child = Child(name=name, date_of_birth=dob, sex=sex)
        db.session.add(child)
        db.session.commit()
        
        return jsonify({
            "message": "Child added successfully",
            "child": child.to_dict()
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400


@app.route("/api/children", methods=["GET"])
def list_children():
    """Get all children"""
    try:
        children = Child.query.all()
        return jsonify([c.to_dict() for c in children]), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@app.route("/api/children/<int:child_id>", methods=["GET"])
def get_child(child_id):
    """Get specific child details"""
    try:
        child = Child.query.get_or_404(child_id)
        return jsonify(child.to_dict()), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 404


@app.route("/api/children/<int:child_id>", methods=["DELETE"])
def delete_child(child_id):
    """Delete a child profile"""
    try:
        child = Child.query.get_or_404(child_id)
        db.session.delete(child)
        db.session.commit()
        return jsonify({"message": "Child deleted successfully"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400


# --- Daily Intake Management ---
@app.route("/api/children/<int:child_id>/intake", methods=["POST"])
def add_intake_and_recommend(child_id):
    """Add daily intake and get immediate recommendations"""
    try:
        child = Child.query.get_or_404(child_id)
        data = request.get_json()
        
        # Parse intake data
        dt = datetime.fromisoformat(data["date"]).date()
        meal_items = data.get("meal_items", [])
        total_calories = float(data.get("total_calories", 0.0))
        total_protein = float(data.get("total_protein", 0.0))
        
        # Create intake record
        intake = DailyIntake(
            child_id=child_id,
            date=dt,
            meal_items=meal_items,
            total_calories=total_calories,
            total_protein=total_protein
        )
        db.session.add(intake)
        db.session.commit()
        
        # Fetch recent data for recommendations
        intakes = DailyIntake.query.filter_by(child_id=child_id)\
            .order_by(DailyIntake.date.desc()).limit(14).all()
        opds = OPDReport.query.filter_by(child_id=child_id)\
            .order_by(OPDReport.date.asc()).all()
        
        # Generate recommendations
        result = evaluate_intake(
            child.to_dict(),
            [i.to_dict() for i in intakes][:7],
            [o.to_dict() for o in opds]
        )
        
        return jsonify({
            "message": "Intake recorded successfully",
            "intake": intake.to_dict(),
            "recommendation": result
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400


@app.route("/api/children/<int:child_id>/intake", methods=["GET"])
def get_intakes(child_id):
    """Get all intake records for a child"""
    try:
        Child.query.get_or_404(child_id)
        records = DailyIntake.query.filter_by(child_id=child_id)\
            .order_by(DailyIntake.date.asc()).all()
        return jsonify([r.to_dict() for r in records]), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@app.route("/api/children/<int:child_id>/intake/<int:intake_id>", methods=["DELETE"])
def delete_intake(child_id, intake_id):
    """Delete an intake record"""
    try:
        intake = DailyIntake.query.filter_by(id=intake_id, child_id=child_id).first_or_404()
        db.session.delete(intake)
        db.session.commit()
        return jsonify({"message": "Intake deleted successfully"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400


# --- OPD Report Management ---
@app.route("/api/children/<int:child_id>/opd", methods=["POST"])
def add_opd_and_recommend(child_id):
    """Add OPD report and get immediate recommendations"""
    try:
        child = Child.query.get_or_404(child_id)
        data = request.get_json()
        
        # Parse OPD data
        dt = datetime.fromisoformat(data["date"]).date()
        weight = float(data["weight_kg"])
        height = float(data["height_cm"])
        muac = float(data["muac_cm"]) if data.get("muac_cm") else None
        notes = data.get("notes", "")
        
        # Create OPD record
        opd = OPDReport(
            child_id=child_id,
            date=dt,
            weight_kg=weight,
            height_cm=height,
            muac_cm=muac,
            notes=notes
        )
        db.session.add(opd)
        db.session.commit()
        
        # Fetch recent data for recommendations
        intakes = DailyIntake.query.filter_by(child_id=child_id)\
            .order_by(DailyIntake.date.desc()).limit(14).all()
        opds = OPDReport.query.filter_by(child_id=child_id)\
            .order_by(OPDReport.date.asc()).all()
        
        # Generate recommendations
        result = evaluate_intake(
            child.to_dict(),
            [i.to_dict() for i in intakes][:7],
            [o.to_dict() for o in opds]
        )
        
        return jsonify({
            "message": "OPD report recorded successfully",
            "opd": opd.to_dict(),
            "recommendation": result
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400


@app.route("/api/children/<int:child_id>/opd", methods=["GET"])
def get_opds(child_id):
    """Get all OPD reports for a child"""
    try:
        Child.query.get_or_404(child_id)
        records = OPDReport.query.filter_by(child_id=child_id)\
            .order_by(OPDReport.date.asc()).all()
        return jsonify([r.to_dict() for r in records]), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@app.route("/api/children/<int:child_id>/opd/<int:opd_id>", methods=["DELETE"])
def delete_opd(child_id, opd_id):
    """Delete an OPD report"""
    try:
        opd = OPDReport.query.filter_by(id=opd_id, child_id=child_id).first_or_404()
        db.session.delete(opd)
        db.session.commit()
        return jsonify({"message": "OPD report deleted successfully"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400


# --- Recommendations ---
@app.route("/api/children/<int:child_id>/recommend", methods=["GET"])
def recommend(child_id):
    """Get recommendations without adding new data"""
    try:
        child = Child.query.get_or_404(child_id)
        
        intakes = DailyIntake.query.filter_by(child_id=child_id)\
            .order_by(DailyIntake.date.desc()).limit(14).all()
        opds = OPDReport.query.filter_by(child_id=child_id)\
            .order_by(OPDReport.date.asc()).all()
        
        result = evaluate_intake(
            child.to_dict(),
            [i.to_dict() for i in intakes][:7],
            [o.to_dict() for o in opds]
        )
        
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400


# --- Dashboard Statistics ---
@app.route("/api/children/<int:child_id>/stats", methods=["GET"])
def get_stats(child_id):
    """Get comprehensive statistics for a child"""
    try:
        child = Child.query.get_or_404(child_id)
        
        # Get recent intakes (last 30 days)
        intakes = DailyIntake.query.filter_by(child_id=child_id)\
            .order_by(DailyIntake.date.desc()).limit(30).all()
        
        # Get all OPD reports
        opds = OPDReport.query.filter_by(child_id=child_id)\
            .order_by(OPDReport.date.desc()).all()
        
        stats = {
            "child": child.to_dict(),
            "intake_summary": {
                "total_records": len(intakes),
                "avg_calories": sum(i.total_calories for i in intakes) / len(intakes) if intakes else 0,
                "avg_protein": sum(i.total_protein for i in intakes) / len(intakes) if intakes else 0,
            },
            "opd_summary": {
                "total_records": len(opds),
                "latest_weight": opds[0].weight_kg if opds else None,
                "latest_height": opds[0].height_cm if opds else None,
                "latest_muac": opds[0].muac_cm if opds else None,
            }
        }
        
        return jsonify(stats), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400


# ==================== FRONTEND ROUTES ====================

@app.route("/")
def index():
    """Serve the main dashboard"""
    html = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Child Nutrition Dashboard</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        
        .container { max-width: 1400px; margin: 0 auto; }
        
        .header {
            background: white;
            padding: 30px;
            border-radius: 15px;
            margin-bottom: 30px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
        }
        
        .header h1 {
            color: #667eea;
            font-size: 2.5em;
            margin-bottom: 10px;
        }
        
        .header p {
            color: #666;
            font-size: 1.1em;
        }
        
        .main-grid {
            display: grid;
            grid-template-columns: 350px 1fr;
            gap: 30px;
            margin-bottom: 30px;
        }
        
        .sidebar {
            display: flex;
            flex-direction: column;
            gap: 20px;
        }
        
        .card {
            background: white;
            padding: 25px;
            border-radius: 15px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
        }
        
        .card h2 {
            color: #333;
            margin-bottom: 20px;
            font-size: 1.5em;
            border-bottom: 2px solid #667eea;
            padding-bottom: 10px;
        }
        
        .form-group {
            margin-bottom: 15px;
        }
        
        .form-group label {
            display: block;
            margin-bottom: 5px;
            color: #555;
            font-weight: 600;
        }
        
        .form-group input,
        .form-group select,
        .form-group textarea {
            width: 100%;
            padding: 12px;
            border: 2px solid #e0e0e0;
            border-radius: 8px;
            font-size: 1em;
            transition: border-color 0.3s;
        }
        
        .form-group input:focus,
        .form-group select:focus,
        .form-group textarea:focus {
            outline: none;
            border-color: #667eea;
        }
        
        .btn {
            width: 100%;
            padding: 14px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 8px;
            font-size: 1em;
            font-weight: 600;
            cursor: pointer;
            transition: transform 0.2s;
        }
        
        .btn:hover {
            transform: translateY(-2px);
        }
        
        .btn:active {
            transform: translateY(0);
        }
        
        .child-selector {
            display: flex;
            gap: 10px;
            margin-bottom: 20px;
        }
        
        .child-selector select {
            flex: 1;
        }
        
        .child-selector button {
            padding: 12px 20px;
            background: #4CAF50;
            color: white;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            font-weight: 600;
        }
        
        .tabs {
            display: flex;
            gap: 10px;
            margin-bottom: 20px;
        }
        
        .tab {
            flex: 1;
            padding: 12px;
            background: #f5f5f5;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            font-weight: 600;
            transition: all 0.3s;
        }
        
        .tab.active {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }
        
        .tab-content {
            display: none;
        }
        
        .tab-content.active {
            display: block;
        }
        
        .meal-item {
            display: flex;
            gap: 10px;
            margin-bottom: 10px;
            align-items: center;
        }
        
        .meal-item input {
            flex: 1;
        }
        
        .meal-item button {
            padding: 10px 15px;
            background: #f44336;
            color: white;
            border: none;
            border-radius: 6px;
            cursor: pointer;
        }
        
        .add-meal-btn {
            width: 100%;
            padding: 10px;
            background: #4CAF50;
            color: white;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            margin-top: 10px;
        }
        
        .dashboard-content {
            display: grid;
            gap: 20px;
        }
        
        .recommendation-card {
            background: white;
            padding: 25px;
            border-radius: 15px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
        }
        
        .recommendation-card h3 {
            color: #667eea;
            margin-bottom: 15px;
            font-size: 1.3em;
        }
        
        .alert {
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 10px;
            line-height: 1.6;
        }
        
        .alert-warning {
            background: #fff3cd;
            border-left: 4px solid #ffc107;
            color: #856404;
        }
        
        .alert-success {
            background: #d4edda;
            border-left: 4px solid #28a745;
            color: #155724;
        }
        
        .alert-info {
            background: #d1ecf1;
            border-left: 4px solid #17a2b8;
            color: #0c5460;
        }
        
        .alert-danger {
            background: #f8d7da;
            border-left: 4px solid #dc3545;
            color: #721c24;
        }
        
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-bottom: 20px;
        }
        
        .stat-card {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 10px;
            text-align: center;
        }
        
        .stat-card h4 {
            font-size: 0.9em;
            opacity: 0.9;
            margin-bottom: 5px;
        }
        
        .stat-card .value {
            font-size: 2em;
            font-weight: bold;
        }
        
        .history-list {
            max-height: 400px;
            overflow-y: auto;
        }
        
        .history-item {
            background: #f8f9ff;
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 10px;
            border-left: 4px solid #667eea;
        }
        
        .history-item .date {
            font-weight: 600;
            color: #667eea;
            margin-bottom: 5px;
        }
        
        .history-item .details {
            color: #666;
            font-size: 0.9em;
        }
        
        .modal {
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(0,0,0,0.5);
            z-index: 1000;
            align-items: center;
            justify-content: center;
        }
        
        .modal.show {
            display: flex;
        }
        
        @media (max-width: 1024px) {
            .main-grid {
                grid-template-columns: 1fr;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🍎 Child Nutrition Tracker</h1>
            <p>Monitor and improve your child's nutritional health with AI-powered recommendations</p>
        </div>

        <div class="main-grid">
            <div class="sidebar">
                <div class="card">
                    <h2>Select Child</h2>
                    <div class="child-selector">
                        <select id="childSelect">
                            <option value="">Select a child...</option>
                        </select>
                        <button onclick="showAddChildModal()">+ Add</button>
                    </div>
                </div>

                <div class="card">
                    <div class="tabs">
                        <button class="tab active" onclick="switchTab('intake')">Daily Intake</button>
                        <button class="tab" onclick="switchTab('opd')">OPD Report</button>
                    </div>

                    <div id="intakeTab" class="tab-content active">
                        <form id="intakeForm">
                            <div class="form-group">
                                <label>Date</label>
                                <input type="date" id="intakeDate" required>
                            </div>
                            
                            <div class="form-group">
                                <label>Meals</label>
                                <div id="mealItems">
                                    <div class="meal-item">
                                        <input type="text" placeholder="Food item" class="meal-name" required>
                                        <input type="number" placeholder="Calories" class="meal-calories" step="0.1" required>
                                        <input type="number" placeholder="Protein (g)" class="meal-protein" step="0.1" required>
                                        <button type="button" onclick="removeMeal(this)">×</button>
                                    </div>
                                </div>
                                <button type="button" class="add-meal-btn" onclick="addMealItem()">+ Add Meal</button>
                            </div>

                            <button type="submit" class="btn">Submit Intake</button>
                        </form>
                    </div>

                    <div id="opdTab" class="tab-content">
                        <form id="opdForm">
                            <div class="form-group">
                                <label>Date</label>
                                <input type="date" id="opdDate" required>
                            </div>
                            <div class="form-group">
                                <label>Weight (kg)</label>
                                <input type="number" id="opdWeight" step="0.1" required>
                            </div>
                            <div class="form-group">
                                <label>Height (cm)</label>
                                <input type="number" id="opdHeight" step="0.1" required>
                            </div>
                            <div class="form-group">
                                <label>MUAC (cm) - Optional</label>
                                <input type="number" id="opdMuac" step="0.1">
                            </div>
                            <div class="form-group">
                                <label>Notes</label>
                                <textarea id="opdNotes" rows="3"></textarea>
                            </div>
                            <button type="submit" class="btn">Submit Report</button>
                        </form>
                    </div>
                </div>
            </div>

            <div class="dashboard-content">
                <div id="noChildMessage" class="card">
                    <h2>Welcome!</h2>
                    <p style="color: #666; margin-top: 10px;">Please add a child to start tracking their nutrition.</p>
                </div>

                <div id="dashboardData" style="display: none;">
                    <div class="stats-grid">
                        <div class="stat-card">
                            <h4>Avg Daily Calories</h4>
                            <div class="value" id="avgCalories">-</div>
                        </div>
                        <div class="stat-card">
                            <h4>Avg Daily Protein</h4>
                            <div class="value" id="avgProtein">-</div>
                        </div>
                        <div class="stat-card">
                            <h4>Latest Weight</h4>
                            <div class="value" id="latestWeight">-</div>
                        </div>
                        <div class="stat-card">
                            <h4>Growth Trend</h4>
                            <div class="value" id="growthTrend">-</div>
                        </div>
                    </div>

                    <div class="recommendation-card">
                        <h3>📋 Nutritional Recommendations</h3>
                        <div id="recommendations">
                            <p style="color: #999;">Submit intake data to see personalized recommendations</p>
                        </div>
                    </div>

                    <div class="card">
                        <h3 style="color: #667eea; margin-bottom: 15px;">Recent Intake History</h3>
                        <div id="intakeHistory" class="history-list">
                            <p style="color: #999;">No intake records yet</p>
                        </div>
                    </div>

                    <div class="card">
                        <h3 style="color: #667eea; margin-bottom: 15px;">OPD Report History</h3>
                        <div id="opdHistory" class="history-list">
                            <p style="color: #999;">No OPD reports yet</p>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <div id="addChildModal" class="modal">
        <div class="card" style="max-width: 400px; margin: 20px;">
            <h2>Add New Child</h2>
            <form id="addChildForm">
                <div class="form-group">
                    <label>Name</label>
                    <input type="text" id="childName" required>
                </div>
                <div class="form-group">
                    <label>Date of Birth</label>
                    <input type="date" id="childDob" required>
                </div>
                <div class="form-group">
                    <label>Sex</label>
                    <select id="childSex">
                        <option value="male">Male</option>
                        <option value="female">Female</option>
                    </select>
                </div>
                <button type="submit" class="btn">Add Child</button>
                <button type="button" class="btn" style="background: #999; margin-top: 10px;" onclick="hideAddChildModal()">Cancel</button>
            </form>
        </div>
    </div>

    <script>
        const API_BASE = '/api';
        let currentChildId = null;

        document.getElementById('intakeDate').valueAsDate = new Date();
        document.getElementById('opdDate').valueAsDate = new Date();

        loadChildren();

        function switchTab(tabName) {
            document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
            document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
            
            if (tabName === 'intake') {
                document.querySelector('.tab:first-child').classList.add('active');
                document.getElementById('intakeTab').classList.add('active');
            } else {
                document.querySelector('.tab:last-child').classList.add('active');
                document.getElementById('opdTab').classList.add('active');
            }
        }

        function addMealItem() {
            const container = document.getElementById('mealItems');
            const newItem = document.createElement('div');
            newItem.className = 'meal-item';
            newItem.innerHTML = `
                <input type="text" placeholder="Food item" class="meal-name" required>
                <input type="number" placeholder="Calories" class="meal-calories" step="0.1" required>
                <input type="number" placeholder="Protein (g)" class="meal-protein" step="0.1" required>
                <button type="button" onclick="removeMeal(this)">×</button>
            `;
            container.appendChild(newItem);
        }

        function removeMeal(btn) {
            const items = document.querySelectorAll('.meal-item');
            if (items.length > 1) {
                btn.parentElement.remove();
            }
        }

        function showAddChildModal() {
            document.getElementById('addChildModal').classList.add('show');
        }

        function hideAddChildModal() {
            document.getElementById('addChildModal').classList.remove('show');
            document.getElementById('addChildForm').reset();
        }

        async function loadChildren() {
            try {
                const response = await fetch(`${API_BASE}/children`);
                const children = await response.json();
                
                const select = document.getElementById('childSelect');
                select.innerHTML = '<option value="">Select a child...</option>';
                
                children.forEach(child => {
                    const option = document.createElement('option');
                    option.value = child.id;
                    option.textContent = `${child.name} (${child.age_years} years old)`;
                    select.appendChild(option);
                });

                if (children.length > 0 && !currentChildId) {
                    select.value = children[0].id;
                    onChildChange();
                }
            } catch (error) {
                console.error('Error loading children:', error);
            }
        }

        document.getElementById('childSelect').addEventListener('change', onChildChange);

        function onChildChange() {
            const select = document.getElementById('childSelect');
            currentChildId = select.value ? parseInt(select.value) : null;
            
            if (currentChildId) {
                document.getElementById('noChildMessage').style.display = 'none';
                document.getElementById('dashboardData').style.display = 'block';
                loadDashboardData();
            } else {
                document.getElementById('noChildMessage').style.display = 'block';
                document.getElementById('dashboardData').style.display = 'none';
            }
        }

        async function loadDashboardData() {
            if (!currentChildId) return;

            try {
                const intakeResponse = await fetch(`${API_BASE}/children/${currentChildId}/intake`);
                const intakes = await intakeResponse.json();
                displayIntakeHistory(intakes);

                const opdResponse = await fetch(`${API_BASE}/children/${currentChildId}/opd`);
                const opds = await opdResponse.json();
                displayOpdHistory(opds);

                calculateStats(intakes, opds);

                const recResponse = await fetch(`${API_BASE}/children/${currentChildId}/recommend`);
                const recommendations = await recResponse.json();
                displayRecommendations(recommendations);
            } catch (error) {
                console.error('Error loading dashboard:', error);
            }
        }

        function displayIntakeHistory(intakes) {
            const container = document.getElementById('intakeHistory');
            if (intakes.length === 0) {
                container.innerHTML = '<p style="color: #999;">No intake records yet</p>';
                return;
            }

            container.innerHTML = intakes.slice(-10).reverse().map(intake => `
                <div class="history-item">
                    <div class="date">${new Date(intake.date).toLocaleDateString()}</div>
                    <div class="details">
                        Calories: ${intake.total_calories.toFixed(0)} kcal | 
                        Protein: ${intake.total_protein.toFixed(1)} g<br>
                        <small>${intake.meal_items.join(', ')}</small>
                    </div>
                </div>
            `).join('');
        }

        function displayOpdHistory(opds) {
            const container = document.getElementById('opdHistory');
            if (opds.length === 0) {
                container.innerHTML = '<p style="color: #999;">No OPD reports yet</p>';
                return;
            }

            container.innerHTML = opds.slice(-10).reverse().map(opd => `
                <div class="history-item">
                    <div class="date">${new Date(opd.date).toLocaleDateString()}</div>
                    <div class="details">
                        Weight: ${opd.weight_kg.toFixed(1)} kg | 
                        Height: ${opd.height_cm.toFixed(1)} cm
                        ${opd.muac_cm ? ` | MUAC: ${opd.muac_cm.toFixed(1)} cm` : ''}
                        ${opd.notes ? `<br><small>${opd.notes}</small></small>` : ''}
                    </div>
                </div>
            `).join('');
        }

        function calculateStats(intakes, opds) {
            const avgCal = intakes.length > 0 
                ? intakes.reduce((sum, i) => sum + i.total_calories, 0) / intakes.length 
                : 0;
            document.getElementById('avgCalories').textContent = avgCal.toFixed(0);

            const avgProt = intakes.length > 0 
                ? intakes.reduce((sum, i) => sum + i.total_protein, 0) / intakes.length 
                : 0;
            document.getElementById('avgProtein').textContent = avgProt.toFixed(1) + 'g';

            if (opds.length > 0) {
                const latest = opds[opds.length - 1];
                document.getElementById('latestWeight').textContent = latest.weight_kg.toFixed(1) + ' kg';

                if (opds.length >= 2) {
                    const previous = opds[opds.length - 2];
                    const diff = latest.weight_kg - previous.weight_kg;
                    document.getElementById('growthTrend').textContent = diff >= 0 ? '↑' : '↓';
                } else {
                    document.getElementById('growthTrend').textContent = '-';
                }
            } else {
                document.getElementById('latestWeight').textContent = '-';
                document.getElementById('growthTrend').textContent = '-';
            }
        }

        function displayRecommendations(data) {
            const container = document.getElementById('recommendations');
            if (!data || !data.suggestions || data.suggestions.length === 0) {
                container.innerHTML = '<p style="color: #999;">No recommendations available yet. Add more data to get personalized suggestions.</p>';
                return;
            }

            container.innerHTML = data.suggestions.map(suggestion => {
                let alertClass = 'alert-info';
                if (suggestion.includes('🚨') || suggestion.includes('CRITICAL')) {
                    alertClass = 'alert-danger';
                } else if (suggestion.includes('⚠️') || suggestion.includes('Warning') || suggestion.includes('Concern')) {
                    alertClass = 'alert-warning';
                } else if (suggestion.includes('✓') || suggestion.includes('Good') || suggestion.includes('Excellent')) {
                    alertClass = 'alert-success';
                }
                
                return `<div class="alert ${alertClass}">${suggestion}</div>`;
            }).join('');
        }

        document.getElementById('addChildForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const data = {
                name: document.getElementById('childName').value,
                date_of_birth: document.getElementById('childDob').value,
                sex: document.getElementById('childSex').value
            };

            try {
                const response = await fetch(`${API_BASE}/children`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(data)
                });

                if (response.ok) {
                    hideAddChildModal();
                    await loadChildren();
                    alert('Child added successfully!');
                }
            } catch (error) {
                console.error('Error adding child:', error);
                alert('Error adding child. Please try again.');
            }
        });

        document.getElementById('intakeForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            if (!currentChildId) {
                alert('Please select a child first');
                return;
            }

            const mealItems = Array.from(document.querySelectorAll('.meal-item')).map(item => ({
                name: item.querySelector('.meal-name').value,
                calories: parseFloat(item.querySelector('.meal-calories').value),
                protein: parseFloat(item.querySelector('.meal-protein').value)
            }));

            const totalCalories = mealItems.reduce((sum, m) => sum + m.calories, 0);
            const totalProtein = mealItems.reduce((sum, m) => sum + m.protein, 0);

            const data = {
                date: document.getElementById('intakeDate').value,
                meal_items: mealItems.map(m => m.name),
                total_calories: totalCalories,
                total_protein: totalProtein
            };

            try {
                const response = await fetch(`${API_BASE}/children/${currentChildId}/intake`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(data)
                });

                if (response.ok) {
                    const result = await response.json();
                    displayRecommendations(result.recommendation);
                    loadDashboardData();
                    e.target.reset();
                    document.getElementById('intakeDate').valueAsDate = new Date();
                    alert('Intake recorded successfully!');
                }
            } catch (error) {
                console.error('Error submitting intake:', error);
                alert('Error recording intake. Please try again.');
            }
        });

        document.getElementById('opdForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            if (!currentChildId) {
                alert('Please select a child first');
                return;
            }

            const data = {
                date: document.getElementById('opdDate').value,
                weight_kg: parseFloat(document.getElementById('opdWeight').value),
                height_cm: parseFloat(document.getElementById('opdHeight').value),
                muac_cm: document.getElementById('opdMuac').value ? parseFloat(document.getElementById('opdMuac').value) : null,
                notes: document.getElementById('opdNotes').value
            };

            try {
                const response = await fetch(`${API_BASE}/children/${currentChildId}/opd`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(data)
                });

                if (response.ok) {
                    const result = await response.json();
                    displayRecommendations(result.recommendation);
                    loadDashboardData();
                    e.target.reset();
                    document.getElementById('opdDate').valueAsDate = new Date();
                    alert('OPD report recorded successfully!');
                }
            } catch (error) {
                console.error('Error submitting OPD:', error);
                alert('Error recording OPD report. Please try again.');
            }
        });
    </script>
</body>
</html>
    """
    return render_template_string(html)


# ==================== ERROR HANDLERS ====================

@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Resource not found"}), 404


@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return jsonify({"error": "Internal server error"}), 500


# ==================== RUN APPLICATION ====================

if __name__ == "__main__":
    print("\n" + "="*50)
    print("Child Nutrition Tracking System")
    print("="*50)
    print("\nStarting Flask server...")
    print("Dashboard available at: http://localhost:5000")
    print("API available at: http://localhost:5000/api")
    print("\nPress CTRL+C to stop the server\n")
    
    app.run(debug=True, port=5000, host='0.0.0.0')