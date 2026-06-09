/* ============================================================================
   tournament.js — derives the group + knockout structure from team strength.
   Builds:  WC.groups  (12 groups: standings, group-winner & qualify markets)
            WC.bracket (projected Round of 32 → Final, model favourites)
   Augments window.WC. All figures are mock / projected.
   ========================================================================== */
(function () {
  "use strict";
  const WC = window.WC;
  if (!WC) return;

  const round2 = (v) => Math.round(v * 100) / 100;
  const clamp = (v, lo, hi) => Math.max(lo, Math.min(hi, v));
  // seeded RNG so standings are stable across reloads
  function mulberry32(a) { return function () { a |= 0; a = (a + 0x6D2B79F5) | 0; let t = Math.imul(a ^ (a >>> 15), 1 | a); t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t; return ((t ^ (t >>> 14)) >>> 0) / 4294967296; }; }
  function hash(s) { let h = 0; for (let i = 0; i < s.length; i++) h = (h * 31 + s.charCodeAt(i)) | 0; return Math.abs(h); }

  const byCode = {};
  WC.teams.forEach((t) => (byCode[t.code] = t));

  // probability team A beats team B (Elo-style on the 0–100 power rating)
  function pairProbs(sA, sB) {
    const diff = sA - sB;
    const pA = 1 / (1 + Math.pow(10, -diff / 24));
    const dr = clamp(0.28 * Math.exp(-Math.abs(diff) / 46), 0.09, 0.30);
    return { wA: (1 - dr) * pA, wB: (1 - dr) * (1 - pA), dr };
  }
  function expectedPoints(team, group) {
    let pts = 0;
    group.forEach((o) => {
      if (o.code === team.code) return;
      const { wA, dr } = pairProbs(team.str, o.str);
      pts += 3 * wA + 1 * dr;
    });
    return pts;
  }

  // seeded "book" price around the fair price → realistic EV spread
  function priced(prob, seed) {
    const fair = 1 / prob;
    const adj = 0.88 + ((hash(seed) % 22) / 100); // 0.88–1.09
    const dec = round2(clamp(fair * adj, 1.02, 1001));
    return { dec, implied: 1 / dec, model: prob, ev: prob * dec - 1 };
  }

  /* ---- group simulation ----------------------------------------------- */
  const groups = WC.GROUP_LETTERS.map((letter) => {
    const teams = WC.teams.filter((t) => t.group === letter);
    const N = 6000;
    const rng = mulberry32(hash("grp" + letter) || 1);
    const gw = {}, qual = {}, third = {};
    teams.forEach((t) => { gw[t.code] = 0; qual[t.code] = 0; third[t.code] = 0; });

    for (let s = 0; s < N; s++) {
      const pts = {}, gd = {};
      teams.forEach((t) => { pts[t.code] = 0; gd[t.code] = 0; });
      for (let i = 0; i < teams.length; i++) {
        for (let j = i + 1; j < teams.length; j++) {
          const A = teams[i], B = teams[j];
          const { wA, wB } = pairProbs(A.str, B.str);
          const r = rng();
          if (r < wA) { pts[A.code] += 3; gd[A.code] += 1; gd[B.code] -= 1; }
          else if (r < wA + wB) { pts[B.code] += 3; gd[B.code] += 1; gd[A.code] -= 1; }
          else { pts[A.code] += 1; pts[B.code] += 1; }
        }
      }
      const order = [...teams].sort((a, b) =>
        pts[b.code] - pts[a.code] || gd[b.code] - gd[a.code] || b.str - a.str || (rng() - 0.5));
      gw[order[0].code]++; qual[order[0].code]++; qual[order[1].code]++; third[order[2].code]++;
    }

    const rows = teams.map((t) => {
      const gwProb = clamp(gw[t.code] / N, 0.001, 0.999);
      const qualProb = clamp(qual[t.code] / N, 0.001, 0.999);
      const thirdProb = third[t.code] / N;
      const xp = expectedPoints(t, teams);
      return {
        code: t.code, name: t.name, str: t.str, group: letter,
        dec: t.dec, ev: t.ev, form: t.form,
        gwProb, qualProb, thirdProb, xp,
        gwMarket: priced(gwProb, "gw" + t.code),
        qualMarket: priced(qualProb, "ql" + t.code),
      };
    }).sort((a, b) => b.xp - a.xp);
    rows.forEach((r, i) => (r.projRank = i + 1));
    return { letter, rows };
  });
  WC.groups = groups;

  /* ---- knockout bracket (projected) ----------------------------------- */
  // qualifiers: 12 winners + 12 runners-up + 8 best third-placed
  const winners = [], runners = [], thirds = [];
  groups.forEach((g) => {
    winners.push({ ...g.rows[0], slot: "1" + g.letter });
    runners.push({ ...g.rows[1], slot: "2" + g.letter });
    thirds.push({ ...g.rows[2], slot: "3" + g.letter });
  });
  const bestThirds = [...thirds].sort((a, b) => b.xp - a.xp).slice(0, 8);
  const qualifiers = [...winners, ...runners, ...bestThirds];

  // seed by power rating, then arrange into standard bracket slot order
  qualifiers.sort((a, b) => b.str - a.str);
  let slots = [1, 2];
  while (slots.length < 32) {
    const len = slots.length * 2, out = [];
    for (const s of slots) { out.push(s); out.push(len + 1 - s); }
    slots = out;
  }
  const seeded = slots.map((seed) => qualifiers[seed - 1]);

  function favourite(a, b) {
    if (!a) return b; if (!b) return a;
    const { wA, wB } = pairProbs(a.str, b.str);
    const total = wA + wB || 1;
    const pA = wA / total;
    return { ...(pA >= 0.5 ? a : b), winProb: Math.max(pA, 1 - pA) };
  }

  const ROUND_NAMES = ["Round of 32", "Round of 16", "Quarter-finals", "Semi-finals", "Final"];
  const rounds = [];
  let current = seeded;
  for (let r = 0; r < ROUND_NAMES.length; r++) {
    const matches = [];
    for (let i = 0; i < current.length; i += 2) {
      const a = current[i], b = current[i + 1];
      matches.push({ a, b, winner: favourite(a, b) });
    }
    rounds.push({ name: ROUND_NAMES[r], matches });
    current = matches.map((m) => m.winner);
  }
  WC.bracket = { rounds, champion: current[0], qualifiers: qualifiers.length };
})();
