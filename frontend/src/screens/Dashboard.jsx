/* ============================================================================
   Dashboard.jsx — Today's Best Value screen
   ========================================================================== */
import React from 'react';
import { Icon, EdgeBadge, VerdictChip, ProbCompare, AreaChart, BalanceNumber, fmtPct, fmtSign, fmtMoney } from '../components/primitives.jsx';
import { TeamTokenAuto } from '../components/TeamTokenWithColors.jsx';
import {
  recommendedStakeStaged, stageLabel,
  valueScore, isValuePick,
  formatOdds, buildBankrollHistory,
} from '../api.js';

// Risk selector scales the staged stake (Conservative ×0.7 / Balanced ×1.0 / Aggressive ×1.3)
const RISK_SCALER = { conservative: 0.7, balanced: 1.0, aggressive: 1.3 };

/**
 * Build the value-play list using balanced-value filtering:
 *   - model >= 0.33 AND dec <= 4.0 AND edge > 0
 * Ranked by value_score = edge * model (not raw EV).
 * Outright rows are filtered to those that pass (rare: champion prob rarely ≥ 33%).
 * Match rows come from the API's pre-computed best leg (which already passed the filter).
 */
function buildValuePlays(outright, matches, bankrollBalance, riskKey) {
  const scaler = RISK_SCALER[riskKey] ?? 1.0;

  // Outright plays: apply same balanced-value filter
  const out = outright
    .filter((t) => isValuePick(t.model, t.dec, t.edge ?? (t.model - t.fair)))
    .map((t) => {
      const edge = t.edge ?? (t.model - (t.fair ?? t.implied));
      return {
        key: 'o:' + t.code, type: 'Outright', market: 'To win the World Cup',
        code: t.code, name: t.name, dec: t.dec, model: t.model, implied: t.implied,
        ev: t.ev, edge, fair: t.fair ?? t.implied, conf: t.conf, verdict: t.verdict,
        stage: 'group', // outright bets use conservative group params
        valueScore: valueScore(t.model, t.fair ?? t.implied),
        stake: recommendedStakeStaged(t.model, t.dec, bankrollBalance, 'group', scaler),
      };
    });

  // Match plays: API pre-selects the best value leg per match via value_score filter.
  // m.best is null when no leg passes the filter — we skip those.
  const mt = matches
    .filter((m) => m.best && isValuePick(m.best.model, m.best.dec, m.best.edge ?? 0))
    .map((m) => {
      const leg = m.best;
      const edge = leg.edge ?? (leg.model - (leg.fair ?? leg.implied));
      const stage = m.stage || 'group';
      return {
        key: 'm:' + m.id + ':' + leg.kind, type: 'Match',
        market: (leg.label || 'Result') + ' — ' + m.homeName + ' v ' + m.awayName,
        code: leg.kind === 'away' ? m.away : m.home,
        name: leg.label || 'Match result',
        dec: leg.dec, model: leg.model, implied: leg.implied,
        ev: leg.ev, edge, fair: leg.fair ?? leg.implied, conf: m.conf,
        stage, verdict: leg.verdict,
        valueScore: valueScore(leg.model, leg.fair ?? leg.implied),
        stake: recommendedStakeStaged(leg.model, leg.dec, bankrollBalance, stage, scaler),
      };
    });

  // Sort by value_score descending (edge × probability — penalises longshots)
  return [...out, ...mt]
    .filter((p) => p.ev != null)
    .sort((a, b) => b.valueScore - a.valueScore);
}

export default function Dashboard({ outright, matches, bankroll, riskKey, oddsFmt, placed, onAdd, go }) {
  if (!outright.length && !matches.length) {
    return (
      <div className="screen dash">
        <div className="empty">No data available yet. Start the backend and run a refresh.</div>
      </div>
    );
  }

  const balance = bankroll?.balance ?? 100;
  const start = bankroll?.start ?? 100;
  const currency = bankroll?.currency ?? '€';
  const settled = bankroll?.settled_bets ?? [];
  const open = bankroll?.open_bets ?? [];

  const plays = buildValuePlays(outright, matches, balance, riskKey);
  const hero = plays[0];
  const rest = plays.slice(1, 7);
  const roi = start > 0 ? (balance - start) / start : 0;
  const openStaked = open.reduce((s, b) => s + (b.stake || 0), 0);
  const history = buildBankrollHistory(start, settled);

  if (!hero) {
    return (
      <div className="screen dash">
        <div className="screen-head">
          <div><div className="eyebrow">Command Center</div><h1>Dashboard</h1></div>
        </div>
        <div className="empty">No strong value right now — no selection clears the model ≥ 33% / odds ≤ 4.0 / positive-edge filter.</div>
      </div>
    );
  }

  const today = new Date().toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric', year: 'numeric' }).toUpperCase();

  return (
    <div className="screen dash">
      <div className="screen-head">
        <div>
          <div className="eyebrow">Command Center · Group Stage</div>
          <h1>Today&rsquo;s Best Value</h1>
        </div>
        <div className="head-meta">
          <span className="kicker">{today}</span>
          <span className="live-dot" /> {matches.length} fixtures tracked
        </div>
      </div>

      <div className="dash-grid">
        {/* hero value play */}
        <div className="card hero-play">
          <div className="hero-tag"><Icon name="bolt" size={13} /> TOP VALUE PLAY</div>
          <div className="hero-body">
            <TeamTokenAuto code={hero.code} size={64} radius={16} />
            <div className="hero-info">
              <div className="hero-name">{hero.name}</div>
              <div className="hero-market">{hero.market}</div>
              <div className="hero-stats">
                <div className="hs"><label>BOOK ODDS</label><b className="mono">{formatOdds(hero.dec, oddsFmt)}</b></div>
                <div className="hs"><label>MODEL WIN%</label><b className="mono">{fmtPct(hero.model)}</b></div>
                <div className="hs"><label>EXPECTED VALUE</label><b className="mono pos">{fmtSign(hero.ev)}</b></div>
                <div className="hs"><label>CONFIDENCE</label><b className="mono">{hero.conf}/100</b></div>
              </div>
            </div>
          </div>
          <div className="hero-foot">
            <ProbCompare implied={hero.implied} model={hero.model} />
            <div className="hero-cta">
              <div className="rec-stake">
                <label>RECOMMENDED STAKE</label>
                <b className="mono">{fmtMoney(hero.stake, currency)}<span className="stake-pct"> ({balance > 0 ? Math.round(hero.stake / balance * 100) : 0}% of bankroll)</span></b>
                <span className="ret">to return {fmtMoney(hero.stake * hero.dec, currency)}</span>
                <span className="stage-tag">{stageLabel(hero.stage)}</span>
              </div>
              <button className={`btn primary ${placed.has(hero.key) ? 'is-done' : ''}`}
                disabled={placed.has(hero.key)} onClick={() => onAdd(hero)}>
                {placed.has(hero.key) ? 'Added ✓' : 'Place Bet'}
              </button>
            </div>
          </div>
        </div>

        {/* bankroll snapshot */}
        <div className="card bankroll-snap" onClick={() => go('bankroll')}>
          <div className="card-head"><span>Bankroll</span><Icon name="arrow" size={15} /></div>
          <BalanceNumber value={balance} sym={currency} />
          <div className={`roi ${roi >= 0 ? 'pos' : 'neg'}`}>{fmtSign(roi)} ROI · all-time</div>
          <AreaChart data={history} w={300} h={96} />
          <div className="snap-row">
            <div><label>OPEN STAKES</label><b className="mono">{fmtMoney(openStaked, currency)}</b></div>
            <div><label>OPEN BETS</label><b className="mono">{open.length}</b></div>
          </div>
        </div>

        {/* value leaderboard */}
        <div className="card value-board">
          <div className="card-head"><span>Value Leaderboard</span>
            <span className="head-note">ranked by edge × probability</span></div>
          <div className="vb-list">
            {rest.length === 0 && (
              <div className="empty-note">No further value picks pass the filter right now.</div>
            )}
            {rest.map((p, i) => (
              <div className="vb-row" key={p.key}>
                <span className="vb-rank mono">{String(i + 2).padStart(2, '0')}</span>
                <TeamTokenAuto code={p.code} size={32} />
                <div className="vb-main">
                  <div className="vb-name">{p.name}<span className={`vb-type t-${p.type.toLowerCase()}`}>{p.type}</span></div>
                  <div className="vb-market">{p.market}</div>
                  <div className="vb-stage-tag">{stageLabel(p.stage)}</div>
                </div>
                <div className="vb-odds mono">{formatOdds(p.dec, oddsFmt)}</div>
                <EdgeBadge value={p.ev} />
                <VerdictChip verdict={p.verdict} ev={p.ev} />
                <div className="vb-stake-wrap">
                  <span className="vb-stake-amt mono">{fmtMoney(p.stake, currency)}</span>
                  <span className="vb-stake-pct">({balance > 0 ? Math.round(p.stake / balance * 100) : 0}%)</span>
                </div>
                <button className={`btn ghost sm ${placed.has(p.key) ? 'is-done' : ''}`}
                  disabled={placed.has(p.key)} onClick={() => onAdd(p)}>
                  {placed.has(p.key) ? '✓' : 'Bet'}
                </button>
              </div>
            ))}
          </div>
        </div>

        {/* upcoming fixtures — sorted chronologically by kickoff */}
        <div className="card upcoming">
          <div className="card-head"><span>Next Fixtures</span>
            <button className="link-btn" onClick={() => go('matches')}>Analyze all <Icon name="arrow" size={13} /></button>
          </div>
          <div className="up-list">
            {[...matches]
              .filter((m) => m.best)
              .sort((a, b) => {
                if (a.kickoff && b.kickoff) return new Date(a.kickoff) - new Date(b.kickoff);
                if (a.kickoff) return -1;
                if (b.kickoff) return 1;
                return 0;
              })
              .slice(0, 4)
              .map((m) => {
                const kickoffLabel = m.kickoff
                  ? new Date(m.kickoff).toLocaleString('en-US', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit', timeZone: 'UTC', hour12: false }).replace(',', ' ·')
                  : (m.day && m.time ? `${m.day} · ${m.time}` : '');
                return (
                  <button className="up-row" key={m.id} onClick={() => go('matches', m.id)}>
                    <div className="up-teams">
                      <TeamTokenAuto code={m.home} size={28} radius={7} />
                      <span className="up-vs mono">v</span>
                      <TeamTokenAuto code={m.away} size={28} radius={7} />
                    </div>
                    <div className="up-when">
                      <span className="mono">{kickoffLabel}</span>
                      <span className="up-pick">Pick: {m.best.label}</span>
                    </div>
                    <EdgeBadge value={m.best.ev} size="sm" />
                  </button>
                );
              })
            }
          </div>
        </div>
      </div>
    </div>
  );
}
