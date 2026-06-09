/* ============================================================================
   app.jsx — shell, navigation, global state, top-bar controls, tweaks
   ========================================================================== */

const TWEAK_DEFAULTS = /*EDITMODE-BEGIN*/{
  "accent": ["#C6FF3A", "#0b0d12"],
  "fontFamily": "Archivo",
  "density": "comfy",
  "grid": true
}/*EDITMODE-END*/;

const ACCENTS = {
  "#C6FF3A": "Lime", "#34E5FF": "Cyan", "#FF4D9D": "Magenta", "#FFB020": "Amber",
};

const NAV = [
  { id: "dashboard", label: "Dashboard", icon: "dashboard" },
  { id: "outright", label: "Outright Board", icon: "trophy" },
  { id: "groups", label: "Groups", icon: "groups" },
  { id: "bracket", label: "Bracket", icon: "bracket" },
  { id: "matches", label: "Match Analysis", icon: "match" },
  { id: "teamstats", label: "Team Stats", icon: "stats" },
  { id: "bankroll", label: "Bankroll", icon: "wallet" },
];

function App() {
  const WC = window.WC;
  const [t, setTweak] = useTweaks(TWEAK_DEFAULTS);
  const [screen, setScreen] = React.useState("dashboard");
  const [focusMatch, setFocusMatch] = React.useState(null);
  const [focusTeam, setFocusTeam] = React.useState(null);
  const [focusPlayer, setFocusPlayer] = React.useState(null);
  const [prevScreen, setPrevScreen] = React.useState("dashboard");
  const [playerBack, setPlayerBack] = React.useState("teamstats");
  const [riskKey, setRiskKey] = React.useState("balanced");
  const [oddsFmt, setOddsFmt] = React.useState("decimal");
  const [openBets, setOpenBets] = React.useState([]);
  const [placed, setPlaced] = React.useState(() => new Set());
  const [toast, setToast] = React.useState(null);

  const go = (s, payload) => { setScreen(s); if (s === "matches" && payload) setFocusMatch(payload); };
  const goTeam = (code) => { if (screen !== "team" && screen !== "player") setPrevScreen(screen); setFocusTeam(code); setScreen("team"); };
  const goPlayer = (p) => { setPlayerBack(screen); setFocusPlayer(p); setScreen("player"); };
  const back = () => setScreen(prevScreen || "teamstats");
  const backFromPlayer = () => setScreen(playerBack || "teamstats");

  const onAdd = (play) => {
    if (placed.has(play.key)) return;
    setOpenBets((b) => [...b, play]);
    setPlaced((p) => new Set(p).add(play.key));
    setToast(`Added — ${fmtMoney(play.stake, WC.bankroll.currency)} on ${play.name}`);
  };
  const onRemove = (key) => {
    setOpenBets((b) => b.filter((x) => x.key !== key));
    setPlaced((p) => { const n = new Set(p); n.delete(key); return n; });
  };
  React.useEffect(() => {
    if (!toast) return;
    const id = setTimeout(() => setToast(null), 2400);
    return () => clearTimeout(id);
  }, [toast]);

  const accent = Array.isArray(t.accent) ? t.accent[0] : t.accent;
  const accentInk = Array.isArray(t.accent) ? (t.accent[1] || "#0b0d12") : "#0b0d12";
  const rootStyle = {
    "--accent": accent, "--accent-ink": accentInk, "--pos": accent,
    "--ui-font": `"${t.fontFamily}", system-ui, sans-serif`,
  };

  const screenProps = { WC, riskKey, oddsFmt, bankroll: WC.bankroll, openBets, placed, onAdd, go, goTeam, goPlayer };

  return (
    <div className={`app density-${t.density} ${t.grid ? "grid-on" : ""}`} style={rootStyle}>
      {/* nav rail */}
      <aside className="nav-rail">
        <div className="brand">
          <div className="brand-mark"><Icon name="bolt" size={18} /></div>
          <div className="brand-txt"><b>EDGE</b><span>WC26</span></div>
        </div>
        <nav>
          {NAV.map((n) => (
            <button key={n.id} className={`nav-item ${screen === n.id ? "on" : ""}`}
              onClick={() => setScreen(n.id)}>
              <Icon name={n.icon} size={19} />
              <span>{n.label}</span>
              {n.id === "bankroll" && openBets.length > 0 && <em className="nav-badge">{openBets.length}</em>}
            </button>
          ))}
        </nav>
        <div className="rail-foot">
          <div className="risk-mini">
            <label>RISK PROFILE</label>
            <b>{WC.RISK[riskKey].label}</b>
          </div>
        </div>
      </aside>

      {/* top bar */}
      <header className="top-bar">
        <div className="tb-balance">
          <span className="tb-label">BANKROLL</span>
          <b className="mono">{fmtMoney(WC.bankroll.balance, WC.bankroll.currency)}</b>
        </div>
        <div className="tb-controls">
          <div className="tb-ctl">
            <label>ODDS</label>
            <div className="seg-group sm">
              {[["decimal", "Dec"], ["american", "US"], ["fractional", "Frac"]].map(([id, lbl]) => (
                <button key={id} className={`seg ${oddsFmt === id ? "on" : ""}`} onClick={() => setOddsFmt(id)}>{lbl}</button>
              ))}
            </div>
          </div>
          <div className="tb-ctl">
            <label>RISK</label>
            <div className="seg-group sm">
              {Object.entries(WC.RISK).map(([id, r]) => (
                <button key={id} className={`seg ${riskKey === id ? "on" : ""}`} onClick={() => setRiskKey(id)} title={`${Math.round(r.mult*100)}% Kelly · cap ${Math.round(r.cap*100)}%`}>{r.label[0]}{r.label.slice(1,3)}</button>
              ))}
            </div>
          </div>
        </div>
      </header>

      {/* main */}
      <main className="main-area">
        {screen === "dashboard" && <Dashboard {...screenProps} />}
        {screen === "outright" && <OutrightBoard {...screenProps} />}
        {screen === "groups" && <Groups {...screenProps} />}
        {screen === "bracket" && <Bracket WC={WC} goTeam={goTeam} />}
        {screen === "matches" && <MatchAnalysis {...screenProps} focusId={focusMatch} />}
        {screen === "teamstats" && <TeamStats {...screenProps} />}
        {screen === "team" && focusTeam && <TeamDetail {...screenProps} code={focusTeam} back={back} />}
        {screen === "player" && focusPlayer && <PlayerDetail WC={WC} player={focusPlayer} oddsFmt={oddsFmt} riskKey={riskKey} bankroll={WC.bankroll} placed={placed} onAdd={onAdd} goTeam={goTeam} back={backFromPlayer} />}
        {screen === "bankroll" && <BankrollTracker WC={WC} bankroll={WC.bankroll} oddsFmt={oddsFmt} openBets={openBets} onRemove={onRemove} />}
      </main>

      {toast && <div className="toast"><Icon name="bolt" size={13} /> {toast}</div>}

      <TweaksPanel>
        <TweakSection label="Accent" />
        <TweakColor label="Theme color" value={t.accent}
          options={[["#C6FF3A", "#0b0d12"], ["#34E5FF", "#0b0d12"], ["#FF4D9D", "#0b0d12"], ["#FFB020", "#0b0d12"]]}
          onChange={(v) => setTweak("accent", v)} />
        <TweakSection label="Typography" />
        <TweakSelect label="UI typeface" value={t.fontFamily}
          options={["Archivo", "Saira", "Sora"]} onChange={(v) => setTweak("fontFamily", v)} />
        <TweakSection label="Layout" />
        <TweakRadio label="Density" value={t.density} options={["compact", "comfy"]}
          onChange={(v) => setTweak("density", v)} />
        <TweakToggle label="Grid texture" value={t.grid} onChange={(v) => setTweak("grid", v)} />
      </TweaksPanel>
    </div>
  );
}

ReactDOM.createRoot(document.getElementById("root")).render(<App />);
