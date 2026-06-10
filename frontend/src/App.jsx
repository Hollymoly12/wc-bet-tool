/* ============================================================================
   App.jsx — shell, navigation, global state, data fetching
   ========================================================================== */
import React from 'react';
import { Icon, fmtMoney } from './components/primitives.jsx';
import { setColorMap } from './components/TeamTokenWithColors.jsx';
import {
  fetchOutright, fetchMatches, fetchGroups, fetchBracket,
  fetchTeams, fetchBankroll, RISK, formatOdds, recommendedStake,
  placeBet, setTeamNameCache,
} from './api.js';

import Dashboard from './screens/Dashboard.jsx';
import OutrightBoard from './screens/OutrightBoard.jsx';
import MatchAnalysis from './screens/MatchAnalysis.jsx';
import Groups from './screens/Groups.jsx';
import Bracket from './screens/Bracket.jsx';
import TeamStats from './screens/TeamStats.jsx';
import TeamDetail from './screens/TeamDetail.jsx';
import Bankroll from './screens/Bankroll.jsx';

const NAV = [
  { id: 'dashboard', label: 'Dashboard', icon: 'dashboard' },
  { id: 'outright', label: 'Outright Board', icon: 'trophy' },
  { id: 'groups', label: 'Groups', icon: 'groups' },
  { id: 'bracket', label: 'Bracket', icon: 'bracket' },
  { id: 'matches', label: 'Match Analysis', icon: 'match' },
  { id: 'teamstats', label: 'Team Stats', icon: 'stats' },
  { id: 'bankroll', label: 'Bankroll', icon: 'wallet' },
];

export default function App() {
  const [screen, setScreen] = React.useState('dashboard');
  const [focusMatch, setFocusMatch] = React.useState(null);
  const [focusTeam, setFocusTeam] = React.useState(null);
  const [prevScreen, setPrevScreen] = React.useState('dashboard');
  const [riskKey, setRiskKey] = React.useState('balanced');
  const [oddsFmt, setOddsFmt] = React.useState('decimal');

  // ── Client-side bet staging (before placing) ────────────────────────────
  const [openBets, setOpenBets] = React.useState([]);
  const [placed, setPlaced] = React.useState(() => new Set());
  const [toast, setToast] = React.useState(null);

  // ── Remote data ─────────────────────────────────────────────────────────
  const [outright, setOutright] = React.useState([]);
  const [matches, setMatches] = React.useState([]);
  const [groups, setGroups] = React.useState([]);
  const [bracket, setBracket] = React.useState(null);
  const [teams, setTeams] = React.useState([]);
  const [bankroll, setBankroll] = React.useState(null);
  const [loading, setLoading] = React.useState(true);
  const [loadError, setLoadError] = React.useState(null);

  // Build team-form lookup and color map from teams list
  const teamForms = React.useMemo(() => {
    const map = {};
    for (const t of teams) map[t.code] = t.form || '';
    return map;
  }, [teams]);

  // ── Initial data load ───────────────────────────────────────────────────
  React.useEffect(() => {
    let cancelled = false;
    async function load() {
      try {
        // Load teams first so we have colors + name cache
        const teamsData = await fetchTeams();
        if (cancelled) return;
        setTeams(teamsData);
        setTeamNameCache(teamsData);

        // Load outright (has colors) + everything else in parallel
        const [outrightData, matchesData, groupsData, bracketData, bankrollData] = await Promise.allSettled([
          fetchOutright(),
          fetchMatches(),
          fetchGroups(),
          fetchBracket(),
          fetchBankroll(),
        ]);
        if (cancelled) return;

        // Populate color map from outright rows
        const colorMap = {};
        for (const t of teamsData) colorMap[t.code] = ['#1a1e28', '#2a2f3e'];
        if (outrightData.status === 'fulfilled') {
          for (const r of (outrightData.value || [])) {
            if (r.colors && r.colors.length >= 2) colorMap[r.code] = r.colors;
          }
        }
        setColorMap(colorMap);

        if (outrightData.status === 'fulfilled') setOutright(outrightData.value || []);
        if (matchesData.status === 'fulfilled') setMatches(matchesData.value || []);
        if (groupsData.status === 'fulfilled') setGroups(groupsData.value || []);
        if (bracketData.status === 'fulfilled') setBracket(bracketData.value || null);
        if (bankrollData.status === 'fulfilled') {
          const br = bankrollData.value || null;
          // API doesn't include currency field — inject default
          setBankroll(br ? { currency: '€', ...br } : null);
        }

        setLoadError(null);
      } catch (e) {
        if (!cancelled) setLoadError(e.message || 'Failed to load data');
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    load();
    return () => { cancelled = true; };
  }, []);

  const refreshBankroll = React.useCallback(async () => {
    try {
      const data = await fetchBankroll();
      setBankroll(data);
    } catch (_) { /* silent */ }
  }, []);

  // ── Navigation ──────────────────────────────────────────────────────────
  const go = (s, payload) => {
    setScreen(s);
    if (s === 'matches' && payload) setFocusMatch(payload);
  };
  const goTeam = (code) => {
    if (screen !== 'team') setPrevScreen(screen);
    setFocusTeam(code);
    setScreen('team');
  };
  const back = () => setScreen(prevScreen || 'dashboard');

  // ── Bet management ──────────────────────────────────────────────────────
  const onAdd = async (play) => {
    if (placed.has(play.key)) return;
    setOpenBets((b) => [...b, play]);
    setPlaced((p) => new Set(p).add(play.key));
    setToast(`Added — ${fmtMoney(play.stake, bankroll?.currency ?? '€')} on ${play.name}`);
    // Try to persist to backend
    try {
      await placeBet(play);
      refreshBankroll();
    } catch (_) { /* offline / seed mode — keep client state */ }
  };

  const onRemove = (keyOrId) => {
    setOpenBets((b) => b.filter((x) => x.key !== keyOrId));
    setPlaced((p) => {
      const n = new Set(p);
      n.delete(keyOrId);
      return n;
    });
  };

  React.useEffect(() => {
    if (!toast) return;
    const id = setTimeout(() => setToast(null), 2400);
    return () => clearTimeout(id);
  }, [toast]);

  // ── Loading / error state ───────────────────────────────────────────────
  if (loading) {
    return (
      <div className="loading-screen">
        <div className="loading-spin" />
        <div className="loading-text">Loading data…</div>
      </div>
    );
  }

  if (loadError) {
    return (
      <div className="loading-screen">
        <div className="error-card" style={{ maxWidth: 480 }}>
          <b>Could not connect to backend</b>
          <p style={{ margin: '8px 0 0', opacity: 0.8 }}>{loadError}</p>
          <p style={{ margin: '8px 0 0', opacity: 0.6, fontSize: 12 }}>
            Make sure the backend is running: <code>cd backend &amp;&amp; .venv/bin/uvicorn app.main:app --port 8000</code>
          </p>
        </div>
      </div>
    );
  }

  const balance = bankroll?.balance ?? 100;
  const currency = bankroll?.currency ?? '€';

  const commonProps = {
    outright, matches, groups, teams, bankroll,
    riskKey, oddsFmt, placed, onAdd, go, goTeam,
  };

  return (
    <div className="app density-comfy grid-on">
      {/* nav rail */}
      <aside className="nav-rail">
        <div className="brand">
          <div className="brand-mark"><Icon name="bolt" size={18} /></div>
          <div className="brand-txt"><b>EDGE</b><span>WC26</span></div>
        </div>
        <nav>
          {NAV.map((n) => (
            <button key={n.id} className={`nav-item ${screen === n.id || (screen === 'team' && n.id === 'teamstats') ? 'on' : ''}`}
              onClick={() => { if (n.id !== 'team') setFocusTeam(null); setScreen(n.id); }}>
              <Icon name={n.icon} size={19} />
              <span>{n.label}</span>
              {n.id === 'bankroll' && openBets.length > 0 && <em className="nav-badge">{openBets.length}</em>}
            </button>
          ))}
        </nav>
        <div className="rail-foot">
          <div className="risk-mini">
            <label>RISK PROFILE</label>
            <b>{RISK[riskKey]?.label || 'Balanced'}</b>
          </div>
        </div>
      </aside>

      {/* top bar */}
      <header className="top-bar">
        <div className="tb-balance">
          <span className="tb-label">BANKROLL</span>
          <b className="mono">{fmtMoney(balance, currency)}</b>
        </div>
        <div className="tb-controls">
          <div className="tb-ctl">
            <label>ODDS</label>
            <div className="seg-group sm">
              {[['decimal', 'Dec'], ['american', 'US'], ['fractional', 'Frac']].map(([id, lbl]) => (
                <button key={id} className={`seg ${oddsFmt === id ? 'on' : ''}`} onClick={() => setOddsFmt(id)}>{lbl}</button>
              ))}
            </div>
          </div>
          <div className="tb-ctl">
            <label>RISK</label>
            <div className="seg-group sm">
              {Object.entries(RISK).map(([id, r]) => (
                <button key={id} className={`seg ${riskKey === id ? 'on' : ''}`} onClick={() => setRiskKey(id)}
                  title={`${Math.round(r.mult * 100)}% Kelly · cap ${Math.round(r.cap * 100)}%`}>
                  {r.label[0]}{r.label.slice(1, 3)}
                </button>
              ))}
            </div>
          </div>
        </div>
      </header>

      {/* main content */}
      <main className="main-area">
        {screen === 'dashboard' && (
          <Dashboard {...commonProps} />
        )}
        {screen === 'outright' && (
          <OutrightBoard outright={outright} bankroll={bankroll}
            riskKey={riskKey} oddsFmt={oddsFmt} placed={placed} onAdd={onAdd} goTeam={goTeam} />
        )}
        {screen === 'groups' && (
          <Groups groups={groups} riskKey={riskKey} oddsFmt={oddsFmt}
            bankroll={bankroll} placed={placed} onAdd={onAdd} goTeam={goTeam} />
        )}
        {screen === 'bracket' && (
          <Bracket bracket={bracket} goTeam={goTeam} />
        )}
        {screen === 'matches' && (
          <MatchAnalysis matches={matches} teamForms={teamForms} bankroll={bankroll}
            riskKey={riskKey} oddsFmt={oddsFmt} placed={placed} onAdd={onAdd}
            focusId={focusMatch} goTeam={goTeam} />
        )}
        {screen === 'teamstats' && (
          <TeamStats teams={teams} goTeam={goTeam} />
        )}
        {screen === 'team' && focusTeam && (
          <TeamDetail code={focusTeam} matches={matches} oddsFmt={oddsFmt}
            go={go} back={back} />
        )}
        {screen === 'bankroll' && (
          <Bankroll bankroll={bankroll} oddsFmt={oddsFmt} openBets={openBets}
            onRemove={onRemove} onBankrollRefresh={refreshBankroll} />
        )}
      </main>

      {toast && (
        <div className="toast">
          <Icon name="bolt" size={13} /> {toast}
        </div>
      )}
    </div>
  );
}
