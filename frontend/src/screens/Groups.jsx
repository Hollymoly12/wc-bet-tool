/* ============================================================================
   Groups.jsx — 12 group cards with win/qualify markets
   ========================================================================== */
import React from 'react';
import { Icon, EdgeBadge, fmtMoney } from '../components/primitives.jsx';
import { TeamTokenAuto } from '../components/TeamTokenWithColors.jsx';
import { recommendedStake, formatOdds } from '../api.js';

function GroupBetChip({ marketKey, label, code, name, letter, mkt, riskKey, bankroll, oddsFmt, placed, onAdd }) {
  const key = `${marketKey}:${code}`;
  const stake = recommendedStake(mkt.model, mkt.dec, bankroll?.balance ?? 1000, riskKey);
  const currency = bankroll?.currency ?? '$';
  const done = placed.has(key);
  return (
    <button
      className={`gbet ${mkt.ev > 0 ? 'val' : ''} ${done ? 'on' : ''}`}
      disabled={done}
      title={`${label} · model ${(mkt.model * 100).toFixed(0)}%`}
      onClick={() => onAdd({ key, name: `${name} · ${label}`, code,
        market: `${name} — ${label} ${letter}`, dec: mkt.dec, model: mkt.model, ev: mkt.ev, stake })}
    >
      <span className="gbet-odds mono">{done ? '✓' : formatOdds(mkt.dec, oddsFmt)}</span>
      <EdgeBadge value={mkt.ev} size="sm" />
    </button>
  );
}

function GroupCard({ g, riskKey, oddsFmt, bankroll, placed, onAdd, goTeam }) {
  return (
    <div className="card group-card">
      <div className="gc-head">
        <span className="gc-letter">{g.letter}</span>
        <span className="gc-title">Group {g.letter}</span>
        <span className="gc-note">top 2 advance · + best 3rd</span>
      </div>
      <div className="gc-cols">
        <span className="gc-c-team">Team</span>
        <span>Win grp</span>
        <span>Qualify</span>
        <span className="gc-c-q">Qual %</span>
      </div>
      {(g.rows || []).map((r) => (
        <div key={r.code} className={`gc-row rank-${r.projRank}`}>
          <span className="gc-rank mono">{r.projRank}</span>
          <button className="gc-team" onClick={() => goTeam(r.code)}>
            <TeamTokenAuto code={r.code} size={26} radius={7} />
            <span>{r.name}</span>
          </button>
          {r.gwMarket && (
            <GroupBetChip marketKey="gw" label="Win Group" code={r.code} name={r.name} letter={g.letter}
              mkt={r.gwMarket} riskKey={riskKey} bankroll={bankroll} oddsFmt={oddsFmt} placed={placed} onAdd={onAdd} />
          )}
          {r.qualMarket && (
            <GroupBetChip marketKey="ql" label="To Qualify" code={r.code} name={r.name} letter={g.letter}
              mkt={r.qualMarket} riskKey={riskKey} bankroll={bankroll} oddsFmt={oddsFmt} placed={placed} onAdd={onAdd} />
          )}
          <span className="gc-qbar">
            <span className="gc-qfill" style={{ width: Math.round(r.qualProb * 100) + '%' }} />
            <em className="mono">{Math.round(r.qualProb * 100)}%</em>
          </span>
        </div>
      ))}
    </div>
  );
}

export default function Groups({ groups, riskKey, oddsFmt, bankroll, placed, onAdd, goTeam }) {
  if (!groups || !groups.length) {
    return (
      <div className="screen groups">
        <div className="screen-head">
          <div><div className="eyebrow">Group Stage</div><h1>Groups</h1></div>
        </div>
        <div className="empty">No group data available yet.</div>
      </div>
    );
  }

  const teamCount = groups.reduce((s, g) => s + (g.rows?.length || 0), 0);

  return (
    <div className="screen groups">
      <div className="screen-head">
        <div>
          <div className="eyebrow">{teamCount} teams · {groups.length} groups</div>
          <h1>Group Stage</h1>
        </div>
        <div className="head-meta">
          <span className="value-pill"><Icon name="bolt" size={12} /> winner &amp; qualify markets</span>
        </div>
      </div>
      <div className="legend-bar">
        <span><i className="lg-dot q1" /> Projected to advance (top 2)</span>
        <span><i className="lg-dot q3" /> Best-3rd contention</span>
        <span className="dim">Ranked by projected points · click a team for its page</span>
      </div>
      <div className="groups-grid">
        {groups.map((g) => (
          <GroupCard key={g.letter} g={g} riskKey={riskKey} oddsFmt={oddsFmt}
            bankroll={bankroll} placed={placed} onAdd={onAdd} goTeam={goTeam} />
        ))}
      </div>
    </div>
  );
}
