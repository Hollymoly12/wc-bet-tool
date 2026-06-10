/* ============================================================================
   Bankroll.jsx — Bankroll tracker with open/settled bets
   ========================================================================== */
import React from 'react';
import { AreaChart, BalanceNumber, fmtPct, fmtSign, fmtMoney } from '../components/primitives.jsx';
import { TeamTokenAuto } from '../components/TeamTokenWithColors.jsx';
import { formatOdds, buildBankrollHistory, deleteBet, settleBet } from '../api.js';

export default function BankrollScreen({ bankroll, oddsFmt, openBets, onRemove, onBankrollRefresh }) {
  const balance = bankroll?.balance ?? 100;
  const start = bankroll?.start ?? 100;
  const currency = bankroll?.currency ?? '€';
  const settled = bankroll?.settled_bets ?? [];
  const open = bankroll?.open_bets ?? [];

  const roi = start > 0 ? (balance - start) / start : 0;
  const wins = settled.filter((b) => b.result === 'won');
  const winRate = settled.length > 0 ? wins.length / settled.length : 0;
  const totalStaked = settled.reduce((s, b) => s + (b.stake || 0), 0);
  const totalPnl = settled.reduce((s, b) => s + (b.pnl || 0), 0);
  const openStaked = open.reduce((s, b) => s + (b.stake || 0), 0);
  const openReturn = open.reduce((s, b) => s + (b.stake || 0) * (b.dec || 1), 0);
  const history = buildBankrollHistory(start, settled);

  const stats = [
    { label: 'Settled P&L', val: fmtMoney(totalPnl, currency), cls: totalPnl >= 0 ? 'pos' : 'neg' },
    { label: 'Win rate', val: settled.length ? fmtPct(winRate, 0) : '—' },
    { label: 'Total staked', val: fmtMoney(totalStaked, currency) },
    { label: 'Open exposure', val: fmtMoney(openStaked, currency) },
  ];

  const handleSettle = async (id, result) => {
    try {
      await settleBet(id, result);
      onBankrollRefresh?.();
    } catch (e) {
      console.error('settle error', e);
    }
  };

  const handleDelete = async (id) => {
    try {
      await deleteBet(id);
      onBankrollRefresh?.();
      onRemove?.(id);
    } catch (e) {
      console.error('delete error', e);
    }
  };

  // Combine client-side open bets (placed this session) + server open bets
  const allOpenBets = [...open, ...openBets.filter((b) => !open.find((s) => s.key === b.key))];

  return (
    <div className="screen bankroll">
      <div className="screen-head">
        <div>
          <div className="eyebrow">Money Management</div>
          <h1>Bankroll Tracker</h1>
        </div>
        <div className="head-meta"><span className="kicker">START {fmtMoney(start, currency)}</span></div>
      </div>

      <div className="bk-top">
        <div className="card bk-hero">
          <label>CURRENT BALANCE</label>
          <BalanceNumber value={balance} sym={currency} />
          <div className={`roi ${roi >= 0 ? 'pos' : 'neg'}`}>{fmtSign(roi)} ROI · {fmtMoney(balance - start, currency)} all-time</div>
          <AreaChart data={history} w={560} h={150} />
        </div>
        <div className="bk-stats">
          {stats.map((s) => (
            <div className="card stat-card" key={s.label}>
              <label>{s.label}</label>
              <b className={`mono ${s.cls || ''}`}>{s.val}</b>
            </div>
          ))}
        </div>
      </div>

      <div className="bk-tables">
        {/* open positions */}
        <div className="card">
          <div className="card-head">
            <span>Open Positions</span>
            <span className="head-note">{allOpenBets.length} active · {fmtMoney(openReturn, currency)} potential return</span>
          </div>
          {allOpenBets.length === 0 ? (
            <div className="empty">No open bets yet. Add picks from the Dashboard, Board, or Match Analysis.</div>
          ) : (
            <table className="data-table compact">
              <thead>
                <tr>
                  <th>Pick</th>
                  <th className="num">Odds</th>
                  <th className="num">Stake</th>
                  <th className="num">To return</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {allOpenBets.map((b) => (
                  <tr key={b.id || b.key}>
                    <td className="team-cell">
                      <TeamTokenAuto code={b.team || b.code || 'BRA'} size={26} />
                      <span className="bet-pick">{b.market || b.pick}</span>
                    </td>
                    <td className="num mono">{formatOdds(b.dec, oddsFmt)}</td>
                    <td className="num mono">{fmtMoney(b.stake, currency)}</td>
                    <td className="num mono pos">{fmtMoney(b.stake * b.dec, currency)}</td>
                    <td className="num" style={{ display: 'flex', gap: '6px', justifyContent: 'flex-end' }}>
                      {b.id ? (
                        <>
                          <button className="btn ghost sm" onClick={() => handleSettle(b.id, 'won')}>Won</button>
                          <button className="btn ghost sm" onClick={() => handleSettle(b.id, 'lost')}>Lost</button>
                          <button className="btn ghost sm" onClick={() => handleDelete(b.id)}>Void</button>
                        </>
                      ) : (
                        <button className="btn ghost sm" onClick={() => onRemove?.(b.key)}>Void</button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>

        {/* settled history */}
        <div className="card">
          <div className="card-head"><span>Settled History</span></div>
          {settled.length === 0 ? (
            <div className="empty">No settled bets yet.</div>
          ) : (
            <table className="data-table compact">
              <thead>
                <tr>
                  <th>Pick</th>
                  <th className="num">Stake</th>
                  <th className="num">Odds</th>
                  <th className="num">Result</th>
                  <th className="num">P&L</th>
                </tr>
              </thead>
              <tbody>
                {settled.map((b) => (
                  <tr key={b.id}>
                    <td className="team-cell">
                      <TeamTokenAuto code={b.team || 'BRA'} size={26} />
                      <span className="bet-pick">{b.pick || b.market}</span>
                    </td>
                    <td className="num mono">{fmtMoney(b.stake, currency)}</td>
                    <td className="num mono">{formatOdds(b.dec, oddsFmt)}</td>
                    <td className="num"><span className={`result ${b.result}`}>{b.result === 'won' ? 'WON' : b.result === 'void' ? 'VOID' : 'LOST'}</span></td>
                    <td className={`num mono ${(b.pnl || 0) >= 0 ? 'pos' : 'neg'}`}>{fmtMoney(b.pnl || 0, currency)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>
    </div>
  );
}
