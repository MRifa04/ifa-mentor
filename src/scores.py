"""
Foydalanuvchi ballarini bazadan o'qish.

UI va planner modullari CURRENT_SCORES o'rniga shu moduldan foydalanadi.
"""

from config.settings import CURRENT_SCORES

SKILL_KEYS = (
    "listening",
    "reading",
    "writing",
    "speaking",
)

EXAM_SKILLS = SKILL_KEYS

EXAM_SKILL_DISPLAY = (
    ("reading", "Reading", "#10B981"),
    ("listening", "Listening", "#8B5CF6"),
    ("speaking", "Speaking", "#3B82F6"),
    ("writing", "Writing", "#C084FC"),
)

EXAM_SKILL_NAMES = {
    key: label for key, label, _ in EXAM_SKILL_DISPLAY
}

EXAM_SKILL_LABELS = frozenset(EXAM_SKILL_NAMES.values())


def _baseline_scores():
    return {
        "listening": int(CURRENT_SCORES.get("listening", 0)),
        "reading": int(CURRENT_SCORES.get("reading", 0)),
        "writing": int(CURRENT_SCORES.get("writing", 0)),
        "speaking": int(CURRENT_SCORES.get("speaking", 0)),
        "vocabulary": int(CURRENT_SCORES.get("vocabulary", 0)),
        "overall": int(CURRENT_SCORES.get("overall", 0)),
    }


def _calc_overall(scores):
    main = [
        scores.get("listening", 0),
        scores.get("reading", 0),
        scores.get("writing", 0),
        scores.get("speaking", 0),
    ]
    return round(sum(main) / len(main))


def get_current_scores(db=None):
    """
    Eng so'nggi progress yozuvidan ballarni qaytaradi.
    Bazada ma'lumot bo'lmasa settings.py dagi boshlang'ich qiymatlar ishlatiladi.
    """
    scores = _baseline_scores()

    if db is None:
        return scores

    latest = db.get_latest_progress()
    if not latest:
        return scores

    for key in SKILL_KEYS + ("vocabulary",):
        value = latest.get(key)
        if value is not None and value > 0:
            scores[key] = int(round(value))

    overall = latest.get("overall")
    if overall is not None and overall > 0:
        scores["overall"] = int(round(overall))
    else:
        scores["overall"] = _calc_overall(scores)

    return scores


def get_weakest_skill(scores=None, db=None):
    scores = scores or get_current_scores(db)
    skills = {
        "Reading": scores.get("reading", 0),
        "Listening": scores.get("listening", 0),
        "Speaking": scores.get("speaking", 0),
        "Writing": scores.get("writing", 0),
    }
    return min(skills, key=skills.get)


def minutes_by_skill(plan):
    totals = {
        "Reading": 0,
        "Listening": 0,
        "Speaking": 0,
        "Writing": 0,
    }

    for task in plan or []:
        skill = task.get("skill", "")
        if skill not in totals:
            continue
        if task.get("is_completed"):
            continue
        totals[skill] += int(
            task.get("duration_minutes", 0) or 0
        )

    return totals
