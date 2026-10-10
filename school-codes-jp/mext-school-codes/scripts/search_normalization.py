"""Conservative, explicitly documented search-only Unicode equivalences.

Never use this module to modify MEXT source data or displayed official names.
Only approved character pairs are folded. In particular, avoid blanket NFKC:
it changes other characters, punctuation and width distinctions.

The compatibility ideographs below were observed in the baseline dataset.
They are search aliases, NOT assertions that the source spelling is erroneous.
"""
from __future__ import annotations

import unicodedata

# Explicitly approved search equivalents; keep original characters in storage.
SEARCH_ALIASES = {
    "\uFA10": "\u585A",  # 塚 -> 塚
    "\uFA11": "\u5D0E",  # 﨑 -> 崎
    "\uFA26": "\u90FD",  # 都 -> 都
}


def normalize_search(text: str) -> str:
    """Return a search comparison key, without altering the input text.

    NFC only canonicalizes equivalent sequences; no blanket compatibility fold.
    A limited alias table handles the three verified search equivalences.
    """
    if not isinstance(text, str):
        raise TypeError("normalize_search expects str")
    canonical = unicodedata.normalize("NFC", text)
    return "".join(SEARCH_ALIASES.get(char, char) for char in canonical)


def matches_search(query: str, candidate: str) -> bool:
    """Case-sensitive substring match after conservative alias folding."""
    return normalize_search(query) in normalize_search(candidate)
