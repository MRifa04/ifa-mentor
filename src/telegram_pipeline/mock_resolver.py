"""Mock imtihonlarni juftlash va ishonch darajasini hisoblash."""

from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from src.telegram_grouping import (
    make_mock_folder,
    make_mock_set_id,
    safe_set_slug,
)
from src.telegram_pipeline.file_classifier import (
    ROLE_ANSWERS,
    ROLE_LISTENING,
    ROLE_READING,
    ClassifiedMessage,
)

CONFIDENCE_AUTO = 0.75
PDF_AUDIO_GAP_SECONDS = 180


@dataclass
class MockBundle:
    """Bitta mock imtihon to'plami."""

    set_id: str
    set_title: str
    folder: str
    channel_name: str
    day_number: int = 0
    confidence: float = 0.0
    status: str = "review"
    listening: list[ClassifiedMessage] = field(default_factory=list)
    reading: list[ClassifiedMessage] = field(default_factory=list)
    answers: list[ClassifiedMessage] = field(default_factory=list)
    reasons: list[str] = field(default_factory=list)

    @property
    def all_items(self) -> list[ClassifiedMessage]:
        return self.reading + self.answers + self.listening

    @property
    def summary(self) -> str:
        return (
            f"Reading {len(self.reading)} | "
            f"Answers {len(self.answers)} | "
            f"Listening {len(self.listening)}"
        )


class MockResolver:
    """
    PDF (reading/javob) + audio album (listening) ni juftlaydi.
    Bir xil Day raqamli fayllar bitta to'plamga birlashtiriladi.
  """

    def resolve(
        self,
        items: list[ClassifiedMessage],
        channel_name: str,
    ) -> list[MockBundle]:
        pdfs = [i for i in items if i.role in (ROLE_READING, ROLE_ANSWERS)]
        audios = [i for i in items if i.role == ROLE_LISTENING]
        albums = self._group_audios(audios)
        used_albums: set[int] = set()
        bundles: list[MockBundle] = []

        by_day: dict[int, dict] = defaultdict(
            lambda: {"reading": [], "answers": []}
        )
        pdfs_no_day: list[ClassifiedMessage] = []

        for pdf in pdfs:
            if pdf.day_number:
                bucket = (
                    "answers" if pdf.role == ROLE_ANSWERS else "reading"
                )
                by_day[pdf.day_number][bucket].append(pdf)
            else:
                pdfs_no_day.append(pdf)

        for day in sorted(by_day.keys(), reverse=True):
            group = by_day[day]
            reading = self._pick_best_pdf(group["reading"])
            answers = self._pick_best_pdf(group["answers"])
            anchor = reading or answers
            if not anchor:
                continue

            album, gap = self._best_album(anchor, albums, used_albums)
            bundle = self._build_bundle(
                anchor,
                album,
                gap,
                channel_name,
                reading=reading,
                answers=answers,
            )
            bundles.append(bundle)
            if album is not None:
                used_albums.add(id(album))

        pdfs_no_day.sort(
            key=lambda p: p.raw.date or datetime.min,
            reverse=True,
        )
        for pdf in pdfs_no_day:
            album, gap = self._best_album(pdf, albums, used_albums)
            reading = [pdf] if pdf.role == ROLE_READING else []
            answers = [pdf] if pdf.role == ROLE_ANSWERS else []
            bundle = self._build_bundle(
                pdf,
                album,
                gap,
                channel_name,
                reading=reading[0] if reading else None,
                answers=answers[0] if answers else None,
            )
            bundles.append(bundle)
            if album is not None:
                used_albums.add(id(album))

        for album in albums:
            if id(album) in used_albums:
                continue
            day = album[0].day_number if album else 0
            merged = False
            if day:
                for bundle in bundles:
                    if (
                        bundle.day_number == day
                        and bundle.channel_name == channel_name
                    ):
                        bundle.listening.extend(album)
                        used_albums.add(id(album))
                        parts = [
                            a.part_order for a in album if a.part_order
                        ]
                        bundle.reasons.append(
                            f"Listening qo'shildi ({len(album)} audio)"
                        )
                        if len(bundle.listening) >= 4:
                            bundle.confidence = min(
                                bundle.confidence + 0.15, 1.0
                            )
                        merged = True
                        break
            if merged:
                continue
            bundles.append(
                self._build_listening_only(album, channel_name)
            )

        return bundles

    def _pick_best_pdf(
        self,
        pdfs: list[ClassifiedMessage],
    ) -> Optional[ClassifiedMessage]:
        if not pdfs:
            return None
        return max(pdfs, key=lambda p: (p.confidence, p.raw.message_id))

    def _group_audios(
        self,
        audios: list[ClassifiedMessage],
    ) -> list[list[ClassifiedMessage]]:
        by_group: dict = defaultdict(list)
        for audio in audios:
            gid = audio.raw.grouped_id or f"solo_{audio.raw.message_id}"
            by_group[gid].append(audio)

        albums = list(by_group.values())

        sorted_solo = [a for a in audios if not a.raw.grouped_id]
        sorted_solo.sort(key=lambda x: x.raw.date or datetime.min)
        if sorted_solo:
            current = [sorted_solo[0]]
            for item in sorted_solo[1:]:
                d0 = current[0].raw.date
                d1 = item.raw.date
                if (
                    d0 and d1
                    and abs((d1 - d0).total_seconds()) <= PDF_AUDIO_GAP_SECONDS
                ):
                    current.append(item)
                else:
                    if len(current) >= 2:
                        albums.append(current)
                    current = [item]
            if len(current) >= 2:
                albums.append(current)

        for album in albums:
            album.sort(key=lambda x: x.part_order or 999)
        return albums

    def _best_album(
        self,
        pdf: ClassifiedMessage,
        albums: list[list[ClassifiedMessage]],
        used: set,
    ):
        best = None
        best_gap = PDF_AUDIO_GAP_SECONDS + 1
        pdf_date = pdf.raw.date

        for album in albums:
            if id(album) in used:
                continue
            dates = [a.raw.date for a in album if a.raw.date]
            if not dates or not pdf_date:
                continue
            anchor = min(dates)
            gap = abs((pdf_date - anchor).total_seconds())
            if gap <= PDF_AUDIO_GAP_SECONDS and gap < best_gap:
                best_gap = gap
                best = album
        return best, best_gap

    def _score_bundle(
        self,
        pdf: ClassifiedMessage,
        album: Optional[list[ClassifiedMessage]],
        gap: float,
        has_answers: bool = False,
    ) -> tuple[float, list[str], str]:
        score = 0.0
        reasons = []

        if pdf.day_number:
            score += 0.35
            reasons.append(f"PDF Day {pdf.day_number}")
        elif pdf.test_number:
            score += 0.2
            reasons.append(f"Test {pdf.test_number}")

        if pdf.role == ROLE_READING:
            score += 0.15
            if pdf.includes_answers:
                reasons.append("PDF savol+javob")

        if has_answers:
            score += 0.05
            reasons.append("Alohida javoblar PDF")

        if album:
            parts = [a.part_order for a in album if a.part_order]
            album_len = len(album)
            if album_len >= 4:
                score += 0.25
                reasons.append(f"{album_len} ta listening audio")
            elif album_len >= 2:
                score += 0.15
                reasons.append(f"{album_len} ta audio (kam)")
            if parts and len(set(parts)) == len(parts):
                score += 0.1
                reasons.append("Part tartibi aniq")
            if gap <= PDF_AUDIO_GAP_SECONDS:
                score += 0.15
                reasons.append(f"Vaqt yaqin ({int(gap)}s)")
        else:
            reasons.append("Listening audio topilmadi")

        score = min(score, 1.0)
        status = "auto_attached" if score >= CONFIDENCE_AUTO else "review"
        return score, reasons, status

    def _build_bundle(
        self,
        anchor: ClassifiedMessage,
        album: Optional[list[ClassifiedMessage]],
        gap: float,
        channel_name: str,
        reading: Optional[ClassifiedMessage] = None,
        answers: Optional[ClassifiedMessage] = None,
    ) -> MockBundle:
        day = anchor.day_number
        if day:
            set_id = make_mock_set_id(channel_name, day)
            title = f"Mock Day {day}"
            folder = make_mock_folder(day)
        else:
            slug = safe_set_slug(channel_name)
            set_id = f"{slug}:exam_{anchor.raw.message_id}"
            title = f"Mock #{anchor.raw.message_id}"
            folder = make_mock_folder(0, anchor.raw.message_id)

        reading_item = reading or (
            anchor if anchor.role == ROLE_READING else None
        )
        answers_item = answers or (
            anchor if anchor.role == ROLE_ANSWERS else None
        )

        score, reasons, status = self._score_bundle(
            anchor,
            album,
            gap,
            has_answers=bool(answers_item),
        )

        return MockBundle(
            set_id=set_id,
            set_title=title,
            folder=folder,
            channel_name=channel_name,
            day_number=day,
            confidence=score,
            status=status,
            listening=album or [],
            reading=[reading_item] if reading_item else [],
            answers=[answers_item] if answers_item else [],
            reasons=reasons,
        )

    def _build_listening_only(
        self,
        album: list[ClassifiedMessage],
        channel_name: str,
    ) -> MockBundle:
        mid = album[0].raw.message_id
        day = album[0].day_number
        slug = safe_set_slug(channel_name)

        if day:
            set_id = f"{slug}:listening_day_{day}"
            title = f"Listening Day {day}"
            folder = make_mock_folder(day)
        else:
            set_id = f"{slug}:listening_{mid}"
            title = f"Listening #{mid}"
            folder = f"listening_{mid}"

        parts = [a.part_order for a in album if a.part_order]
        reasons = ["Faqat listening audio"]
        score = 0.45
        if len(album) >= 4:
            score += 0.2
            reasons.append(f"{len(album)} ta part")
        if parts:
            score += 0.1

        return MockBundle(
            set_id=set_id,
            set_title=title,
            folder=folder,
            channel_name=channel_name,
            day_number=day,
            confidence=min(score, 1.0),
            status="review",
            listening=album,
            reasons=reasons,
        )
