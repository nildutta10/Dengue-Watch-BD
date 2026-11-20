def estimate_risk(recent_reports):
    """
    A transparent DEMO heuristic, not a medically validated forecast.
    Uses recent reported case counts only. A production forecast needs
    reliable time-series history, population denominators, weather/vector
    indicators, model validation, and public-health review.
    """
    values = [int(r["affected"]) for r in recent_reports if r.get("affected") is not None]
    if not values:
        return {
            "risk_level": "Insufficient data",
            "risk_percent": None,
            "outlook": "Add verified reports to calculate a demonstration risk score.",
            "basis": "No recent reports found.",
            "weeks": []
        }

    latest = values[0]
    previous = values[1] if len(values) > 1 else latest
    change = ((latest - previous) / max(previous, 1)) * 100
    # Score is a simple illustrative index, not probability of infection.
    score = max(5, min(95, int(35 + change * 0.6 + min(latest, 500) * 0.04)))
    if score >= 65:
        level = "High"
    elif score >= 40:
        level = "Moderate"
    else:
        level = "Low"

    weeks = []
    for week in range(1, 5):
        estimate = max(0, round(latest * (1 + (change / 100) * week * 0.25)))
        weeks.append({"week": f"Week {week}", "illustrative_cases": estimate})

    return {
        "risk_level": level,
        "risk_percent": score,
        "outlook": "Illustrative risk index based on recent entered reports; not an individual infection probability.",
        "basis": f"Latest reported count: {latest}; previous available count: {previous}; change: {change:.1f}%.",
        "weeks": weeks
    }
