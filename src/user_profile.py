"""Foydalanuvchi profilini bazadan o'qish."""

from config.settings import (
    CURRENT_LEVEL,
    DAILY_STUDY_TIME,
    TARGET_DATE,
    TARGET_LEVEL,
    USER_NAME,
)


def get_profile(db=None):
    profile = {
        "name": USER_NAME,
        "current_level": CURRENT_LEVEL,
        "target_level": TARGET_LEVEL,
        "target_date": TARGET_DATE,
        "daily_minutes": DAILY_STUDY_TIME,
    }

    if db is None:
        return profile

    user = db.get_user()
    if not user:
        return profile

    if user.get("name"):
        profile["name"] = user["name"]
    if user.get("current_level"):
        profile["current_level"] = user["current_level"]
    if user.get("target_level"):
        profile["target_level"] = user["target_level"]
    if user.get("target_date"):
        profile["target_date"] = user["target_date"]
    if user.get("daily_minutes"):
        profile["daily_minutes"] = int(user["daily_minutes"])

    return profile
