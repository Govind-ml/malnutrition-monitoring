# recommender.py
from datetime import datetime, date

def calculate_age_in_months(date_of_birth):
    """Calculate age in months from date of birth"""
    if isinstance(date_of_birth, str):
        dob = datetime.fromisoformat(date_of_birth).date()
    else:
        dob = date_of_birth
    
    today = date.today()
    age_months = (today.year - dob.year) * 12 + (today.month - dob.month)
    return age_months

def get_calorie_requirements(age_months, sex='unknown'):
    """Get daily calorie requirements based on age"""
    if age_months < 6:
        return 650  # 0-6 months (breastfeeding + complementary)
    elif age_months < 12:
        return 850  # 6-12 months
    elif age_months < 24:
        return 1000  # 1-2 years
    elif age_months < 36:
        return 1200  # 2-3 years
    elif age_months < 60:
        return 1400  # 3-5 years
    elif age_months < 84:
        return 1600  # 5-7 years
    elif age_months < 120:
        return 1800  # 7-10 years
    else:
        return 2000  # 10+ years

def get_protein_requirements(age_months, weight_kg=None):
    """Get daily protein requirements in grams"""
    if weight_kg:
        # 1-1.5g per kg body weight for children
        return weight_kg * 1.2
    
    # Fallback to age-based estimates
    if age_months < 6:
        return 10
    elif age_months < 12:
        return 14
    elif age_months < 24:
        return 16
    elif age_months < 36:
        return 20
    elif age_months < 60:
        return 24
    elif age_months < 84:
        return 28
    elif age_months < 120:
        return 32
    else:
        return 40

def calculate_bmi(weight_kg, height_cm):
    """Calculate BMI"""
    if height_cm > 0:
        height_m = height_cm / 100
        return weight_kg / (height_m ** 2)
    return 0

def assess_growth_status(age_months, weight_kg, height_cm, muac_cm=None):
    """Assess child's growth and nutritional status"""
    bmi = calculate_bmi(weight_kg, height_cm)
    issues = []
    
    # Weight-for-age assessment (simplified)
    if age_months < 24:
        expected_weight = 3.5 + (age_months * 0.5)  # Rough estimate
    elif age_months < 60:
        expected_weight = 12 + ((age_months - 24) * 0.2)
    else:
        expected_weight = 14 + ((age_months - 60) * 0.15)
    
    weight_ratio = weight_kg / expected_weight
    
    if weight_ratio < 0.7:
        issues.append("severe_underweight")
    elif weight_ratio < 0.85:
        issues.append("underweight")
    elif weight_ratio > 1.25:
        issues.append("overweight")
    
    # MUAC assessment (for children 6-59 months)
    if muac_cm and 6 <= age_months < 60:
        if muac_cm < 11.5:
            issues.append("severe_acute_malnutrition")
        elif muac_cm < 12.5:
            issues.append("moderate_acute_malnutrition")
    
    # BMI assessment
    if age_months >= 24:
        if bmi < 14:
            issues.append("severely_wasted")
        elif bmi < 15:
            issues.append("wasted")
        elif bmi > 18 and age_months < 60:
            issues.append("overweight_bmi")
        elif bmi > 20 and age_months >= 60:
            issues.append("overweight_bmi")
    
    return issues, bmi, weight_ratio

def evaluate_intake(child, recent_intakes, opd_reports):
    """
    Main evaluation function that generates human-readable recommendations
    
    Args:
        child: dict with child info (date_of_birth, sex)
        recent_intakes: list of recent daily intake dicts (last 7 days)
        opd_reports: list of all OPD report dicts
    
    Returns:
        dict with suggestions and analysis
    """
    suggestions = []
    
    # Calculate child's age
    age_months = calculate_age_in_months(child['date_of_birth'])
    age_years = age_months / 12
    
    # Get latest OPD report
    latest_opd = opd_reports[-1] if opd_reports else None
    
    # Get nutritional requirements
    calorie_req = get_calorie_requirements(age_months, child.get('sex'))
    
    if latest_opd:
        weight_kg = latest_opd['weight_kg']
        protein_req = get_protein_requirements(age_months, weight_kg)
    else:
        weight_kg = None
        protein_req = get_protein_requirements(age_months)
    
    # Analyze recent intake
    if recent_intakes:
        avg_calories = sum(i['total_calories'] for i in recent_intakes) / len(recent_intakes)
        avg_protein = sum(i['total_protein'] for i in recent_intakes) / len(recent_intakes)
        
        # Calorie assessment
        calorie_percentage = (avg_calories / calorie_req) * 100
        
        if calorie_percentage < 70:
            suggestions.append(
                f"⚠️ URGENT: Your child is consuming only {calorie_percentage:.0f}% of their daily calorie needs "
                f"({avg_calories:.0f} out of {calorie_req} calories). This is critically low. "
                f"Please increase portion sizes and add calorie-rich foods like bananas, peanut butter, and full-fat milk."
            )
        elif calorie_percentage < 85:
            suggestions.append(
                f"⚠️ Warning: Your child is getting {calorie_percentage:.0f}% of recommended calories "
                f"({avg_calories:.0f} out of {calorie_req} calories). "
                f"Try adding healthy snacks between meals like fruits, nuts, and yogurt."
            )
        elif calorie_percentage < 95:
            suggestions.append(
                f"✓ Good progress! Your child is consuming {calorie_percentage:.0f}% of their daily calorie needs "
                f"({avg_calories:.0f} out of {calorie_req} calories). "
                f"Just a little more to reach the ideal amount."
            )
        elif calorie_percentage <= 110:
            suggestions.append(
                f"✓ Excellent! Your child is meeting their calorie needs perfectly "
                f"({avg_calories:.0f} calories daily). Keep up the good work!"
            )
        else:
            suggestions.append(
                f"⚠️ Note: Your child is consuming {calorie_percentage:.0f}% of recommended calories "
                f"({avg_calories:.0f} out of {calorie_req} calories). "
                f"This is slightly high. Focus on nutrient-dense foods rather than empty calories."
            )
        
        # Protein assessment
        protein_percentage = (avg_protein / protein_req) * 100
        
        if protein_percentage < 70:
            suggestions.append(
                f"⚠️ URGENT: Protein intake is very low at {avg_protein:.1f}g daily "
                f"(needs {protein_req:.0f}g). Add protein-rich foods like eggs, dal, milk, chicken, or fish to every meal."
            )
        elif protein_percentage < 85:
            suggestions.append(
                f"⚠️ Protein intake is below recommended levels ({avg_protein:.1f}g out of {protein_req:.0f}g daily). "
                f"Include more lentils, eggs, paneer, or lean meat in the diet."
            )
        elif protein_percentage <= 110:
            suggestions.append(
                f"✓ Great! Protein intake is adequate at {avg_protein:.1f}g daily "
                f"({protein_percentage:.0f}% of {protein_req:.0f}g requirement)."
            )
        else:
            suggestions.append(
                f"✓ Protein intake is good at {avg_protein:.1f}g daily. This is {protein_percentage:.0f}% of the requirement."
            )
    else:
        suggestions.append(
            f"ℹ️ No recent intake data available. For a child aged {age_years:.1f} years, "
            f"aim for {calorie_req} calories and {protein_req:.0f}g protein daily."
        )
    
    # Analyze growth from OPD reports
    if latest_opd:
        weight_kg = latest_opd['weight_kg']
        height_cm = latest_opd['height_cm']
        muac_cm = latest_opd.get('muac_cm')
        
        issues, bmi, weight_ratio = assess_growth_status(age_months, weight_kg, height_cm, muac_cm)
        
        if "severe_underweight" in issues:
            suggestions.append(
                f"🚨 CRITICAL: Your child's weight ({weight_kg:.1f}kg) is significantly below normal for their age. "
                f"Please consult a pediatrician immediately. Increase meal frequency to 5-6 times daily with calorie-dense foods."
            )
        elif "underweight" in issues:
            suggestions.append(
                f"⚠️ Your child's weight ({weight_kg:.1f}kg) is below the healthy range. "
                f"Focus on nutritious, calorie-rich foods and consider consulting a nutritionist."
            )
        elif "overweight" in issues or "overweight_bmi" in issues:
            suggestions.append(
                f"⚠️ Your child's weight ({weight_kg:.1f}kg, BMI: {bmi:.1f}) is above the healthy range. "
                f"Focus on balanced meals with vegetables, limit sweets and fried foods, and encourage physical activity."
            )
        else:
            suggestions.append(
                f"✓ Your child's weight ({weight_kg:.1f}kg) is in a healthy range for their age. "
                f"Continue maintaining a balanced diet!"
            )
        
        if "severe_acute_malnutrition" in issues:
            suggestions.append(
                f"🚨 CRITICAL: MUAC measurement ({muac_cm:.1f}cm) indicates severe acute malnutrition. "
                f"Immediate medical intervention is required. Please visit a health facility urgently."
            )
        elif "moderate_acute_malnutrition" in issues:
            suggestions.append(
                f"⚠️ MUAC measurement ({muac_cm:.1f}cm) shows moderate acute malnutrition. "
                f"Increase protein and calorie intake immediately and monitor weekly."
            )
        
        # Growth trend analysis
        if len(opd_reports) >= 2:
            previous_opd = opd_reports[-2]
            weight_change = weight_kg - previous_opd['weight_kg']
            height_change = height_cm - previous_opd['height_cm']
            
            date_diff = (datetime.fromisoformat(latest_opd['date']) - 
                        datetime.fromisoformat(previous_opd['date'])).days
            months_diff = date_diff / 30
            
            if months_diff > 0:
                monthly_weight_gain = weight_change / months_diff
                monthly_height_gain = height_change / months_diff
                
                # Expected growth rates
                if age_months < 12:
                    expected_weight_gain = 0.4  # kg per month
                    expected_height_gain = 2.5  # cm per month
                elif age_months < 24:
                    expected_weight_gain = 0.25
                    expected_height_gain = 1.5
                else:
                    expected_weight_gain = 0.2
                    expected_height_gain = 0.7
                
                if monthly_weight_gain < expected_weight_gain * 0.5:
                    suggestions.append(
                        f"⚠️ Growth Concern: Weight gain is slow ({weight_change:.2f}kg in {months_diff:.1f} months). "
                        f"Expected gain is around {expected_weight_gain:.1f}kg per month at this age. "
                        f"Increase meal frequency and calorie intake."
                    )
                elif monthly_weight_gain >= expected_weight_gain * 0.8:
                    suggestions.append(
                        f"✓ Good Growth! Your child has gained {weight_change:.2f}kg over {months_diff:.1f} months, "
                        f"which is healthy. Keep maintaining the current nutrition pattern."
                    )
                
                if monthly_height_gain < expected_height_gain * 0.5 and age_months < 60:
                    suggestions.append(
                        f"⚠️ Height growth is slower than expected ({height_change:.1f}cm in {months_diff:.1f} months). "
                        f"Ensure adequate protein, calcium, and vitamin D intake. Consider adding milk, eggs, and leafy greens."
                    )
    else:
        suggestions.append(
            "ℹ️ No OPD measurements recorded yet. Please add weight, height, and MUAC measurements "
            "to get comprehensive growth assessments."
        )
    
    # General dietary recommendations
    if age_months < 6:
        suggestions.append(
            "ℹ️ For infants under 6 months: Continue exclusive breastfeeding. "
            "Consult your pediatrician before starting any complementary foods."
        )
    elif age_months < 12:
        suggestions.append(
            "ℹ️ For 6-12 months: Introduce mashed foods like rice cereal, mashed vegetables, "
            "pureed fruits, and well-cooked dal. Continue breastfeeding alongside solid foods."
        )
    elif age_months < 24:
        suggestions.append(
            "ℹ️ For 1-2 years: Offer a variety of soft, chopped foods. Include rice, dal, vegetables, "
            "fruits, eggs, and milk. Feed 5-6 times daily in small portions."
        )
    else:
        suggestions.append(
            "ℹ️ General tip: Ensure a balanced plate with whole grains, proteins (dal/eggs/meat), "
            "vegetables, fruits, and dairy. Limit processed foods and sugary drinks."
        )
    
    # If no issues found and everything looks good
    if not suggestions or all('✓' in s for s in suggestions):
        suggestions.append(
            "🎉 Overall, your child's nutrition is on track! Continue with the current diet pattern "
            "and maintain regular health check-ups."
        )
    
    return {
        "suggestions": suggestions,
        "age_months": age_months,
        "calorie_requirement": calorie_req,
        "protein_requirement": protein_req,
        "average_intake": {
            "calories": sum(i['total_calories'] for i in recent_intakes) / len(recent_intakes) if recent_intakes else 0,
            "protein": sum(i['total_protein'] for i in recent_intakes) / len(recent_intakes) if recent_intakes else 0
        }
    }