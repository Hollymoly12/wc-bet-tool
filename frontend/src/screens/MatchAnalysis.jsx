/* ============================================================================
   MatchAnalysis.jsx — Match list + detail with markets, H2H, news
   ========================================================================== */
import React from 'react';
import { Icon, EdgeBadge, VerdictChip, ProbCompare, FormDots, fmtPct, fmtSign, fmtMoney } from '../components/primitives.jsx';
import { TeamTokenAuto } from '../components/TeamTokenWithColors.jsx';
import { recommendedStakeStaged, stageLabel, formatOdds } from '../api.js';

const RISK_SCALER = { conservative: 0.7, balanced: 1.0, aggressive: 1.3 };

const NEWS_TAG_LABELS = { injury: 'INJURY', form: 'FORM', lineup: 'LINEUP', susp: 'SUSP', intel: 'INTEL' };

function NewsItemComp({ n }) {
  return (
    <div className="news-item">
      <span className={`news-tag t-${n.tag}`}>{NEWS_TAG_LABELS[n.tag] || n.tag.toUpperCase()}</span>
      <div className="news-b"><p>{n.text}</p><time>{n.published_at ? new Date(n.published_at).toLocaleDateString() : ''}</time></div>
    </div>
  );
}

function H2HCard({ h2h }) {
  if (!h2h || !h2h.length) return null;
  return (
    <div className="card h2h">
      <div className="card-head"><span>Head to Head</span><span className="head-note">recent meetings</span></div>
      <div className="h2h-list">
        {h2h.map((h, i) => (
          <div className="h2h-row" key={i}>
            <span className="h2h-d mono">{h.d || h.date || ''}</span>
            <span className="h2h-s mono">{h.s || h.score || ''}</span>
            <span className="h2h-n">{h.n || h.note || ''}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

function MarketRow({ s, matchId, home, away, homeName, awayName, riskKey, oddsFmt, bankroll, placed, onAdd }) {
  const stake = recommendedStake(s.model, s.dec, bankroll?.balance ?? 100, riskKey);
  const currency = bankroll?.currency ?? '€';
  const key = s.key || `mk:${matchId}:${s.cat}:${s.kind || s.label}`;
  return (
    <div className={`mk-row`}>
      <span className="mk-label">{s.label}</span>
      <span className="mk-odds mono">{formatOdds(s.dec, oddsFmt)}</span>
      <span className="mk-model mono dim">{fmtPct(s.model)}</span>
      <span className="r"><EdgeBadge value={s.ev} size="sm" /></span>
      <span className="r"><VerdictChip ev={s.ev} /></span>
      <span className="mk-stake mono">{s.ev > 0 ? fmtMoney(stake, currency) : '—'}</span>
      <button className={`btn ghost sm ${placed.has(key) ? 'is-done' : ''}`}
        disabled={placed.has(key) || s.ev <= 0}
        onClick={() => onAdd({
          key, name: s.label, code: s.kind === 'away' ? away : home,
          market: `${s.cat || 'Market'} · ${s.label} — ${homeName} v ${awayName}`,
          dec: s.dec, model: s.model, ev: s.ev, stake,
        })}>
        {placed.has(key) ? '✓' : 'Bet'}
      </button>
    </div>
  );
}

const MK_TABS = [['All', 'All'], ['Match Result', 'Result'], ['Double Chance', 'Dbl Chance'],
  ['Draw No Bet', 'DNB'], ['Total Goals', 'Goals'], ['Both Teams Score', 'BTTS']];

export default function MatchAnalysis({ matches, teamForms, bankroll, riskKey, oddsFmt, placed, onAdd, focusId, goTeam }) {
  // Chronological order by kickoff (matches without a kickoff go last).
  const sortedMatches = React.useMemo(
    () => [...matches].sort((a, b) => {
      if (!a.kickoff && !b.kickoff) return 0;
      if (!a.kickoff) return 1;
      if (!b.kickoff) return -1;
      return new Date(a.kickoff) - new Date(b.kickoff);
    }),
    [matches],
  );
  const firstId = sortedMatches[0]?.id;
  const [sel, setSel] = React.useState(focusId || firstId || null);
  const [mkCat, setMkCat] = React.useState('All');

  React.useEffect(() => {
    if (focusId) setSel(focusId);
  }, [focusId]);

  React.useEffect(() => {
    if (!sel && firstId) setSel(firstId);
  }, [firstId]);

  const m = matches.find((x) => x.id === sel) || sortedMatches[0];
  const currency = bankroll?.currency ?? '€';

  if (!matches.length) {
    return (
      <div className="screen match">
        <div className="screen-head">
          <div><div className="eyebrow">Single Match Model</div><h1>Match Analysis</h1></div>
        </div>
        <div className="empty">No match data available yet.</div>
      </div>
    );
  }

  const filteredMarkets = m
    ? (m.markets || []).filter((c) => mkCat === 'All' || c.cat === mkCat)
    : [];

  const homeForm = m ? (teamForms[m.home] || '') : '';
  const awayForm = m ? (teamForms[m.away] || '') : '';

  return (
    <div className="screen match">
      <div className="screen-head">
        <div>
          <div className="eyebrow">Single Match Model</div>
          <h1>Match Analysis</h1>
        </div>
      </div>

      <div className="match-layout">
        {/* match list sidebar */}
        <div className="match-list">
          {sortedMatches.map((x) => (
            <button key={x.id} className={`ml-row ${x.id === sel ? 'on' : ''}`} onClick={() => setSel(x.id)}>
              <div className="ml-teams">
                <TeamTokenAuto code={x.home} size={26} radius={6} />
                <TeamTokenAuto code={x.away} size={26} radius={6} />
              </div>
              <div className="ml-info">
                <div className="ml-name">{x.home} <span className="dim">v</span> {x.away}</div>
                <div className="ml-when mono">{x.kickoff
                  ? new Date(x.kickoff).toLocaleString('en-US', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit', timeZone: 'UTC', hour12: false }).replace(',', ' ·')
                  : `${x.day} · ${x.time}`}</div>
              </div>
              {x.best && <EdgeBadge value={x.best.ev} size="sm" />}
            </button>
          ))}
        </div>

        {/* match detail */}
        {m && (
          <div className="match-detail">
            {/* fixture header */}
            <div className="card md-head">
              <div className="md-fixture">
                <div className="md-team clickable" onClick={() => goTeam(m.home)}>
                  <TeamTokenAuto code={m.home} size={56} radius={14} />
                  <div>
                    <div className="md-tname">{m.homeName}</div>
                    <FormDots form={homeForm} size={13} />
                  </div>
                </div>
                <div className="md-vs">
                  <span className="mono">VS</span>
                  <span className="md-conf"><Icon name="target" size={12} /> {m.conf}/100 conf</span>
                </div>
                <div className="md-team right clickable" onClick={() => goTeam(m.away)}>
                  <div>
                    <div className="md-tname">{m.awayName}</div>
                    <FormDots form={awayForm} size={13} />
                  </div>
                  <TeamTokenAuto code={m.away} size={56} radius={14} />
                </div>
              </div>
              <div className="md-meta">
                <span><Icon name="clock" size={13} /> {m.day} · {m.time} ET</span>
                <span><Icon name="pin" size={13} /> {m.venue}</span>
                <span className="grp-tag">Group {m.group}</span>
              </div>
            </div>

            {/* outcome grid (1X2 legs) */}
            {m.legs && m.legs.length > 0 && (
              <div className="outcome-grid">
                {m.legs.map((leg) => {
                  const isBest = m.best && leg.kind === m.best.kind;
                  // A leg is only a recommendation if it passes the value filter
                  // (model >= 33%, odds <= 4.0, positive edge) — not just EV>0.
                  const isValue = leg.is_value === true;
                  const balance = bankroll?.balance ?? 100;
                  const stake = recommendedStakeStaged(leg.model, leg.dec, balance, m.stage, RISK_SCALER[riskKey] ?? 1.0);
                  const key = `m:${m.id}:${leg.kind}`;
                  return (
                    <div key={leg.kind} className={`card outcome ${isBest ? 'best' : ''}`}>
                      {isBest && <div className="best-flag"><Icon name="bolt" size={11} /> MODEL PICK</div>}
                      <div className="oc-head">
                        <span className="oc-label">{leg.label}</span>
                        <VerdictChip ev={leg.ev} />
                      </div>
                      <div className="oc-odds mono">{formatOdds(leg.dec, oddsFmt)}</div>
                      <ProbCompare implied={leg.implied} model={leg.model} />
                      <div className="oc-ev">
                        <div><label>EXPECTED VALUE</label><EdgeBadge value={leg.ev} size="lg" /></div>
                        <div className="oc-stake"><label>STAKE</label>
                          <b className="mono">{isValue ? fmtMoney(stake, currency) : '—'}</b>
                          {isValue && balance > 0 && (
                            <>
                              <span className="oc-stake-pct">{Math.round(stake / balance * 100)}% · {stageLabel(m.stage)}</span>
                            </>
                          )}</div>
                      </div>
                      <button className={`btn ${isBest ? 'primary' : 'ghost'} ${placed.has(key) ? 'is-done' : ''}`}
                        disabled={placed.has(key) || !isValue}
                        onClick={() => onAdd({ key, name: leg.label, code: leg.kind === 'away' ? m.away : m.home,
                          market: `${leg.label} — ${m.homeName} v ${m.awayName}`,
                          dec: leg.dec, model: leg.model, ev: leg.ev, stake })}>
                        {placed.has(key) ? 'Added ✓' : isValue ? 'Place Bet' : 'No value'}
                      </button>
                    </div>
                  );
                })}
              </div>
            )}

            {/* markets table */}
            {m.markets && m.markets.length > 0 && (
              <div className="card markets">
                <div className="card-head">
                  <span>All Markets</span>
                  {m.topMarket && (
                    <span className="head-note">
                      best edge: {m.topMarket.cat} · {m.topMarket.label} <span className="pos">{fmtSign(m.topMarket.ev)}</span>
                    </span>
                  )}
                </div>
                <div className="seg-group sm mk-tabs">
                  {MK_TABS.map(([id, lbl]) => (
                    <button key={id} className={`seg ${mkCat === id ? 'on' : ''}`} onClick={() => setMkCat(id)}>{lbl}</button>
                  ))}
                </div>
                <div className="mk-table">
                  <div className="mk-row mk-headrow">
                    <span>Selection</span><span>Odds</span><span>Model</span>
                    <span className="r">Edge</span><span className="r">Verdict</span><span>Stake</span><span></span>
                  </div>
                  {filteredMarkets.map((c) => (
                    <React.Fragment key={c.cat}>
                      <div className="mk-group">{c.cat}<span className="mk-group-note">{c.note}</span></div>
                      {(c.sels || []).map((s) => (
                        <MarketRow key={s.key || s.label} s={s}
                          matchId={m.id} home={m.home} away={m.away}
                          homeName={m.homeName} awayName={m.awayName}
                          riskKey={riskKey} oddsFmt={oddsFmt}
                          bankroll={bankroll} placed={placed} onAdd={onAdd} />
                      ))}
                    </React.Fragment>
                  ))}
                </div>
              </div>
            )}

            {/* H2H */}
            {m.h2h && m.h2h.length > 0 && (
              <div className="mid-grid">
                <H2HCard h2h={m.h2h} />
              </div>
            )}

            {/* model read */}
            <div className="card md-note">
              <div className="note-head"><Icon name="target" size={14} /> Model read</div>
              <p>
                The model gives <b>{m.homeName}</b> a {fmtPct(m.legs?.[0]?.model ?? 0)} win probability versus the
                book&rsquo;s implied {fmtPct(m.legs?.[0]?.implied ?? 0)}.
                {m.xg && m.xg.length >= 2 && ` Projected xG: ${m.xg[0].toFixed(2)} – ${m.xg[1].toFixed(2)}.`}
                {m.best && ` The best edge is ${m.best.label} at `}
                {m.best && <span className="pos">{fmtSign(m.best.ev)}</span>}
                {m.best && ` EV, confidence ${m.conf}/100.`}
              </p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
