"""12 ta ingliz zamonining universal ma'lumot strukturasi."""

PRONOUNS = ["I", "You", "We", "They", "He", "She", "It"]

MASTERY_LEVELS = [
    (0, 20, "Beginner"),
    (21, 40, "Recognition"),
    (41, 60, "Formation"),
    (61, 80, "Application"),
    (81, 90, "Fluency"),
    (91, 100, "Mastered"),
]


def _usage(title, rule_uz, examples, exception=None):
    item = {
        "title": title,
        "rule_uz": rule_uz,
        "examples": examples,
    }
    if exception:
        item["exception"] = exception
    return item


def _mistake(wrong, correct, reason_uz):
    return {
        "wrong": wrong,
        "correct": correct,
        "reason_uz": reason_uz,
    }


def _build_pronoun_rows(aux_map, verb_fn, note=""):
    rows = []
    for pronoun in PRONOUNS:
        aux = aux_map.get(pronoun, aux_map.get("default", ""))
        verb = verb_fn(pronoun)
        rows.append({
            "pronoun": pronoun,
            "auxiliary": aux,
            "verb": verb,
            "sentence": f"{pronoun} {aux} {verb}".replace("  ", " ").strip(),
        })
    if note:
        for row in rows:
            row["note"] = note
    return rows


TENSE_REGISTRY = {}


def _register(tense):
    TENSE_REGISTRY[tense["key"]] = tense


# ── PRESENT ──────────────────────────────────────────────────

_register({
    "key": "present_simple",
    "name": "Present Simple",
    "uzbek_name": "Hozirgi oddiy zamon",
    "group": "Present",
    "time": "Hozirgi vaqt, odat, doimiy holat, jadval",
    "meaning": "Odat, umumiy haqiqat, doimiy vaziyat va jadvaldagi voqealar.",
    "timeline": "●━━━━━━━●  (takrorlanuvchi / doimiy)",
    "formula": {
        "affirmative": "S + V1(s/es)",
        "negative": "S + do/does + not + V1",
        "question": "Do/Does + S + V1?",
        "wh_question": "WH + do/does + S + V1?",
    },
    "auxiliary": {
        "rule": "I/You/We/They → do | He/She/It → does",
        "forms": {"I": "do", "You": "do", "We": "do", "They": "do",
                  "He": "does", "She": "does", "It": "does"},
    },
    "verb_form": {
        "v1": "Asosiy fe'l (work, go, study)",
        "v2": "—",
        "v3": "—",
        "ving": "—",
        "rule_uz": "He/She/It bilan affirmative gapda V1 + s/es.",
    },
    "pronouns": _build_pronoun_rows(
        {"I": "", "You": "", "We": "", "They": "",
         "He": "", "She": "", "It": ""},
        lambda p: "work" if p in ("He", "She", "It") else "work",
    ),
    "affirmative": {
        "formula": "S + V1(s/es)",
        "examples": ["I work every day.", "He works in a bank."],
        "breakdown": ["I = Subject", "work = V1", "He = Subject", "works = V1 + s"],
    },
    "negative": {
        "formula": "S + do/does + not + V1",
        "examples": ["I do not work on Sundays.", "She does not like coffee."],
        "breakdown": ["Subject + Auxiliary + NOT + Verb"],
    },
    "question": {
        "formula": "Do/Does + S + V1?",
        "examples": ["Do you work here?", "Does he speak English?"],
        "breakdown": ["Auxiliary + Subject + V1?"],
    },
    "wh_question": {
        "formula": "WH + do/does + S + V1?",
        "examples": ["Where do you work?", "When does she study?"],
        "breakdown": ["WH word + Auxiliary + Subject + V1?"],
    },
    "usage": [
        _usage("Habit", "Har kuni takrorlanadigan odatlar.",
               ["I study English every day.", "She usually wakes up at 7."]),
        _usage("General truth", "Umumiy haqiqatlar.",
               ["Water boils at 100°C.", "The sun rises in the east."]),
        _usage("Permanent situation", "Uzoq davom etadigan holat.",
               ["She lives in Tashkent.", "They work at IFA."]),
        _usage("Timetable", "Jadvaldagi kelajak voqealar.",
               ["The train leaves at 8.", "School starts on Monday."]),
    ],
    "signal_words": [
        "always", "usually", "often", "sometimes", "rarely", "never",
        "every day", "every week", "on Mondays",
    ],
    "signal_note": (
        "Signal words faqat ipucu — har doim Present Simple "
        "demak emas. Kontekstni ham ko'ring."
    ),
    "examples": [
        "I drink tea every morning.",
        "He doesn't play football.",
        "Do they live here?",
        "What do you want?",
    ],
    "common_mistakes": [
        _mistake("Does he works?", "Does he work?",
                 "Savolda does bilan fe'l V1 shaklida qoladi."),
        _mistake("She don't like it.", "She doesn't like it.",
                 "He/She/It bilan does not ishlatiladi."),
    ],
    "comparison": {
        "with": "present_continuous",
        "points": [
            ("Vaqt", "Odat / doimiy", "Hozir davom etayotgan"),
            ("Formula", "S + V1", "S + am/is/are + V-ing"),
            ("Misol", "I work every day.", "I am working now."),
        ],
    },
    "transformations": [
        {"from": "He works here.", "to_negative": "He doesn't work here.",
         "to_question": "Does he work here?",
         "to_wh": "Where does he work?"},
    ],
    "important_rule": (
        "Does he work? ✅  |  Does he works? ❌ — "
        "Yordamchi fe'l zamon ma'nosini o'z zimmasiga oladi."
    ),
})

_register({
    "key": "present_continuous",
    "name": "Present Continuous",
    "uzbek_name": "Hozirgi davomiy zamon",
    "group": "Present",
    "time": "Hozir, hozirgi paytda davom etayotgan jarayon",
    "meaning": "Gap aytish vaqtida yoki yaqin atrofda davom etayotgan harakat.",
    "timeline": "●→→→→→●  (hozir davom etmoqda)",
    "formula": {
        "affirmative": "S + am/is/are + V-ing",
        "negative": "S + am/is/are + not + V-ing",
        "question": "Am/Is/Are + S + V-ing?",
        "wh_question": "WH + am/is/are + S + V-ing?",
    },
    "auxiliary": {
        "rule": "I → am | He/She/It → is | You/We/They → are",
        "forms": {"I": "am", "You": "are", "We": "are", "They": "are",
                  "He": "is", "She": "is", "It": "is"},
    },
    "verb_form": {
        "v1": "—", "v2": "—", "v3": "—",
        "ving": "work → working, study → studying",
        "rule_uz": "Asosiy fe'l -ing qo'shimchasi bilan ishlatiladi.",
    },
    "pronouns": _build_pronoun_rows(
        {"I": "am", "You": "are", "We": "are", "They": "are",
         "He": "is", "She": "is", "It": "is"},
        lambda p: "working",
    ),
    "affirmative": {"formula": "S + am/is/are + V-ing",
                    "examples": ["I am studying now.", "She is reading a book."],
                    "breakdown": ["Subject + be + V-ing"]},
    "negative": {"formula": "S + am/is/are + not + V-ing",
                 "examples": ["I am not sleeping.", "They are not watching TV."],
                 "breakdown": ["Subject + be + not + V-ing"]},
    "question": {"formula": "Am/Is/Are + S + V-ing?",
                 "examples": ["Are you listening?", "Is he working?"],
                 "breakdown": ["Be + Subject + V-ing?"]},
    "wh_question": {"formula": "WH + am/is/are + S + V-ing?",
                    "examples": ["What are you doing?", "Where is she going?"],
                    "breakdown": ["WH + be + Subject + V-ing?"]},
    "usage": [
        _usage("Now", "Hozir bo'layotgan ish.",
               ["I am working now.", "Look! It is raining."]),
        _usage("Temporary", "Vaqtinchalik holat.",
               ["She is staying with her friend this week."]),
        _usage("Future arrangement", "Kelishilgan reja.",
               ["We are meeting tomorrow at 5."]),
    ],
    "signal_words": ["now", "at the moment", "currently", "right now", "today",
                     "this week", "look!", "listen!"],
    "signal_note": "Now ko'p hollarda Present Continuous, lekin har doim emas.",
    "examples": ["They are playing football.", "Is he coming?"],
    "common_mistakes": [
        _mistake("I am work now.", "I am working now.", "Be + V-ing kerak."),
        _mistake("She is knowing him.", "She knows him.",
                 "Know kabi state verb odatda continuous emas."),
    ],
    "comparison": {"with": "present_simple",
                   "points": [("Ma'no", "Odat", "Hozirgi jarayon"),
                              ("Misol", "I work.", "I am working.")]},
    "transformations": [
        {"from": "She is studying.", "to_negative": "She isn't studying.",
         "to_question": "Is she studying?", "to_wh": "What is she studying?"},
    ],
    "important_rule": "State verbs (know, like, want) odatda continuous emas.",
})

# Compact templates for remaining tenses
_REMAINING = [
    ("present_perfect", "Present Perfect", "Hozirgi tugallangan zamon",
     "Present", "O'tmishda boshlangan, hozirgi natijasi bor",
     "S + have/has + V3", "have/has", "V3",
     "already, yet, just, ever, never, since, for"),
    ("present_perfect_continuous", "Present Perfect Continuous",
     "Hozirgi tugallangan davomiy zamon", "Present",
     "O'tmishda boshlangan va hali ham davom etayotgan",
     "S + have/has been + V-ing", "have/has been", "V-ing",
     "for, since, all day, lately"),
    ("past_simple", "Past Simple", "O'tmish oddiy zamon", "Past",
     "O'tmishda tugallangan aniq voqea",
     "S + V2 / S + did + V1", "did", "V2 (positive), V1 (neg/q)",
     "yesterday, last week, ago, in 2020"),
    ("past_continuous", "Past Continuous", "O'tmish davomiy zamon", "Past",
     "O'tmishda ma'lum paytda davom etgan jarayon",
     "S + was/were + V-ing", "was/were", "V-ing",
     "while, when, at 8 o'clock yesterday"),
    ("past_perfect", "Past Perfect", "O'tmish tugallangan zamon", "Past",
     "Boshqa o'tmish voqeadan oldin bo'lgan",
     "S + had + V3", "had", "V3",
     "before, after, by the time, already"),
    ("past_perfect_continuous", "Past Perfect Continuous",
     "O'tmish tugallangan davomiy zamon", "Past",
     "O'tmishdagi nuqtagacha davom etgan jarayon",
     "S + had been + V-ing", "had been", "V-ing",
     "for, since, before"),
    ("future_simple", "Future Simple", "Kelasi oddiy zamon", "Future",
     "Kelajakdagi voqea, bashorat, qaror",
     "S + will + V1", "will", "V1",
     "tomorrow, next week, soon, in 2027"),
    ("future_continuous", "Future Continuous", "Kelasi davomiy zamon", "Future",
     "Kelajakda ma'lum paytda davom etadigan",
     "S + will be + V-ing", "will be", "V-ing",
     "this time tomorrow, at 5 pm tomorrow"),
    ("future_perfect", "Future Perfect", "Kelasi tugallangan zamon", "Future",
     "Kelajakdagi ma'lum paytgacha tugaydigan",
     "S + will have + V3", "will have", "V3",
     "by, by the time, before"),
    ("future_perfect_continuous", "Future Perfect Continuous",
     "Kelasi tugallangan davomiy zamon", "Future",
     "Kelajakdagi paytgacha davom etgan bo'ladi",
     "S + will have been + V-ing", "will have been", "V-ing",
     "for, by, by the time"),
]

for (key, name, uz, group, meaning, aff, aux, vform, signals) in _REMAINING:
    neg = aff.replace("S + ", "S + " + aux.split("/")[0].split()[0] + " not + ") if "will" in aux else f"S + {aux.split('/')[0] if '/' in aux else aux} + not + ..."
    if key == "past_simple":
        neg = "S + did not + V1"
        q = "Did + S + V1?"
        wh = "WH + did + S + V1?"
        aff_f = "S + V2 (positive) | S + did + V1 (neg/q)"
    elif "will" in aux:
        neg = f"S + {aux} + not + {vform}"
        q = f"Will + S + {vform}?"
        wh = f"WH + will + S + {vform}?"
        aff_f = aff
    elif "had" in aux:
        neg = f"S + {aux} + not + {vform}"
        q = f"Had + S + {vform}?"
        wh = f"WH + had + S + {vform}?"
        aff_f = aff
    elif "have" in aux:
        neg = f"S + have/has + not + {vform}"
        q = f"Have/Has + S + {vform}?"
        wh = f"WH + have/has + S + {vform}?"
        aff_f = aff
    else:
        neg = f"S + was/were + not + {vform}"
        q = f"Was/Were + S + {vform}?"
        wh = f"WH + was/were + S + {vform}?"
        aff_f = aff

    compare_key = {
        "present_perfect": "past_simple",
        "past_simple": "present_perfect",
        "past_continuous": "past_simple",
        "future_simple": "present_simple",
    }.get(key, "present_simple")

    _register({
        "key": key,
        "name": name,
        "uzbek_name": uz,
        "group": group,
        "time": meaning.split(".")[0] if "." in meaning else meaning,
        "meaning": meaning,
        "timeline": f"● {'━' * 8} ●",
        "formula": {
            "affirmative": aff_f if key == "past_simple" else aff,
            "negative": neg,
            "question": q,
            "wh_question": wh,
        },
        "auxiliary": {"rule": aux, "forms": {}},
        "verb_form": {
            "v1": "Asosiy fe'l" if vform == "V1" else "—",
            "v2": "O'tmish shakl" if vform == "V2 (positive), V1 (neg/q)" else "—",
            "v3": "Uchinchi shakl" if vform == "V3" else "—",
            "ving": "-ing shakl" if "ing" in vform.lower() else "—",
            "rule_uz": f"Bu zamonda asosiy fe'l shakli: {vform}",
        },
        "pronouns": [],
        "affirmative": {"formula": aff_f if key == "past_simple" else aff,
                        "examples": [f"Example for {name}."],
                        "breakdown": ["Subject + Auxiliary + Verb"]},
        "negative": {"formula": neg,
                     "examples": [f"Negative example for {name}."],
                     "breakdown": ["Subject + Auxiliary + NOT + Verb"]},
        "question": {"formula": q, "examples": [f"Question for {name}?"],
                     "breakdown": ["Auxiliary + Subject + Verb?"]},
        "wh_question": {"formula": wh,
                        "examples": [f"Where ... {name.lower()}?"],
                        "breakdown": ["WH + Auxiliary + Subject + Verb?"]},
        "usage": [
            _usage("Asosiy holat", meaning,
                   [f"Usage example 1 — {name}.",
                    f"Usage example 2 — {name}."]),
        ],
        "signal_words": signals.split(", "),
        "signal_note": "Signal words faqat ipucu — kontekstni ham tekshiring.",
        "examples": [f"{name} example sentence."],
        "common_mistakes": [
            _mistake(f"Wrong {name}", f"Correct {name}",
                     f"{name} uchun formula va yordamchi fe'lni tekshiring."),
        ],
        "comparison": {"with": compare_key,
                       "points": [("Formula", aff, "See related tense")]},
        "transformations": [],
        "important_rule": (
            f"{name}: yordamchi fe'l zamon ma'nosini o'z zimmasiga oladi."
        ),
    })


TENSE_EXTRAS = {
    "past_simple": {
        "examples": [
            "He went to school yesterday.",
            "They didn't watch TV last night.",
            "Did you finish your homework?",
        ],
        "affirmative": {
            "formula": "S + V2",
            "examples": ["I visited Samarkand last year."],
            "breakdown": ["Subject + V2"],
        },
        "common_mistakes": [
            _mistake("I didn't went.", "I didn't go.",
                     "Did o'tgan zamon ma'nosini o'z zimmasiga oladi, fe'l V1."),
            _mistake("Did you went?", "Did you go?",
                     "Savolda did bilan V1 ishlatiladi."),
        ],
        "transformations": [{
            "from": "She studied English.",
            "to_negative": "She didn't study English.",
            "to_question": "Did she study English?",
            "to_wh": "What did she study?",
        }],
        "usage": [
            _usage("Finished past action", "O'tmishda tugallangan ish.",
                   ["I met him yesterday.", "She left at 6 pm."]),
            _usage("Past habit", "O'tmishdagi odat.",
                   ["We always played outside as children."]),
        ],
    },
    "past_continuous": {
        "examples": [
            "She was studying at 8 pm.",
            "They weren't watching TV.",
            "Was he sleeping?",
        ],
        "common_mistakes": [
            _mistake("She was study.", "She was studying.",
                     "Was/were + V-ing kerak."),
        ],
        "transformations": [{
            "from": "He was working.",
            "to_negative": "He wasn't working.",
            "to_question": "Was he working?",
            "to_wh": "What was he doing?",
        }],
        "usage": [
            _usage("Past moment", "O'tmishdagi ma'lum paytda davom etgan.",
                   ["At 7 pm, I was cooking dinner."]),
        ],
    },
    "present_perfect": {
        "examples": [
            "I have lived here for five years.",
            "She has never been to London.",
            "Have you finished yet?",
        ],
        "transformations": [{
            "from": "I have seen that film.",
            "to_negative": "I haven't seen that film.",
            "to_question": "Have you seen that film?",
            "to_wh": "What have you seen?",
        }],
        "usage": [
            _usage("Life experience", "Hayot tajribasi.",
                   ["I have visited Paris twice."]),
            _usage("Unfinished time", "Hali tugamagan davr.",
                   ["I have read three books this month."]),
        ],
    },
    "present_perfect_continuous": {
        "examples": [
            "She has been working all day.",
            "How long have you been waiting?",
        ],
        "usage": [
            _usage("Duration", "Qancha vaqtdan beri davom etayotgan.",
                   ["I have been studying for two hours."]),
        ],
    },
    "past_perfect": {
        "examples": [
            "I had finished before he came.",
            "Had they left when you arrived?",
        ],
        "usage": [
            _usage("Earlier past", "Boshqa o'tmish voqeadan oldin.",
                   ["She had already eaten when I called."]),
        ],
    },
    "past_perfect_continuous": {
        "examples": [
            "They had been waiting for an hour.",
        ],
        "usage": [
            _usage("Duration before past", "O'tmishdagi nuqtagacha davom etgan.",
                   ["He had been driving for six hours."]),
        ],
    },
    "future_simple": {
        "examples": [
            "We will visit London next year.",
            "She won't be late.",
            "Will you help me?",
        ],
        "transformations": [{
            "from": "I will call you.",
            "to_negative": "I won't call you.",
            "to_question": "Will you call me?",
            "to_wh": "When will you call me?",
        }],
        "usage": [
            _usage("Prediction", "Bashorat.",
                   ["It will rain tomorrow."]),
            _usage("Decision", "Tezda qilingan qaror.",
                   ["I'll help you with that."]),
        ],
    },
    "future_continuous": {
        "examples": [
            "This time tomorrow, I will be flying to Dubai.",
        ],
        "usage": [
            _usage("Future in progress", "Kelajakdagi davom etayotgan jarayon.",
                   ["At 8 pm, we will be having dinner."]),
        ],
    },
    "future_perfect": {
        "examples": [
            "By 2030, I will have graduated.",
        ],
        "usage": [
            _usage("Completed before future point",
                   "Kelajakdagi paytgacha tugaydigan.",
                   ["By June, I will have finished the course."]),
        ],
    },
    "future_perfect_continuous": {
        "examples": [
            "By June, I will have been studying for 2 years.",
        ],
        "usage": [
            _usage("Duration until future",
                   "Kelajakdagi paytgacha davom etgan bo'ladi.",
                   ["By next month, she will have been working here for a year."]),
        ],
    },
}

for _key, _extra in TENSE_EXTRAS.items():
    if _key in TENSE_REGISTRY:
        TENSE_REGISTRY[_key].update(_extra)


TENSE_ORDER = [
    "present_simple", "present_continuous",
    "present_perfect", "present_perfect_continuous",
    "past_simple", "past_continuous",
    "past_perfect", "past_perfect_continuous",
    "future_simple", "future_continuous",
    "future_perfect", "future_perfect_continuous",
]


def get_all_tenses():
    return [TENSE_REGISTRY[k] for k in TENSE_ORDER if k in TENSE_REGISTRY]


def get_tense(key):
    return TENSE_REGISTRY.get(key)


def get_mastery_label(pct):
    for low, high, label in MASTERY_LEVELS:
        if low <= pct <= high:
            return label
    return "Beginner"
