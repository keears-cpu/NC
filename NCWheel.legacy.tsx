import React, { useMemo } from "react";

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
  motion?: string;
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
  motion?: string;
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
  orb_text?: string;
  is_major?: boolean;
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
    country_code?: string | null;
    latitude?: number;
    longitude?: number;
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
  rawSymbol?: string;
  startLon: number;
  endLon: number;
  label?: string;
};

type HexagramBand = {
  gate: number;
  symbol?: string;
  startLon: number;
  endLon: number;
};

type AdvancedAstroWheelProps = {
  chart: NatalChartRecord;
  size?: number;
  hexagramCsvText?: string;
  showHexagramLabels?: boolean;
  showMinorTicks?: boolean;
  className?: string;
};

const ZODIAC_SYMBOLS: Record<string, string> = {
  Aries: "♈",
  Taurus: "♉",
  Gemini: "♊",
  Cancer: "♋",
  Leo: "♌",
  Virgo: "♍",
  Libra: "♎",
  Scorpio: "♏",
  Sagittarius: "♐",
  Capricorn: "♑",
  Aquarius: "♒",
  Pisces: "♓",
};

const ELEMENT_FILL: Record<string, string> = {
  Aries: "#fde2e4",
  Leo: "#fde2e4",
  Sagittarius: "#fde2e4",
  Taurus: "#e6f4ea",
  Virgo: "#e6f4ea",
  Capricorn: "#e6f4ea",
  Gemini: "#e3f2fd",
  Libra: "#e3f2fd",
  Aquarius: "#e3f2fd",
  Cancer: "#ede7f6",
  Scorpio: "#ede7f6",
  Pisces: "#ede7f6",
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
  juno: "⚵",
  vesta: "⚶",
  vulcan: "V",
  hygeia: "H",
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

const ASPECT_STYLE: Record<string, { stroke: string; dasharray?: string; width: number }> = {
  conjunction: { stroke: "#94a3b8", width: 1.1 },
  sextile: { stroke: "#2563eb", width: 1.05 },
  square: { stroke: "#ef4444", width: 1.1 },
  trine: { stroke: "#2563eb", width: 1.15 },
  opposition: { stroke: "#ef4444", width: 1.2 },
  quincunx: { stroke: "#f59e0b", width: 0.95, dasharray: "3 3" },
};

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

function midpointLon(startLon: number, endLon: number) {
  return normalizeLon(startLon + normalizeLon(endLon - startLon) / 2);
}

function signOfLon(lon: number) {
  const signs = [
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
  ];
  return signs[Math.floor(normalizeLon(lon) / 30)];
}

function formatDeg(value: number) {
  const deg = Math.floor(value);
  const minute = Math.round((value - deg) * 60);
  return `${deg}°${String(minute).padStart(2, "0")}’`;
}

function ringArcPath(center: number, outerR: number, innerR: number, startLon: number, endLon: number, anchorLon: number) {
  const p1 = polarRelative(startLon, anchorLon, outerR, center);
  const p2 = polarRelative(endLon, anchorLon, outerR, center);
  const p3 = polarRelative(endLon, anchorLon, innerR, center);
  const p4 = polarRelative(startLon, anchorLon, innerR, center);
  const span = normalizeLon(endLon - startLon);
  const largeArc = span > 180 ? 1 : 0;
  return [
    `M ${p1.x} ${p1.y}`,
    `A ${outerR} ${outerR} 0 ${largeArc} 0 ${p2.x} ${p2.y}`,
    `L ${p3.x} ${p3.y}`,
    `A ${innerR} ${innerR} 0 ${largeArc} 1 ${p4.x} ${p4.y}`,
    "Z",
  ].join(" ");
}

function linePoint(center: number, radius: number, lon: number, anchorLon: number) {
  return polarRelative(lon, anchorLon, radius, center);
}

function buildCollisionLayout(items: Array<Body | Point | { id: string; classification: Classification; lon: number }>, anchorLon: number) {
  const sorted = [...items]
    .map((item) => ({ item, relativeLon: normalizeLon(item.lon - anchorLon) }))
    .sort((a, b) => a.relativeLon - b.relativeLon);

  const placements = new Map<string, { ringOffset: number; tangentOffset: number; degreeOffset: number }>();
  const groups: typeof sorted[] = [];
  let current: typeof sorted = [];

  for (const entry of sorted) {
    const prev = current[current.length - 1];
    if (!prev || entry.relativeLon - prev.relativeLon <= 7.5) {
      current.push(entry);
    } else {
      groups.push(current);
      current = [entry];
    }
  }
  if (current.length) groups.push(current);

  for (const group of groups) {
    group.forEach((entry, index) => {
      const centerOffset = index - (group.length - 1) / 2;
      const ringOffset = Math.abs(centerOffset) % 3;
      placements.set(entry.item.id, {
        ringOffset: ringOffset * 10 + (entry.item.classification === "mathematical_point" ? 4 : 0),
        tangentOffset: centerOffset * 8,
        degreeOffset: centerOffset * 2.8,
      });
    });
  }

  return placements;
}

function parseHexagramCsv(csvText?: string): HexagramArc[] {
  if (!csvText?.trim()) return [];

  const signBase: Record<string, number> = {
    양: 0,
    양자리: 0,
    황소: 30,
    황소자리: 30,
    쌍둥이: 60,
    쌍둥: 60,
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
  if (lines.length < 2) return [];

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

    const match = degreeRange.match(/^([^\s]+)\s+(\d{2})°\s*(\d{2})['’](?:\s*\d{2}["”])?\s*~\s*(\d{2})°\s*(\d{2})['’](?:\s*\d{2}["”])?$/);
    if (!match) continue;

    const [, signKo, startDeg, startMin, endDeg, endMin] = match;
    const base = signBase[signKo];
    if (base == null) continue;

    parsed.push({
      key,
      gate,
      line: lineNo,
      symbol,
      rawSymbol,
      startLon: base + Number(startDeg) + Number(startMin) / 60,
      endLon: base + Number(endDeg) + Number(endMin) / 60,
      label: String(gate),
    });
  }

  return parsed;
}

function buildHexagramFallback(): HexagramArc[] {
  const result: HexagramArc[] = [];
  const span = 360 / 64;
  for (let i = 0; i < 64; i += 1) {
    result.push({
      key: `${i + 1}`,
      gate: i + 1,
      line: 0,
      startLon: i * span,
      endLon: (i + 1) * span,
      label: String(i + 1),
    });
  }
  return result;
}

function groupHexagramBands(items: HexagramArc[]): HexagramBand[] {
  if (!items.length) return [];

  const bands: HexagramBand[] = [];
  let current: HexagramBand | null = null;

  for (const item of items) {
    if (!current || current.gate !== item.gate) {
      if (current) bands.push(current);
      current = {
        gate: item.gate,
        symbol: item.symbol,
        startLon: item.startLon,
        endLon: item.endLon,
      };
      continue;
    }
    current.endLon = item.endLon;
  }

  if (current) bands.push(current);
  return bands;
}

function lonInArc(lon: number, startLon: number, endLon: number) {
  const normalizedLon = normalizeLon(lon);
  const normalizedStart = normalizeLon(startLon);
  const normalizedEnd = normalizeLon(endLon);

  if (normalizedStart <= normalizedEnd) {
    return normalizedLon >= normalizedStart && normalizedLon < normalizedEnd;
  }
  return normalizedLon >= normalizedStart || normalizedLon < normalizedEnd;
}

function findHexagramKeyForLon(items: HexagramArc[], lon: number) {
  const match = items.find((item) => lonInArc(lon, item.startLon, item.endLon));
  return match ? `${match.gate}.${match.line}` : null;
}

export default function AdvancedAstroWheel({
  chart,
  size = 760,
  hexagramCsvText,
  showHexagramLabels = true,
  showMinorTicks = true,
  className,
}: AdvancedAstroWheelProps) {
  const center = size / 2;
  const outerR = size * 0.475;
  const ascAnchorLon = chart.angles.asc.lon;
  const hexagramOuterR = outerR * 1.0;
  const hexagramInnerR = outerR * 0.948;
  const zodiacOuterR = outerR * 0.935;
  const zodiacInnerR = outerR * 0.84;
  const planetBandR = outerR * 0.77;
  const degreeBandR = outerR * 0.675;
  const gateLineBandR = outerR * 0.635;
  const houseOuterR = outerR * 0.73;
  const houseInnerR = outerR * 0.43;
  const houseLabelR = outerR * 0.53;
  const angleLabelR = outerR * 0.64;
  const aspectWebR = outerR * 0.43;
  const pointBaseR = planetBandR;
  const anglePointBaseR = outerR * 0.55;

  const lineRing = useMemo(() => {
    const parsed = parseHexagramCsv(hexagramCsvText);
    return parsed.length ? parsed : buildHexagramFallback();
  }, [hexagramCsvText]);

  const hexagramBands = useMemo(() => groupHexagramBands(lineRing), [lineRing]);
  const majorPlanetIds = useMemo(
    () => new Set(["sun", "moon", "mercury", "venus", "mars", "jupiter", "saturn", "uranus", "neptune", "pluto"]),
    []
  );

  const plottables = useMemo(() => {
    const extras: Array<Body | Point> = [
      {
        id: "asc",
        label: "Asc",
        classification: "angle",
        sign: chart.angles.asc.sign,
        degree: chart.angles.asc.degree,
        formatted: chart.angles.asc.formatted,
        lon: chart.angles.asc.lon,
        house: 1,
      },
      {
        id: "mc",
        label: "MC",
        classification: "angle",
        sign: chart.angles.mc.sign,
        degree: chart.angles.mc.degree,
        formatted: chart.angles.mc.formatted,
        lon: chart.angles.mc.lon,
        house: 10,
      },
    ];
    return [...chart.bodies, ...chart.points, ...extras];
  }, [chart]);

  const placements = useMemo(() => buildCollisionLayout(plottables, ascAnchorLon), [plottables, ascAnchorLon]);
  const bodyLookup = useMemo(() => new Map(plottables.map((item) => [item.id, item])), [plottables]);

  const aspectLines = useMemo(() => {
    const innerAspectRadius = outerR * 0.42;
    return chart.aspects
      .map((aspect) => {
        const a = bodyLookup.get(aspect.point_a);
        const b = bodyLookup.get(aspect.point_b);
        if (!a || !b) return null;
        const p1 = linePoint(center, innerAspectRadius, a.lon, ascAnchorLon);
        const p2 = linePoint(center, innerAspectRadius, b.lon, ascAnchorLon);
        return { ...aspect, p1, p2 };
      })
      .filter((item): item is Aspect & { p1: { x: number; y: number }; p2: { x: number; y: number } } => Boolean(item));
  }, [chart.aspects, bodyLookup, center, outerR, ascAnchorLon]);

  const signArcs = Array.from({ length: 12 }).map((_, index) => {
    const startLon = index * 30;
    const endLon = startLon + 30;
    const sign = signOfLon(startLon);
    return {
      sign,
      path: ringArcPath(center, zodiacOuterR, zodiacInnerR, startLon, endLon, ascAnchorLon),
      labelPos: linePoint(center, outerR * 0.893, startLon + 15, ascAnchorLon),
      labelLon: startLon + 15,
    };
  });

  const majorTickLons = Array.from({ length: 72 }).map((_, i) => i * 5);
  const minorTickLons = Array.from({ length: 360 }).map((_, i) => i);

  return (
    <div className={className}>
      <svg viewBox={`0 0 ${size} ${size}`} className="h-full w-full">
        <defs>
          <filter id="wheelShadow" x="-20%" y="-20%" width="140%" height="140%">
            <feDropShadow dx="0" dy="10" stdDeviation="12" floodColor="#0f172a" floodOpacity="0.08" />
          </filter>
        </defs>

        <rect x="0" y="0" width={size} height={size} rx={36} fill="#f8fafc" />
        <g filter="url(#wheelShadow)">
          <circle cx={center} cy={center} r={outerR} fill="#fffdf9" stroke="#d6d3d1" strokeWidth={1.6} />
        </g>

        <circle cx={center} cy={center} r={hexagramOuterR * 1.01} fill="none" stroke="#a78bfa" strokeWidth={1.8} />
        <circle cx={center} cy={center} r={hexagramInnerR} fill="none" stroke="#c4b5fd" strokeWidth={0.8} />
        {hexagramBands.map((item) => {
          const mid = midpointLon(item.startLon, item.endLon);
          const start = linePoint(center, hexagramOuterR * 1.01, item.startLon, ascAnchorLon);
          const end = linePoint(center, hexagramInnerR, item.startLon, ascAnchorLon);
          const symbolPos = linePoint(center, outerR * 0.992, mid, ascAnchorLon);
          const numberPos = linePoint(center, outerR * 0.962, mid, ascAnchorLon);
          return (
            <g key={`gate-${item.gate}-${item.startLon}`}>
              <line x1={start.x} y1={start.y} x2={end.x} y2={end.y} stroke="#8b5cf6" strokeOpacity={0.78} strokeWidth={0.95} />
              {item.symbol && (
                <text
                  x={symbolPos.x}
                  y={symbolPos.y}
                  textAnchor="middle"
                  dominantBaseline="middle"
                  fontSize={size * 0.019}
                  fill="#7c3aed"
                  fillOpacity={0.95}
                  fontWeight={500}
                >
                  {item.symbol}
                </text>
              )}
              <text
                x={numberPos.x}
                y={numberPos.y}
                textAnchor="middle"
                dominantBaseline="middle"
                fontSize={size * 0.0115}
                fill="#6d28d9"
                fillOpacity={0.78}
                fontWeight={400}
              >
                {item.gate}
              </text>
            </g>
          );
        })}

        {showMinorTicks &&
          minorTickLons.map((lon) => {
            const start = linePoint(center, zodiacOuterR, lon, ascAnchorLon);
            const end = linePoint(center, zodiacOuterR - outerR * (lon % 5 === 0 ? 0.026 : 0.016), lon, ascAnchorLon);
            return <line key={`minor-${lon}`} x1={start.x} y1={start.y} x2={end.x} y2={end.y} stroke="#cbd5e1" strokeOpacity={0.7} strokeWidth={lon % 5 === 0 ? 0.8 : 0.45} />;
          })}
        {majorTickLons.map((lon) => {
          const start = linePoint(center, zodiacOuterR, lon, ascAnchorLon);
          const end = linePoint(center, zodiacOuterR - outerR * 0.03, lon, ascAnchorLon);
          return (
            <g key={`major-${lon}`}>
              <line x1={start.x} y1={start.y} x2={end.x} y2={end.y} stroke="#94a3b8" strokeOpacity={0.9} strokeWidth={lon % 30 === 0 ? 1 : 0.7} />
            </g>
          );
        })}

        {signArcs.map((arc) => (
          <g key={arc.sign}>
            <path d={arc.path} fill={ELEMENT_FILL[arc.sign]} fillOpacity={0.42} stroke="#cbd5e1" strokeWidth={0.8} />
            <text
              x={arc.labelPos.x}
              y={arc.labelPos.y}
              textAnchor="middle"
              dominantBaseline="middle"
              fontSize={size * 0.022}
              fill="#475569"
              fillOpacity={0.98}
              fontWeight={600}
              letterSpacing={0}
              transform={`rotate(${180 - normalizeLon(arc.labelLon - ascAnchorLon)} ${arc.labelPos.x} ${arc.labelPos.y})`}
            >
              {ZODIAC_SYMBOLS[arc.sign]}
            </text>
          </g>
        ))}

        <circle cx={center} cy={center} r={houseOuterR} fill="none" stroke="#cbd5e1" strokeWidth={1.2} />
        <circle cx={center} cy={center} r={outerR * 0.72} fill="none" stroke="#dbe4ee" strokeWidth={1} />

        {chart.houses.map((house) => {
          const outer = linePoint(center, houseOuterR, house.lon, ascAnchorLon);
          const inner = linePoint(center, houseInnerR, house.lon, ascAnchorLon);
          const next = chart.houses[house.house % 12];
          const mid = midpointLon(house.lon, next.lon);
          const labelPos = linePoint(center, houseLabelR, mid, ascAnchorLon);
          const isAngleHouse = [1, 4, 7, 10].includes(house.house);
          return (
            <g key={`house-${house.house}`}>
              <line x1={inner.x} y1={inner.y} x2={outer.x} y2={outer.y} stroke={isAngleHouse ? "#475569" : "#94a3b8"} strokeWidth={isAngleHouse ? 1.5 : 0.9} />
              <text x={labelPos.x} y={labelPos.y} textAnchor="middle" dominantBaseline="middle" fontSize={size * 0.019} fill={isAngleHouse ? "#475569" : "#64748b"} fillOpacity={0.75} fontWeight={600}>
                {house.house}
              </text>
            </g>
          );
        })}

        {[chart.angles.asc, chart.angles.mc, chart.angles.dsc, chart.angles.ic].map((angle) => {
          const pos = linePoint(center, angleLabelR, angle.lon, ascAnchorLon);
          const accent = angle.id === "asc" || angle.id === "mc" ? "#0f172a" : "#475569";
          return (
            <g key={angle.id}>
              <circle cx={pos.x} cy={pos.y} r={size * 0.02} fill="#ffffff" stroke={accent} strokeWidth={1.2} />
              <text x={pos.x} y={pos.y} textAnchor="middle" dominantBaseline="middle" fontSize={size * 0.012} fill={accent} fontWeight={700}>
                {BODY_GLYPH[angle.id]}
              </text>
            </g>
          );
        })}

        <circle cx={center} cy={center} r={aspectWebR} fill="#fff" stroke="#e7e5e4" strokeWidth={1.1} />
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
              strokeOpacity={0.7}
              strokeDasharray={style.dasharray}
            />
          );
        })}

        {plottables.map((point, index) => {
          const place = placements.get(point.id) || { ringOffset: 0, tangentOffset: 0, degreeOffset: 0 };
          const isAngle = point.classification === "angle";
          const isMajorPlanet = majorPlanetIds.has(point.id);
          const baseRadius = isAngle
            ? anglePointBaseR
            : isMajorPlanet
              ? pointBaseR + place.ringOffset * (outerR * 0.018)
              : planetBandR - outerR * 0.03 + place.ringOffset * (outerR * 0.012);
          const base = linePoint(center, baseRadius + place.ringOffset, point.lon, ascAnchorLon);
          const tangent = ((90 - normalizeLon(point.lon - ascAnchorLon)) * Math.PI) / 180;
          const radial = ((180 - normalizeLon(point.lon - ascAnchorLon)) * Math.PI) / 180;
          const pos = {
            x: base.x + Math.cos(tangent) * (isMajorPlanet ? place.tangentOffset * 1.35 : place.tangentOffset),
            y: base.y - Math.sin(tangent) * (isMajorPlanet ? place.tangentOffset * 1.35 : place.tangentOffset),
          };
          const degreeAnchor = linePoint(
            center,
            degreeBandR + (isMajorPlanet ? place.ringOffset * (outerR * 0.014) : place.ringOffset * (outerR * 0.008)),
            point.lon,
            ascAnchorLon
          );
          const degreePos = {
            x: degreeAnchor.x + Math.cos(tangent) * (isMajorPlanet ? place.tangentOffset * 0.55 : place.tangentOffset * 0.35),
            y: degreeAnchor.y - Math.sin(tangent) * (isMajorPlanet ? place.tangentOffset * 0.55 : place.tangentOffset * 0.35),
          };
          const gateAnchor = linePoint(
            center,
            gateLineBandR + (isMajorPlanet ? place.ringOffset * (outerR * 0.01) : 0),
            point.lon,
            ascAnchorLon
          );
          const hexagramPos = {
            x: gateAnchor.x + Math.cos(tangent) * (isMajorPlanet ? place.tangentOffset * 0.38 : 0),
            y: gateAnchor.y - Math.sin(tangent) * (isMajorPlanet ? place.tangentOffset * 0.38 : 0),
          };
          const glyph = BODY_GLYPH[point.id] || point.label.slice(0, 2);
          const gateLine = findHexagramKeyForLon(lineRing, point.lon);
          const degreeRotation = 180 - normalizeLon(point.lon - ascAnchorLon);

          return (
            <g key={`${point.id}-${index}`}>
              <circle cx={pos.x} cy={pos.y} r={isAngle ? size * 0.0145 : isMajorPlanet ? size * 0.014 : size * 0.0125} fill={isAngle ? "#0f172a" : "#ffffff"} stroke="#94a3b8" strokeWidth={0.8} />
              <text x={pos.x} y={pos.y} textAnchor="middle" dominantBaseline="middle" fontSize={isAngle ? size * 0.0125 : isMajorPlanet ? size * 0.021 : size * 0.018} fill={isAngle ? "#ffffff" : "#0f172a"} fontWeight={700}>
                {glyph}
              </text>
              <text
                x={degreePos.x}
                y={degreePos.y}
                textAnchor="middle"
                dominantBaseline="middle"
                fontSize={isMajorPlanet ? size * 0.0175 : size * 0.013}
                fill="#334155"
                fontWeight={isMajorPlanet ? 700 : 600}
                transform={`rotate(${degreeRotation} ${degreePos.x} ${degreePos.y})`}
              >
                {formatDeg(point.degree)}
              </text>
              {gateLine && !isAngle && (
                <text
                  x={hexagramPos.x}
                  y={hexagramPos.y}
                  textAnchor="middle"
                  dominantBaseline="middle"
                  fontSize={isMajorPlanet ? size * 0.0125 : size * 0.0105}
                  fill="#6d28d9"
                  fillOpacity={0.72}
                  fontWeight={500}
                  transform={`rotate(${degreeRotation} ${hexagramPos.x} ${hexagramPos.y})`}
                >
                  {gateLine}
                </text>
              )}
              {point.retrograde && (
                <text x={degreePos.x + size * 0.02} y={degreePos.y} textAnchor="start" fontSize={size * 0.013} fill="#dc2626" fontWeight={700}>
                  R
                </text>
              )}
            </g>
          );
        })}

        <circle cx={center} cy={center} r={outerR * 0.175} fill="#fafaf9" stroke="#d6d3d1" strokeWidth={1.1} />
        <text x={center} y={center - size * 0.018} textAnchor="middle" fontSize={size * 0.026} fill="#475569" fontWeight={600}>
          {chart.input.person_name || "Chart"}
        </text>
        <text x={center} y={center + size * 0.012} textAnchor="middle" fontSize={size * 0.014} fill="#64748b">
          {chart.input.birth_date} · {chart.input.birth_time_local}
        </text>
      </svg>
    </div>
  );
}
