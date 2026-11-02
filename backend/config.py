import os
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

RODIUMAI_URL = "https://api.rodiumai.io/v1/chat/completions"
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
PROMPTS_DIR = BASE_DIR / "agent" / "prompts"

MAX_TOOL_ROUNDS = 6
DEFAULT_MODEL = os.getenv("RODIUMAI_MODEL", "openai/gpt-4o-mini")


def get_rodiumai_api_key() -> str:
    key = os.getenv("RODIUMAI_API_KEY")
    if not key:
        raise RuntimeError("RODIUMAI_API_KEY est manquante dans l'environnement.")
    return key


@lru_cache
def load_vendeur_prompt() -> str:
    path = PROMPTS_DIR / "vendeur_system.md"
    return path.read_text(encoding="utf-8")
