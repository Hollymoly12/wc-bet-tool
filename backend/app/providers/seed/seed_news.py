"""Seed news provider — static team news transcribed from project/match-extra.js WC.NEWS."""
from __future__ import annotations
from datetime import datetime, timezone
from app.providers.base import NewsItem

# Transcribed verbatim from project/match-extra.js WC.NEWS
# Covers the ~16 teams that have entries: ESP, CRO, ARG, NGA, ENG, USA,
# BRA, MAR, FRA, DEN, GER, JPN, POR, MEX, NED, SEN
NEWS: dict[str, list[tuple[str, str]]] = {
    "ESP": [
        ("form",   "Unbeaten in last 14 competitive matches; midfield press rated elite."),
        ("lineup", "Pedri returns to full training, expected to start in the No.8 role."),
        ("injury", "Left-back Balde a minor doubt with a tight hamstring."),
    ],
    "CRO": [
        ("intel",  "Veteran core; struggles to convert chances in transition."),
        ("injury", "Key playmaker managing a calf knock, fitness assessed daily."),
    ],
    "ARG": [
        ("form",   "Won 8 of last 10; defense conceded just twice in qualifying."),
        ("lineup", "Manager hints at a more direct front line for the opener."),
    ],
    "NGA": [
        ("intel",  "Pacey on the counter but vulnerable to set-piece deliveries."),
        ("susp",   "First-choice DM one booking away from suspension."),
    ],
    "ENG": [
        ("form",   "Strong qualifying campaign; high xG but wasteful in the box."),
        ("injury", "Starting CB ruled out, reshuffle at the back expected."),
    ],
    "USA": [
        ("form",   "Home-soil momentum; three straight clean sheets in friendlies."),
        ("intel",  "High home-crowd factor; press intensity up sharply at venue."),
    ],
    "BRA": [
        ("form",   "Free-scoring front three; model loves the attacking output."),
        ("lineup", "Rotation likely at full-back to manage minutes."),
    ],
    "MAR": [
        ("intel",  "Compact block, dangerous on the break — covers spreads well."),
        ("injury", "Right wing-back returns from injury, eased back into squad."),
    ],
    "FRA": [
        ("form",   "Deep, balanced squad; model rates them a tier-1 threat."),
        ("susp",   "Midfield anchor suspended for the opener — depth tested."),
    ],
    "DEN": [
        ("intel",  "Set-piece specialists; over-performs on aerial duels."),
        ("injury", "Striker a game-time decision with an ankle issue."),
    ],
    "GER": [
        ("form",   "Dominates possession but leaks chances on the counter."),
        ("lineup", "New double-pivot trialed in last warm-up — looked solid."),
    ],
    "JPN": [
        ("form",   "Sharp pressing unit; punching above FIFA ranking lately."),
        ("intel",  "Quick, technical wide players stretch high defensive lines."),
    ],
    "POR": [
        ("form",   "Prolific attack; model flags strong handicap value."),
        ("injury", "First-choice keeper fit again after a knock."),
    ],
    "MEX": [
        ("intel",  "Energetic but inconsistent; draws frequent at this level."),
        ("susp",   "Captain carries a yellow into the fixture."),
    ],
    "NED": [
        ("form",   "Build-up heavy side; clean-sheet rate trending up."),
        ("lineup", "Shift to a back three expected against pacey opponents."),
    ],
    "SEN": [
        ("intel",  "Physical, athletic squad; thrives in open, end-to-end games."),
        ("injury", "Talisman forward managed minutes — expected to start."),
    ],
}


class SeedNewsProvider:
    def fetch_news(self) -> list[NewsItem]:
        now = datetime.now(timezone.utc)
        out: list[NewsItem] = []
        for code, items in NEWS.items():
            for tag, text in items:
                out.append(NewsItem(
                    code=code,
                    tag=tag,
                    text=text,
                    source="seed",
                    url="",
                    published_at=now,
                ))
        return out
