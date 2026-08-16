"""Universal Tenses Engine — formula, practice, mastery."""

import json
import random

from src.tenses.registry import (
    TENSE_REGISTRY,
    TENSE_ORDER,
    get_tense,
    get_all_tenses,
    get_mastery_label,
    PRONOUNS,
)


class TensesEngine:
  SKILL_AREAS = [
      "formula", "affirmative", "negative", "question",
      "wh_question", "usage", "recognition",
      "transformation", "translation", "creation",
  ]

  def __init__(self, db, ai=None):
      self.db = db
      self.ai = ai
      self.db.ensure_tense_mastery()

  def list_tenses(self):
      return get_all_tenses()

  def get(self, tense_key):
      tense = get_tense(tense_key)
      if not tense:
          return None
      data = dict(tense)
      data["pronouns"] = self.build_pronoun_table(tense_key)
      data["mastery"] = self.db.get_tense_mastery(tense_key)
      return data

  def build_pronoun_table(self, tense_key):
      tense = get_tense(tense_key)
      if not tense:
          return []

      if tense.get("pronouns") and tense_key == "present_simple":
          return self._present_simple_pronouns()
      if tense.get("pronouns") and tense_key == "present_continuous":
          return tense["pronouns"]

      return self._generic_pronoun_hint(tense)

  def _present_simple_pronouns(self):
      rows = []
      for p in PRONOUNS:
          if p in ("He", "She", "It"):
              rows.append({
                  "pronoun": p,
                  "auxiliary": "does",
                  "verb": "works",
                  "sentence": f"{p} works.",
                  "note": "V1 + s/es",
              })
          else:
              rows.append({
                  "pronoun": p,
                  "auxiliary": "—",
                  "verb": "work",
                  "sentence": f"{p} work.",
                  "note": "V1",
              })
      return rows

  def _generic_pronoun_hint(self, tense):
      aux = tense.get("auxiliary", {}).get("rule", "")
      formula = tense.get("formula", {}).get("affirmative", "")
      return [{
          "pronoun": "All",
          "auxiliary": aux,
          "verb": formula,
          "sentence": f"Formula: {formula}",
          "note": tense.get("important_rule", ""),
      }]

  def get_comparison(self, tense_key):
      tense = get_tense(tense_key)
      if not tense or not tense.get("comparison"):
          return None
      other_key = tense["comparison"].get("with")
      other = get_tense(other_key)
      return {
          "current": tense["name"],
          "other": other["name"] if other else other_key,
          "points": tense["comparison"].get("points", []),
      }

  def generate_practice_set(self, tense_key, count=3):
      """Har bir mashq uchun kamida 3 ta avtomatik vazifa."""
      tense = get_tense(tense_key)
      if not tense:
          return []

      name = tense["name"]
      pool = []

      example = self._best_example(tense)
      if "example" in example.lower() and tense_key not in (
          "present_simple", "present_continuous"
      ):
          example = self._fallback_example(tense_key, tense)
      wrong_options = self._distractor_tenses(tense_key, name)

      pool.append({
          "type": "recognize",
          "level": 1,
          "label": "Zamonni aniqlang",
          "question": (
              f"Qaysi zamon ushbu gapga mos?\n"
              f"\"{example}\""
          ),
          "answer": name,
          "skill": "recognition",
      })

      complete = self._complete_exercise(tense_key, tense)
      if complete:
          pool.append({
              "type": "complete",
              "level": 2,
              "label": "Bo'sh joyni to'ldiring",
              "question": complete["question"],
              "answer": complete["answer"],
              "skill": "formula",
          })

      transform = self._transform_exercise(tense)
      if transform:
          pool.append({
              "type": "transform",
              "level": 3,
              "label": "Gapni o'zgartiring",
              "question": transform["question"],
              "answer": transform["answer"],
              "skill": "transformation",
          })

      mistake = self._mistake_exercise(tense)
      if mistake:
          pool.append({
              "type": "fix",
              "level": 3,
              "label": "Xatoni tuzating",
              "question": mistake["question"],
              "answer": mistake["answer"],
              "skill": "negative",
          })

      formula_q = self._formula_exercise(tense)
      if formula_q:
          pool.append({
              "type": "formula",
              "level": 2,
              "label": "Formula",
              "question": formula_q["question"],
              "answer": formula_q["answer"],
              "skill": "formula",
          })

      translate = self._translate_exercise(tense_key, tense)
      if translate:
          pool.append({
              "type": "translate",
              "level": 4,
              "label": "Tarjima qiling",
              "question": translate["question"],
              "answer": translate["answer"],
              "skill": "translation",
          })

      create = {
          "type": "create",
          "level": 5,
          "label": "Gap tuzing",
          "question": (
              f"{name} da o'z gapingizni tuzing "
              f"(kamida 5 so'z)."
          ),
          "answer": "",
          "skill": "creation",
      }
      pool.append(create)

      random.shuffle(pool)
      selected = pool[:max(count, 3)]
      if len(selected) < count:
          selected = (pool * 2)[:count]
      return selected

  def _best_example(self, tense):
      for source in (
          tense.get("examples", []),
          tense.get("affirmative", {}).get("examples", []),
          tense.get("question", {}).get("examples", []),
      ):
          for item in source:
              text = str(item).strip()
              if text and "example sentence" not in text.lower():
                  if "usage example" not in text.lower():
                      return text

      for usage in tense.get("usage", []):
          examples = usage.get("examples", [])
          if examples:
              return examples[0]

      transforms = tense.get("transformations", [])
      if transforms:
          return transforms[0].get("from", tense["name"])

      return f"I study English. ({tense['name']})"

  def _fallback_example(self, tense_key, tense):
      fallbacks = {
          "past_continuous": "She was studying at 8 pm.",
          "past_simple": "He went to school yesterday.",
          "past_perfect": "I had finished my work before he came.",
          "past_perfect_continuous": "They had been waiting for an hour.",
          "present_perfect": "I have lived here for five years.",
          "present_perfect_continuous": "She has been working all day.",
          "future_simple": "We will visit London next year.",
          "future_continuous": "This time tomorrow, I will be flying.",
          "future_perfect": "By 2030, I will have graduated.",
          "future_perfect_continuous": "By June, I will have been studying for 2 years.",
      }
      return fallbacks.get(
          tense_key,
          f"Example sentence for {tense['name']}.",
      )

  def _distractor_tenses(self, tense_key, correct_name):
      group = get_tense(tense_key).get("group", "Present")
      others = [
          get_tense(k)["name"]
          for k in TENSE_ORDER
          if k != tense_key and get_tense(k)
      ]
      random.shuffle(others)
      options = [correct_name] + others[:3]
      random.shuffle(options)
      return options

  def _complete_exercise(self, tense_key, tense):
      bank = {
          "present_simple": (
              "She ___ (work) every day.",
              "works",
          ),
          "present_continuous": (
              "They ___ (play) football now.",
              "are playing",
          ),
          "past_simple": (
              "Yesterday I ___ (go) to school.",
              "went",
          ),
          "past_continuous": (
              "At 8 pm, she ___ (study).",
              "was studying",
          ),
          "present_perfect": (
              "I ___ (finish) my homework.",
              "have finished",
          ),
          "future_simple": (
              "We ___ (visit) London next year.",
              "will visit",
          ),
      }
      if tense_key in bank:
          q, a = bank[tense_key]
          return {"question": q, "answer": a}

      formula = tense.get("formula", {}).get("affirmative", "")
      return {
          "question": (
              f"Formula bo'yicha bo'sh joyni to'ldiring:\n"
              f"{formula}\n"
              f"She ___ every day."
          ),
          "answer": "works",
      }

  def _transform_exercise(self, tense):
      transforms = tense.get("transformations", [])
      if transforms:
          item = transforms[0]
          return {
              "question": (
                  f"Negative shaklga o'zgartiring:\n"
                  f"\"{item['from']}\""
              ),
              "answer": item.get("to_negative", ""),
          }
      return None

  def _mistake_exercise(self, tense):
      mistakes = tense.get("common_mistakes", [])
      if mistakes:
          m = mistakes[0]
          return {
              "question": (
                  f"Xatoni tuzating:\n\"{m['wrong']}\""
              ),
              "answer": m["correct"],
          }
      return None

  def _formula_exercise(self, tense):
      negative = tense.get("formula", {}).get("negative", "")
      if not negative:
          return None
      return {
          "question": (
              f"{tense['name']} ning NEGATIVE formulasi qanday?"
          ),
          "answer": negative,
      }

  def _translate_exercise(self, tense_key, tense):
      bank = {
          "present_simple": (
              "Men har kuni ingliz tilini o'rganaman.",
              "I study English every day.",
          ),
          "present_continuous": (
              "Men hozir ishlayapman.",
              "I am working now.",
          ),
          "past_simple": (
              "Kecha u maktabga bordi.",
              "He went to school yesterday.",
          ),
          "future_simple": (
              "Biz ertaga kelamiz.",
              "We will come tomorrow.",
          ),
      }
      if tense_key in bank:
          q, a = bank[tense_key]
          return {"question": q, "answer": a}
      return None

  def generate_practice(self, tense_key, level=1):
      """Eski API — bitta vazifa."""
      exercises = self.generate_practice_set(tense_key, count=1)
      return exercises[:1] if exercises else []

  def check_answer(self, tense_key, exercise, user_answer):
      user_answer = (user_answer or "").strip()
      correct = str(exercise.get("answer", "")).strip()
      skill = exercise.get("skill", "formula")

      if exercise.get("type") == "transform":
          expected = str(exercise.get("answer", "")).strip()
          if expected:
              is_ok = (
                  user_answer.lower() == expected.lower()
                  or expected.lower() in user_answer.lower()
              )
              return {
                  "correct": is_ok,
                  "feedback": (
                      "✅ To'g'ri!" if is_ok
                      else f"❌ To'g'ri javob: {expected}"
                  ),
                  "skill": skill,
              }
          return {
              "correct": True,
              "feedback": "Transform mashq tekshirildi.",
              "skill": skill,
          }

      if exercise.get("type") == "formula":
          expected = str(exercise.get("answer", "")).strip().lower()
          given = user_answer.lower().replace(" ", "")
          expected_cmp = expected.replace(" ", "")
          is_ok = (
              given == expected_cmp
              or expected in user_answer.lower()
          )
          return {
              "correct": is_ok,
              "feedback": (
                  "✅ To'g'ri!" if is_ok
                  else f"❌ To'g'ri formula: {exercise.get('answer')}"
              ),
              "skill": skill,
          }

      if exercise.get("type") == "create":
          if self.ai and hasattr(self.ai, "check_tense_sentence"):
              return self.ai.check_tense_sentence(
                  tense_key, user_answer
              )
          return {
              "correct": len(user_answer.split()) >= 5,
              "feedback": (
                  "Yaxshi! Gap tuzildi."
                  if len(user_answer.split()) >= 5
                  else "Kamida 5 so'z yozing."
              ),
              "skill": skill,
          }

      is_correct = (
          user_answer.lower() == correct.lower()
          or user_answer.lower() in correct.lower()
      )
      feedback = "✅ To'g'ri!" if is_correct else (
          f"❌ To'g'ri javob: {correct}"
      )
      return {"correct": is_correct, "feedback": feedback, "skill": skill}

  def record_practice(self, tense_key, level, result):
      skill = result.get("skill", "formula")
      correct = 1 if result.get("correct") else 0
      self.db.log_tense_practice(
          tense_key, level, skill, correct, 1,
          result.get("feedback", ""),
      )
      return self.update_mastery(tense_key)

  def update_mastery(self, tense_key):
      logs = self.db.get_tense_practice_summary(tense_key)
      breakdown = {}
      for area in self.SKILL_AREAS:
          stats = logs.get(area, {"correct": 0, "total": 0})
          total = stats["total"]
          if total > 0:
              breakdown[area] = round(
                  stats["correct"] / total * 100, 1
              )
          else:
              breakdown[area] = 0

      if breakdown:
          pct = round(sum(breakdown.values()) / len(breakdown), 1)
      else:
          pct = 0

      weak = sorted(breakdown, key=breakdown.get)[:2]
      feedback_parts = []
      for w in weak:
          if breakdown[w] < 70:
              feedback_parts.append(
                  f"{w.replace('_', ' ').title()} zaif"
              )

      feedback = (
          f"{get_tense(tense_key)['name']}: {pct}% — "
          f"{get_mastery_label(pct)}. "
          + (". ".join(feedback_parts) if feedback_parts else "Yaxshi!")
      )

      self.db.save_tense_mastery(tense_key, pct, breakdown, feedback)
      return {
          "pct": pct,
          "label": get_mastery_label(pct),
          "breakdown": breakdown,
          "feedback": feedback,
      }

  def get_weakest_tenses(self, limit=3):
      all_m = self.db.get_all_tense_mastery()
      sorted_m = sorted(all_m, key=lambda x: x.get("mastery_pct", 0))
      return sorted_m[:limit]
