import logging
import re
from dataclasses import dataclass
from pathlib import Path

from pypdf import PdfReader

logger = logging.getLogger("student_support_prospectus")


@dataclass(frozen=True)
class ProspectusMatch:
    page: int
    text: str
    score: int


class ProspectusRetriever:
    """Simple local retriever for the UDSM undergraduate prospectus PDF."""

    def __init__(self, pdf_path: str, index_path: str | None = None, max_pages: int = 3) -> None:
        self.pdf_path = Path(pdf_path)
        self.index_path = Path(index_path) if index_path else None
        self.max_pages = max_pages
        self._pages: list[tuple[int, str]] | None = None

    def search(self, question: str) -> list[ProspectusMatch]:
        terms = self._terms(question)
        if not terms:
            if self._is_general_udsm_question(question):
                return [
                    ProspectusMatch(page=page, text=text[:900].strip(), score=1)
                    for page, text in self._load_pages()[: self.max_pages]
                ]
            return []

        matches: list[ProspectusMatch] = []
        for page_number, text in self._load_pages():
            lowered = text.lower()
            score = sum(lowered.count(term) for term in terms)
            score += self._phrase_boost(lowered, question)
            if score:
                matches.append(
                    ProspectusMatch(
                        page=page_number,
                        text=self._trim(text, terms),
                        score=score,
                    )
                )

        matches.sort(key=lambda match: match.score, reverse=True)
        if self._is_general_admission_question(question):
            return matches[:1]
        return matches[: self.max_pages]

    def _phrase_boost(self, lowered_text: str, question: str) -> int:
        lowered_question = question.lower()
        phrases = {
            "admission": [
                "admission regulations",
                "admission requirements",
                "minimum entry qualifications",
                "entry requirements",
                "admission criteria",
            ],
            "hostel": ["accommodation", "hostel", "residence"],
            "fee": ["fees", "tuition", "requisite university fees"],
            "registration": ["registration", "register", "registered"],
        }
        score = 0
        for trigger, boosted_phrases in phrases.items():
            if trigger in lowered_question:
                score += sum(20 for phrase in boosted_phrases if phrase in lowered_text)
        return score

    def _load_pages(self) -> list[tuple[int, str]]:
        if self._pages is not None:
            return self._pages

        if self.index_path and self.index_path.exists():
            self._pages = self._load_index()
            logger.info("Loaded %s prospectus pages from %s", len(self._pages), self.index_path)
            return self._pages

        if not self.pdf_path.exists():
            logger.warning("Prospectus PDF not found: %s", self.pdf_path)
            self._pages = []
            return self._pages

        reader = PdfReader(str(self.pdf_path))
        pages: list[tuple[int, str]] = []
        for index, page in enumerate(reader.pages, start=1):
            text = " ".join((page.extract_text() or "").split())
            if text:
                pages.append((index, text))

        logger.info("Loaded %s prospectus pages from %s", len(pages), self.pdf_path)
        self._pages = pages
        return pages

    def _load_index(self) -> list[tuple[int, str]]:
        content = self.index_path.read_text(encoding="utf-8")
        pages: list[tuple[int, str]] = []
        for section in content.split("--- Page "):
            if not section.strip():
                continue
            marker, _, text = section.partition("---")
            try:
                page_number = int(marker.strip())
            except ValueError:
                continue
            cleaned = " ".join(text.split())
            if cleaned:
                pages.append((page_number, cleaned))
        return pages

    def _terms(self, question: str) -> list[str]:
        words = re.findall(r"[a-z0-9]+", question.lower())
        stopwords = {
            "about",
            "and",
            "are",
            "dar",
            "does",
            "for",
            "from",
            "how",
            "is",
            "it",
            "me",
            "of",
            "salaam",
            "tell",
            "the",
            "to",
            "udsm",
            "university",
            "what",
            "where",
            "which",
        }
        return [word for word in words if len(word) > 2 and word not in stopwords]

    def _is_general_udsm_question(self, question: str) -> bool:
        lowered = question.lower()
        return "udsm" in lowered or "university of dar es salaam" in lowered

    def _is_general_admission_question(self, question: str) -> bool:
        lowered = question.lower()
        return "admission" in lowered and self._is_general_udsm_question(question)

    def _trim(self, text: str, terms: list[str], size: int = 900) -> str:
        lowered = text.lower()
        positions = [lowered.find(term) for term in terms if lowered.find(term) >= 0]
        if not positions:
            return text[:size]

        midpoint = min(positions)
        start = max(0, midpoint - size // 3)
        end = min(len(text), start + size)
        return text[start:end].strip()
