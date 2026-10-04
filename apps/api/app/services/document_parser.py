import io
import json
import re
from typing import Any

import httpx
from pypdf import PdfReader

from app.core.config import get_settings
from app.schemas.interviewers import ParsedProfileDocumentResponse


class DocumentParserService:
    @staticmethod
    def extract_text(file_bytes: bytes, filename: str) -> str:
        """Extracts text from PDF bytes or plain text bytes."""
        if filename.lower().endswith(".pdf") or file_bytes.startswith(b"%PDF"):
            try:
                reader = PdfReader(io.BytesIO(file_bytes))
                extracted = [page.extract_text() or "" for page in reader.pages]
                full_text = "\n".join(extracted).strip()
                if full_text:
                    return full_text
            except Exception:
                pass
        try:
            return file_bytes.decode("utf-8", errors="replace").strip()
        except Exception:
            return ""

    @classmethod
    async def parse_profile_document(
        cls, file_bytes: bytes, filename: str
    ) -> ParsedProfileDocumentResponse:
        text = cls.extract_text(file_bytes, filename)
        if not text:
            return ParsedProfileDocumentResponse(raw_preview="Could not extract text from document.")

        settings = get_settings()
        if settings.gemini_api_key:
            parsed = await cls._parse_with_gemini(text, settings.gemini_api_key)
            if parsed:
                return parsed

        return cls._fallback_heuristic_parse(text)

    @classmethod
    async def _parse_with_gemini(
        cls, text: str, api_key: str
    ) -> ParsedProfileDocumentResponse | None:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
        prompt = (
            "You are an expert technical resume & LinkedIn profile parser for an engineering mock interview platform.\n"
            "Analyze the provided text from a LinkedIn profile / resume and return JSON matching this schema:\n"
            "{\n"
            '  "title": string (current or highest engineering title & company, e.g. "Staff Software Engineer @ Google"),\n'
            '  "bio": string (concise 2-3 sentence summary of engineering expertise, architecture/systems experience, and mentoring background),\n'
            '  "years_experience": integer (estimated total years of professional engineering experience),\n'
            '  "skills": list of strings (key technical domains e.g. ["System Design", "Distributed Systems", "Python", "Kubernetes"]),\n'
            '  "suggested_rate": integer (suggested hourly mock interview rate in INR e.g. 5000),\n'
            '  "suggested_currency": "INR"\n'
            "}\n\n"
            f"DOCUMENT TEXT:\n{text[:12000]}"
        )
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"responseMimeType": "application/json"},
        }
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                res = await client.post(url, json=payload)
                if res.status_code == 200:
                    data = res.json()
                    candidates = data.get("candidates", [])
                    if candidates:
                        raw_content = candidates[0]["content"]["parts"][0]["text"]
                        parsed_json: dict[str, Any] = json.loads(raw_content)
                        return ParsedProfileDocumentResponse(
                            title=parsed_json.get("title"),
                            bio=parsed_json.get("bio"),
                            years_experience=parsed_json.get("years_experience"),
                            skills=parsed_json.get("skills", []),
                            suggested_rate_minor=int(parsed_json.get("suggested_rate", 5000)) * 100
                            if parsed_json.get("suggested_rate")
                            else 500000,
                            suggested_currency=parsed_json.get("suggested_currency", "INR"),
                            raw_preview=text[:500],
                        )
        except Exception:
            pass
        return None

    @classmethod
    def _fallback_heuristic_parse(cls, text: str) -> ParsedProfileDocumentResponse:
        lines = [line.strip() for line in text.split("\n") if line.strip()]

        # Heuristic 1: Extract Job Title
        title_candidates = [
            line
            for line in lines
            if any(
                kw in line.lower()
                for kw in [
                    "engineer",
                    "architect",
                    "developer",
                    "lead",
                    "manager",
                    "director",
                    "principal",
                    "staff",
                ]
            )
            and len(line) < 120
        ]
        title = title_candidates[0] if title_candidates else "Software Engineer"

        # Heuristic 2: Extract Years of Experience from dates (e.g. 2015 - 2024, or 2018 - Present)
        years_found = [int(y) for y in re.findall(r"\b(19\d\d|20\d\d)\b", text)]
        years_exp = 5
        if years_found:
            min_year = min(years_found)
            current_year = 2026
            calculated = current_year - min_year
            if 0 <= calculated <= 50:
                years_exp = calculated

        # Heuristic 3: Common Tech Skills
        known_skills = [
            "System Design",
            "Distributed Systems",
            "Python",
            "Go",
            "Golang",
            "Java",
            "TypeScript",
            "JavaScript",
            "React",
            "Kubernetes",
            "Docker",
            "AWS",
            "GCP",
            "PostgreSQL",
            "Redis",
            "Microservices",
            "Algorithms",
            "Data Structures",
            "Machine Learning",
            "C++",
            "Rust",
        ]
        skills_detected = [
            skill for skill in known_skills if re.search(r"\b" + re.escape(skill) + r"\b", text, re.IGNORECASE)
        ]

        # Heuristic 4: Summary / Bio
        summary_lines = lines[:4]
        bio = (
            " ".join(summary_lines)
            if summary_lines
            else f"Experienced {title} with {years_exp}+ years in software engineering and system architecture."
        )
        if len(bio) > 1000:
            bio = bio[:997] + "..."

        return ParsedProfileDocumentResponse(
            title=title,
            bio=bio,
            years_experience=years_exp,
            skills=skills_detected[:10],
            suggested_rate_minor=500000,
            suggested_currency="INR",
            raw_preview=text[:500],
        )
