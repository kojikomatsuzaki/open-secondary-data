"""Search-only Unicode equivalences loaded from the reviewed YAML registry.

Source and display strings are never modified. Candidate mappings are ignored.
Requires PyYAML (see the GitHub Actions test workflow).
"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path
import unicodedata

import yaml

DEFAULT_REGISTRY = Path(__file__).resolve().parents[1] / "metadata" / "search-variants.yaml"


@lru_cache(maxsize=8)
def load_search_aliases(path: str | Path = DEFAULT_REGISTRY) -> dict[str, str]:
    """Read and validate *automatic* single-character mappings only."""
    with Path(path).open(encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    if not isinstance(data, dict) or not isinstance(data.get("automatic"), list):
        raise ValueError("Registry must contain an automatic list")
    aliases: dict[str, str] = {}
    for entry in data["automatic"]:
        if not isinstance(entry, dict) or entry.get("scope") != "search_only":
            raise ValueError("Automatic mapping requires scope=search_only")
        canonical = entry.get("canonical")
        variants = entry.get("variants")
        if not isinstance(canonical, str) or len(canonical) != 1:
            raise ValueError("Canonical search character must be one codepoint")
        if not isinstance(variants, list) or not variants:
            raise ValueError("Each mapping requires variants")
        for variant in variants:
            if not isinstance(variant, str) or len(variant) != 1 or variant == canonical:
                raise ValueError("Each variant must be one distinct codepoint")
            if variant in aliases and aliases[variant] != canonical:
                raise ValueError(f"Conflicting mappings for {variant!r}")
            aliases[variant] = canonical
    return aliases


def normalize_search(text: str, registry_path: str | Path = DEFAULT_REGISTRY) -> str:
    """Return a conservative search key; no blanket NFKC or IVS stripping."""
    if not isinstance(text, str):
        raise TypeError("normalize_search expects str")
    aliases = load_search_aliases(str(registry_path))
    return "".join(aliases.get(ch, ch) for ch in unicodedata.normalize("NFC", text))


def matches_search(query: str, candidate: str, registry_path: str | Path = DEFAULT_REGISTRY) -> bool:
    """Case-sensitive substring match after approved alias folding."""
    return normalize_search(query, registry_path) in normalize_search(candidate, registry_path)
