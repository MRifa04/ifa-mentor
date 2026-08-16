"""Mock validatsiya va PDF ajratish testlari."""

import os
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.mock_pdf_text import (
    extract_listening_part_text,
    extract_reading_part_text,
    _paper_section,
)
from src.mock_validation import (
    ValidationResult,
    exam_pdf,
    validate_listening,
    validate_mock_materials,
    validate_for_skill,
)


SAMPLE_PDF_TEXT = """
PAPER 1 LISTENING
Part 1
Question 1
A) one
B) two

Part 2
Question 2
Choose answer

Part 3
Gap fill text

PAPER 2 READING
Part 1
Reading passage one

Part 2
Reading passage two

PAPER 3 WRITING
Write an essay about technology.

PAPER 4 SPEAKING
Part 1
Introduce yourself
"""


class PdfTextExtractionTests(unittest.TestCase):
    def test_listening_part_extraction(self):
        part1 = extract_listening_part_text(SAMPLE_PDF_TEXT, 1)
        self.assertIn("Question 1", part1)
        self.assertNotIn("PAPER 2", part1)

        part2 = extract_listening_part_text(SAMPLE_PDF_TEXT, 2)
        self.assertIn("Question 2", part2)

    def test_reading_part_extraction(self):
        part1 = extract_reading_part_text(SAMPLE_PDF_TEXT, 1)
        self.assertIn("Reading passage one", part1)
        self.assertNotIn("PAPER 3", part1)

    def test_paper_sections(self):
        writing = _paper_section(SAMPLE_PDF_TEXT, 3)
        self.assertIn("Write an essay", writing)
        speaking = _paper_section(SAMPLE_PDF_TEXT, 4)
        self.assertIn("Introduce yourself", speaking)


class MockValidationTests(unittest.TestCase):
    def _materials(self, tmpdir):
        pdf_path = os.path.join(tmpdir, "exam.pdf")
        with open(pdf_path, "w", encoding="utf-8") as handle:
            handle.write("pdf")

        audios = []
        for part in range(1, 7):
            audio_path = os.path.join(tmpdir, f"part_{part}.mp3")
            with open(audio_path, "wb") as handle:
                handle.write(b"audio")
            audios.append({
                "file_type": "audio",
                "file_path": audio_path,
                "part_order": part,
                "material_role": "listening",
            })

        return [
            {
                "file_type": "pdf",
                "file_path": pdf_path,
                "material_role": "reading",
                "title": "Day 1",
            },
            *audios,
        ]

    @patch("src.mock_validation.get_listening_part_from_pdf")
    @patch("src.mock_validation.get_reading_part_from_pdf")
    def test_validate_full_mock_ok(self, mock_reading, mock_listening):
        with tempfile.TemporaryDirectory() as tmpdir:
            materials = self._materials(tmpdir)
            mock_listening.side_effect = (
                lambda path, part: f"Listening Part {part} text"
            )
            mock_reading.side_effect = (
                lambda path, part: f"Reading Part {part} text"
            )

            result = validate_mock_materials(materials)
            self.assertIsInstance(result, ValidationResult)
            self.assertTrue(result.ok)
            self.assertGreaterEqual(result.score, 0.8)

    @patch("src.mock_validation.get_listening_part_from_pdf")
    def test_validate_listening_missing_audio_file(self, mock_listening):
        with tempfile.TemporaryDirectory() as tmpdir:
            materials = self._materials(tmpdir)
            materials[1]["file_path"] = os.path.join(
                tmpdir, "missing.mp3"
            )
            mock_listening.return_value = "Part text"

            result = validate_listening(materials)
            self.assertFalse(result.ok)
            self.assertTrue(any("Audio fayl" in issue for issue in result.issues))

    def test_exam_pdf_skips_answers(self):
        materials = [
            {
                "file_type": "pdf",
                "material_role": "answers",
                "file_path": "/a.pdf",
            },
            {
                "file_type": "pdf",
                "material_role": "reading",
                "file_path": "/exam.pdf",
            },
        ]
        pdf = exam_pdf(materials)
        self.assertEqual(pdf["file_path"], "/exam.pdf")

    @patch("src.mock_validation.get_listening_part_from_pdf")
    def test_validate_for_skill_listening(self, mock_listening):
        with tempfile.TemporaryDirectory() as tmpdir:
            materials = self._materials(tmpdir)[:3]
            mock_listening.return_value = "text"
            result = validate_for_skill(materials, "Listening")
            self.assertTrue(result.ok)


if __name__ == "__main__":
    unittest.main()
