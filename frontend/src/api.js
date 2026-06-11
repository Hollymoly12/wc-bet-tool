/* ============================================================================
   api.js — data layer: fetches from VITE_API_URL and adapts shapes for UI
   ========================================================================== */

const BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

async function get(path) {
  const res = await fetch(`${BASE}${path}`);
  if (!res.ok) throw new Error(`${res.status} ${res.statusText} — ${path}`);
  return res.json();
}

async function post(path, body) {
  const res = await fetch(`${BASE}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(`${res.status} ${res.statusText} — ${path}`);
  return res.json();
}

async function del(path) {
  const res = await fetch(`${BASE}${path}`, { method: 'DELETE' });
  if (!res.ok && res.status !== 204) throw new Error(`${res.status} ${res.statusText} — ${path}`);
  return res.status === 204 ? null : res.json();
}

// ── Outright rows ──────────────────────────────────────────────────────────
// API returns: [{code, name, group, colors, dec, model, implied, fair, edge, ev, kelly, verdict, str}]
// We add a synthetic `conf` (0-100) for UI compat
export async function fetchOutright() {
  const rows = await get('/outright');
  return rows.map(adaptOutrightRow);
}

function adaptOutrightRow(r) {
  return {
    ...r,
    conf: computeConf(r.model),
  };
}

// ── Team name cache (populated by fetchTeams) ──────────────────────────────
let _teamNameCache = {};
export function setTeamNameCache(teams) {
  _teamNameCache = {};
  for (const t of teams) _teamNameCache[t.code] = t.name;
}
function teamName(code) { return _teamNameCache[code] || code; }

// ── Matches ────────────────────────────────────────────────────────────────
// API returns MatchSummary + legs + best + markets (raw model probs dict)
export async function fetchMatches() {
  const rows = await get('/matches');
  return rows.map(adaptMatch);
}

export async function fetchMatch(id) {
  const row = await get(`/matches/${encodeURIComponent(id)}`);
  return adaptMatch(row);
}

function adaptMatch(m) {
  // Resolve full names from cache if API returned codes as names
  const homeName = (m.homeName && m.homeName !== m.home) ? m.homeName : teamName(m.home);
  const awayName = (m.awayName && m.awayName !== m.away) ? m.awayName : teamName(m.away);

  // Enrich legs with UI labels, keys, team code
  const legs = (m.legs || []).map((leg) => ({
    ...leg,
    label: kindLabel(leg.kind, homeName, awayName),
    key: `m:${m.id}:${leg.kind}`,
    code: leg.kind === 'away' ? m.away : m.home,
  }));

  // best comes from API; enrich it too
  let best = m.best ? {
    ...m.best,
    label: kindLabel(m.best.kind, homeName, awayName),
    key: `m:${m.id}:${m.best.kind}`,
    code: m.best.kind === 'away' ? m.away : m.home,
  } : (legs.length > 0 ? legs.reduce((a, b) => (b.ev > a.ev ? b : a), legs[0]) : null);

  // markets: the API returns a raw dict of model probs (no EV), we skip showing
  // the deep markets table in seed mode since there are no odds to de-vig.
  // We expose an empty array so the component renders gracefully.
  const markets = buildMarketsFromDict(m.markets, m, legs);
  const topMarket = findTopMarket(markets) || best;

  // xg: may be a dict {home, away, total} or array
  let xgArr = null;
  if (m.xg) {
    if (Array.isArray(m.xg)) xgArr = m.xg;
    else if (typeof m.xg === 'object') xgArr = [m.xg.home ?? 0, m.xg.away ?? 0];
  }

  return {
    ...m,
    homeName,
    awayName,
    legs,
    best,
    markets,
    topMarket,
    conf: m.conf ?? computeConf(best?.model ?? 0.33),
    h2h: m.h2h || [],
    xg: xgArr,
    mu: xgArr ? xgArr[0] : null,
  };
}

function kindLabel(kind, homeName, awayName) {
  if (kind === 'home') return homeName || 'Home';
  if (kind === 'away') return awayName || 'Away';
  if (kind === 'draw') return 'Draw';
  return kind;
}

// Build a simple market display from the raw model-probs dict.
// The seed API markets dict has keys like "1x2", "totals", "btts"
// containing raw model probs (not de-vigged with book odds).
// We only expose the 1X2 market since that's what has EV from the legs.
function buildMarketsFromDict(marketsDict, m, legs) {
  if (!marketsDict || typeof marketsDict !== 'object' || !legs.length) return [];

  const groups = [];

  // 1X2 — use the pre-computed legs which already have EV
  const resultSels = legs.filter((l) => ['home', 'draw', 'away'].includes(l.kind));
  if (resultSels.length) {
    groups.push({
      cat: 'Match Result',
      note: '1X2',
      sels: resultSels.map((l) => ({
        ...l,
        cat: 'Match Result',
        key: `mk:${m.id}:1x2:${l.kind}`,
      })),
    });
  }

  // Totals — model probs only (no EV without book odds)
  const totals = marketsDict.totals;
  if (totals && typeof totals === 'object') {
    const sels = Object.entries(totals)
      .filter(([k]) => k.startsWith('over_'))
      .slice(0, 4)
      .map(([k, prob]) => ({
        label: k.replace('_', ' ').replace('.', '.'),
        kind: k,
        dec: 1 / prob,
        model: prob,
        implied: prob,
        fair: prob,
        edge: 0,
        ev: 0,
        kelly: 0,
        verdict: 'pass',
        cat: 'Total Goals',
        key: `mk:${m.id}:totals:${k}`,
        code: m.home,
      }));
    if (sels.length) groups.push({ cat: 'Total Goals', note: 'model probability', sels });
  }

  return groups;
}

function findTopMarket(markets) {
  let top = null;
  for (const group of markets) {
    for (const s of group.sels) {
      if (!top || (s.ev != null && s.ev > (top.ev ?? -Infinity))) {
        top = { ...s, cat: group.cat };
      }
    }
  }
  return top;
}

// ── Groups ─────────────────────────────────────────────────────────────────
export async function fetchGroups() {
  return get('/groups');
}

// ── Bracket ────────────────────────────────────────────────────────────────
export async function fetchBracket() {
  return get('/bracket');
}

// ── Teams ──────────────────────────────────────────────────────────────────
export async function fetchTeams() {
  return get('/teams');
}

export async function fetchTeam(code) {
  return get(`/teams/${encodeURIComponent(code)}`);
}

// ── Players ────────────────────────────────────────────────────────────────
export async function fetchPlayers(code) {
  return get(`/players?code=${encodeURIComponent(code)}`);
}

export async function fetchPlayer(id) {
  return get(`/players/${id}`);
}

// ── News ───────────────────────────────────────────────────────────────────
export async function fetchNews(code) {
  return get(`/news/${encodeURIComponent(code)}`);
}

// ── Bankroll ───────────────────────────────────────────────────────────────
export async function fetchBankroll() {
  return get('/bankroll');
}

export async function placeBet(bet) {
  return post('/bankroll/bets', {
    key: bet.key,
    pick: bet.name || bet.market,
    team: bet.code || '',
    market: bet.market || '',
    stake: bet.stake,
    dec: bet.dec,
  });
}

export async function deleteBet(id) {
  return del(`/bankroll/bets/${id}`);
}

export async function settleBet(id, result) {
  return post(`/bankroll/bets/${id}/settle`, { result });
}

// ── Meta ───────────────────────────────────────────────────────────────────
export async function fetchMeta() {
  return get('/meta');
}

// ── Helpers ────────────────────────────────────────────────────────────────
function computeConf(model) {
  const sharpness = Math.abs(model - 0.5) * 2;
  return Math.round(Math.max(0, Math.min(1, 0.45 + 0.45 * sharpness)) * 100);
}

// ── Betting math (mirrors backend/app/models/betting.py) ──────────────────
export const RISK = {
  conservative: { label: 'Conservative', mult: 0.25, cap: 0.04 },
  balanced:     { label: 'Balanced',     mult: 0.50, cap: 0.07 },
  aggressive:   { label: 'Aggressive',   mult: 1.00, cap: 0.12 },
};

// Stage-aware staking params (mirrors backend STAGE_STAKING)
export const STAGE_STAKING = {
  group:    { mult: 0.25, cap: 0.03, label: 'Group · ¼-Kelly' },
  knockout: { mult: 0.50, cap: 0.07, label: 'Knockout · ½-Kelly' },
};

function kellyFull(p, dec) {
  const b = dec - 1;
  if (b <= 0) return 0;
  return Math.max(0, (b * p - (1 - p)) / b);
}

// Legacy risk-profile stake (kept for backward compat; app now prefers staged)
export function recommendedStake(p, dec, bankroll, riskKey = 'balanced') {
  const r = RISK[riskKey] || RISK.balanced;
  const rawF = kellyFull(p, dec) * r.mult;
  const f = Math.min(rawF, r.cap);
  const stake = Math.round(bankroll * f);
  // Ensure a genuine positive-edge bet doesn't round to €0
  if (stake === 0 && rawF > 0 && bankroll * f >= 0.5) return 1;
  return stake;
}

/**
 * Stage-aware staking: group = ¼-Kelly capped 3%; knockout = ½-Kelly capped 7%.
 * An optional riskScaler (Conservative=0.7 / Balanced=1.0 / Aggressive=1.3)
 * scales the output but is always clamped to the stage cap.
 */
export function recommendedStakeStaged(p, dec, bankroll, stage = 'group', riskScaler = 1.0) {
  const params = STAGE_STAKING[stage] || STAGE_STAKING.group;
  const rawF = kellyFull(p, dec) * params.mult;
  const f = Math.min(rawF * riskScaler, params.cap);
  const stake = Math.round(bankroll * f);
  if (stake === 0 && rawF > 0 && bankroll * f >= 0.5) return 1;
  return stake;
}

/** Return the STAGE_STAKING label for display, e.g. "Group · ¼-Kelly". */
export function stageLabel(stage = 'group') {
  return (STAGE_STAKING[stage] || STAGE_STAKING.group).label;
}

/** Pick-ranking score = expected value at the offered odds (mirrors backend). */
export function valueScore(model, dec) {
  return model * dec - 1;
}

/** Returns true when a selection is a recommendable pick: PROFITABLE at the
 *  offered odds (EV ≥ 1%), a likely-enough outcome (≥33%), not a longshot (≤4.0).
 *  Mirrors the backend is_value_pick. */
export const EV_VALUE = 0.01;
export function isValuePick(model, dec) {
  return model >= 0.33 && dec <= 4.0 && (model * dec - 1) >= EV_VALUE;
}

export function formatOdds(dec, fmt = 'decimal') {
  if (fmt === 'decimal') return dec.toFixed(2);
  if (fmt === 'american') {
    if (dec >= 2) return '+' + Math.round((dec - 1) * 100);
    return '-' + Math.round(100 / (dec - 1));
  }
  if (fmt === 'fractional') {
    const num = dec - 1;
    const gcd = (a, b) => (b < 0.0001 ? a : gcd(b, a % b));
    const denom = 100;
    const numerator = Math.round(num * denom);
    const g = gcd(numerator, denom);
    return `${numerator / g}/${denom / g}`;
  }
  return dec.toFixed(2);
}

// Build bankroll history from settled bets (fallback sparkline)
export function buildBankrollHistory(start, settledBets) {
  let balance = start;
  const history = [{ v: start, label: 'Start' }];
  for (const bet of settledBets) {
    balance += bet.pnl || 0;
    history.push({ v: balance, label: '' });
  }
  history[history.length - 1] = { ...history[history.length - 1], label: 'Now' };
  return history;
}
