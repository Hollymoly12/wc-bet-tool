/* ============================================================================
   TeamDetail.jsx — national team drill-down page
   ========================================================================== */
import React from 'react';
import { Icon, EdgeBadge, FormDots, fmtPct, fmtMoney } from '../components/primitives.jsx';
import { TeamTokenAuto } from '../components/TeamTokenWithColors.jsx';
import { formatOdds, fetchTeam } from '../api.js';

function StatTile({ label, value, cls }) {
  return (
    <div className="card stat-card">
      <label>{label}</label>
      <b className={`mono ${cls || ''}`}>{value}</b>
    </div>
  );
}

function BackBar({ onBack, crumb }) {
  return (
    <button className="back-btn" onClick={onBack}>
      <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M15 6l-6 6 6 6" />
      </svg>
      {crumb}
    </button>
  );
}

const SQUAD_LINES = [['GK', 'Goalkeeper'], ['DEF', 'Defenders'], ['MID', 'Midfielders'], ['FWD', 'Forwards']];

export default function TeamDetail({ code, matches, oddsFmt, go, back }) {
  const [team, setTeam] = React.useState(null);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState(null);

  React.useEffect(() => {
    if (!code) return;
    setLoading(true);
    setError(null);
    fetchTeam(code)
      .then(setTeam)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [code]);

  if (loading) {
    return (
      <div className="screen teamdetail">
        <BackBar onBack={back} crumb="Back" />
        <div className="empty">Loading team data…</div>
      </div>
    );
  }

  if (error || !team) {
    return (
      <div className="screen teamdetail">
        <BackBar onBack={back} crumb="Back" />
        <div className="error-card">{error || 'Team not found'}</div>
      </div>
    );
  }

  const teamMatches = matches.filter((m) => m.home === code || m.away === code);
  const outright = team.outright;

  const squadByLine = {};
  for (const p of (team.squad || [])) {
    const line = p.pos?.slice(0, 3).toUpperCase() === 'GK' ? 'GK'
      : p.pos?.toUpperCase().includes('DEF') ? 'DEF'
      : p.pos?.toUpperCase().includes('MID') ? 'MID'
      : p.pos?.toUpperCase().includes('FWD') || p.pos?.toUpperCase().includes('ATT') ? 'FWD'
      : 'MID';
    if (!squadByLine[line]) squadByLine[line] = [];
    squadByLine[line].push({ ...p, line });
  }

  const newsItems = team.news || [];

  return (
    <div className="screen teamdetail">
      <BackBar onBack={back} crumb="Back" />

      <div className="td-hero card">
        <TeamTokenAuto code={code} size={76} radius={18} />
        <div className="td-hero-main">
          <h1>{team.name}</h1>
          <div className="td-hero-meta">
            <span className="grp-tag">Group {team.group}</span>
            <FormDots form={team.form} size={13} />
          </div>
        </div>
        {outright && (
          <div className="td-outright">
            <label>TO WIN THE CUP</label>
            <div className="td-outright-row">
              <b className="mono">{formatOdds(outright.dec, oddsFmt)}</b>
              {outright.ev != null && <EdgeBadge value={outright.ev} />}
            </div>
            {outright.model != null && (
              <span className="mono dim">model {fmtPct(outright.model)}</span>
            )}
          </div>
        )}
      </div>

      <div className="td-section-label">Team ratings</div>
      <div className="td-stats">
        <StatTile label="Strength rating" value={(team.str ?? 0).toFixed(3)} />
        <StatTile label="ELO" value={Math.round(team.elo ?? 0)} />
        <StatTile label="Attack" value={(team.attack ?? 0).toFixed(2)} cls="pos" />
        <StatTile label="Defense" value={(team.defense ?? 0).toFixed(2)} />
      </div>

      {teamMatches.length > 0 && (
        <>
          <div className="td-section-label">Fixtures</div>
          <div className="td-fixtures">
            {teamMatches.map((m) => (
              <button key={m.id} className="up-row" onClick={() => go('matches', m.id)}>
                <div className="up-teams">
                  <TeamTokenAuto code={m.home} size={26} radius={7} />
                  <span className="up-vs mono">v</span>
                  <TeamTokenAuto code={m.away} size={26} radius={7} />
                </div>
                <div className="up-when">
                  <span className="mono">{m.day} · {m.time}</span>
                  {m.best && <span className="up-pick">Model pick: {m.best.label}</span>}
                </div>
                {m.best && <EdgeBadge value={m.best.ev} size="sm" />}
              </button>
            ))}
          </div>
        </>
      )}

      {team.squad && team.squad.length > 0 && (
        <>
          <div className="td-section-label">
            Squad · {team.squad.length} players
          </div>
          <div className="card squad-card">
            {SQUAD_LINES.map(([ln, lbl]) => {
              const ps = squadByLine[ln] || [];
              if (!ps.length) return null;
              return (
                <div className="squad-group" key={ln}>
                  <div className="squad-group-h">
                    <span className={`pos-tag pl-${ln.toLowerCase()}`}>{lbl}</span>
                    <span className="squad-count mono">{ps.length}</span>
                  </div>
                  {ps.map((p) => (
                    <div className={`squad-row ${p.starter ? 'is-xi' : ''}`} key={p.id || p.name}>
                      <span className="sq-num mono">{p.starter ? '★' : p.number}</span>
                      <div className="sq-name">
                        <span>{p.name}</span>
                        <em>{p.club}</em>
                      </div>
                      <span className="sq-pos mono dim">{p.pos}</span>
                      <svg className="sq-arrow" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                        <path d="M9 6l6 6-6 6" />
                      </svg>
                    </div>
                  ))}
                </div>
              );
            })}
          </div>
        </>
      )}

      {newsItems.length > 0 && (
        <>
          <div className="td-section-label">Team News</div>
          <div className="card" style={{ padding: 'var(--pad)' }}>
            {newsItems.map((n, i) => (
              <div key={i} className="news-item">
                <span className={`news-tag t-${n.tag || 'intel'}`}>{(n.tag || 'intel').toUpperCase()}</span>
                <div className="news-b">
                  <p>{n.text}</p>
                  <time>{n.published_at ? new Date(n.published_at).toLocaleDateString() : ''}</time>
                </div>
              </div>
            ))}
          </div>
        </>
      )}
    </div>
  );
}
