/* ============================================================================
   bracket.jsx — Bracket screen: projected knockout tree (Round of 32 → Final)
   built from the group model. Favoured team highlighted in each tie.
   ========================================================================== */

function BracketTeam({ t, isWinner, goTeam, showProb }) {
  if (!t) return <div className="bt empty"><span className="bt-code">—</span></div>;
  return (
    <button className={`bt ${isWinner ? "win" : ""}`} onClick={() => t && goTeam(t.code)}>
      <TeamToken code={t.code} size={20} radius={5} />
      <span className="bt-code">{t.code}</span>
      {showProb && t.winProb && <span className="bt-prob mono">{Math.round(t.winProb * 100)}%</span>}
    </button>
  );
}

function BracketMatch({ m, goTeam }) {
  const wc = m.winner && m.winner.code;
  return (
    <div className="bmatch">
      <BracketTeam t={m.a} isWinner={m.a && m.a.code === wc} goTeam={goTeam} />
      <BracketTeam t={m.b} isWinner={m.b && m.b.code === wc} goTeam={goTeam} />
    </div>
  );
}

function Bracket({ WC, goTeam }) {
  const { rounds, champion } = WC.bracket;
  return (
    <div className="screen bracket">
      <div className="screen-head">
        <div>
          <div className="eyebrow">Knockout phase · 32 teams</div>
          <h1>Projected Bracket</h1>
        </div>
        <div className="head-meta">
          {champion && (
            <div className="champ-chip">
              <span className="champ-l"><Icon name="trophy" size={13} /> Model champion</span>
              <button className="champ-team" onClick={() => goTeam(champion.code)}>
                <TeamToken code={champion.code} size={24} radius={6} /> {champion.name}
              </button>
            </div>
          )}
        </div>
      </div>

      <div className="bracket-note dim">
        Seeded from projected group finishes (12 winners · 12 runners-up · 8 best thirds). The model&rsquo;s favourite advances in each tie — tap any nation to open its page. Scroll horizontally to follow the path to the final.
      </div>

      <div className="card bracket-scroll">
        <div className="bracket-rounds">
          {rounds.map((rd, ri) => (
            <div className={`bround r-${ri}`} key={rd.name}>
              <div className="bround-h">{rd.name}<span className="mono">{rd.matches.length}</span></div>
              <div className="bround-matches">
                {rd.matches.map((m, mi) => <BracketMatch key={mi} m={m} goTeam={goTeam} />)}
              </div>
            </div>
          ))}
          <div className="bround r-trophy">
            <div className="bround-h">Champion</div>
            <div className="bround-matches">
              <div className="bchamp">
                {champion && <>
                  <TeamToken code={champion.code} size={44} radius={11} />
                  <div className="bchamp-name">{champion.name}</div>
                  <div className="bchamp-odds mono">{champion.winProb ? Math.round(champion.winProb * 100) + "% in final" : ""}</div>
                </>}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

Object.assign(window, { Bracket, BracketMatch, BracketTeam });
