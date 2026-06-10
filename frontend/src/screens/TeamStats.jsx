/* ============================================================================
   TeamStats.jsx — Team Stats table (simplified, no player props since
   /players endpoint returns minimal data without props in seed mode)
   ========================================================================== */
import React from 'react';
import { FormDots } from '../components/primitives.jsx';
import { TeamTokenAuto } from '../components/TeamTokenWithColors.jsx';

export default function TeamStats({ teams, goTeam }) {
  const [sort, setSort] = React.useState('str');

  const rows = React.useMemo(() => {
    const asc = false;
    return [...teams].sort((a, b) => {
      const av = a[sort] ?? 0, bv = b[sort] ?? 0;
      return asc ? av - bv : bv - av;
    });
  }, [sort, teams]);

  if (!teams || !teams.length) {
    return (
      <div className="screen teamstats">
        <div className="screen-head">
          <div><div className="eyebrow">Stats</div><h1>Team Stats</h1></div>
        </div>
        <div className="empty">No team data available yet.</div>
      </div>
    );
  }

  const Th = ({ id, children }) => (
    <th className={`num ${sort === id ? 'sorted' : ''}`}
      onClick={id ? () => setSort(id) : undefined}
      style={{ cursor: id ? 'pointer' : 'default' }}>
      {children}{sort === id ? <span className="sort-caret">▾</span> : null}
    </th>
  );

  return (
    <div className="screen teamstats">
      <div className="screen-head">
        <div>
          <div className="eyebrow">Stats &amp; Ratings</div>
          <h1>Team Stats</h1>
        </div>
      </div>

      <div className="card table-card">
        <table className="data-table">
          <thead>
            <tr>
              <th>#</th><th>Team</th><th>Grp</th>
              <Th id="str">Strength</Th>
              <Th id="elo">ELO</Th>
              <th>Form</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((t, i) => (
              <tr key={t.code}>
                <td className="num rank mono">{String(i + 1).padStart(2, '0')}</td>
                <td className="team-cell clickable" onClick={() => goTeam(t.code)}>
                  <TeamTokenAuto code={t.code} size={30} />
                  <span>{t.name}</span>
                </td>
                <td className="mono grp">{t.group}</td>
                <td className="num mono dim">{(t.str ?? 0).toFixed(3)}</td>
                <td className="num mono dim">{Math.round(t.elo ?? 0)}</td>
                <td><FormDots form={t.form} size={12} /></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
