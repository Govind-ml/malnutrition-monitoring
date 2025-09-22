# recommender.py
from datetime import date, datetime
from statistics import mean

AGE_ENERGY_REQUIREMENTS = [
    (6, 11, 500),
    (12, 23, 900),
    (24, 35, 1200),
    (36, 59, 1400),
]

def age_in_months(dob):
    today = date.today()
    return (today.year - dob.year) * 12 + (today.month - dob.month) - (1 if today.day < dob.day else 0)

def recommended_kcal_for_age_months(months):
    for min_m, max_m, kcal in AGE_ENERGY_REQUIREMENTS:
        if min_m <= months <= max_m:
            return kcal
    return 1200

def evaluate_intake(child, intakes, opd_reports):
    """
    Synchronous evaluation: returns dict {status, score, suggestions}
    child: dict with date_of_birth isoformat
    intakes: list of DailyIntake dicts (most recent first preferred)
    opd_reports: list of OPDReport dicts (any order)
    """
    dob = child["date_of_birth"]
    dob_dt = datetime.fromisoformat(dob).date()
    months = age_in_months(dob_dt)
    rec_kcal = recommended_kcal_for_age_months(months)

    if not intakes:
        return {"status": "no_data", "score": None, "suggestions": ["No intake data provided. Please log daily intake."]}

    calories = [i["total_calories"] for i in intakes if i.get("total_calories") is not None]
    mean_cal = mean(calories) if calories else 0
    calorie_pct = mean_cal / rec_kcal if rec_kcal else 0

    suggestions = []
    status = "normal"
    score = round(calorie_pct, 2)

    if calorie_pct < 0.7:
        status = "under_intake"
        suggestions.append(f"Average intake {mean_cal:.0f} kcal/day ({int(100*calorie_pct)}% of recommended {rec_kcal} kcal/day). Increase energy-dense meals.")
    elif calorie_pct < 0.9:
        status = "at_risk"
        suggestions.append(f"Average intake {mean_cal:.0f} kcal/day is below recommendation; monitor closely.")
    else:
        suggestions.append("Average calorie intake meets or exceeds recommendation.")

    # growth trend
    if len(opd_reports) >= 2:
        opd_sorted = sorted(opd_reports, key=lambda x: x["date"])
        weights = [r["weight_kg"] for r in opd_sorted[-3:]]  # last up to 3
        if len(weights) >= 2:
            delta = weights[-1] - weights[0]
            if delta < 0:
                status = "weight_loss"
                suggestions.append(f"Weight decreased by {delta:.2f} kg over recent OPD reports — clinical review recommended.")
            else:
                suggestions.append(f"Weight change over recent reports: {delta:.2f} kg (positive).")

    if opd_reports:
        latest = sorted(opd_reports, key=lambda x: x["date"])[-1]
        muac = latest.get("muac_cm")
        if muac:
            if muac < 11.5:
                status = "severe_malnutrition"
                suggestions.append("MUAC < 11.5 cm — possible severe acute malnutrition. Refer to clinician immediately.")
            elif muac < 12.5:
                if status != "severe_malnutrition":
                    status = "moderate_malnutrition"
                suggestions.append("MUAC between 11.5 and 12.5 cm — moderate malnutrition risk. Nutritional counselling recommended.")

    suggestions.append("Feeding tips: increase meal frequency, include eggs/legumes/dairy, add healthy oils for energy density.")
    return {"status": status, "score": score, "suggestions": suggestions}
