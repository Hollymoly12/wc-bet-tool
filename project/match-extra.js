/* ============================================================================
   match-extra.js — extended betting markets, team news, comp stats, H2H
   Augments window.WC (loaded after data.js). All figures are mock data.
   ========================================================================== */
(function () {
  "use strict";
  const WC = window.WC;
  if (!WC) return;

  const round2 = (v) => Math.round(v * 100) / 100;
  const fact = (k) => (k <= 1 ? 1 : k * fact(k - 1));
  const pois = (k, mu) => (Math.exp(-mu) * Math.pow(mu, k)) / fact(k);
  const cdf = (n, mu) => { let s = 0; for (let k = 0; k <= n; k++) s += pois(k, mu); return s; };

  // deterministic per-selection EV so the value spread is stable + believable
  function hash(s) { let h = 0; for (let i = 0; i < s.length; i++) h = (h * 31 + s.charCodeAt(i)) | 0; return Math.abs(h); }
  const EV_CHOICES = [-0.09, -0.06, -0.04, -0.02, 0.03, 0.05, 0.08, 0.11];
  const seedEV = (id, k) => EV_CHOICES[hash(id + k) % EV_CHOICES.length];

  // build a selection from a model probability + seeded edge
  function mkSel(matchId, cat, label, model, code) {
    const ev0 = seedEV(matchId, cat + "|" + label);
    const dec = round2((1 / model) * (1 + ev0));
    const implied = 1 / dec;
    return {
      key: `x:${matchId}:${cat}:${label}`,
      cat, label, model, dec, implied,
      ev: model * dec - 1, code,
    };
  }

  // expected goals per fixture [home, away]
  const GOALS = {
    m1: [1.9, 0.8], m2: [2.2, 0.6], m3: [1.4, 1.2], m4: [1.7, 0.9],
    m5: [2.0, 0.7], m6: [1.5, 1.1], m7: [1.8, 0.8], m8: [1.6, 1.0],
  };

  function buildMarkets(m) {
    const [pH, pD, pA] = m.model;
    const [xgH, xgA] = GOALS[m.id] || [1.6, 1.0];
    const mu = xgH + xgA;
    const over25 = 1 - cdf(2, mu), over35 = 1 - cdf(3, mu);
    const bttsYes = (1 - Math.exp(-xgH)) * (1 - Math.exp(-xgA));

    const cats = [
      {
        cat: "Match Result", note: "1X2",
        sels: m.legs.map((l) => ({
          key: "m:" + m.id + ":" + l.kind, cat: "Match Result",
          label: l.label, model: l.model, dec: l.dec, implied: l.implied, ev: l.ev,
          code: l.kind === "away" ? m.away : m.home,
        })),
      },
      {
        cat: "Double Chance", note: "two outcomes",
        sels: [
          mkSel(m.id, "Double Chance", `${m.home} or Draw`, pH + pD, m.home),
          mkSel(m.id, "Double Chance", `${m.home} or ${m.away}`, pH + pA, m.home),
          mkSel(m.id, "Double Chance", `Draw or ${m.away}`, pD + pA, m.away),
        ],
      },
      {
        cat: "Draw No Bet", note: "draw refunds",
        sels: [
          mkSel(m.id, "Draw No Bet", `${m.homeName}`, pH / (pH + pA), m.home),
          mkSel(m.id, "Draw No Bet", `${m.awayName}`, pA / (pH + pA), m.away),
        ],
      },
      {
        cat: "Total Goals", note: `model x̄ ${mu.toFixed(2)}`,
        sels: [
          mkSel(m.id, "Total Goals", "Over 2.5", over25, m.home),
          mkSel(m.id, "Total Goals", "Under 2.5", 1 - over25, m.away),
          mkSel(m.id, "Total Goals", "Over 3.5", over35, m.home),
          mkSel(m.id, "Total Goals", "Under 3.5", 1 - over35, m.away),
        ],
      },
      {
        cat: "Both Teams Score", note: "BTTS",
        sels: [
          mkSel(m.id, "Both Teams Score", "Yes", bttsYes, m.home),
          mkSel(m.id, "Both Teams Score", "No", 1 - bttsYes, m.away),
        ],
      },
    ];

    // best-value selection across every market on this fixture
    let top = null;
    cats.forEach((c) => c.sels.forEach((s) => { if (!top || s.ev > top.ev) top = s; }));
    return { cats, top, xgH, xgA, mu };
  }

  /* ---- comparison stats (per team) ------------------------------------ */
  WC.STATS = {
    ESP: { rank: 2, gpg: 2.4, xg: 2.2, poss: 64, cs: 55 },
    CRO: { rank: 9, gpg: 1.5, xg: 1.4, poss: 54, cs: 38 },
    ARG: { rank: 1, gpg: 2.3, xg: 2.1, poss: 58, cs: 60 },
    NGA: { rank: 28, gpg: 1.4, xg: 1.3, poss: 49, cs: 33 },
    ENG: { rank: 4, gpg: 2.0, xg: 1.9, poss: 60, cs: 50 },
    USA: { rank: 11, gpg: 1.7, xg: 1.6, poss: 52, cs: 40 },
    BRA: { rank: 3, gpg: 2.2, xg: 2.0, poss: 59, cs: 52 },
    MAR: { rank: 13, gpg: 1.6, xg: 1.5, poss: 53, cs: 45 },
    FRA: { rank: 5, gpg: 2.3, xg: 2.1, poss: 57, cs: 54 },
    DEN: { rank: 18, gpg: 1.6, xg: 1.5, poss: 55, cs: 42 },
    GER: { rank: 10, gpg: 2.1, xg: 1.9, poss: 62, cs: 44 },
    JPN: { rank: 17, gpg: 1.8, xg: 1.6, poss: 54, cs: 41 },
    POR: { rank: 6, gpg: 2.1, xg: 1.9, poss: 58, cs: 48 },
    MEX: { rank: 14, gpg: 1.5, xg: 1.4, poss: 51, cs: 36 },
    NED: { rank: 7, gpg: 1.9, xg: 1.8, poss: 58, cs: 46 },
    SEN: { rank: 19, gpg: 1.5, xg: 1.4, poss: 50, cs: 39 },
  };

  /* ---- team news (per team) ------------------------------------------- */
  // tag: injury | form | lineup | susp | intel
  WC.NEWS = {
    ESP: [
      { tag: "form", text: "Unbeaten in last 14 competitive matches; midfield press rated elite.", time: "2h ago" },
      { tag: "lineup", text: "Pedri returns to full training, expected to start in the No.8 role.", time: "6h ago" },
      { tag: "injury", text: "Left-back Balde a minor doubt with a tight hamstring.", time: "1d ago" },
    ],
    CRO: [
      { tag: "intel", text: "Veteran core; struggles to convert chances in transition.", time: "4h ago" },
      { tag: "injury", text: "Key playmaker managing a calf knock, fitness assessed daily.", time: "1d ago" },
    ],
    ARG: [
      { tag: "form", text: "Won 8 of last 10; defense conceded just twice in qualifying.", time: "1h ago" },
      { tag: "lineup", text: "Manager hints at a more direct front line for the opener.", time: "5h ago" },
    ],
    NGA: [
      { tag: "intel", text: "Pacey on the counter but vulnerable to set-piece deliveries.", time: "3h ago" },
      { tag: "susp", text: "First-choice DM one booking away from suspension.", time: "8h ago" },
    ],
    ENG: [
      { tag: "form", text: "Strong qualifying campaign; high xG but wasteful in the box.", time: "2h ago" },
      { tag: "injury", text: "Starting CB ruled out, reshuffle at the back expected.", time: "7h ago" },
    ],
    USA: [
      { tag: "form", text: "Home-soil momentum; three straight clean sheets in friendlies.", time: "1h ago" },
      { tag: "intel", text: "High home-crowd factor; press intensity up sharply at venue.", time: "5h ago" },
    ],
    BRA: [
      { tag: "form", text: "Free-scoring front three; model loves the attacking output.", time: "2h ago" },
      { tag: "lineup", text: "Rotation likely at full-back to manage minutes.", time: "9h ago" },
    ],
    MAR: [
      { tag: "intel", text: "Compact block, dangerous on the break — covers spreads well.", time: "3h ago" },
      { tag: "injury", text: "Right wing-back returns from injury, eased back into squad.", time: "1d ago" },
    ],
    FRA: [
      { tag: "form", text: "Deep, balanced squad; model rates them a tier-1 threat.", time: "1h ago" },
      { tag: "susp", text: "Midfield anchor suspended for the opener — depth tested.", time: "6h ago" },
    ],
    DEN: [
      { tag: "intel", text: "Set-piece specialists; over-performs on aerial duels.", time: "4h ago" },
      { tag: "injury", text: "Striker a game-time decision with an ankle issue.", time: "1d ago" },
    ],
    GER: [
      { tag: "form", text: "Dominates possession but leaks chances on the counter.", time: "2h ago" },
      { tag: "lineup", text: "New double-pivot trialed in last warm-up — looked solid.", time: "8h ago" },
    ],
    JPN: [
      { tag: "form", text: "Sharp pressing unit; punching above FIFA ranking lately.", time: "3h ago" },
      { tag: "intel", text: "Quick, technical wide players stretch high defensive lines.", time: "7h ago" },
    ],
    POR: [
      { tag: "form", text: "Prolific attack; model flags strong handicap value.", time: "2h ago" },
      { tag: "injury", text: "First-choice keeper fit again after a knock.", time: "1d ago" },
    ],
    MEX: [
      { tag: "intel", text: "Energetic but inconsistent; draws frequent at this level.", time: "4h ago" },
      { tag: "susp", text: "Captain carries a yellow into the fixture.", time: "9h ago" },
    ],
    NED: [
      { tag: "form", text: "Build-up heavy side; clean-sheet rate trending up.", time: "1h ago" },
      { tag: "lineup", text: "Shift to a back three expected against pacey opponents.", time: "6h ago" },
    ],
    SEN: [
      { tag: "intel", text: "Physical, athletic squad; thrives in open, end-to-end games.", time: "3h ago" },
      { tag: "injury", text: "Talisman forward managed minutes — expected to start.", time: "1d ago" },
    ],
  };

  /* ---- head to head (per fixture) ------------------------------------- */
  const H2H = {
    m1: [{ d: "2024", s: "2–2", n: "Euro group stage" }, { d: "2022", s: "1–0", n: "Nations League" }, { d: "2021", s: "5–3", n: "Nations League final (aet)" }],
    m2: [{ d: "2018", s: "—", n: "No recent meeting" }, { d: "2002", s: "0–1", n: "World Cup group" }],
    m3: [{ d: "2022", s: "0–0", n: "World Cup group" }, { d: "2010", s: "1–1", n: "World Cup group" }, { d: "2024", s: "2–1", n: "Friendly" }],
    m4: [{ d: "2023", s: "2–1", n: "Friendly" }, { d: "2019", s: "—", n: "No competitive meeting" }],
    m5: [{ d: "2022", s: "2–0", n: "Nations League" }, { d: "2018", s: "0–0", n: "World Cup group" }, { d: "2002", s: "2–0", n: "World Cup group" }],
    m6: [{ d: "2023", s: "1–4", n: "Friendly (GER home loss)" }, { d: "2022", s: "1–2", n: "World Cup group" }],
    m7: [{ d: "2024", s: "—", n: "No recent meeting" }, { d: "2014", s: "—", n: "No competitive meeting" }],
    m8: [{ d: "2023", s: "2–1", n: "Friendly" }, { d: "2002", s: "—", n: "No competitive meeting" }],
  };

  // attach to each match
  WC.matches.forEach((m) => {
    const built = buildMarkets(m);
    m.markets = built.cats;
    m.topMarket = built.top;
    m.xgH = built.xgH; m.xgA = built.xgA; m.mu = built.mu;
    m.h2h = H2H[m.id] || [];
  });
})();
