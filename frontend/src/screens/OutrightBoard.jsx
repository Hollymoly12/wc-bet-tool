/* ============================================================================
   OutrightBoard.jsx — Champion Value Board
   ========================================================================== */
import React from 'react';
import { Icon, EdgeBadge, VerdictChip, ConfMeter, fmtPct, fmtMoney } from '../components/primitives.jsx';
import { TeamTokenAuto } from '../components/TeamTokenWithColors.jsx';
import { recommendedStake, formatOdds } from '../api.js';

export default function OutrightBoard({ outright, bankroll, riskKey, oddsFmt, placed, onAdd, goTeam }) {
  const [sort, setSort] = React.useState('ev');
  const [valueOnly, setValueOnly] = React.useState(false);

  const balance = bankroll?.balance ?? 1000;
  const currency = bankroll?.currency ?? '$';

  const rows = React.useMemo(() => {
    let r = outright.map((t) => ({
      ...t, key: 'o:' + t.code,
      stake: recommendedStake(t.model, t.dec, balance, riskKey),
    }));
    if (valueOnly) r = r.filter((t) => t.ev > 0);
    const cmp = {
      ev: (a, b) => b.ev - a.ev,
      model: (a, b) => b.model - a.model,
      odds: (a, b) => a.dec - b.dec,
      conf: (a, b) => b.conf - a.conf,
    }[sort] || ((a, b) => b.ev - a.ev);
    return [...r].sort(cmp);
  }, [sort, valueOnly, riskKey, balance, outright]);

  const valueCount = outright.filter((t) => t.ev > 0).length;

  const Th = ({ id, children, num }) => (
    <th className={`${num ? 'num' : ''} ${sort === id ? 'sorted' : ''}`}
      onClick={id ? () => setSort(id) : undefined} style={{ cursor: id ? 'pointer' : 'default' }}>
      {children}{sort === id ? <span className="sort-caret">▾</span> : null}
    </th>
  );

  if (!outright.length) {
    return (
      <div className="screen outright">
        <div className="screen-head">
          <div><div className="eyebrow">Outright Market</div><h1>Champion Value Board</h1></div>
        </div>
        <div className="empty">No outright data yet.</div>
      </div>
    );
  }

  return (
    <div className="screen outright">
      <div className="screen-head">
        <div>
          <div className="eyebrow">Outright Market · {outright.length} contenders</div>
          <h1>Champion Value Board</h1>
        </div>
        <div className="head-meta">
          <span className="value-pill"><Icon name="bolt" size={12} /> {valueCount} value edges</span>
        </div>
      </div>

      <div className="toolbar">
        <div className="seg-group">
          {[['ev', 'Expected value'], ['model', 'Model win%'], ['odds', 'Shortest odds'], ['conf', 'Confidence']].map(([id, lbl]) => (
            <button key={id} className={`seg ${sort === id ? 'on' : ''}`} onClick={() => setSort(id)}>{lbl}</button>
          ))}
        </div>
        <button className={`toggle-pill ${valueOnly ? 'on' : ''}`} onClick={() => setValueOnly(!valueOnly)}>
          <span className="dot" /> Positive EV only
        </button>
      </div>

      <div className="card table-card">
        <table className="data-table">
          <thead>
            <tr>
              <Th>#</Th><Th>Team</Th><Th>Grp</Th>
              <Th id="odds" num>Book</Th>
              <Th num>Implied</Th>
              <Th id="model" num>Model</Th>
              <Th id="ev" num>Edge (EV)</Th>
              <Th id="conf" num>Conf</Th>
              <Th num>Stake</Th>
              <Th></Th>
            </tr>
          </thead>
          <tbody>
            {rows.map((t, i) => (
              <tr key={t.code} className={t.ev > 0.03 ? 'row-value' : ''}>
                <td className="num rank mono">{String(i + 1).padStart(2, '0')}</td>
                <td className="team-cell clickable" onClick={() => goTeam(t.code)}>
                  <TeamTokenAuto code={t.code} size={30} />
                  <span>{t.name}</span>
                </td>
                <td className="mono grp">{t.group}</td>
                <td className="num mono">{formatOdds(t.dec, oddsFmt)}</td>
                <td className="num mono dim">{fmtPct(t.implied)}</td>
                <td className="num mono">{fmtPct(t.model)}</td>
                <td className="num"><EdgeBadge value={t.ev} /></td>
                <td className="num"><ConfMeter value={t.conf} segments={6} /></td>
                <td className="num mono stake-cell">{t.ev > 0 ? fmtMoney(t.stake, currency) : '—'}</td>
                <td className="num">
                  <button className={`btn ghost sm ${placed.has(t.key) ? 'is-done' : ''}`}
                    disabled={placed.has(t.key) || t.ev <= 0} onClick={() => onAdd({
                      key: t.key, name: t.name, code: t.code, market: 'To win the World Cup',
                      dec: t.dec, model: t.model, ev: t.ev, stake: t.stake,
                    })}>
                    {placed.has(t.key) ? '✓' : 'Bet'}
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
