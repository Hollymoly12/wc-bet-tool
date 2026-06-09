/* ============================================================================
   World Cup Bet Tool — mock data + betting math
   2026 FIFA World Cup (projected). All figures are illustrative mock data.
   Exposes window.WC
   ========================================================================== */
(function () {
  "use strict";

  /* ---- odds + probability math ---------------------------------------- */

  // decimal odds -> implied probability (book's price, includes margin)
  const impliedProb = (dec) => 1 / dec;

  // expected value per 1 unit staked, given model "true" probability
  // EV = p * (dec) - 1   (returns staked unit on win incl stake)
  const ev = (p, dec) => p * dec - 1;

  // full Kelly fraction of bankroll. b = net odds, p = win prob, q = lose
  const kellyFull = (p, dec) => {
    const b = dec - 1;
    const f = (b * p - (1 - p)) / b;
    return Math.max(0, f);
  };

  // odds formatting across decimal / american / fractional
  function gcd(a, b) { return b ? gcd(b, a % b) : a; }
  function formatOdds(dec, fmt) {
    if (fmt === "american") {
      if (dec >= 2) return "+" + Math.round((dec - 1) * 100);
      return "" + Math.round(-100 / (dec - 1));
    }
    if (fmt === "fractional") {
      const num = Math.round((dec - 1) * 100);
      const den = 100;
      const g = gcd(num, den) || 1;
      return `${num / g}/${den / g}`;
    }
    return dec.toFixed(2);
  }

  const RISK = {
    conservative: { label: "Conservative", mult: 0.25, cap: 0.04 },
    balanced: { label: "Balanced", mult: 0.5, cap: 0.07 },
    aggressive: { label: "Aggressive", mult: 1.0, cap: 0.12 },
  };

  // recommended stake (currency) for a wager given bankroll + risk profile
  function recommendedStake(p, dec, bankroll, riskKey) {
    const r = RISK[riskKey] || RISK.balanced;
    const f = Math.min(kellyFull(p, dec) * r.mult, r.cap);
    return Math.round((bankroll * f) / 5) * 5; // round to nearest 5
  }

  /* ---- team palette ---------------------------------------------------- */
  // [primary, secondary] used for the duotone country tokens
  const C = {
    ESP: ["#C60B1E", "#FFC400"], FRA: ["#1F3A93", "#ED2939"],
    BRA: ["#009C3B", "#FFDF00"], ARG: ["#6CACE4", "#FFFFFF"],
    ENG: ["#E1232C", "#1B2A6B"], GER: ["#111111", "#D00C27"],
    POR: ["#006600", "#D52B1E"], NED: ["#FF6A13", "#21468B"],
    BEL: ["#111111", "#FDDA24"], ITA: ["#0066A6", "#FFFFFF"],
    CRO: ["#D6122A", "#1A4B9B"], URU: ["#55B0E2", "#111111"],
    COL: ["#FCD116", "#003893"], USA: ["#1B2A6B", "#E1232C"],
    MEX: ["#006847", "#CE1126"], MAR: ["#C1272D", "#006233"],
    JPN: ["#1A2C6B", "#E60012"], SEN: ["#00853F", "#FDEF42"],
    SUI: ["#D52B1E", "#FFFFFF"], DEN: ["#C8102E", "#FFFFFF"],
    KOR: ["#13205B", "#CD2E3A"], CAN: ["#D52B1E", "#FFFFFF"],
    ECU: ["#FFD100", "#0072CE"], NGA: ["#008751", "#FFFFFF"],
    QAT: ["#8A1538", "#FFFFFF"], KSA: ["#006C35", "#FFFFFF"],
    UZB: ["#1EB53A", "#0099B5"], IRN: ["#239F40", "#DA0000"],
    JOR: ["#111111", "#CE1126"], SRB: ["#C6363C", "#0C4076"],
    NZL: ["#111111", "#FFFFFF"], AUS: ["#00843D", "#FFCD00"],
    CRC: ["#002B7F", "#CE1126"], GHA: ["#006B3F", "#FCD116"],
    PAN: ["#005293", "#DA121A"], EGY: ["#CE1126", "#1B1B1B"],
    JAM: ["#009B3A", "#FED100"], CIV: ["#FF8200", "#009E60"],
    PAR: ["#0038A8", "#D52B1E"], TUN: ["#E70013", "#FFFFFF"],
    VEN: ["#7B1113", "#FCD116"], UKR: ["#005BBB", "#FFD500"],
    IRQ: ["#007A3D", "#CE1126"], AUT: ["#ED2939", "#FFFFFF"],
    CMR: ["#007A5E", "#CE1126"], NOR: ["#BA0C2F", "#00205B"],
    ALG: ["#006233", "#D21034"], TUR: ["#E30A17", "#FFFFFF"],
  };
  const NAME = {
    ESP: "Spain", FRA: "France", BRA: "Brazil", ARG: "Argentina",
    ENG: "England", GER: "Germany", POR: "Portugal", NED: "Netherlands",
    BEL: "Belgium", ITA: "Italy", CRO: "Croatia", URU: "Uruguay",
    COL: "Colombia", USA: "USA", MEX: "Mexico", MAR: "Morocco",
    JPN: "Japan", SEN: "Senegal", SUI: "Switzerland", DEN: "Denmark",
    KOR: "South Korea", CAN: "Canada", ECU: "Ecuador", NGA: "Nigeria",
    QAT: "Qatar", KSA: "Saudi Arabia", UZB: "Uzbekistan", IRN: "Iran",
    JOR: "Jordan", SRB: "Serbia", NZL: "New Zealand", AUS: "Australia",
    CRC: "Costa Rica", GHA: "Ghana", PAN: "Panama", EGY: "Egypt",
    JAM: "Jamaica", CIV: "Ivory Coast", PAR: "Paraguay", TUN: "Tunisia",
    VEN: "Venezuela", UKR: "Ukraine", IRQ: "Iraq", AUT: "Austria",
    CMR: "Cameroon", NOR: "Norway", ALG: "Algeria", TUR: "T\u00fcrkiye",
  };

  /* ---- outright winner market — 48 teams, 12 groups (A–L) ------------- */
  // dec = book decimal odds, model = model win prob, str = 0–100 power rating
  const rawTeams = [
    // Group A
    { code: "ARG", group: "A", dec: 8.0,   model: 0.135,  conf: 81, form: "WWWWD", str: 89 },
    { code: "URU", group: "A", dec: 29.0,  model: 0.028,  conf: 62, form: "WWDWL", str: 75 },
    { code: "NGA", group: "A", dec: 91.0,  model: 0.008,  conf: 46, form: "LWDWW", str: 64 },
    { code: "QAT", group: "A", dec: 751.0, model: 0.0010, conf: 40, form: "LWLDL", str: 52 },
    // Group B
    { code: "ESP", group: "B", dec: 5.5,   model: 0.205,  conf: 84, form: "WWWDW", str: 92 },
    { code: "CRO", group: "B", dec: 34.0,  model: 0.024,  conf: 60, form: "DWWDL", str: 74 },
    { code: "KSA", group: "B", dec: 501.0, model: 0.0015, conf: 42, form: "WLDLW", str: 55 },
    { code: "UZB", group: "B", dec: 751.0, model: 0.0010, conf: 41, form: "DWLDW", str: 54 },
    // Group C
    { code: "ENG", group: "C", dec: 7.0,   model: 0.118,  conf: 74, form: "WDWLW", str: 85 },
    { code: "USA", group: "C", dec: 26.0,  model: 0.046,  conf: 57, form: "WWDWW", str: 70 },
    { code: "IRN", group: "C", dec: 251.0, model: 0.0030, conf: 55, form: "WWDLW", str: 61 },
    { code: "JOR", group: "C", dec: 1001.0,model: 0.0008, conf: 38, form: "DLWDL", str: 50 },
    // Group D
    { code: "BRA", group: "D", dec: 7.5,   model: 0.150,  conf: 79, form: "WDWWW", str: 88 },
    { code: "MAR", group: "D", dec: 34.0,  model: 0.027,  conf: 61, form: "WWDWW", str: 73 },
    { code: "SRB", group: "D", dec: 151.0, model: 0.0050, conf: 57, form: "WLWDL", str: 68 },
    { code: "NZL", group: "D", dec: 1001.0,model: 0.0008, conf: 36, form: "WWLDL", str: 48 },
    // Group E
    { code: "FRA", group: "E", dec: 6.0,   model: 0.182,  conf: 82, form: "WWLWW", str: 90 },
    { code: "DEN", group: "E", dec: 51.0,  model: 0.015,  conf: 52, form: "WLWDW", str: 69 },
    { code: "AUS", group: "E", dec: 301.0, model: 0.0020, conf: 52, form: "WDWLL", str: 58 },
    { code: "CRC", group: "E", dec: 751.0, model: 0.0010, conf: 41, form: "LWDLW", str: 51 },
    // Group F
    { code: "GER", group: "F", dec: 11.0,  model: 0.072,  conf: 68, form: "WLWDW", str: 82 },
    { code: "JPN", group: "F", dec: 51.0,  model: 0.020,  conf: 56, form: "WWWDL", str: 68 },
    { code: "GHA", group: "F", dec: 301.0, model: 0.0020, conf: 50, form: "WLDWL", str: 60 },
    { code: "PAN", group: "F", dec: 751.0, model: 0.0010, conf: 42, form: "WDLWL", str: 52 },
    // Group G
    { code: "POR", group: "G", dec: 13.0,  model: 0.071,  conf: 70, form: "WWDLW", str: 83 },
    { code: "MEX", group: "G", dec: 41.0,  model: 0.018,  conf: 54, form: "WDLWD", str: 66 },
    { code: "EGY", group: "G", dec: 151.0, model: 0.0050, conf: 56, form: "WWDWL", str: 66 },
    { code: "JAM", group: "G", dec: 751.0, model: 0.0010, conf: 43, form: "LWDLW", str: 53 },
    // Group H
    { code: "NED", group: "H", dec: 15.0,  model: 0.058,  conf: 66, form: "DWWLW", str: 80 },
    { code: "SEN", group: "H", dec: 67.0,  model: 0.012,  conf: 50, form: "WDWLD", str: 67 },
    { code: "CIV", group: "H", dec: 151.0, model: 0.0050, conf: 56, form: "WWLWD", str: 65 },
    { code: "PAR", group: "H", dec: 251.0, model: 0.0030, conf: 50, form: "DWDLW", str: 57 },
    // Group I
    { code: "ITA", group: "I", dec: 23.0,  model: 0.034,  conf: 59, form: "WDWWL", str: 78 },
    { code: "BEL", group: "I", dec: 26.0,  model: 0.030,  conf: 58, form: "WLDWL", str: 76 },
    { code: "TUN", group: "I", dec: 301.0, model: 0.0020, conf: 50, form: "WDLDW", str: 59 },
    { code: "VEN", group: "I", dec: 301.0, model: 0.0020, conf: 48, form: "DWLDW", str: 56 },
    // Group J
    { code: "COL", group: "J", dec: 41.0,  model: 0.017,  conf: 53, form: "DWDWW", str: 71 },
    { code: "SUI", group: "J", dec: 81.0,  model: 0.009,  conf: 47, form: "DLWDW", str: 65 },
    { code: "UKR", group: "J", dec: 201.0, model: 0.0040, conf: 57, form: "WLWDW", str: 67 },
    { code: "IRQ", group: "J", dec: 751.0, model: 0.0010, conf: 42, form: "DLWDL", str: 53 },
    // Group K
    { code: "AUT", group: "K", dec: 67.0,  model: 0.012,  conf: 60, form: "WWDWL", str: 70 },
    { code: "KOR", group: "K", dec: 81.0,  model: 0.010,  conf: 48, form: "WDLWW", str: 62 },
    { code: "CMR", group: "K", dec: 251.0, model: 0.0030, conf: 54, form: "WLWDL", str: 63 },
    { code: "CAN", group: "K", dec: 101.0, model: 0.007,  conf: 44, form: "WLDWL", str: 60 },
    // Group L
    { code: "NOR", group: "L", dec: 81.0,  model: 0.010,  conf: 61, form: "WWWDL", str: 71 },
    { code: "TUR", group: "L", dec: 151.0, model: 0.0050, conf: 60, form: "WDWWL", str: 69 },
    { code: "ALG", group: "L", dec: 201.0, model: 0.0040, conf: 56, form: "WWDWL", str: 64 },
    { code: "ECU", group: "L", dec: 67.0,  model: 0.011,  conf: 49, form: "DWDLW", str: 63 },
  ];

  const teams = rawTeams.map((t) => {
    const imp = impliedProb(t.dec);
    return {
      ...t,
      name: NAME[t.code],
      colors: C[t.code],
      implied: imp,
      edge: t.model - imp,        // probability edge
      ev: ev(t.model, t.dec),     // EV per unit
      kelly: kellyFull(t.model, t.dec),
    };
  });

  /* ---- match market (group stage marquee fixtures) -------------------- */
  // outcome probs: home win / draw / away win
  const rawMatches = [
    { id: "m1", home: "ESP", away: "CRO", group: "B", day: "Jun 13", time: "18:00", venue: "Mercedes-Benz Stadium · Atlanta",
      odds: [1.62, 4.0, 5.8], model: [0.64, 0.22, 0.14], conf: 78 },
    { id: "m2", home: "ARG", away: "NGA", group: "A", day: "Jun 13", time: "21:00", venue: "Estadio Azteca · Mexico City",
      odds: [1.40, 4.6, 8.5], model: [0.74, 0.18, 0.08], conf: 81 },
    { id: "m3", home: "ENG", away: "USA", group: "B", day: "Jun 14", time: "15:00", venue: "MetLife Stadium · New York",
      odds: [1.78, 3.7, 4.8], model: [0.50, 0.25, 0.25], conf: 64 },
    { id: "m4", home: "BRA", away: "MAR", group: "C", day: "Jun 14", time: "18:00", venue: "SoFi Stadium · Los Angeles",
      odds: [1.55, 4.1, 6.2], model: [0.58, 0.24, 0.18], conf: 71 },
    { id: "m5", home: "FRA", away: "DEN", group: "E", day: "Jun 15", time: "21:00", venue: "Lumen Field · Seattle",
      odds: [1.50, 4.2, 6.8], model: [0.70, 0.18, 0.12], conf: 76 },
    { id: "m6", home: "GER", away: "JPN", group: "F", day: "Jun 15", time: "18:00", venue: "Lincoln Financial Field · Philadelphia",
      odds: [1.72, 3.9, 5.0], model: [0.52, 0.26, 0.22], conf: 63 },
    { id: "m7", home: "POR", away: "MEX", group: "H", day: "Jun 16", time: "21:00", venue: "AT&T Stadium · Dallas",
      odds: [1.68, 3.8, 5.4], model: [0.61, 0.22, 0.17], conf: 69 },
    { id: "m8", home: "NED", away: "SEN", group: "D", day: "Jun 16", time: "15:00", venue: "BMO Field · Toronto",
      odds: [1.70, 3.8, 5.2], model: [0.55, 0.25, 0.20], conf: 60 },
  ];

  const OUTCOME = ["home", "draw", "away"];
  const matches = rawMatches.map((m) => {
    const legs = m.odds.map((dec, i) => ({
      kind: OUTCOME[i],
      label: i === 0 ? NAME[m.home] : i === 1 ? "Draw" : NAME[m.away],
      dec,
      implied: impliedProb(dec),
      model: m.model[i],
      edge: m.model[i] - impliedProb(dec),
      ev: ev(m.model[i], dec),
      kelly: kellyFull(m.model[i], dec),
    }));
    // pick best EV leg as the recommended bet
    const best = legs.reduce((a, b) => (b.ev > a.ev ? b : a));
    return {
      ...m,
      homeName: NAME[m.home], awayName: NAME[m.away],
      homeColors: C[m.home], awayColors: C[m.away],
      legs, best,
    };
  });

  /* ---- bankroll + bet history ----------------------------------------- */
  const bankroll = {
    currency: "$",
    start: 1000,
    balance: 1240,
    history: [
      { label: "Open", v: 1000 },
      { label: "M1", v: 1000 },
      { label: "M2", v: 1085 },
      { label: "M3", v: 1040 },
      { label: "M4", v: 1162 },
      { label: "M5", v: 1118 },
      { label: "M6", v: 1240 },
    ],
  };

  const settledBets = [
    { id: "s1", pick: "Spain to win Group B", team: "ESP", stake: 40, dec: 1.45, result: "won", pnl: 18 },
    { id: "s2", pick: "Argentina ML vs Nigeria", team: "ARG", stake: 55, dec: 1.40, result: "won", pnl: 22 },
    { id: "s3", pick: "Over 2.5 — France/Denmark", team: "FRA", stake: 30, dec: 1.90, result: "lost", pnl: -30 },
    { id: "s4", pick: "Brazil ML vs Morocco", team: "BRA", stake: 45, dec: 1.55, result: "won", pnl: 25 },
    { id: "s5", pick: "Germany ML vs Japan", team: "GER", stake: 35, dec: 1.72, result: "lost", pnl: -35 },
    { id: "s6", pick: "Portugal -1.5 vs Mexico", team: "POR", stake: 25, dec: 2.10, result: "won", pnl: 28 },
  ];

  // group letters in order
  const GROUP_LETTERS = ["A","B","C","D","E","F","G","H","I","J","K","L"];

  window.WC = {
    teams, matches, bankroll, settledBets,
    RISK, NAME, COLORS: C, GROUP_LETTERS,
    impliedProb, ev, kellyFull, formatOdds, recommendedStake,
  };
})();
