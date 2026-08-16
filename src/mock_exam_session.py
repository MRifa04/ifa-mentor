"""Mock imtihon sessiyasi — skill bo'ylab ketma-ket o'tish."""



from src.mock_validation import (

    exam_pdf,

    validate_for_skill,

    validate_mock_materials,

)

from src.telegram_grouping import extract_day_from_set_title



SKILL_PAGES = ["Listening", "Reading", "Writing", "Speaking"]





class MockExamSession:

    def __init__(self, db, mode="full", skill=None, set_id=None):

        self.db = db

        self.mode = mode

        self.results = {}

        self.current_index = 0

        self.mock_set = None

        self.materials = []

        self.validation = None



        if mode == "single" and skill:

            self.skills = [skill.title()]

        else:

            self.skills = SKILL_PAGES.copy()



        self._load_mock_set(set_id)



    def _load_mock_set(self, set_id=None):

        if set_id:

            materials = self.db.get_materials_by_set_id(set_id)

            if materials:

                result = self._validate_materials(materials)

                if result.ok:

                    self.materials = materials

                    self.mock_set = self._set_info_from_materials(materials)

                    self.validation = result

                return



        exams = self.db.get_mock_exams()

        preferred_channels = (

            "Multilevelzone Mock",

            "Multilevel Halikulov",

        )



        def exam_score(exam):

            status = exam.get("status", "")

            status_score = {

                "auto_attached": 3,

                "confirmed": 3,

                "review": 1,

            }.get(status, 0)

            listening = exam.get("listening_count", 0) or 0

            reading = exam.get("reading_count", 0) or 0

            channel_bonus = 0

            for idx, name in enumerate(preferred_channels):

                if exam.get("channel_name") == name:

                    channel_bonus = 10 - idx

                    break

            return (

                channel_bonus,

                status_score,

                min(listening, 6),

                reading,

                exam.get("day_number", 0) or 0,

            )



        ranked = sorted(exams, key=exam_score, reverse=True)

        for exam in ranked:

            materials = self.db.get_materials_by_set_id(exam.get("set_id", ""))

            if not materials:

                continue

            if exam.get("status") not in (

                "auto_attached", "confirmed", "review"

            ):

                continue

            result = self._validate_materials(materials)

            if not result.ok:

                continue

            self.materials = materials

            self.mock_set = exam

            self.validation = result

            return



    def _validate_materials(self, materials):

        if self.mode == "single" and self.skills:

            return validate_for_skill(materials, self.skills[0])

        return validate_mock_materials(materials)



    def _set_info_from_materials(self, materials):

        first = materials[0]

        return {

            "set_id": first.get("set_id", ""),

            "set_title": first.get("set_title", "Mock"),

            "day_number": extract_day_from_set_title(

                first.get("set_title", "")

            ),

            "channel_name": first.get("source_channel", ""),

        }



    @property

    def is_ready(self) -> bool:

        if not self.materials:

            return False

        result = self._validate_materials(self.materials)

        self.validation = result

        return result.ok



    @property

    def title(self) -> str:

        if self.mock_set:

            return self.mock_set.get("set_title", "Mock Imtihon")

        return "Mock Imtihon"



    def current_skill(self) -> str:

        if self.current_index >= len(self.skills):

            return ""

        return self.skills[self.current_index]



    def is_complete(self) -> bool:

        return self.current_index >= len(self.skills)



    def progress_pct(self) -> int:

        if not self.skills:

            return 100

        return int((self.current_index / len(self.skills)) * 100)



    def complete_skill(self, skill: str, score: int, details=None):

        details = details or {}

        max_score = details.get("max_score", 75)

        self.results[skill] = {

            "score": score,

            "max_score": max_score,

            "details": details,

        }

        self.current_index += 1



    def listening_audios(self):

        items = [

            m for m in self.materials

            if m.get("file_type") == "audio"

        ]

        items.sort(key=lambda m: m.get("part_order") or 0)

        return items



    def exam_pdf_material(self):

        return exam_pdf(self.materials)



    def reading_pdf(self):

        return self.exam_pdf_material()



    def build_task(self) -> dict:

        skill = self.current_skill()

        pdf = self.exam_pdf_material()

        task = {

            "type": "mock_exam",

            "skill": skill,

            "mock_title": self.title,

            "set_id": (self.mock_set or {}).get("set_id", ""),

            "step": self.current_index + 1,

            "total_steps": len(self.skills),

            "pdf_material": pdf,

        }

        if skill == "Listening":

            task["audio_files"] = self.listening_audios()

            task["listening_parts"] = [

                a.get("part_order")

                for a in task["audio_files"]

                if a.get("part_order")

            ]

        return task

