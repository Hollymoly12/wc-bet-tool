/* ============================================================================
   TeamTokenWithColors.jsx
   TeamToken wrapper that auto-resolves colors from a shared color cache.
   The cache is populated lazily from /teams API. Pass colorMap from context.
   ========================================================================== */
import React from 'react';
import { TeamToken } from './primitives.jsx';

// Global fallback color map — populated by App on teams fetch
let _colorMap = {};
export function setColorMap(map) { _colorMap = map; }
export function getColorMap() { return _colorMap; }

export function TeamTokenAuto({ code, size, radius }) {
  const colors = _colorMap[code] || ['#1a1e28', '#2a2f3e'];
  return <TeamToken code={code} size={size} radius={radius} colors={colors} />;
}
