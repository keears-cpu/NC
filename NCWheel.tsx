import React, { useMemo } from "react";
import AriesIcon from "./symbols/Aries.svg?url";
import TaurusIcon from "./symbols/Taurus.svg?url";
import GeminiIcon from "./symbols/Gemini.svg?url";
import CancerIcon from "./symbols/Cancer.svg?url";
import LeoIcon from "./symbols/Leo.svg?url";
import VirgoIcon from "./symbols/Virgo.svg?url";
import LibraIcon from "./symbols/Libra.svg?url";
import ScorpioIcon from "./symbols/Scorpio.svg?url";
import SagittariusIcon from "./symbols/Sagittarius.svg?url";
import CapricornIcon from "./symbols/Capricorn.svg?url";
import AquariusIcon from "./symbols/Aquarius.svg?url";
import PiscesIcon from "./symbols/Pisces.svg?url";

type AngleKey = "asc" | "mc" | "dsc" | "ic";
type Classification = "planet" | "asteroid" | "mathematical_point" | "angle" | "hypothetical";

type Body = {
  id: string;
  label: string;
  classification: Classification;
  sign: string;
  degree: number;
  formatted: string;
  lon: number;
  house?: number | null;
  retrograde?: boolean;
};

type Point = {
  id: string;
  label: string;
  classification: Classification;
  definition?: string;
  sign: string;
  degree: number;
  formatted: string;
  lon: number;
  house?: number | null;
  retrograde?: boolean;
};

type HouseCusp = {
  house: number;
  sign: string;
  degree: number;
  formatted: string;
  lon: number;
};

type AnglePoint = {
  id: AngleKey;
  label: string;
  sign: string;
  degree: number;
  formatted: string;
  lon: number;
};

type Aspect = {
  id: string;
  point_a: string;
  point_b: string;
  aspect_type: string;
};

type NatalChartRecord = {
  metadata: {
    chart_id: string;
    status: string;
    warnings?: string[];
    engine_name?: string;
  };
  input: {
    person_name?: string | null;
    birth_date: string;
    birth_time_local: string;
    timezone: string;
    birth_place_name: string;
  };
  settings: {
    zodiac_type: string;
    house_system: string;
    node_mode: string;
    lilith_mode: string;
  };
  angles: Record<AngleKey, AnglePoint>;
  houses: HouseCusp[];
  bodies: Body[];
  points: Point[];
  aspects: Aspect[];
  availability?: {
    core_complete?: boolean;
    soft_missing?: string[];
  };
};

type HexagramArc = {
  key: string;
  gate: number;
  line: number;
  symbol?: string;
  startLon: number;
  endLon: number;
};

type HexagramBand = {
  gate: number;
  symbol?: string;
  startLon: number;
  endLon: number;
};

type Plottable = Body | Point | { id: string; label: string; classification: Classification; degree: number; lon: number; retrograde?: boolean };

type AdvancedAstroWheelProps = {
  chart: NatalChartRecord;
  size?: number;
  hexagramCsvText?: string;
  show64Key?: boolean;
  className?: string;
};

const ZODIAC_SYMBOLS: Record<string, string> = {
  Aries: AriesIcon,
  Taurus: TaurusIcon,
  Gemini: GeminiIcon,
  Cancer: CancerIcon,
  Leo: LeoIcon,
  Virgo: VirgoIcon,
  Libra: LibraIcon,
  Scorpio: ScorpioIcon,
  Sagittarius: SagittariusIcon,
  Capricorn: CapricornIcon,
  Aquarius: AquariusIcon,
  Pisces: PiscesIcon,
};

const ELEMENT_FILL: Record<string, string> = {
  Aries: "#fde8e8",
  Taurus: "#ecf6e9",
  Gemini: "#e8f2fc",
  Cancer: "#f2edf9",
  Leo: "#fde8e8",
  Virgo: "#ecf6e9",
  Libra: "#e8f2fc",
  Scorpio: "#f2edf9",
  Sagittarius: "#fde8e8",
  Capricorn: "#ecf6e9",
  Aquarius: "#e8f2fc",
  Pisces: "#f2edf9",
};

const SIGN_SEQUENCE = [
  "Aries",
  "Taurus",
  "Gemini",
  "Cancer",
  "Leo",
  "Virgo",
  "Libra",
  "Scorpio",
  "Sagittarius",
  "Capricorn",
  "Aquarius",
  "Pisces",
] as const;

const SIGN_ICON_OFFSET: Record<string, { x: number; y: number }> = {
  Aries: { x: 0, y: 0 },
  Taurus: { x: 0, y: 0 },
  Gemini: { x: 0, y: 0 },
  Cancer: { x: 0, y: 0 },
  Leo: { x: 0, y: 0 },
  Virgo: { x: 0, y: 0 },
  Libra: { x: 0, y: 0 },
  Scorpio: { x: 0, y: 0 },
  Sagittarius: { x: 0, y: 0 },
  Capricorn: { x: 0, y: 0 },
  Aquarius: { x: 0, y: 0 },
  Pisces: { x: 0, y: 0 },
};

const BODY_GLYPH: Record<string, string> = {
  sun: "☉",
  moon: "☽",
  mercury: "☿",
  venus: "♀",
  mars: "♂",
  jupiter: "♃",
  saturn: "♄",
  uranus: "♅",
  neptune: "♆",
  pluto: "♇",
  chiron: "⚷",
  north_node_true: "☊",
  north_node_mean: "☊",
  lilith_mean: "⚸",
  lilith_true: "⚸",
  fortune: "⊗",
  vertex: "Vx",
  asc: "ASC",
  mc: "MC",
  dsc: "DSC",
  ic: "IC",
};

const ASPECT_STYLE: Record<string, { stroke: string; width: number; dasharray?: string }> = {
  conjunction: { stroke: "#94a3b8", width: 1 },
  sextile: { stroke: "#3b82f6", width: 1.1 },
  square: { stroke: "#ef4444", width: 1.1 },
  trine: { stroke: "#3b82f6", width: 1.1 },
  opposition: { stroke: "#ef4444", width: 1.2 },
  quincunx: { stroke: "#f59e0b", width: 0.95, dasharray: "4 3" },
};

const MAJOR_PLANETS = new Set(["sun", "moon", "mercury", "venus", "mars", "jupiter", "saturn", "uranus", "neptune", "pluto"]);
const DEEP_GRAY = "#475569";

function normalizeLon(lon: number) {
  let value = lon % 360;
  if (value < 0) value += 360;
  return value;
}

function polarRelative(lon: number, anchorLon: number, radius: number, center: number) {
  const delta = normalizeLon(lon - anchorLon);
  const theta = ((180 - delta) * Math.PI) / 180;
  return {
    x: center + Math.cos(theta) * radius,
    y: center + Math.sin(theta) * radius,
  };
}

function linePoint(center: number, radius: number, lon: number, anchorLon: number) {
  return polarRelative(lon, anchorLon, radius, center);
}

function midpointLon(startLon: number, endLon: number) {
  return normalizeLon(startLon + normalizeLon(endLon - startLon) / 2);
}

function signOfLon(lon: number) {
  return SIGN_SEQUENCE[Math.floor(normalizeLon(lon) / 30)];
}

function formatDeg(value: number) {
  const deg = Math.floor(value);
  const min = Math.round((value - deg) * 60);
  return `${deg}°${String(min).padStart(2, "0")}’`;
}

function ringArcPath(center: number, outerR: number, innerR: number, startLon: number, endLon: number, anchorLon: number) {
  const p1 = polarRelative(startLon, anchorLon, outerR, center);
  const p2 = polarRelative(endLon, anchorLon, outerR, center);
  const p3 = polarRelative(endLon, anchorLon, innerR, center);
  const p4 = polarRelative(startLon, anchorLon, innerR, center);
  const largeArc = normalizeLon(endLon - startLon) > 180 ? 1 : 0;
  return [
    `M ${p1.x} ${p1.y}`,
    `A ${outerR} ${outerR} 0 ${largeArc} 0 ${p2.x} ${p2.y}`,
    `L ${p3.x} ${p3.y}`,
    `A ${innerR} ${innerR} 0 ${largeArc} 1 ${p4.x} ${p4.y}`,
    "Z",
  ].join(" ");
}

function parseHexagramCsv(csvText?: string): HexagramArc[] {
  if (!csvText?.trim()) return [];

  const signBase: Record<string, number> = {
    양: 0,
    양자리: 0,
    황소: 30,
    황소자리: 30,
    쌍둥: 60,
    쌍둥이: 60,
    쌍둥이자리: 60,
    게: 90,
    게자리: 90,
    사자: 120,
    사자자리: 120,
    처녀: 150,
    처녀자리: 150,
    천칭: 180,
    천칭자리: 180,
    전갈: 210,
    전갈자리: 210,
    사수: 240,
    사수자리: 240,
    염소: 270,
    염소자리: 270,
    물병: 300,
    물병자리: 300,
    물고기: 330,
    물고기자리: 330,
  };

  const lines = csvText.split(/\r?\n/).map((value) => value.trim()).filter(Boolean);
  const parsed: HexagramArc[] = [];

  for (const line of lines.slice(1)) {
    const firstComma = line.indexOf(",");
    const lastComma = line.lastIndexOf(",");
    if (firstComma < 0 || lastComma < 0 || firstComma === lastComma) continue;

    const key = line.slice(0, firstComma).trim();
    const degreeRange = line.slice(firstComma + 1, lastComma).trim().replace(/^"|"$/g, "");
    const rawSymbol = line.slice(lastComma + 1).trim();
    const symbol = rawSymbol.split(/\s+/)[0] || "";
    const [gateText, lineText] = key.split(".");
    const gate = Number(gateText);
    const lineNo = Number(lineText);
    if (!Number.isFinite(gate) || !Number.isFinite(lineNo)) continue;

    const match = degreeRange.match(/^([^\s]+)\s+(\d{2})°\s*(\d{2})['’](?:\s*\d{2}(?:"|”){1,2})?\s*~\s*(\d{2})°\s*(\d{2})['’](?:\s*\d{2}(?:"|”){1,2})?$/);
    if (!match) continue;

    const [, signKo, startDeg, startMin, endDeg, endMin] = match;
    const base = signBase[signKo];
    if (base == null) continue;

    parsed.push({
      key,
      gate,
      line: lineNo,
      symbol,
      startLon: base + Number(startDeg) + Number(startMin) / 60,
      endLon: base + Number(endDeg) + Number(endMin) / 60,
    });
  }

  return parsed;
}

function buildHexagramFallback() {
  const bands: HexagramArc[] = [];
  const step = 360 / 64;
  for (let i = 0; i < 64; i += 1) {
    bands.push({
      key: `${i + 1}.1`,
      gate: i + 1,
      line: 1,
      startLon: i * step,
      endLon: (i + 1) * step,
    });
  }
  return bands;
}

function groupHexagramBands(items: HexagramArc[]): HexagramBand[] {
  if (!items.length) return [];
  const bands: HexagramBand[] = [];
  let current: HexagramBand | null = null;
  for (const item of items) {
    if (!current || current.gate !== item.gate) {
      if (current) bands.push(current);
      current = { gate: item.gate, symbol: item.symbol, startLon: item.startLon, endLon: item.endLon };
    } else {
      current.endLon = item.endLon;
    }
  }
  if (current) bands.push(current);
  return bands;
}

function lonInArc(lon: number, startLon: number, endLon: number) {
  const target = normalizeLon(lon);
  const start = normalizeLon(startLon);
  const end = normalizeLon(endLon);
  if (start <= end) return target >= start && target < end;
  return target >= start || target < end;
}

function findHexagramKeyForLon(items: HexagramArc[], lon: number) {
  const match = items.find((item) => lonInArc(lon, item.startLon, item.endLon));
  return match ? `${match.gate}.${match.line}` : null;
}

function uprightRotation(angle: number) {
  const normalized = ((angle % 360) + 360) % 360;
  return normalized > 90 && normalized < 270 ? normalized + 180 : normalized;
}

function buildOrbitLayout(items: Plottable[], anchorLon: number) {
  const sorted = [...items]
    .map((item) => ({ item, rel: normalizeLon(item.lon - anchorLon) }))
    .sort((a, b) => a.rel - b.rel);

  const placements = new Map<string, { track: number; angleOffset: number }>();
  let group: typeof sorted = [];
  const groups: typeof sorted[] = [];

  for (const entry of sorted) {
    const previous = group[group.length - 1];
    if (!previous || entry.rel - previous.rel <= 11) {
      group.push(entry);
    } else {
      groups.push(group);
      group = [entry];
    }
  }
  if (group.length) groups.push(group);

  for (const bucket of groups) {
    bucket.forEach((entry, index) => {
      const centerOffset = index - (bucket.length - 1) / 2;
      const trackPattern = [0, 1, 2, 3, 4, 3, 2, 1];
      const patternIndex = Math.min(trackPattern.length - 1, Math.abs(Math.round(centerOffset)));
      placements.set(entry.item.id, {
        track: trackPattern[patternIndex],
        angleOffset: centerOffset * (entry.rel < 40 || entry.rel > 320 ? 4.6 : 3.2),
      });
    });
  }

  return placements;
}

export default function AdvancedAstroWheel({
  chart,
  size = 760,
  hexagramCsvText,
  show64Key = false,
  className,
}: AdvancedAstroWheelProps) {
  const center = size / 2;
  const outerR = size * 0.452;
  const anchorLon = chart.angles.asc.lon;
  const HEX_OUTER_R = outerR * 1.02;
  const HEX_INNER_R = outerR * 0.89;
  const TICK_OUTER_R = outerR * (show64Key ? 0.888 : 0.99);
  const TICK_LONG_R = outerR * (show64Key ? 0.865 : 0.966);
  const TICK_SHORT_R = outerR * (show64Key ? 0.875 : 0.976);
  const SIGN_OUTER_R = outerR * (show64Key ? 0.86 : 0.958);
  const SIGN_INNER_R = outerR * (show64Key ? 0.73 : 0.81);
  const PLANET_GLYPH_MAJOR_R = outerR * (show64Key ? 0.695 : 0.758);
  const PLANET_GLYPH_MINOR_R = outerR * (show64Key ? 0.695 : 0.758);
  const DEGREE_MAJOR_R = outerR * (show64Key ? 0.605 : 0.665);
  const DEGREE_MINOR_R = outerR * (show64Key ? 0.605 : 0.665);
  const GATE_LABEL_R = outerR * 0.842;
  const INNER_CHART_R = outerR * (show64Key ? 0.495 : 0.525);
  const HOUSE_LABEL_R = outerR * (show64Key ? 0.42 : 0.445);
  const CENTER_DISC_R = outerR * 0.165;

  const hexagramArcs = useMemo(() => {
    const parsed = parseHexagramCsv(hexagramCsvText);
    return parsed.length ? parsed : buildHexagramFallback();
  }, [hexagramCsvText]);

  const hexagramBands = useMemo(() => groupHexagramBands(hexagramArcs), [hexagramArcs]);

  const plottables = useMemo(() => [...chart.bodies, ...chart.points], [chart]);
  const aspectPlottables = useMemo(
    () => [
      ...chart.bodies,
      ...chart.points,
      { id: "asc", label: "Asc", classification: "angle" as const, degree: chart.angles.asc.degree, lon: chart.angles.asc.lon },
      { id: "mc", label: "MC", classification: "angle" as const, degree: chart.angles.mc.degree, lon: chart.angles.mc.lon },
    ],
    [chart],
  );

  const placements = useMemo(() => buildOrbitLayout(plottables, anchorLon), [plottables, anchorLon]);
  const bodyLookup = useMemo(() => new Map(aspectPlottables.map((item) => [item.id, item])), [aspectPlottables]);

  const aspectLines = useMemo(() => {
    const aspectRadius = INNER_CHART_R;
    return chart.aspects
      .map((aspect) => {
        const a = bodyLookup.get(aspect.point_a);
        const b = bodyLookup.get(aspect.point_b);
        if (!a || !b) return null;
        return {
          ...aspect,
          p1: linePoint(center, aspectRadius, a.lon, anchorLon),
          p2: linePoint(center, aspectRadius, b.lon, anchorLon),
        };
      })
      .filter((item): item is Aspect & { p1: { x: number; y: number }; p2: { x: number; y: number } } => Boolean(item));
  }, [chart.aspects, bodyLookup, center, INNER_CHART_R, anchorLon]);

  const signArcs = Array.from({ length: 12 }).map((_, index) => {
    const startLon = index * 30;
    return {
      sign: SIGN_SEQUENCE[index],
      path: ringArcPath(center, SIGN_OUTER_R, SIGN_INNER_R, startLon, startLon + 30, anchorLon),
      symbolPos: linePoint(center, (SIGN_OUTER_R + SIGN_INNER_R) / 2, startLon + 15, anchorLon),
      dividerOuter: linePoint(center, SIGN_OUTER_R, startLon, anchorLon),
      dividerInner: linePoint(center, SIGN_INNER_R, startLon, anchorLon),
    };
  });

  return (
    <div className={className}>
      <svg viewBox={`0 0 ${size} ${size}`} className="h-full w-full">
        <rect x="0" y="0" width={size} height={size} rx={36} fill="#f8fafc" />

        {!show64Key && <circle cx={center} cy={center} r={outerR * 1.004} fill="none" stroke={DEEP_GRAY} strokeWidth={2.1} />}

        {show64Key && (
          <>
            <circle cx={center} cy={center} r={HEX_OUTER_R} fill="none" stroke="#a78bfa" strokeWidth={1.9} />
            <circle cx={center} cy={center} r={HEX_INNER_R} fill="none" stroke={DEEP_GRAY} strokeWidth={1.35} />

            {hexagramBands.map((band) => {
              const mid = midpointLon(band.startLon, band.endLon);
              const bandPath = ringArcPath(center, HEX_OUTER_R, HEX_INNER_R, band.startLon, band.endLon, anchorLon);
              const dividerOuter = linePoint(center, HEX_OUTER_R, band.startLon, anchorLon);
              const dividerInner = linePoint(center, HEX_INNER_R, band.startLon, anchorLon);
              const symbolPos = linePoint(center, outerR * 0.968, mid, anchorLon);
              const gatePos = linePoint(center, outerR * 0.915, mid, anchorLon);
              return (
                <g key={`hex-${band.gate}-${band.startLon}`}>
                  <path d={bandPath} fill="rgba(167,139,250,0.03)" stroke="none" />
                  <line x1={dividerOuter.x} y1={dividerOuter.y} x2={dividerInner.x} y2={dividerInner.y} stroke="#8b5cf6" strokeOpacity={0.9} strokeWidth={0.9} />
                  {band.symbol && (
                    <text x={symbolPos.x} y={symbolPos.y} textAnchor="middle" dominantBaseline="middle" fontSize={size * 0.024} fill="#7c3aed" fontWeight={500}>
                      {band.symbol}
                    </text>
                  )}
                  <text x={gatePos.x} y={gatePos.y} textAnchor="middle" dominantBaseline="middle" fontSize={size * 0.0105} fill="#7c3aed" fillOpacity={0.72}>
                    {band.gate}
                  </text>
                </g>
              );
            })}
          </>
        )}

        {Array.from({ length: 360 }).map((_, lon) => {
          const start = linePoint(center, TICK_OUTER_R, lon, anchorLon);
          const end = linePoint(center, lon % 5 === 0 ? TICK_LONG_R : TICK_SHORT_R, lon, anchorLon);
          return (
            <line
              key={`tick-${lon}`}
              x1={start.x}
              y1={start.y}
              x2={end.x}
              y2={end.y}
              stroke="#cbd5e1"
              strokeOpacity={lon % 5 === 0 ? 0.9 : 0.65}
              strokeWidth={lon % 5 === 0 ? 0.75 : 0.4}
            />
          );
        })}

        {signArcs.map((arc) => (
          <g key={arc.sign}>
            <path d={arc.path} fill={ELEMENT_FILL[arc.sign]} fillOpacity={0.45} stroke="none" />
            <line
              x1={arc.dividerOuter.x}
              y1={arc.dividerOuter.y}
              x2={arc.dividerInner.x}
              y2={arc.dividerInner.y}
              stroke="#d8dee8"
              strokeWidth={0.9}
            />
            <image
              href={ZODIAC_SYMBOLS[arc.sign]}
              x={arc.symbolPos.x - size * 0.0155 + (SIGN_ICON_OFFSET[arc.sign]?.x ?? 0)}
              y={arc.symbolPos.y - size * 0.0155 + (SIGN_ICON_OFFSET[arc.sign]?.y ?? 0)}
              width={size * 0.031}
              height={size * 0.031}
              preserveAspectRatio="xMidYMid meet"
            />
          </g>
        ))}

        <circle cx={center} cy={center} r={SIGN_INNER_R} fill="none" stroke={DEEP_GRAY} strokeWidth={1.8} />

        {[chart.angles.asc, chart.angles.mc, chart.angles.dsc, chart.angles.ic].map((angle) => {
          const pos = linePoint(center, outerR * 0.555, angle.lon, anchorLon);
          const accent = DEEP_GRAY;
          return (
            <g key={angle.id}>
              <text x={pos.x} y={pos.y} textAnchor="middle" dominantBaseline="middle" fontSize={size * 0.0115} fill={accent} fontWeight={700}>
                {BODY_GLYPH[angle.id]}
              </text>
            </g>
          );
        })}

        <circle cx={center} cy={center} r={INNER_CHART_R} fill="#fff" fillOpacity={0.97} stroke="#edf2f7" strokeWidth={1.1} />
        {aspectLines.map((aspect) => {
          const style = ASPECT_STYLE[aspect.aspect_type] || { stroke: "#94a3b8", width: 1 };
          return (
            <line
              key={aspect.id}
              x1={aspect.p1.x}
              y1={aspect.p1.y}
              x2={aspect.p2.x}
              y2={aspect.p2.y}
              stroke={style.stroke}
              strokeWidth={style.width}
              strokeOpacity={0.78}
              strokeDasharray={style.dasharray}
            />
          );
        })}

        {plottables.map((point) => {
          const placement = placements.get(point.id) || { track: 0, angleOffset: 0 };
          const isMajorPlanet = MAJOR_PLANETS.has(point.id);
          const glyphRadius = isMajorPlanet ? PLANET_GLYPH_MAJOR_R : PLANET_GLYPH_MINOR_R;
          const degreeRadius = isMajorPlanet ? DEGREE_MAJOR_R : DEGREE_MINOR_R;
          const gateRadius = GATE_LABEL_R + placement.track * outerR * 0.005;
          const shiftedLon = normalizeLon(point.lon + placement.angleOffset);
          const glyphPos = linePoint(center, glyphRadius, shiftedLon, anchorLon);
          const degreePos = linePoint(center, degreeRadius, shiftedLon, anchorLon);
          const rawRotation = 180 - normalizeLon(shiftedLon - anchorLon);
          const rotation = uprightRotation(rawRotation);
          const gateAnchor = linePoint(center, gateRadius, point.lon, anchorLon);
          const gateTangent = ((90 - normalizeLon(point.lon - anchorLon)) * Math.PI) / 180;
          const gatePos = {
            x: gateAnchor.x + Math.cos(gateTangent) * placement.angleOffset * 0.85,
            y: gateAnchor.y - Math.sin(gateTangent) * placement.angleOffset * 0.85,
          };
          const gateRotation = uprightRotation(180 - normalizeLon(point.lon - anchorLon));
          const glyph = BODY_GLYPH[point.id] || point.label.slice(0, 2);
          const gateLine = findHexagramKeyForLon(hexagramArcs, point.lon);
          const glyphFill = point.id === "sun" || point.id === "moon" ? "#7c3aed" : "#0f172a";
          const glyphFontSize = glyph.length > 1 ? size * 0.0165 : size * 0.019;

          return (
            <g key={point.id}>
              <text x={glyphPos.x} y={glyphPos.y} textAnchor="middle" dominantBaseline="middle" fontSize={glyphFontSize} fill={glyphFill} fontWeight={700}>
                {glyph}
              </text>
              <text
                x={degreePos.x}
                y={degreePos.y}
                textAnchor="middle"
                dominantBaseline="middle"
                fontSize={isMajorPlanet ? size * 0.0165 : size * 0.0125}
                fill="#1f3553"
                fontWeight={700}
                transform={`rotate(${rotation} ${degreePos.x} ${degreePos.y})`}
              >
                {formatDeg(point.degree)}
              </text>
              {show64Key && gateLine && (
                <text
                  x={gatePos.x}
                  y={gatePos.y}
                  textAnchor="middle"
                  dominantBaseline="middle"
                  fontSize={isMajorPlanet ? size * 0.0115 : size * 0.0095}
                  fill="#7c3aed"
                  fontWeight={600}
                  transform={`rotate(${gateRotation} ${gatePos.x} ${gatePos.y})`}
                >
                  {gateLine}
                </text>
              )}
              {point.retrograde && (
                <text x={degreePos.x + size * 0.014} y={degreePos.y} textAnchor="start" dominantBaseline="middle" fontSize={size * 0.0115} fill="#dc2626" fontWeight={700}>
                  R
                </text>
              )}
            </g>
          );
        })}

        {chart.houses.map((house) => {
          const outer = linePoint(center, SIGN_INNER_R, house.lon, anchorLon);
          const inner = linePoint(center, CENTER_DISC_R, house.lon, anchorLon);
          const next = chart.houses[house.house % 12];
          const labelPos = linePoint(center, HOUSE_LABEL_R, midpointLon(house.lon, next.lon), anchorLon);
          const isAngleHouse = [1, 4, 7, 10].includes(house.house);
          return (
            <g key={`house-${house.house}`}>
              <line
                x1={inner.x}
                y1={inner.y}
                x2={outer.x}
                y2={outer.y}
                stroke={isAngleHouse ? "#334155" : "#94a3b8"}
                strokeWidth={isAngleHouse ? 1.7 : 1.15}
              />
              <text x={labelPos.x} y={labelPos.y} textAnchor="middle" dominantBaseline="middle" fontSize={size * 0.015} fill="#7b8799" fontWeight={700}>
                {house.house}
              </text>
            </g>
          );
        })}

        <circle cx={center} cy={center} r={CENTER_DISC_R} fill="#fafaf9" stroke={DEEP_GRAY} strokeWidth={1.35} />
        <text x={center} y={center - size * 0.018} textAnchor="middle" fontSize={size * 0.026} fill="#475569" fontWeight={600}>
          {chart.input.person_name || "Chart"}
        </text>
        <text x={center} y={center + size * 0.012} textAnchor="middle" fontSize={size * 0.014} fill="#64748b">
          {chart.input.birth_date} · {chart.input.birth_time_local}
        </text>
        <text x={center} y={center + size * 0.04} textAnchor="middle" fontSize={size * 0.016} fill="#475569" fontWeight={700} letterSpacing="0.16em">
          NATAL.KR
        </text>
        <text x={size * 0.9} y={size * 0.942} textAnchor="end" fontSize={size * 0.0098} fill="#64748b" fontWeight={600}>
          본 차트의 저작권과 사용권은 NATAL.kr에 있습니다.
        </text>
        <text x={size * 0.9} y={size * 0.962} textAnchor="end" fontSize={size * 0.0094} fill="#94a3b8" fontWeight={500}>
          무단 전재 및 배포를 금합니다.
        </text>
      </svg>
    </div>
  );
}
