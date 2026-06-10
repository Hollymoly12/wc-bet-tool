/* ============================================================================
   Bracket.jsx — Projected knockout bracket
   ========================================================================== */
import React from 'react';
import { Icon } from '../components/primitives.jsx';
import { TeamTokenAuto } from '../components/TeamTokenWithColors.jsx';

function BracketTeamBtn({ t, isWinner, goTeam }) {
  if (!t) return <div className="bt empty"><span className="bt-code">—</span></div>;
  return (
    <button className={`bt ${isWinner ? 'win' : ''}`} onClick={() => t && goTeam(t.code)}>
      <TeamTokenAuto code={t.code} size={20} radius={5} />
      <span className="bt-code">{t.code}</span>
      {t.winProb != null && <span className="bt-prob mono">{Math.round(t.winProb * 100)}%</span>}
    </button>
  );
}

function BracketMatchComp({ m, goTeam }) {
  const wc = m.winner?.code;
  return (
    <div className="bmatch">
      <BracketTeamBtn t={m.a} isWinner={m.a && m.a.code === wc} goTeam={goTeam} />
      <BracketTeamBtn t={m.b} isWinner={m.b && m.b.code === wc} goTeam={goTeam} />
    </div>
  );
}

export default function Bracket({ bracket, goTeam }) {
  if (!bracket || !bracket.rounds || !bracket.rounds.length) {
    return (
      <div className="screen bracket">
        <div className="screen-head">
          <div><div className="eyebrow">Knockout phase</div><h1>Projected Bracket</h1></div>
        </div>
        <div className="empty">No bracket data available yet.</div>
      </div>
    );
  }

  const { rounds, champion } = bracket;

  return (
    <div className="screen bracket">
      <div className="screen-head">
        <div>
          <div className="eyebrow">Knockout phase · {rounds[0]?.matches?.length * 2 || 32} teams</div>
          <h1>Projected Bracket</h1>
        </div>
        <div className="head-meta">
          {champion && (
            <div className="champ-chip">
              <span className="champ-l"><Icon name="trophy" size={13} /> Model champion</span>
              <button className="champ-team" onClick={() => goTeam(champion.code)}>
                <TeamTokenAuto code={champion.code} size={24} radius={6} /> {champion.name}
              </button>
            </div>
          )}
        </div>
      </div>

      <div className="bracket-note dim">
        Seeded from projected group finishes. The model&rsquo;s favourite advances in each tie — tap any nation to open its page.
        Scroll horizontally to follow the path to the final.
      </div>

      <div className="card bracket-scroll">
        <div className="bracket-rounds">
          {rounds.map((rd, ri) => (
            <div className={`bround r-${ri}`} key={rd.name}>
              <div className="bround-h">{rd.name}<span className="mono">{rd.matches.length}</span></div>
              <div className="bround-matches">
                {rd.matches.map((m, mi) => <BracketMatchComp key={mi} m={m} goTeam={goTeam} />)}
              </div>
            </div>
          ))}
          <div className="bround r-trophy">
            <div className="bround-h">Champion</div>
            <div className="bround-matches">
              <div className="bchamp">
                {champion && (
                  <>
                    <TeamTokenAuto code={champion.code} size={44} radius={11} />
                    <div className="bchamp-name">{champion.name}</div>
                    <div className="bchamp-odds mono">
                      {champion.winProb ? Math.round(champion.winProb * 100) + '% in final' : ''}
                    </div>
                  </>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
