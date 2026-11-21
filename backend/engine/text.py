import re
import unicodedata


def strip_accents(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFKD", s) if not unicodedata.combining(c))


def norm(s: str) -> str:
    s = unicodedata.normalize("NFKC", s or "")
    s = strip_accents(s).upper()
    return re.sub(r"\s+", " ", s).strip()


def compact(s: str) -> str:
    return re.sub(r"\s+", "", norm(s))


def key(s: str) -> str:
    return re.sub(r"[^A-Z0-9]", "", norm(s))
