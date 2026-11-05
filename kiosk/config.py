"""Settings from environment / .env. Fails fast with a clear message when a value is missing."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")


class MissingSetting(RuntimeError):
    pass


def setting(name: str, default: str | None = None) -> str:
    value = os.environ.get(name, default)
    if not value:
        raise MissingSetting(f"{name} is not set; copy .env.example to .env and fill it in")
    return value
