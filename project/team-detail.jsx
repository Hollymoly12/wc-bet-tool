/* ============================================================================
   team-detail.jsx — drill-down pages:
   • TeamDetail  — one national team: bettable stats, fixtures, full squad
   • PlayerDetail — one player: selection vs club stat lines + bettable props
   Globals shared with other babel scripts; also exported to window.
   ========================================================================== */

function StatTile({ label, value, cls }) {
  return (
    <div className="card stat-card">
      <label>{label}</label>
      <b className={`mono ${cls || ""}`}>{value}</b>
    </div>
  );
}

function BackBar({ onBack, crumb }) {
  return (
    <button className="back-btn" onClick={onBack}>
      <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M15 6l-6 6 6 6" /></svg>
      {crumb}
    </button>
  );
}

/* ============================ TEAM DETAIL ============================ */
const SQUAD_LINES = [["GK", "Goalkeeper"], ["DEF", "Defenders"], ["MID", "Midfielders"], ["FWD", "Forwards"]];

function TeamDetail({ WC, code, oddsFmt, go, goPlayer, back }) {
  const t = WC.teams.find((x) => x.code === code);
  const ts = WC.teamStats.find((x) => x.code === code);
  const squad = WC.lineups[code];
  const fixtures = WC.matches.filter((m) => m.home === code || m.away === code);
  const name = WC.NAME[code];

  return (
    <div className="screen teamdetail">
      <BackBar onBack={back} crumb="Back" />
      <div className="td-hero card">
        <TeamToken code={code} size={76} radius={18} />
        <div className="td-hero-main">
          <h1>{name}</h1>
          <div className="td-hero-meta">
            <span className="grp-tag">Group {ts.group}</span>
            <span className="mono">FIFA #{ts.rank}</span>
            <FormDots form={ts.form} size={13} />
          </div>
        </div>
        {t && (
          <div className="td-outright">
            <label>TO WIN THE CUP</label>
            <div className="td-outright-row">
              <b className="mono">{WC.formatOdds(t.dec, oddsFmt)}</b>
              <EdgeBadge value={t.ev} />
            </div>
            <span className="mono dim">model {fmtPct(t.model)}</span>
          </div>
        )}
      </div>

      <div className="td-section-label">Team form &amp; bettable stats</div>
      <div className="td-stats">
        <StatTile label="Goals / game" value={ts.gpg.toFixed(1)} />
        <StatTile label="Conceded / game" value={ts.gc.toFixed(1)} />
        <StatTile label="Clean sheet" value={ts.cs + "%"} />
        <StatTile label="BTTS rate" value={ts.btts + "%"} />
        <StatTile label="Cards / game" value={ts.cards.toFixed(1)} />
        <StatTile label="Corners / game" value={ts.corners.toFixed(1)} />
        <StatTile label="Possession" value={ts.poss + "%"} />
        <StatTile label="Win probability" value={ts.winPct + "%"} cls="pos" />
      </div>

      {fixtures.length > 0 && (
        <>
          <div className="td-section-label">Fixtures</div>
          <div className="td-fixtures">
            {fixtures.map((m) => (
              <button key={m.id} className="up-row" onClick={() => go("matches", m.id)}>
                <div className="up-teams"><TeamToken code={m.home} size={26} radius={7} /><span className="up-vs mono">v</span><TeamToken code={m.away} size={26} radius={7} /></div>
                <div className="up-when"><span className="mono">{m.day} · {m.time}</span><span className="up-pick">Model pick: {m.best.label}</span></div>
                <EdgeBadge value={m.best.ev} size="sm" />
              </button>
            ))}
          </div>
        </>
      )}

      <div className="td-section-label">
        {squad ? `Selected squad · ${squad.formation} · ${squad.squad.length} players` : "Squad"}
        <span className="td-note">{squad ? "\u2605 = projected XI · click a player for selection & club stats" : ""}</span>
      </div>
      {squad ? (
        <div className="card squad-card">
          {SQUAD_LINES.map(([ln, lbl]) => {
            const ps = squad.squad.filter((p) => p.line === ln);
            if (!ps.length) return null;
            return (
              <div className="squad-group" key={ln}>
                <div className="squad-group-h"><span className={`pos-tag pl-${ln.toLowerCase()}`}>{lbl}</span><span className="squad-count mono">{ps.length}</span></div>
                {ps.map((p) => (
                  <button className={`squad-row ${p.starter ? "is-xi" : ""}`} key={p.n + p.name} onClick={() => goPlayer(p)}>
                    <span className="sq-num mono">{p.starter ? "\u2605" : p.n}</span>
                    <div className="sq-name"><span>{p.name}</span><em>{p.club}</em></div>
                    <span className="sq-pos mono dim">{p.pos}</span>
                    <div className="sq-stat"><label>SÉL</label><b className="mono">{p.sel.caps}<span className="dim"> caps</span></b></div>
                    <div className="sq-stat"><label>SÉL G</label><b className="mono">{p.sel.goals}</b></div>
                    <div className="sq-stat"><label>CLUB G</label><b className="mono">{p.clubStats.goals}</b></div>
                    {p.scorer ? <span className="sq-scorer mono">{WC.formatOdds(p.scorer.dec, oddsFmt)}<i>scorer</i></span> : <span className="sq-scorer dim">—</span>}
                    <svg className="sq-arrow" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M9 6l6 6-6 6" /></svg>
                  </button>
                ))}
              </div>
            );
          })}
        </div>
      ) : (
        <div className="card"><div className="empty">Squad lists are published for teams with confirmed fixtures. Team stats above are available now.</div></div>
      )}
    </div>
  );
}

/* ============================ PLAYER DETAIL ============================ */
function StatLine({ label, value, sub }) {
  return (
    <div className="pd-stat">
      <span className="pd-stat-l">{label}</span>
      <span className="pd-stat-v mono">{value}{sub && <em>{sub}</em>}</span>
    </div>
  );
}

function PlayerDetail({ WC, player: p, oddsFmt, riskKey, bankroll, placed, onAdd, goTeam, back }) {
  const propTiles = [
    p.scorer && { title: "Anytime Scorer", prop: p.scorer, label: "Anytime Scorer" },
    p.shots && { title: `Over ${p.shots.L} Shots`, prop: p.shots, label: `Over ${p.shots.L} Shots` },
    p.sot && { title: `Over ${p.sot.L} SoT`, prop: p.sot, label: `Over ${p.sot.L} SoT` },
    { title: "To Be Carded", prop: p.card, label: "To Be Carded" },
  ].filter(Boolean);

  return (
    <div className="screen playerdetail">
      <BackBar onBack={back} crumb={p.team} />
      <div className="pd-hero card">
        <div className="pd-num mono">{p.n}</div>
        <div className="pd-hero-main">
          <h1>{p.name}</h1>
          <div className="pd-hero-meta">
            <span className={`pos-tag pl-${p.line.toLowerCase()}`}>{p.pos}</span>
            <button className="pd-team-link" onClick={() => goTeam(p.code)}><TeamToken code={p.code} size={20} radius={5} /> {p.team}</button>
            <span className="dim">·</span>
            <span className="pd-club">{p.club}</span>
          </div>
        </div>
      </div>

      <div className="pd-stats-grid">
        <div className="card pd-stat-card">
          <div className="pd-stat-head"><TeamToken code={p.code} size={24} /><b>En sélection</b><span className="head-note">{p.sel.caps} caps</span></div>
          <StatLine label="Caps" value={p.sel.caps} />
          <StatLine label="Goals" value={p.sel.goals} />
          <StatLine label="Assists" value={p.sel.assists} />
          <StatLine label="Goals / 90" value={p.sel.g90.toFixed(2)} />
          <StatLine label="Shots / 90" value={p.sel.sh90.toFixed(1)} />
          <StatLine label="Shots on target / 90" value={p.sel.sot90.toFixed(1)} />
        </div>
        <div className="card pd-stat-card">
          <div className="pd-stat-head club"><span className="pd-club-badge">{p.club}</span><b>En club</b><span className="head-note">2025/26 season</span></div>
          <StatLine label="Appearances" value={p.clubStats.apps} />
          <StatLine label="Goals" value={p.clubStats.goals} />
          <StatLine label="Assists" value={p.clubStats.assists} />
          <StatLine label="Goals / 90" value={p.clubStats.g90.toFixed(2)} />
          <StatLine label="Shots / 90" value={p.clubStats.sh90.toFixed(1)} />
          <StatLine label="Minutes" value={p.clubStats.mins.toLocaleString("en-US")} />
        </div>
      </div>

      <div className="td-section-label">Player props · next match
        <span className="td-note">stakes scale to your {WC.RISK[riskKey].label.toLowerCase()} profile</span></div>
      <div className="card pd-props">
        {propTiles.map((t) => (
          <div className="prop-tile" key={t.label}>
            <label>{t.title}</label>
            <div className="prop-tile-model mono dim">model {(t.prop.model * 100).toFixed(0)}%</div>
            <PropCell prop={t.prop} label={t.label} code={p.code} name={p.name} n={p.n}
              WC={WC} riskKey={riskKey} oddsFmt={oddsFmt} bankroll={bankroll} placed={placed} onAdd={onAdd} />
          </div>
        ))}
      </div>
    </div>
  );
}

Object.assign(window, { TeamDetail, PlayerDetail, StatTile, BackBar });
