/* ============================================================================
   components.jsx — shared UI primitives for the World Cup Bet Tool
   Exports to window. Loaded after React + Babel.
   ========================================================================== */

/* ---- formatting helpers ---------------------------------------------- */
const fmtPct = (n, d = 1) => `${(n * 100).toFixed(d)}%`;
const fmtSign = (n, d = 1) => `${n >= 0 ? "+" : "\u2212"}${Math.abs(n * 100).toFixed(d)}%`;
const fmtMoney = (n, sym = "$") =>
  `${n < 0 ? "\u2212" : ""}${sym}${Math.abs(Math.round(n)).toLocaleString("en-US")}`;

/* ---- count-up hook for hero numbers ---------------------------------- */
function useCountUp(target, dur = 850) {
  const [val, setVal] = React.useState(target);
  const fromRef = React.useRef(target);
  React.useEffect(() => {
    const from = fromRef.current;
    const t0 = performance.now();
    let raf;
    const tick = (now) => {
      const p = Math.min(1, (now - t0) / dur);
      const e = 1 - Math.pow(1 - p, 3); // easeOutCubic
      setVal(from + (target - from) * e);
      if (p < 1) raf = requestAnimationFrame(tick);
      else fromRef.current = target;
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, [target, dur]);
  return val;
}

/* ---- duotone country token ------------------------------------------- */
function TeamToken({ code, size = 34, radius = 9 }) {
  const colors = (window.WC && window.WC.COLORS[code]) || ["#333", "#666"];
  const fs = Math.round(size * 0.36);
  return (
    <div
      className="team-token"
      style={{
        width: size, height: size, borderRadius: radius, fontSize: fs,
        background: `linear-gradient(135deg, ${colors[0]} 0 48%, ${colors[1]} 52% 100%)`,
      }}
    >
      <span style={{ fontSize: fs }}>{code}</span>
    </div>
  );
}

/* ---- W/D/L form trail ------------------------------------------------- */
function FormDots({ form, size = 14 }) {
  const map = { W: "var(--pos)", D: "var(--muted)", L: "var(--neg)" };
  return (
    <div className="form-dots" style={{ gap: Math.round(size * 0.32) }}>
      {form.split("").map((r, i) => (
        <span
          key={i}
          title={r === "W" ? "Win" : r === "D" ? "Draw" : "Loss"}
          style={{
            width: size, height: size, borderRadius: 4,
            background: map[r], color: r === "D" ? "#0b0d12" : "#0b0d12",
            fontSize: Math.round(size * 0.62),
          }}
        >
          {r}
        </span>
      ))}
    </div>
  );
}

/* ---- EV / edge badge -------------------------------------------------- */
function EdgeBadge({ value, kind = "ev", size = "md" }) {
  // value is a fraction (e.g. 0.127 = +12.7%)
  const pos = value >= 0;
  return (
    <span className={`edge-badge ${pos ? "is-pos" : "is-neg"} sz-${size}`}>
      <svg viewBox="0 0 10 10" width="9" height="9" aria-hidden="true"
        style={{ transform: pos ? "none" : "rotate(180deg)" }}>
        <path d="M5 1 L9 8 L1 8 Z" fill="currentColor" />
      </svg>
      {fmtSign(value)}
    </span>
  );
}

/* ---- verdict chip (BET / VALUE / PASS / AVOID) ----------------------- */
function VerdictChip({ ev }) {
  let label, cls;
  if (ev >= 0.10) { label = "STRONG BET"; cls = "v-strong"; }
  else if (ev >= 0.03) { label = "VALUE"; cls = "v-value"; }
  else if (ev >= -0.03) { label = "LEAN PASS"; cls = "v-pass"; }
  else { label = "AVOID"; cls = "v-avoid"; }
  return <span className={`verdict ${cls}`}>{label}</span>;
}

/* ---- implied vs model probability compare bar ------------------------ */
function ProbCompare({ implied, model, height = 8 }) {
  const max = Math.max(implied, model, 0.001);
  return (
    <div className="prob-compare">
      <div className="prob-line">
        <span className="prob-tag">IMPL</span>
        <div className="prob-track" style={{ height }}>
          <div className="prob-fill impl" style={{ width: `${(implied / max) * 100}%` }} />
        </div>
        <span className="prob-num">{fmtPct(implied)}</span>
      </div>
      <div className="prob-line">
        <span className="prob-tag">MODEL</span>
        <div className="prob-track" style={{ height }}>
          <div className="prob-fill model" style={{ width: `${(model / max) * 100}%` }} />
        </div>
        <span className="prob-num">{fmtPct(model)}</span>
      </div>
    </div>
  );
}

/* ---- confidence meter ------------------------------------------------- */
function ConfMeter({ value, segments = 10 }) {
  const lit = Math.round((value / 100) * segments);
  return (
    <div className="conf-meter" title={`Model confidence ${value}/100`}>
      <div className="conf-bars">
        {Array.from({ length: segments }).map((_, i) => (
          <span key={i} className={i < lit ? "on" : ""} />
        ))}
      </div>
      <span className="conf-val">{value}</span>
    </div>
  );
}

/* ---- bankroll area sparkline ----------------------------------------- */
function AreaChart({ data, w = 520, h = 170, pad = 8 }) {
  const vals = data.map((d) => d.v);
  const min = Math.min(...vals), max = Math.max(...vals);
  const span = max - min || 1;
  const innerW = w - pad * 2, innerH = h - pad * 2 - 18;
  const x = (i) => pad + (i / (data.length - 1)) * innerW;
  const y = (v) => pad + innerH - ((v - min) / span) * innerH;
  const line = data.map((d, i) => `${i ? "L" : "M"}${x(i).toFixed(1)},${y(d.v).toFixed(1)}`).join(" ");
  const area = `${line} L${x(data.length - 1).toFixed(1)},${pad + innerH} L${x(0).toFixed(1)},${pad + innerH} Z`;
  const last = data[data.length - 1];
  return (
    <svg className="area-chart" viewBox={`0 0 ${w} ${h}`} preserveAspectRatio="none" width="100%" height={h}>
      <defs>
        <linearGradient id="acFill" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="var(--accent)" stopOpacity="0.28" />
          <stop offset="100%" stopColor="var(--accent)" stopOpacity="0" />
        </linearGradient>
      </defs>
      {[0.25, 0.5, 0.75].map((g) => (
        <line key={g} x1={pad} x2={w - pad} y1={pad + innerH * g} y2={pad + innerH * g}
          stroke="rgba(255,255,255,.05)" strokeWidth="1" />
      ))}
      <path d={area} fill="url(#acFill)" />
      <path d={line} fill="none" stroke="var(--accent)" strokeWidth="2.5"
        strokeLinejoin="round" strokeLinecap="round" />
      <circle cx={x(data.length - 1)} cy={y(last.v)} r="4.5" fill="var(--accent)" />
      <circle cx={x(data.length - 1)} cy={y(last.v)} r="9" fill="var(--accent)" opacity="0.18" />
      {data.map((d, i) => (
        <text key={i} x={x(i)} y={h - 4} fill="var(--faint)" fontSize="10"
          textAnchor="middle" fontFamily="var(--mono)">{d.label}</text>
      ))}
    </svg>
  );
}

/* ---- nav / ui icons --------------------------------------------------- */
const Icon = ({ name, size = 18 }) => {
  const p = {
    width: size, height: size, viewBox: "0 0 24 24", fill: "none",
    stroke: "currentColor", strokeWidth: 1.8, strokeLinecap: "round", strokeLinejoin: "round",
  };
  switch (name) {
    case "dashboard":
      return <svg {...p}><rect x="3" y="3" width="7" height="9" rx="1.5" /><rect x="14" y="3" width="7" height="5" rx="1.5" /><rect x="14" y="12" width="7" height="9" rx="1.5" /><rect x="3" y="16" width="7" height="5" rx="1.5" /></svg>;
    case "trophy":
      return <svg {...p}><path d="M7 4h10v4a5 5 0 0 1-10 0V4Z" /><path d="M7 6H4v1a3 3 0 0 0 3 3M17 6h3v1a3 3 0 0 1-3 3" /><path d="M12 13v4M9 21h6M10 17h4v4h-4z" /></svg>;
    case "match":
      return <svg {...p}><circle cx="12" cy="12" r="9" /><path d="M12 3v18M3 12h18" /></svg>;
    case "wallet":
      return <svg {...p}><rect x="3" y="6" width="18" height="13" rx="2.5" /><path d="M3 9h18M16 13h2" /></svg>;
    case "bolt":
      return <svg {...p} fill="currentColor" stroke="none"><path d="M13 2 4 14h6l-1 8 9-12h-6l1-8Z" /></svg>;
    case "arrow":
      return <svg {...p}><path d="M5 12h14M13 6l6 6-6 6" /></svg>;
    case "clock":
      return <svg {...p}><circle cx="12" cy="12" r="9" /><path d="M12 7v5l3 2" /></svg>;
    case "target":
      return <svg {...p}><circle cx="12" cy="12" r="9" /><circle cx="12" cy="12" r="5" /><circle cx="12" cy="12" r="1.4" fill="currentColor" /></svg>;
    case "pin":
      return <svg {...p}><path d="M12 21s7-6 7-11a7 7 0 1 0-14 0c0 5 7 11 7 11Z" /><circle cx="12" cy="10" r="2.5" /></svg>;
    case "stats":
      return <svg {...p}><path d="M4 20V10M9.5 20V4M15 20v-7M20.5 20V8" /></svg>;
    case "groups":
      return <svg {...p}><rect x="3" y="3" width="7" height="7" rx="1.5" /><rect x="14" y="3" width="7" height="7" rx="1.5" /><rect x="3" y="14" width="7" height="7" rx="1.5" /><rect x="14" y="14" width="7" height="7" rx="1.5" /></svg>;
    case "bracket":
      return <svg {...p}><path d="M4 5h5v6h4M4 19h5v-6M15 9h5M15 9v6h-5M20 9v0" /><path d="M4 5v0M15 9h5v6h-5" /></svg>;
    default:
      return null;
  }
};

Object.assign(window, {
  fmtPct, fmtSign, fmtMoney, useCountUp,
  TeamToken, FormDots, EdgeBadge, VerdictChip, ProbCompare, ConfMeter, AreaChart, Icon,
});
