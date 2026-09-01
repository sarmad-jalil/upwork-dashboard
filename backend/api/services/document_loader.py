from pathlib import Path
from functools import lru_cache
import docx

DOCX_PATH = Path(__file__).parent.parent.parent / "Docs" / "upwork_complete_playbook.docx"

CHAPTER_KEYS = {
    "chapter_1": "Chapter 1",
    "chapter_2": "Chapter 2",
    "chapter_3": "Chapter 3",
    "chapter_4": "Chapter 4",
    "chapter_5": "Chapter 5",
    "chapter_6": "Chapter 6",
}

CHAPTER_TOPICS = {
    "chapter_1": "Profile Optimization (title, bio, positioning, portfolio)",
    "chapter_2": "Job Post Types (recognizing quality jobs)",
    "chapter_3": "Job Selection Strategy (filters, client vetting)",
    "chapter_4": "Proposal Writing Theory (hook, micro-win, process, close)",
    "chapter_5": "Proposal Writing Practice (tone, trim, calm close)",
    "chapter_6": "Client Conversion (first reply, mini plan, upsell, follow-up)",
}


def _load_chunks() -> dict[str, str]:
    doc = docx.Document(DOCX_PATH)
    chunks: dict[str, str] = {k: "" for k in CHAPTER_KEYS}
    current_chapter: str | None = None

    for para in doc.paragraphs:
        text = para.text.strip()
        if not text:
            continue

        if para.style.name == "Heading 1":
            for key, marker in CHAPTER_KEYS.items():
                if marker in text:
                    current_chapter = key
                    break
            else:
                current_chapter = None
            continue

        if current_chapter:
            chunks[current_chapter] += text + "\n"

    return chunks


@lru_cache(maxsize=1)
def get_chunks() -> dict[str, str]:
    return _load_chunks()


def get_chapter(chapter_key: str) -> str:
    chunks = get_chunks()
    return chunks.get(chapter_key, "")


def get_chapters(*chapter_keys: str) -> str:
    chunks = get_chunks()
    parts = []
    for key in chapter_keys:
        topic = CHAPTER_TOPICS.get(key, key)
        content = chunks.get(key, "")
        if content:
            parts.append(f"--- {topic} ---\n{content}")
    return "\n\n".join(parts)


def get_all_chapters() -> str:
    return get_chapters(*CHAPTER_KEYS.keys())
