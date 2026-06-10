"""Lightweight market helpers with NO heavy deps (no scipy/numpy).

Kept separate from pricing.py so the read API (Vercel) can import
`market_from_prob` for the /groups endpoint without transitively pulling in
scipy via the ratings/match_model chain.
"""
from __future__ import annotations


def _shash(s: str) -> int:
    """Stable (non-salted) string hash for deterministic seeding."""
    h = 0
    for i, c in enumerate(s):
        h += ord(c) * (31 ** i)
    return h


def market_from_prob(prob: float, seed: str) -> dict:
    """Build a simple market dict from a model probability with a small margin.

    margin = 0.90 + (stable_hash(seed) % 22) / 100  → range [0.90, 1.12]
    dec = (1 / max(prob, 0.001)) * margin
    """
    prob = max(prob, 1e-3)
    margin = 0.90 + (_shash(seed) % 22) / 100
    dec = round((1 / prob) * margin, 2)
    dec = max(dec, 1.01)
    implied = round(1 / dec, 6)
    ev = round(prob * dec - 1, 6)
    return {"dec": dec, "implied": implied, "model": prob, "ev": ev}
