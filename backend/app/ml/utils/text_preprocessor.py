"""Resume text cleaning, normalization, and section detection."""

import re
from typing import Optional


class TextPreprocessor:
    """Clean and normalize resume text for ML processing."""

    SECTION_HEADERS = [
        "experience", "education", "skills", "projects", "certifications",
        "summary", "objective", "work history", "employment", "achievements",
        "awards", "publications", "languages", "interests", "references",
        "technical skills", "professional experience", "work experience",
        "internships", "volunteer", "extracurricular",
    ]

    @staticmethod
    def clean_text(text: str) -> str:
        if not text:
            return ""
        text = re.sub(r"[^\x00-\x7F]+", " ", text)
        text = re.sub(r"<[^>]+>", " ", text)
        text = re.sub(r"\s+", " ", text)
        text = text.strip()
        return text

    @staticmethod
    def normalize(text: str) -> str:
        if not text:
            return ""
        text = TextPreprocessor.clean_text(text)
        text = text.lower()
        return text

    @staticmethod
    def extract_sections(text: str) -> dict[str, str]:
        if not text:
            return {}
        lines = text.split("\n")
        sections: dict[str, str] = {}
        current_section: Optional[str] = None
        current_content: list[str] = []

        section_pattern = re.compile(
            r"^[" + r"\s*\-_*=#>.|".join([]) + r"]*"
            r"(?:"
            + "|".join(re.escape(h) for h in TextPreprocessor.SECTION_HEADERS)
            + r")"
            r"[" + r"\s*\-_*=#>.|".join([]) + r"]*$",
            re.IGNORECASE,
        )

        for line in lines:
            stripped = line.strip()
            if not stripped:
                continue

            is_header = False
            for header in TextPreprocessor.SECTION_HEADERS:
                clean_stripped = re.sub(r"[\s\-_*=#>.|:]+", "", stripped).lower()
                clean_header = re.sub(r"[\s\-_*=#>.|:]+", "", header).lower()
                if clean_stripped == clean_header or clean_stripped.startswith(clean_header):
                    is_header = True
                    break

            if not is_header:
                is_header = bool(section_pattern.match(stripped))

            if is_header:
                if current_section:
                    sections[current_section] = " ".join(current_content)
                header_key = stripped.lower().rstrip(":").strip()
                for h in TextPreprocessor.SECTION_HEADERS:
                    if h in header_key:
                        header_key = h
                        break
                current_section = header_key
                current_content = []
            else:
                current_content.append(stripped)

        if current_section:
            sections[current_section] = " ".join(current_content)

        return sections

    @staticmethod
    def word_count(text: str) -> int:
        if not text:
            return 0
        return len(re.findall(r"[a-zA-Z0-9+#]+", text))

    @staticmethod
    def sentence_count(text: str) -> int:
        if not text:
            return 0
        return max(1, len(re.split(r"[.!?]+", text.strip())))

    @staticmethod
    def has_sections(text: str) -> dict[str, bool]:
        sections = TextPreprocessor.extract_sections(text)
        return {h: h in sections for h in TextPreprocessor.SECTION_HEADERS[:10]}

    @staticmethod
    def section_completeness(text: str) -> float:
        key_sections = ["experience", "education", "skills", "projects"]
        found = TextPreprocessor.extract_sections(text)
        present = sum(1 for s in key_sections if s in found)
        return present / len(key_sections) if key_sections else 0.0
