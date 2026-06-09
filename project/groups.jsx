/* ============================================================================
   groups.jsx — Groups screen: 12 group cards with projected standings and
   two bettable markets per team (To win group / To qualify).
   ========================================================================== */

function GroupBetChip({ market, label, code, name, letter, mkt, WC, riskKey, oddsFmt, bankroll, placed, onAdd }) {
  const key = `${market}:${code}`;
  const stake = WC.recommendedStake(mkt.model, mkt.dec, bankroll.balance, riskKey);
  const done = placed.has(key);
  return (
    <button className={`gbet ${mkt.ev > 0 ? "val" : ""} ${done ? "on" : ""}`}
      disabled={done} title={`${label} · model ${(mkt.model * 100).toFixed(0)}%`}
      onClick={() => onAdd({ key, name: name + " · " + label, code,
        market: `${name} — ${label} ${letter}`, dec: mkt.dec, model: mkt.model, ev: mkt.ev, stake })}>
      <span className="gbet-odds mono">{done ? "\u2713" : WC.formatOdds(mkt.dec, oddsFmt)}</span>
      <EdgeBadge value={mkt.ev} size="sm" />
    </button>
  );
}

function GroupCard({ g, WC, riskKey, oddsFmt, bankroll, placed, onAdd, goTeam }) {
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
      {g.rows.map((r) => (
        <div key={r.code} className={`gc-row rank-${r.projRank}`}>
          <span className="gc-rank mono">{r.projRank}</span>
          <button className="gc-team" onClick={() => goTeam(r.code)}>
            <TeamToken code={r.code} size={26} radius={7} />
            <span>{r.name}</span>
          </button>
          <GroupBetChip market="gw" label="Win Group" code={r.code} name={r.name} letter={g.letter}
            mkt={r.gwMarket} WC={WC} riskKey={riskKey} oddsFmt={oddsFmt} bankroll={bankroll} placed={placed} onAdd={onAdd} />
          <GroupBetChip market="ql" label="To Qualify —" code={r.code} name={r.name} letter={g.letter}
            mkt={r.qualMarket} WC={WC} riskKey={riskKey} oddsFmt={oddsFmt} bankroll={bankroll} placed={placed} onAdd={onAdd} />
          <span className="gc-qbar">
            <span className="gc-qfill" style={{ width: Math.round(r.qualProb * 100) + "%" }} />
            <em className="mono">{Math.round(r.qualProb * 100)}%</em>
          </span>
        </div>
      ))}
    </div>
  );
}

function Groups({ WC, riskKey, oddsFmt, bankroll, placed, onAdd, goTeam }) {
  return (
    <div className="screen groups">
      <div className="screen-head">
        <div>
          <div className="eyebrow">48 teams · 12 groups</div>
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
        {WC.groups.map((g) => (
          <GroupCard key={g.letter} g={g} WC={WC} riskKey={riskKey} oddsFmt={oddsFmt}
            bankroll={bankroll} placed={placed} onAdd={onAdd} goTeam={goTeam} />
        ))}
      </div>
    </div>
  );
}

Object.assign(window, { Groups, GroupCard });
