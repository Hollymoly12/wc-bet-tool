/* ============================================================================
   lineups.js — builds full squads (24 teams) from window.WC_SQUADS:
   • starting XI (first 11) for the pitch
   • full squad (24–26) for the team page
   • per-player selection vs club stat lines + bettable props
   • 24-team bettable team stats
   Augments window.WC. All figures are mock / projected.
   ========================================================================== */
(function () {
  "use strict";
  const WC = window.WC;
  if (!WC) return;
  const SQUADS = window.WC_SQUADS || {};

  const round2 = (v) => Math.round(v * 100) / 100;
  const round1 = (v) => Math.round(v * 10) / 10;
  const fact = (k) => (k <= 1 ? 1 : k * fact(k - 1));
  const pois = (k, mu) => (Math.exp(-mu) * Math.pow(mu, k)) / fact(k);
  const poisTail = (L, mu) => { let c = 0; for (let k = 0; k <= Math.floor(L); k++) c += pois(k, mu); return 1 - c; };
  function hash(s) { let h = 0; for (let i = 0; i < s.length; i++) h = (h * 31 + s.charCodeAt(i)) | 0; return Math.abs(h); }
  const EV_P = [-0.13, -0.10, -0.08, -0.06, -0.04, -0.02, 0.03, 0.05, 0.08, 0.11];
  const seedEV = (k) => EV_P[hash(k) % EV_P.length];
  const mkProp = (key, model) => {
    model = Math.max(0.02, Math.min(0.97, model));
    const dec = round2((1 / model) * (1 + seedEV(key)));
    return { model, dec, implied: 1 / dec, ev: model * dec - 1 };
  };

  const lineOf = (pos) => {
    if (pos === "GK") return "GK";
    if (["RB", "CB", "LB", "RWB", "LWB"].includes(pos)) return "DEF";
    if (["CDM", "CM", "CAM", "RM", "LM", "DM"].includes(pos)) return "MID";
    return "FWD";
  };

  const BASE = {
    FWD: { g: 0.52, sh: 3.0, sot: 1.25, card: 0.15, a: 0.22 },
    MID: { g: 0.17, sh: 1.7, sot: 0.6, card: 0.22, a: 0.30 },
    DEF: { g: 0.06, sh: 0.7, sot: 0.22, card: 0.30, a: 0.08 },
    GK: { g: 0.0, sh: 0.0, sot: 0.0, card: 0.07, a: 0.02 },
  };
  const chooseLine = (lam) => (lam < 1 ? 0.5 : Math.round(lam) - 0.5);
  const ri = (seed, lo, hi) => lo + (hash(seed) % (hi - lo + 1));

  // base team stats for all 24 contenders (used for attack scaling + team page)
  const EXTRA_BASE = {
    BEL: { rank: 8, gpg: 2.0, xg: 1.8, poss: 58, cs: 45 },
    URU: { rank: 15, gpg: 1.7, xg: 1.6, poss: 52, cs: 44 },
    COL: { rank: 12, gpg: 1.7, xg: 1.6, poss: 54, cs: 47 },
    ITA: { rank: 9, gpg: 1.8, xg: 1.7, poss: 57, cs: 50 },
    SUI: { rank: 20, gpg: 1.5, xg: 1.4, poss: 53, cs: 46 },
    KOR: { rank: 22, gpg: 1.6, xg: 1.5, poss: 52, cs: 40 },
    CAN: { rank: 25, gpg: 1.5, xg: 1.4, poss: 50, cs: 38 },
    ECU: { rank: 24, gpg: 1.4, xg: 1.3, poss: 51, cs: 45 },
  };
  WC.STATS = WC.STATS || {};
  Object.keys(EXTRA_BASE).forEach((c) => { if (!WC.STATS[c]) WC.STATS[c] = EXTRA_BASE[c]; });

  // build a single player record (stats + props) from a squad entry
  function buildPlayer(code, entry, atk, starter) {
    // entry = [num, name, pos, club, tier?]  (club optional string, tier optional number)
    const [n, name, pos] = entry;
    let club = "\u2014", tier = 1;
    for (let i = 3; i < entry.length; i++) {
      if (typeof entry[i] === "string") club = entry[i];
      else if (typeof entry[i] === "number") tier = entry[i];
    }
    const line = lineOf(pos);
    const b = BASE[line];
    const j = 0.85 + (hash(name) % 30) / 100;
    const startBoost = starter ? 1 : 0.62; // bench players accrue fewer minutes
    const gpg = round2(b.g * tier * atk * j);
    const shg = round1(b.sh * tier * j);
    const sotg = round1(b.sot * tier * j);
    const cardP = Math.min(0.55, b.card * j);
    const key = (mkt) => `pp:${code}:${n}:${mkt}`;
    const caps = Math.round(ri(name, 8, 92) * startBoost) + (starter ? 6 : 1);
    const natGoals = Math.round(gpg * caps * 0.5);
    const natAssists = Math.round(caps * (line === "MID" ? 0.12 : line === "FWD" ? 0.10 : line === "DEF" ? 0.03 : 0.0));
    const apps = Math.round(ri(name + "c", 24, 42) * (starter ? 1 : 0.78));
    const clubG90 = round2(gpg * (0.92 + (hash(name) % 22) / 100));
    const clubGoals = Math.round(clubG90 * apps * 0.9);
    const clubAssists = Math.round(apps * (line === "MID" ? 0.18 : line === "FWD" ? 0.14 : line === "DEF" ? 0.05 : 0.01));
    const sel = { caps, goals: natGoals, assists: natAssists, g90: round2(gpg * 0.9), sh90: shg, sot90: sotg, cards: round2(cardP) };
    const clubStats = { apps, goals: clubGoals, assists: clubAssists, g90: clubG90, sh90: round1(shg * 1.05), sot90: round1(sotg * 1.05), mins: apps * (line === "GK" ? 90 : ri(name + "m", 62, 88)) };
    return {
      code, team: WC.NAME[code] || code, n, name, pos, line, tier, starter,
      club, goals: Math.round(gpg * 10), assists: Math.round(b.a * tier * 10),
      gpg, shg, sotg, sel, clubStats,
      scorer: line === "GK" ? null : mkProp(key("scorer"), 1 - Math.exp(-gpg)),
      shots: line === "GK" ? null : (() => { const L = chooseLine(shg); const m = mkProp(key("sh"), poisTail(L, shg)); m.L = L; return m; })(),
      sot: line === "GK" ? null : (() => { const L = chooseLine(sotg); const m = mkProp(key("sot"), poisTail(L, sotg)); m.L = L; return m; })(),
      card: mkProp(key("card"), cardP),
    };
  }

  const lineups = {}, players = [];
  Object.keys(SQUADS).forEach((code) => {
    const [formation, list] = SQUADS[code];
    const teamGpg = (WC.STATS[code] && WC.STATS[code].gpg) || 1.7;
    const atk = teamGpg / 1.8;
    const squad = list.map((entry, idx) => buildPlayer(code, entry, atk, idx < 11));
    squad.forEach((p) => players.push(p));
    lineups[code] = { formation, xi: squad.filter((p) => p.starter).slice(0, 11), squad };
  });

  WC.lineups = lineups;
  WC.players = players;

  /* ---- full 48-team bettable team stats (synth from strength if needed) */
  function synthStats(t) {
    const s = t.str || 55;
    return {
      rank: clampInt(Math.round(64 - (s - 46) * 1.35), 1, 64),
      gpg: round2(0.9 + (s - 46) / 24),
      xg: round2(0.8 + (s - 46) / 25),
      poss: clampInt(Math.round(42 + (s - 46) * 0.7), 35, 70),
      cs: clampInt(Math.round(26 + (s - 46) * 0.85), 20, 62),
    };
  }
  function clampInt(v, lo, hi) { return Math.max(lo, Math.min(hi, v)); }

  WC.teamStats = WC.teams.map((t) => {
    const s = WC.STATS[t.code] || synthStats(t);
    const gc = round1((100 - s.cs) / 100 * 1.4 + 0.5);
    const btts = Math.round(38 + (s.gpg - 1.3) * 22 + gc * 12);
    const cards = round1(1.5 + (s.rank / 30) * 1.6);
    const corners = round1(4.3 + (s.xg - 1.3) * 2.4);
    const winPct = Math.round(Math.max(18, Math.min(72, s.cs * 0.6 + s.gpg * 12)));
    return { code: t.code, name: t.name, group: t.group, form: t.form, ...s, gc, btts: Math.max(34, Math.min(72, btts)), cards, corners, winPct };
  });
})();
