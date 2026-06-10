/* ============================================================================
   Dashboard.jsx — Today's Best Value screen
   ========================================================================== */
import React from 'react';
import { Icon, EdgeBadge, VerdictChip, ProbCompare, AreaChart, BalanceNumber, fmtPct, fmtSign, fmtMoney } from '../components/primitives.jsx';
import { TeamTokenAuto } from '../components/TeamTokenWithColors.jsx';
import { recommendedStake, formatOdds, buildBankrollHistory } from '../api.js';

function buildValuePlays(outright, matches, bankrollBalance, riskKey) {
  const out = outright.map((t) => ({
    key: 'o:' + t.code, type: 'Outright', market: 'To win the World Cup',
    code: t.code, name: t.name, dec: t.dec, model: t.model, implied: t.implied,
    ev: t.ev, conf: t.conf,
    stake: recommendedStake(t.model, t.dec, bankrollBalance, riskKey),
  }));
  const mt = matches
    .filter((m) => m.best)
    .map((m) => ({
      key: 'm:' + m.id + ':' + m.best.kind, type: 'Match',
      market: (m.best.label || 'Result') + ' — ' + m.homeName + ' v ' + m.awayName,
      code: m.best.kind === 'away' ? m.away : m.home,
      name: m.best.label || 'Match result',
      dec: m.best.dec, model: m.best.model, implied: m.best.implied,
      ev: m.best.ev, conf: m.conf,
      stake: recommendedStake(m.best.model, m.best.dec, bankrollBalance, riskKey),
    }));
  return [...out, ...mt].filter((p) => p.ev != null).sort((a, b) => b.ev - a.ev);
}

export default function Dashboard({ outright, matches, bankroll, riskKey, oddsFmt, placed, onAdd, go }) {
  if (!outright.length && !matches.length) {
    return (
      <div className="screen dash">
        <div className="empty">No data available yet. Start the backend and run a refresh.</div>
      </div>
    );
  }

  const balance = bankroll?.balance ?? 1000;
  const start = bankroll?.start ?? 1000;
  const currency = bankroll?.currency ?? '$';
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
        <div className="empty">No value plays found yet.</div>
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
                <b className="mono">{fmtMoney(hero.stake, currency)}</b>
                <span className="ret">to return {fmtMoney(hero.stake * hero.dec, currency)}</span>
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
            <span className="head-note">ranked by expected value</span></div>
          <div className="vb-list">
            {rest.map((p, i) => (
              <div className="vb-row" key={p.key}>
                <span className="vb-rank mono">{String(i + 2).padStart(2, '0')}</span>
                <TeamTokenAuto code={p.code} size={32} />
                <div className="vb-main">
                  <div className="vb-name">{p.name}<span className={`vb-type t-${p.type.toLowerCase()}`}>{p.type}</span></div>
                  <div className="vb-market">{p.market}</div>
                </div>
                <div className="vb-odds mono">{formatOdds(p.dec, oddsFmt)}</div>
                <EdgeBadge value={p.ev} />
                <VerdictChip ev={p.ev} />
                <button className={`btn ghost sm ${placed.has(p.key) ? 'is-done' : ''}`}
                  disabled={placed.has(p.key)} onClick={() => onAdd(p)}>
                  {placed.has(p.key) ? '✓' : '+ ' + fmtMoney(p.stake, currency)}
                </button>
              </div>
            ))}
          </div>
        </div>

        {/* upcoming fixtures */}
        <div className="card upcoming">
          <div className="card-head"><span>Next Fixtures</span>
            <button className="link-btn" onClick={() => go('matches')}>Analyze all <Icon name="arrow" size={13} /></button>
          </div>
          <div className="up-list">
            {matches.slice(0, 4).map((m) => (
              m.best ? (
                <button className="up-row" key={m.id} onClick={() => go('matches', m.id)}>
                  <div className="up-teams">
                    <TeamTokenAuto code={m.home} size={28} radius={7} />
                    <span className="up-vs mono">v</span>
                    <TeamTokenAuto code={m.away} size={28} radius={7} />
                  </div>
                  <div className="up-when">
                    <span className="mono">{m.day} · {m.time}</span>
                    <span className="up-pick">Pick: {m.best.label}</span>
                  </div>
                  <EdgeBadge value={m.best.ev} size="sm" />
                </button>
              ) : null
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
