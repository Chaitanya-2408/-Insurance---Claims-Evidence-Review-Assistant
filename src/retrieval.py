import os
import re
from pathlib import Path

import numpy as np
from google import genai


POLICY_PATH = Path("data/policy/motor_policy.txt")
EMBEDDING_MODEL = "gemini-embedding-001"


class PolicyRetriever:
    """Retrieve relevant sections from the local motor insurance policy."""

    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")

        if not api_key:
            raise RuntimeError(
                "GEMINI_API_KEY environment variable is not set."
            )

        self.client = genai.Client(api_key=api_key)

        self.sections = self._load_policy()
        self.embeddings = None

    def _load_policy(self):
        """Load policy and convert numbered sections into structured data."""

        if not POLICY_PATH.exists():
            raise FileNotFoundError(
                f"Policy file not found: {POLICY_PATH}"
            )

        text = POLICY_PATH.read_text(
            encoding="utf-8"
        )

        pattern = r"(?=^\d+\.\s+[A-Z][^\n]*)"

        raw_sections = re.split(
            pattern,
            text,
            flags=re.MULTILINE
        )

        sections = []

        for section in raw_sections:
            section = section.strip()

            match = re.match(
                r"^(\d+)\.\s+([^\n]+)",
                section
            )

            if not match:
                continue

            section_id = match.group(1)
            title = match.group(2).strip()

            sections.append(
                {
                    "section_id": section_id,
                    "title": title,
                    "text": section
                }
            )

        return sections

    def _embed(self, text):
        """Generate an embedding using Gemini."""

        response = self.client.models.embed_content(
            model=EMBEDDING_MODEL,
            contents=text
        )

        return np.array(
            response.embeddings[0].values,
            dtype=np.float32
        )

    def build_index(self):
        """Generate embeddings for all policy sections."""

        self.embeddings = np.vstack(
            [
                self._embed(section["text"])
                for section in self.sections
            ]
        )

    @staticmethod
    def _cosine_similarity(a, b):
        """Calculate cosine similarity between two vectors."""

        denominator = (
            np.linalg.norm(a)
            * np.linalg.norm(b)
        )

        if denominator == 0:
            return 0.0

        return float(
            np.dot(a, b) / denominator
        )

    def search(self, query, top_k=3):
        """Return the most relevant policy sections."""

        if self.embeddings is None:
            self.build_index()

        query_embedding = self._embed(query)

        scored_sections = []

        for section, embedding in zip(
            self.sections,
            self.embeddings
        ):
            score = self._cosine_similarity(
                query_embedding,
                embedding
            )

            scored_sections.append(
                {
                    "section_id": section["section_id"],
                    "title": section["title"],
                    "text": section["text"],
                    "score": score
                }
            )

        scored_sections.sort(
            key=lambda item: item["score"],
            reverse=True
        )

        return scored_sections[:top_k]