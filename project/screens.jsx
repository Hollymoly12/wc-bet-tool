/* ============================================================================
   screens.jsx — Dashboard, Outright Board, Match Analysis, Bankroll Tracker
   Components pulled from window (components.jsx). Exports screens to window.
   ========================================================================== */

/* build a unified, EV-sorted list of value plays from outrights + matches */
function buildValuePlays(WC, bankroll, riskKey) {
  const out = WC.teams.map((t) => ({
    key: "o:" + t.code, type: "Outright", market: "To win the World Cup",
    code: t.code, name: t.name, dec: t.dec, model: t.model, implied: t.implied,
    ev: t.ev, conf: t.conf,
    stake: WC.recommendedStake(t.model, t.dec, bankroll.balance, riskKey),
  }));
  const mt = WC.matches.map((m) => ({
    key: "m:" + m.id + ":" + m.best.kind, type: "Match", market: m.best.label + " — " + m.homeName + " v " + m.awayName,
    code: m.best.kind === "away" ? m.away : m.home, name: m.best.label, dec: m.best.dec,
    model: m.best.model, implied: m.best.implied, ev: m.best.ev, conf: m.conf,
    stake: WC.recommendedStake(m.best.model, m.best.dec, bankroll.balance, riskKey),
  }));
  return [...out, ...mt].sort((a, b) => b.ev - a.ev);
}

/* ============================ DASHBOARD ============================ */
function Dashboard({ WC, riskKey, oddsFmt, bankroll, openBets, placed, onAdd, go }) {
  const plays = buildValuePlays(WC, bankroll, riskKey);
  const hero = plays[0];
  const rest = plays.slice(1, 7);
  const roi = (bankroll.balance - bankroll.start) / bankroll.start;
  const openStaked = openBets.reduce((s, b) => s + b.stake, 0);

  return (
    <div className="screen dash">
      <div className="screen-head">
        <div>
          <div className="eyebrow">Command Center · Group Stage</div>
          <h1>Today&rsquo;s Best Value</h1>
        </div>
        <div className="head-meta">
          <span className="kicker">MON · JUN 15 · 2026</span>
          <span className="live-dot" /> 8 fixtures tracked
        </div>
      </div>

      <div className="dash-grid">
        {/* hero value play */}
        <div className="card hero-play">
          <div className="hero-tag"><Icon name="bolt" size={13} /> TOP VALUE PLAY</div>
          <div className="hero-body">
            <TeamToken code={hero.code} size={64} radius={16} />
            <div className="hero-info">
              <div className="hero-name">{hero.name}</div>
              <div className="hero-market">{hero.market}</div>
              <div className="hero-stats">
                <div className="hs"><label>BOOK ODDS</label><b className="mono">{WC.formatOdds(hero.dec, oddsFmt)}</b></div>
                <div className="hs"><label>MODEL WIN%</label><b className="mono">{fmtPct(hero.model)}</b></div>
                <div className="hs"><label>EXPECTED VALUE</label><b className="mono pos">{fmtSign(hero.ev)}</b></div>
                <div className="hs"><label>CONFIDENCE</label><b className="mono">{hero.conf}/100</b></div>
              </div>
            </div>
          </div>
          <div className="hero-foot">
            <ProbCompare implied={hero.implied} model={hero.model} />
            <div className="hero-cta">
              <div className="rec-stake">
                <label>RECOMMENDED STAKE</label>
                <b className="mono">{fmtMoney(hero.stake, bankroll.currency)}</b>
                <span className="ret">to return {fmtMoney(hero.stake * hero.dec, bankroll.currency)}</span>
              </div>
              <button className={`btn primary ${placed.has(hero.key) ? "is-done" : ""}`}
                disabled={placed.has(hero.key)} onClick={() => onAdd(hero)}>
                {placed.has(hero.key) ? "Added \u2713" : "Place Bet"}
              </button>
            </div>
          </div>
        </div>

        {/* bankroll snapshot */}
        <div className="card bankroll-snap" onClick={() => go("bankroll")}>
          <div className="card-head"><span>Bankroll</span><Icon name="arrow" size={15} /></div>
          <BalanceNumber value={bankroll.balance} sym={bankroll.currency} />
          <div className={`roi ${roi >= 0 ? "pos" : "neg"}`}>{fmtSign(roi)} ROI · all-time</div>
          <AreaChart data={bankroll.history} w={300} h={96} />
          <div className="snap-row">
            <div><label>OPEN STAKES</label><b className="mono">{fmtMoney(openStaked, bankroll.currency)}</b></div>
            <div><label>OPEN BETS</label><b className="mono">{openBets.length}</b></div>
          </div>
        </div>

        {/* value leaderboard */}
        <div className="card value-board">
          <div className="card-head"><span>Value Leaderboard</span>
            <span className="head-note">ranked by expected value</span></div>
          <div className="vb-list">
            {rest.map((p, i) => (
              <div className="vb-row" key={p.key}>
                <span className="vb-rank mono">{String(i + 2).padStart(2, "0")}</span>
                <TeamToken code={p.code} size={32} />
                <div className="vb-main">
                  <div className="vb-name">{p.name}<span className={`vb-type t-${p.type.toLowerCase()}`}>{p.type}</span></div>
                  <div className="vb-market">{p.market}</div>
                </div>
                <div className="vb-odds mono">{WC.formatOdds(p.dec, oddsFmt)}</div>
                <EdgeBadge value={p.ev} />
                <VerdictChip ev={p.ev} />
                <button className={`btn ghost sm ${placed.has(p.key) ? "is-done" : ""}`}
                  disabled={placed.has(p.key)} onClick={() => onAdd(p)}>
                  {placed.has(p.key) ? "\u2713" : "+ " + fmtMoney(p.stake, bankroll.currency)}
                </button>
              </div>
            ))}
          </div>
        </div>

        {/* upcoming matches strip */}
        <div className="card upcoming">
          <div className="card-head"><span>Next Fixtures</span>
            <button className="link-btn" onClick={() => go("matches")}>Analyze all <Icon name="arrow" size={13} /></button></div>
          <div className="up-list">
            {WC.matches.slice(0, 4).map((m) => (
              <button className="up-row" key={m.id} onClick={() => go("matches", m.id)}>
                <div className="up-teams">
                  <TeamToken code={m.home} size={28} radius={7} />
                  <span className="up-vs mono">v</span>
                  <TeamToken code={m.away} size={28} radius={7} />
                </div>
                <div className="up-when">
                  <span className="mono">{m.day} · {m.time}</span>
                  <span className="up-pick">Pick: {m.best.label}</span>
                </div>
                <EdgeBadge value={m.best.ev} size="sm" />
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

function BalanceNumber({ value, sym }) {
  const v = useCountUp(value);
  return <div className="balance-num mono">{fmtMoney(v, sym)}</div>;
}

/* ========================== OUTRIGHT BOARD ========================== */
function OutrightBoard({ WC, riskKey, oddsFmt, bankroll, placed, onAdd, goTeam }) {
  const [sort, setSort] = React.useState("ev");
  const [valueOnly, setValueOnly] = React.useState(false);
  const rows = React.useMemo(() => {
    let r = WC.teams.map((t) => ({
      ...t, key: "o:" + t.code,
      stake: WC.recommendedStake(t.model, t.dec, bankroll.balance, riskKey),
    }));
    if (valueOnly) r = r.filter((t) => t.ev > 0);
    const cmp = {
      ev: (a, b) => b.ev - a.ev, model: (a, b) => b.model - a.model,
      odds: (a, b) => a.dec - b.dec, conf: (a, b) => b.conf - a.conf,
    }[sort];
    return r.sort(cmp);
  }, [sort, valueOnly, riskKey, bankroll.balance, WC]);

  const valueCount = WC.teams.filter((t) => t.ev > 0).length;

  const Th = ({ id, children, num }) => (
    <th className={`${num ? "num" : ""} ${sort === id ? "sorted" : ""}`}
      onClick={id ? () => setSort(id) : undefined} style={{ cursor: id ? "pointer" : "default" }}>
      {children}{sort === id ? <span className="sort-caret">{"\u25BE"}</span> : null}
    </th>
  );

  return (
    <div className="screen outright">
      <div className="screen-head">
        <div>
          <div className="eyebrow">Outright Market · 24 contenders</div>
          <h1>Champion Value Board</h1>
        </div>
        <div className="head-meta">
          <span className="value-pill"><Icon name="bolt" size={12} /> {valueCount} value edges</span>
        </div>
      </div>

      <div className="toolbar">
        <div className="seg-group">
          {[["ev", "Expected value"], ["model", "Model win%"], ["odds", "Shortest odds"], ["conf", "Confidence"]].map(([id, lbl]) => (
            <button key={id} className={`seg ${sort === id ? "on" : ""}`} onClick={() => setSort(id)}>{lbl}</button>
          ))}
        </div>
        <button className={`toggle-pill ${valueOnly ? "on" : ""}`} onClick={() => setValueOnly(!valueOnly)}>
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
              <tr key={t.code} className={t.ev > 0.03 ? "row-value" : ""}>
                <td className="num rank mono">{String(i + 1).padStart(2, "0")}</td>
                <td className="team-cell clickable" onClick={() => goTeam(t.code)}><TeamToken code={t.code} size={30} /><span>{t.name}</span></td>
                <td className="mono grp">{t.group}</td>
                <td className="num mono">{WC.formatOdds(t.dec, oddsFmt)}</td>
                <td className="num mono dim">{fmtPct(t.implied)}</td>
                <td className="num mono">{fmtPct(t.model)}</td>
                <td className="num"><EdgeBadge value={t.ev} /></td>
                <td className="num"><ConfMeter value={t.conf} segments={6} /></td>
                <td className="num mono stake-cell">{t.ev > 0 ? fmtMoney(t.stake, bankroll.currency) : "\u2014"}</td>
                <td className="num">
                  <button className={`btn ghost sm ${placed.has(t.key) ? "is-done" : ""}`}
                    disabled={placed.has(t.key) || t.ev <= 0} onClick={() => onAdd({
                      key: t.key, name: t.name, code: t.code, market: "To win the World Cup",
                      dec: t.dec, model: t.model, ev: t.ev, stake: t.stake,
                    })}>
                    {placed.has(t.key) ? "\u2713" : "Bet"}
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

/* ========================== MATCH ANALYSIS ========================== */
const NEWS_TAG = { injury: "INJURY", form: "FORM", lineup: "LINEUP", susp: "SUSP", intel: "INTEL" };
function NewsItem({ n }) {
  return (
    <div className="news-item">
      <span className={`news-tag t-${n.tag}`}>{NEWS_TAG[n.tag]}</span>
      <div className="news-b"><p>{n.text}</p><time>{n.time}</time></div>
    </div>
  );
}

const CMP_ROWS = [
  { label: "FIFA Rank", key: "rank", invert: true, max: 30, fmt: (v) => "#" + v },
  { label: "Goals / game", key: "gpg", max: 2.6, fmt: (v) => v.toFixed(1) },
  { label: "Expected goals (xG)", key: "xg", max: 2.4, fmt: (v) => v.toFixed(1) },
  { label: "Possession", key: "poss", max: 70, fmt: (v) => v + "%" },
  { label: "Clean sheets", key: "cs", max: 70, fmt: (v) => v + "%" },
];
function CompareCard({ m, WC }) {
  const hs = WC.STATS[m.home], as = WC.STATS[m.away];
  if (!hs || !as) return null;
  const pct = (v, r) => {
    const p = r.invert ? (r.max - v) / r.max : v / r.max;
    return Math.max(5, Math.min(100, p * 100));
  };
  return (
    <div className="card compare">
      <div className="card-head"><span>Team Comparison</span><span className="head-note">season form</span></div>
      <div className="cmp-legend">
        <span><i className="cdot home" /> {m.home}</span>
        <span>{m.away} <i className="cdot away" /></span>
      </div>
      {CMP_ROWS.map((r) => (
        <div className="cmp-row" key={r.key}>
          <div className="cmp-top">
            <span className="cmp-v">{r.fmt(hs[r.key])}</span>
            <span className="cmp-lbl">{r.label}</span>
            <span className="cmp-v">{r.fmt(as[r.key])}</span>
          </div>
          <div className="cmp-bars">
            <div className="cmp-track left"><span className="cmp-fill home" style={{ width: pct(hs[r.key], r) + "%" }} /></div>
            <div className="cmp-track right"><span className="cmp-fill away" style={{ width: pct(as[r.key], r) + "%" }} /></div>
          </div>
        </div>
      ))}
    </div>
  );
}

function H2HCard({ m }) {
  return (
    <div className="card h2h">
      <div className="card-head"><span>Head to Head</span><span className="head-note">recent meetings</span></div>
      <div className="h2h-list">
        {m.h2h.map((h, i) => (
          <div className="h2h-row" key={i}>
            <span className="h2h-d mono">{h.d}</span>
            <span className="h2h-s mono">{h.s}</span>
            <span className="h2h-n">{h.n}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

function MarketRow({ s, m, WC, riskKey, oddsFmt, bankroll, placed, onAdd }) {
  const stake = WC.recommendedStake(s.model, s.dec, bankroll.balance, riskKey);
  const isTop = m.topMarket && s.key === m.topMarket.key;
  return (
    <div className={`mk-row ${isTop ? "is-top" : ""}`}>
      <span className="mk-label">{s.label}{isTop && <span className="mk-top"><Icon name="bolt" size={9} /> best edge</span>}</span>
      <span className="mk-odds mono">{WC.formatOdds(s.dec, oddsFmt)}</span>
      <span className="mk-model mono dim">{fmtPct(s.model)}</span>
      <span className="r"><EdgeBadge value={s.ev} size="sm" /></span>
      <span className="r"><VerdictChip ev={s.ev} /></span>
      <span className="mk-stake mono">{s.ev > 0 ? fmtMoney(stake, bankroll.currency) : "\u2014"}</span>
      <button className={`btn ghost sm ${placed.has(s.key) ? "is-done" : ""}`}
        disabled={placed.has(s.key) || s.ev <= 0}
        onClick={() => onAdd({ key: s.key, name: s.label, code: s.code,
          market: s.cat + " · " + s.label + " — " + m.home + " v " + m.away,
          dec: s.dec, model: s.model, ev: s.ev, stake })}>
        {placed.has(s.key) ? "\u2713" : "Bet"}
      </button>
    </div>
  );
}

const MK_TABS = [
  ["All", "All"], ["Match Result", "Result"], ["Double Chance", "Dbl Chance"],
  ["Draw No Bet", "DNB"], ["Total Goals", "Goals"], ["Both Teams Score", "BTTS"],
];

function MatchAnalysis({ WC, riskKey, oddsFmt, bankroll, placed, onAdd, focusId, goTeam }) {
  const [sel, setSel] = React.useState(focusId || WC.matches[0].id);
  const [mkCat, setMkCat] = React.useState("All");
  React.useEffect(() => { if (focusId) setSel(focusId); }, [focusId]);
  const m = WC.matches.find((x) => x.id === sel) || WC.matches[0];
  const cats = (m.markets || []).filter((c) => mkCat === "All" || c.cat === mkCat);

  return (
    <div className="screen match">
      <div className="screen-head">
        <div>
          <div className="eyebrow">Single Match Model</div>
          <h1>Match Analysis</h1>
        </div>
      </div>

      <div className="match-layout">
        <div className="match-list">
          {WC.matches.map((x) => (
            <button key={x.id} className={`ml-row ${x.id === sel ? "on" : ""}`} onClick={() => setSel(x.id)}>
              <div className="ml-teams">
                <TeamToken code={x.home} size={26} radius={6} />
                <TeamToken code={x.away} size={26} radius={6} />
              </div>
              <div className="ml-info">
                <div className="ml-name">{x.home} <span className="dim">v</span> {x.away}</div>
                <div className="ml-when mono">{x.day} · {x.time}</div>
              </div>
              <EdgeBadge value={x.best.ev} size="sm" />
            </button>
          ))}
        </div>

        <div className="match-detail">
          <div className="card md-head">
            <div className="md-fixture">
              <div className="md-team clickable" onClick={() => goTeam(m.home)}>
                <TeamToken code={m.home} size={56} radius={14} />
                <div><div className="md-tname">{m.homeName}</div><FormDots form={WC.teams.find(t=>t.code===m.home)?.form || "WWDLW"} size={13} /></div>
              </div>
              <div className="md-vs">
                <span className="mono">VS</span>
                <span className="md-conf"><Icon name="target" size={12} /> {m.conf}/100 conf</span>
              </div>
              <div className="md-team right clickable" onClick={() => goTeam(m.away)}>
                <div><div className="md-tname">{m.awayName}</div><FormDots form={WC.teams.find(t=>t.code===m.away)?.form || "WDWLD"} size={13} /></div>
                <TeamToken code={m.away} size={56} radius={14} />
              </div>
            </div>
            <div className="md-meta">
              <span><Icon name="clock" size={13} /> {m.day} · {m.time} ET</span>
              <span><Icon name="pin" size={13} /> {m.venue}</span>
              <span className="grp-tag">Group {m.group}</span>
            </div>
          </div>

          <div className="outcome-grid">
            {m.legs.map((leg) => {
              const isBest = leg.kind === m.best.kind;
              const stake = WC.recommendedStake(leg.model, leg.dec, bankroll.balance, riskKey);
              const key = "m:" + m.id + ":" + leg.kind;
              return (
                <div key={leg.kind} className={`card outcome ${isBest ? "best" : ""}`}>
                  {isBest && <div className="best-flag"><Icon name="bolt" size={11} /> MODEL PICK</div>}
                  <div className="oc-head">
                    <span className="oc-label">{leg.label}</span>
                    <VerdictChip ev={leg.ev} />
                  </div>
                  <div className="oc-odds mono">{WC.formatOdds(leg.dec, oddsFmt)}</div>
                  <ProbCompare implied={leg.implied} model={leg.model} />
                  <div className="oc-ev">
                    <div><label>EXPECTED VALUE</label><EdgeBadge value={leg.ev} size="lg" /></div>
                    <div className="oc-stake"><label>STAKE</label>
                      <b className="mono">{leg.ev > 0 ? fmtMoney(stake, bankroll.currency) : "\u2014"}</b></div>
                  </div>
                  <button className={`btn ${isBest ? "primary" : "ghost"} ${placed.has(key) ? "is-done" : ""}`}
                    disabled={placed.has(key) || leg.ev <= 0}
                    onClick={() => onAdd({ key, name: leg.label, code: leg.kind === "away" ? m.away : m.home,
                      market: leg.label + " — " + m.homeName + " v " + m.awayName, dec: leg.dec, model: leg.model, ev: leg.ev, stake })}>
                    {placed.has(key) ? "Added \u2713" : leg.ev > 0 ? "Place Bet" : "No value"}
                  </button>
                </div>
              );
            })}
          </div>

          <Pitch m={m} WC={WC} />

          <div className="card markets">
            <div className="card-head"><span>All Markets</span>
              {m.topMarket && <span className="head-note">best edge: {m.topMarket.cat} · {m.topMarket.label} <span className="pos">{fmtSign(m.topMarket.ev)}</span></span>}</div>
            <div className="seg-group sm mk-tabs">
              {MK_TABS.map(([id, lbl]) => (
                <button key={id} className={`seg ${mkCat === id ? "on" : ""}`} onClick={() => setMkCat(id)}>{lbl}</button>
              ))}
            </div>
            <div className="mk-table">
              <div className="mk-row mk-headrow">
                <span>Selection</span><span>Odds</span><span>Model</span>
                <span className="r">Edge</span><span className="r">Verdict</span><span>Stake</span><span></span>
              </div>
              {cats.map((c) => (
                <React.Fragment key={c.cat}>
                  <div className="mk-group">{c.cat}<span className="mk-group-note">{c.note}</span></div>
                  {c.sels.map((s) => (
                    <MarketRow key={s.key} s={s} m={m} WC={WC} riskKey={riskKey}
                      oddsFmt={oddsFmt} bankroll={bankroll} placed={placed} onAdd={onAdd} />
                  ))}
                </React.Fragment>
              ))}
            </div>
          </div>

          <div className="mid-grid">
            <CompareCard m={m} WC={WC} />
            <H2HCard m={m} />
          </div>

          <div className="card news">
            <div className="card-head"><span>Team News &amp; Intel</span><span className="head-note">latest reports</span></div>
            <div className="news-cols">
              {[m.home, m.away].map((code) => (
                <div className="news-col" key={code}>
                  <div className="news-col-head"><TeamToken code={code} size={26} radius={7} />
                    <b>{WC.NAME[code]}</b><FormDots form={WC.teams.find((t) => t.code === code)?.form || "WWDLW"} size={11} /></div>
                  {(WC.NEWS[code] || []).map((n, i) => <NewsItem key={i} n={n} />)}
                </div>
              ))}
            </div>
          </div>

          <div className="card md-note">
            <div className="note-head"><Icon name="target" size={14} /> Model read</div>
            <p>The model gives <b>{m.homeName}</b> a {fmtPct(m.legs[0].model)} win probability versus the book&rsquo;s implied {fmtPct(m.legs[0].implied)},
              with a projected goal expectation of <b className="mono">{m.mu ? m.mu.toFixed(2) : "\u2014"}</b>.
              The best edge on the board is <b>{m.topMarket ? m.topMarket.cat + " · " + m.topMarket.label : m.best.label}</b> at <span className="pos">{fmtSign(m.topMarket ? m.topMarket.ev : m.best.ev)}</span> EV,
              backed by recent form and a confidence rating of {m.conf}/100. Stakes scale to your {WC.RISK[riskKey].label.toLowerCase()} profile.</p>
          </div>
        </div>
      </div>
    </div>
  );
}

/* ========================= BANKROLL TRACKER ========================= */
function BankrollTracker({ WC, bankroll, oddsFmt, openBets, onRemove }) {
  const roi = (bankroll.balance - bankroll.start) / bankroll.start;
  const settled = WC.settledBets;
  const wins = settled.filter((b) => b.result === "won");
  const winRate = wins.length / settled.length;
  const totalStaked = settled.reduce((s, b) => s + b.stake, 0);
  const totalPnl = settled.reduce((s, b) => s + b.pnl, 0);
  const openStaked = openBets.reduce((s, b) => s + b.stake, 0);
  const openReturn = openBets.reduce((s, b) => s + b.stake * b.dec, 0);

  const stats = [
    { label: "Settled P&L", val: fmtMoney(totalPnl, bankroll.currency), cls: totalPnl >= 0 ? "pos" : "neg" },
    { label: "Win rate", val: fmtPct(winRate, 0) },
    { label: "Total staked", val: fmtMoney(totalStaked, bankroll.currency) },
    { label: "Open exposure", val: fmtMoney(openStaked, bankroll.currency) },
  ];

  return (
    <div className="screen bankroll">
      <div className="screen-head">
        <div>
          <div className="eyebrow">Money Management</div>
          <h1>Bankroll Tracker</h1>
        </div>
        <div className="head-meta"><span className="kicker">START {fmtMoney(bankroll.start, bankroll.currency)}</span></div>
      </div>

      <div className="bk-top">
        <div className="card bk-hero">
          <label>CURRENT BALANCE</label>
          <BalanceNumber value={bankroll.balance} sym={bankroll.currency} />
          <div className={`roi ${roi >= 0 ? "pos" : "neg"}`}>{fmtSign(roi)} ROI · {fmtMoney(bankroll.balance - bankroll.start, bankroll.currency)} all-time</div>
          <AreaChart data={bankroll.history} w={560} h={150} />
        </div>
        <div className="bk-stats">
          {stats.map((s) => (
            <div className="card stat-card" key={s.label}>
              <label>{s.label}</label>
              <b className={`mono ${s.cls || ""}`}>{s.val}</b>
            </div>
          ))}
        </div>
      </div>

      <div className="bk-tables">
        <div className="card">
          <div className="card-head"><span>Open Positions</span>
            <span className="head-note">{openBets.length} active · {fmtMoney(openReturn, bankroll.currency)} potential return</span></div>
          {openBets.length === 0 ? (
            <div className="empty">No open bets yet. Add picks from the Dashboard, Board, or Match Analysis.</div>
          ) : (
            <table className="data-table compact">
              <thead><tr><th>Pick</th><th className="num">Odds</th><th className="num">Stake</th><th className="num">To return</th><th></th></tr></thead>
              <tbody>
                {openBets.map((b) => (
                  <tr key={b.key}>
                    <td className="team-cell"><TeamToken code={WC.COLORS[b.code] ? b.code : "ESP"} size={26} /><span className="bet-pick">{b.market}</span></td>
                    <td className="num mono">{WC.formatOdds(b.dec, oddsFmt)}</td>
                    <td className="num mono">{fmtMoney(b.stake, bankroll.currency)}</td>
                    <td className="num mono pos">{fmtMoney(b.stake * b.dec, bankroll.currency)}</td>
                    <td className="num"><button className="btn ghost sm" onClick={() => onRemove(b.key)}>Void</button></td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>

        <div className="card">
          <div className="card-head"><span>Settled History</span></div>
          <table className="data-table compact">
            <thead><tr><th>Pick</th><th className="num">Stake</th><th className="num">Odds</th><th className="num">Result</th><th className="num">P&L</th></tr></thead>
            <tbody>
              {settled.map((b) => (
                <tr key={b.id}>
                  <td className="team-cell"><TeamToken code={b.team} size={26} /><span className="bet-pick">{b.pick}</span></td>
                  <td className="num mono">{fmtMoney(b.stake, bankroll.currency)}</td>
                  <td className="num mono">{WC.formatOdds(b.dec, oddsFmt)}</td>
                  <td className="num"><span className={`result ${b.result}`}>{b.result === "won" ? "WON" : "LOST"}</span></td>
                  <td className={`num mono ${b.pnl >= 0 ? "pos" : "neg"}`}>{fmtMoney(b.pnl, bankroll.currency)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

Object.assign(window, { Dashboard, OutrightBoard, MatchAnalysis, BankrollTracker, buildValuePlays });
