/* ============================================================================
   team-stats.jsx — pitch/lineup component (used in Match Analysis) +
   Team Stats screen (24-team bettable stat table + player props grid).
   Globals shared with other babel scripts; also exported to window.
   ========================================================================== */

/* ---- lineup pitch --------------------------------------------------- */
function PlayerPin({ p, x, y, color }) {
  return (
    <div className="pl" style={{ left: x + "%", top: y + "%" }}>
      <span className="pl-dot" style={{ background: color }}>{p.n}</span>
      <span className="pl-name">{p.name}</span>
    </div>
  );
}

function Pitch({ m, WC }) {
  const home = WC.lineups[m.home], away = WC.lineups[m.away];
  if (!home || !away) return null;
  const XPOS = { home: { GK: 6, DEF: 20, MID: 34, FWD: 45 }, away: { GK: 94, DEF: 80, MID: 66, FWD: 55 } };
  const LINES = ["GK", "DEF", "MID", "FWD"];
  const side = (lu, s, code) => {
    const color = WC.COLORS[code][0];
    return LINES.flatMap((ln) => {
      const ps = lu.xi.filter((p) => p.line === ln);
      return ps.map((p, i) => (
        <PlayerPin key={code + p.n} p={p} x={XPOS[s][ln]} y={((i + 1) / (ps.length + 1)) * 100} color={color} />
      ));
    });
  };
  return (
    <div className="card lineups">
      <div className="card-head"><span>Confirmed Lineups</span>
        <span className="head-note">projected XI · locks ~1h to kickoff</span></div>
      <div className="lu-formations">
        <span><i className="cdot" style={{ background: WC.COLORS[m.home][0] }} /> <b>{m.homeName}</b> · {home.formation}</span>
        <span>{away.formation} · <b>{m.awayName}</b> <i className="cdot" style={{ background: WC.COLORS[m.away][0] }} /></span>
      </div>
      <div className="pitch">
        <div className="pitch-cl" /><div className="pitch-circle" />
        <div className="pitch-box left" /><div className="pitch-box right" />
        {side(home, "home", m.home)}
        {side(away, "away", m.away)}
      </div>
    </div>
  );
}

/* ---- player prop cell ----------------------------------------------- */
function PropCell({ prop, label, code, name, n, WC, riskKey, oddsFmt, bankroll, placed, onAdd }) {
  if (!prop) return <span className="pc empty">{"\u2014"}</span>;
  const key = `pp:${code}:${n}:${label}`;
  const stake = WC.recommendedStake(prop.model, prop.dec, bankroll.balance, riskKey);
  const done = placed.has(key);
  return (
    <button className={`pc ${prop.ev > 0 ? "val" : ""} ${done ? "on" : ""}`}
      disabled={prop.ev <= 0 || done} title={`${label} · model ${(prop.model * 100).toFixed(0)}%`}
      onClick={() => onAdd({ key, name: name + " · " + label, code,
        market: label + " — " + name, dec: prop.dec, model: prop.model, ev: prop.ev, stake })}>
      <span className="pc-odds mono">{WC.formatOdds(prop.dec, oddsFmt)}</span>
      <EdgeBadge value={prop.ev} size="sm" />
    </button>
  );
}

/* ---- team stats screen ---------------------------------------------- */
const TS_COLS = [
  ["rank", "Rank", (s) => "#" + s.rank, true],
  ["gpg", "Goals/g", (s) => s.gpg.toFixed(1)],
  ["gc", "Conc/g", (s) => s.gc.toFixed(1), true],
  ["cs", "Clean sheet", (s) => s.cs + "%"],
  ["btts", "BTTS", (s) => s.btts + "%"],
  ["cards", "Cards/g", (s) => s.cards.toFixed(1)],
  ["corners", "Corners/g", (s) => s.corners.toFixed(1)],
  ["winPct", "Win prob", (s) => s.winPct + "%"],
];

function TeamStats({ WC, riskKey, oddsFmt, bankroll, placed, onAdd, goTeam, goPlayer }) {
  const [view, setView] = React.useState("teams");
  const [sort, setSort] = React.useState("rank");
  const [team, setTeam] = React.useState("All");
  const [posF, setPosF] = React.useState("All");
  const [q, setQ] = React.useState("");

  const rows = React.useMemo(() => {
    const asc = sort === "rank" || sort === "gc";
    return [...WC.teamStats].sort((a, b) => (asc ? a[sort] - b[sort] : b[sort] - a[sort]));
  }, [sort, WC]);

  const teamCodes = Object.keys(WC.lineups);
  const players = React.useMemo(() => {
    return WC.players.filter((p) =>
      (team === "All" || p.code === team) &&
      (posF === "All" || p.line === posF) &&
      (q === "" || p.name.toLowerCase().includes(q.toLowerCase()))
    ).sort((a, b) => b.gpg - a.gpg);
  }, [team, posF, q, WC]);

  return (
    <div className="screen teamstats">
      <div className="screen-head">
        <div>
          <div className="eyebrow">Stats &amp; Player Props</div>
          <h1>{view === "teams" ? "Team Stats" : "Player Props"}</h1>
        </div>
        <div className="head-meta">
          <div className="seg-group">
            <button className={`seg ${view === "teams" ? "on" : ""}`} onClick={() => setView("teams")}>Teams</button>
            <button className={`seg ${view === "props" ? "on" : ""}`} onClick={() => setView("props")}>Player Props</button>
          </div>
        </div>
      </div>

      {view === "teams" && (
        <div className="card table-card">
          <table className="data-table">
            <thead>
              <tr>
                <th>#</th><th>Team</th><th>Grp</th>
                {TS_COLS.map(([id, lbl]) => (
                  <th key={id} className={`num ${sort === id ? "sorted" : ""}`} style={{ cursor: "pointer" }} onClick={() => setSort(id)}>
                    {lbl}{sort === id ? <span className="sort-caret">{"\u25BE"}</span> : null}
                  </th>
                ))}
                <th>Form</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((s, i) => (
                <tr key={s.code}>
                  <td className="num rank mono">{String(i + 1).padStart(2, "0")}</td>
                  <td className="team-cell clickable" onClick={() => goTeam(s.code)}><TeamToken code={s.code} size={30} /><span>{s.name}</span></td>
                  <td className="mono grp">{s.group}</td>
                  {TS_COLS.map(([id, lbl, fmt]) => (
                    <td key={id} className={`num mono ${sort === id ? "" : "dim"}`}>{fmt(s)}</td>
                  ))}
                  <td><FormDots form={s.form} size={12} /></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {view === "props" && (
        <>
          <div className="toolbar props-toolbar">
            <div className="filter-group">
              <select className="ts-select" value={team} onChange={(e) => setTeam(e.target.value)}>
                <option value="All">All teams</option>
                {teamCodes.map((c) => <option key={c} value={c}>{WC.NAME[c]}</option>)}
              </select>
              <div className="seg-group sm">
                {["All", "GK", "DEF", "MID", "FWD"].map((p) => (
                  <button key={p} className={`seg ${posF === p ? "on" : ""}`} onClick={() => setPosF(p)}>{p}</button>
                ))}
              </div>
            </div>
            <input className="ts-search" placeholder="Search player…" value={q} onChange={(e) => setQ(e.target.value)} />
          </div>

          <div className="card table-card">
            <table className="data-table props-table">
              <thead>
                <tr>
                  <th>Player</th><th>Pos</th><th className="num">G / A</th>
                  <th className="num">Anytime Scorer</th><th className="num">Shots O/U</th>
                  <th className="num">SoT O/U</th><th className="num">To Be Carded</th>
                </tr>
              </thead>
              <tbody>
                {players.map((p) => (
                  <tr key={p.code + p.n}>
                    <td className="team-cell clickable" onClick={() => goPlayer(p)}><TeamToken code={p.code} size={28} /><div className="pl-cell"><span>{p.name}</span><em>{p.team}</em></div></td>
                    <td><span className={`pos-tag pl-${p.line.toLowerCase()}`}>{p.pos}</span></td>
                    <td className="num mono ga">{p.goals}<span className="dim"> / {p.assists}</span></td>
                    <td className="num"><PropCell prop={p.scorer} label="Anytime Scorer" {...{ code: p.code, name: p.name, n: p.n, WC, riskKey, oddsFmt, bankroll, placed, onAdd }} /></td>
                    <td className="num"><PropCell prop={p.shots} label={p.shots ? `Over ${p.shots.L} Shots` : ""} {...{ code: p.code, name: p.name, n: p.n, WC, riskKey, oddsFmt, bankroll, placed, onAdd }} /></td>
                    <td className="num"><PropCell prop={p.sot} label={p.sot ? `Over ${p.sot.L} SoT` : ""} {...{ code: p.code, name: p.name, n: p.n, WC, riskKey, oddsFmt, bankroll, placed, onAdd }} /></td>
                    <td className="num"><PropCell prop={p.card} label="To Be Carded" {...{ code: p.code, name: p.name, n: p.n, WC, riskKey, oddsFmt, bankroll, placed, onAdd }} /></td>
                  </tr>
                ))}
              </tbody>
            </table>
            {players.length === 0 && <div className="empty">No players match these filters.</div>}
          </div>
        </>
      )}
    </div>
  );
}

Object.assign(window, { Pitch, PlayerPin, PropCell, TeamStats });
