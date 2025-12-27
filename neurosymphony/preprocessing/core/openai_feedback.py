from __future__ import annotations

import os
import re
from dataclasses import dataclass
from typing import List, Optional, Tuple

import numpy as np


INSTR_IS_NARRATIVE = (
    "Il seguente testo contiene un feedback narrativo dal quale estrarre informazioni emotive?\n"
    "Rispondi esclusivamente con un 1 o un 0 se sì o se no."
)

INSTR_RATING = (
    "Analizza il seguente testo per identificare il contenuto emotivo e dai un rating da 0 a 10 per valutarne la **valenza** "
    "(da 0, estremamente negativa, a 10, estremamente positiva) ed **arousal** ossia il livello di attivazione emotiva "
    "(da 0, nessuna attivazione, a 10, massima attivazione) compilando il seguente schema:\n"
    "valenza ###INSERISCI QUA###; arousal ###INSERISCI QUA###\n\n"
)


def _extract_arousal_valence(text: str) -> Tuple[Optional[int], Optional[int]]:
    arousal_match = re.search(r"arousal\W*(\d+)", text, flags=re.IGNORECASE)
    valence_match = re.search(r"valenza\W*(\d+)", text, flags=re.IGNORECASE)
    arousal = int(arousal_match.group(1)) if arousal_match else None
    valence = int(valence_match.group(1)) if valence_match else None
    return arousal, valence


class OpenAIChat:
    """Small compatibility wrapper supporting openai>=1 and legacy openai<1."""

    def __init__(self, model: str = "gpt-4o-mini", api_key: Optional[str] = False):
        self.model = model
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise RuntimeError("OPENAI_API_KEY is not set")

        # Try new SDK first
        self._client = None
        try:
            from openai import OpenAI  # type: ignore

            self._client = OpenAI(api_key=self.api_key)
            self._mode = "new"
        except Exception:
            import openai  # type: ignore

            openai.api_key = self.api_key
            self._openai = openai
            self._mode = "legacy"

    def complete(self, messages: List[dict]) -> str:
        if self._mode == "new":
            resp = self._client.chat.completions.create(model=self.model, messages=messages)
            return resp.choices[0].message.content or ""
        resp = self._openai.ChatCompletion.create(model=self.model, messages=messages)
        return resp["choices"][0]["message"]["content"]


def is_narrative(chat: OpenAIChat, text: str) -> bool:
    messages = [
        {"role": "system", "content": "Sei un musicologo."},
        {"role": "user", "content": INSTR_IS_NARRATIVE},
        {"role": "assistant", "content": text},
    ]
    out = chat.complete(messages).strip()
    return out.startswith("1")


def rate_valence_arousal(chat: OpenAIChat, text: str, repeats: int = 5) -> Tuple[float, float]:
    ar: List[int] = []
    val: List[int] = []

    messages = [
        {"role": "system", "content": "Sei un musicologo."},
        {"role": "user", "content": INSTR_RATING + text.strip()},
    ]

    for _ in range(max(1, int(repeats))):
        out = chat.complete(messages)
        a, v = _extract_arousal_valence(out)
        if a is not None and v is not None:
            ar.append(a)
            val.append(v)

    if not ar:
        return float("nan"), float("nan")
    return float(np.mean(ar)), float(np.mean(val))
