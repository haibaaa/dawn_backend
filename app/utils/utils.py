from datetime import date


def get_priority(
    deadline: date = None, estimated_hours: float = 0, grade_impact: float = 0
):
    # Now you can see exactly what affects the score
    score = grade_impact * 1.5
    # ... your priority logic ...
    return float(score)
