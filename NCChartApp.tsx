import React, { useEffect, useMemo, useRef, useState } from "react";
import NCWheel from "./NCWheel";
import hexagramCsvText from "./src/data/hexagram-64key.csv?raw";

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
  definition: string;
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
  orb_text: string;
};

type NatalChartRecord = {
  metadata: {
    chart_id: string;
    engine_name: string;
    status: string;
    warnings?: string[];
  };
  input: {
    person_name?: string | null;
    birth_date: string;
    birth_time_local: string;
    timezone: string;
    birth_place_name: string;
    country_code?: string | null;
    latitude: number;
    longitude: number;
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
  availability: {
    core_complete: boolean;
    soft_missing: string[];
  };
};

type WorkspaceMode = "public" | "internal";
type ReportPreset = "core_snapshot" | "core_report" | "adult_deep_blueprint" | "teen_growth_report" | "child_parenting_report";

type SavedLead = {
  id: string;
  label: string;
  phone: string;
  email: string;
  birth_place_name: string;
  created_at: string;
  form: {
    person_name: string;
    phone: string;
    email: string;
    birth_date: string;
    birth_time_local: string;
    timezone: string;
    birth_place_name: string;
    country_code: string;
    latitude: string;
    longitude: string;
    report_preset: ReportPreset;
    report_viewer_code: string;
  };
  chart: NatalChartRecord;
};

type RemoteStoredChart = {
  record_id: string;
  person_name?: string | null;
  phone?: string | null;
  birth_date: string;
  birth_time_local?: string | null;
  birth_place_name?: string | null;
  email?: string | null;
  created_at?: string | null;
  report_preset?: ReportPreset | null;
  report_addons?: string[] | null;
  report_id?: string | null;
  report_viewer_code?: string | null;
  report_product_code?: string | null;
  report_payment_status?: string | null;
  chart_svg?: string | null;
  chart_svg_updated_at?: string | null;
  chart?: NatalChartRecord | null;
};

type RemoteStoredChartGroup = {
  date: string;
  items: RemoteStoredChart[];
};

type CitySuggestion = {
  label: string;
  local_label?: string;
  country_code: string;
  timezone: string;
  latitude: number;
  longitude: number;
  source: "preset" | "api";
  priority?: number;
  aliases?: string[];
};

const KOREA_CITY_PRESETS: CitySuggestion[] = [
  { label: "Seoul, South Korea", local_label: "서울", country_code: "KR", timezone: "Asia/Seoul", latitude: 37.5665, longitude: 126.978, source: "preset", priority: 100, aliases: ["seoul", "서울", "서울시", "서울특별시"] },
  { label: "Busan, South Korea", local_label: "부산", country_code: "KR", timezone: "Asia/Seoul", latitude: 35.1796, longitude: 129.0756, source: "preset", priority: 98, aliases: ["busan", "pusan", "부산", "부산시", "부산광역시"] },
  { label: "Incheon, South Korea", local_label: "인천", country_code: "KR", timezone: "Asia/Seoul", latitude: 37.4563, longitude: 126.7052, source: "preset", priority: 97, aliases: ["incheon", "인천", "인천시", "인천광역시"] },
  { label: "Daegu, South Korea", local_label: "대구", country_code: "KR", timezone: "Asia/Seoul", latitude: 35.8714, longitude: 128.6014, source: "preset", priority: 95, aliases: ["daegu", "대구", "대구시", "대구광역시"] },
  { label: "Daejeon, South Korea", local_label: "대전", country_code: "KR", timezone: "Asia/Seoul", latitude: 36.3504, longitude: 127.3845, source: "preset", priority: 95, aliases: ["daejeon", "대전", "대전시", "대전광역시"] },
  { label: "Gwangju, South Korea", local_label: "광주", country_code: "KR", timezone: "Asia/Seoul", latitude: 35.1595, longitude: 126.8526, source: "preset", priority: 94, aliases: ["gwangju", "광주", "광주시", "광주광역시"] },
  { label: "Ulsan, South Korea", local_label: "울산", country_code: "KR", timezone: "Asia/Seoul", latitude: 35.5384, longitude: 129.3114, source: "preset", priority: 93, aliases: ["ulsan", "울산", "울산시", "울산광역시"] },
  { label: "Suwon, South Korea", local_label: "수원", country_code: "KR", timezone: "Asia/Seoul", latitude: 37.2636, longitude: 127.0286, source: "preset", priority: 92, aliases: ["suwon", "수원", "수원시"] },
  { label: "Seongnam, South Korea", local_label: "성남", country_code: "KR", timezone: "Asia/Seoul", latitude: 37.4201, longitude: 127.1262, source: "preset", priority: 91, aliases: ["seongnam", "성남", "성남시"] },
  { label: "Anyang, South Korea", local_label: "안양", country_code: "KR", timezone: "Asia/Seoul", latitude: 37.3943, longitude: 126.9568, source: "preset", priority: 90, aliases: ["anyang", "안양", "안양시"] },
  { label: "Guri, South Korea", local_label: "구리", country_code: "KR", timezone: "Asia/Seoul", latitude: 37.5943, longitude: 127.1296, source: "preset", priority: 90, aliases: ["guri", "구리", "구리시"] },
  { label: "Namyangju, South Korea", local_label: "남양주", country_code: "KR", timezone: "Asia/Seoul", latitude: 37.636, longitude: 127.2165, source: "preset", priority: 89, aliases: ["namyangju", "남양주", "남양주시"] },
  { label: "Jeonju, South Korea", local_label: "전주", country_code: "KR", timezone: "Asia/Seoul", latitude: 35.8242, longitude: 127.148, source: "preset", priority: 89, aliases: ["jeonju", "전주", "전주시"] },
  { label: "Cheongju, South Korea", local_label: "청주", country_code: "KR", timezone: "Asia/Seoul", latitude: 36.6424, longitude: 127.489, source: "preset", priority: 89, aliases: ["cheongju", "청주", "청주시"] },
  { label: "Jeju, South Korea", local_label: "제주", country_code: "KR", timezone: "Asia/Seoul", latitude: 33.4996, longitude: 126.5312, source: "preset", priority: 88, aliases: ["jeju", "제주", "제주시"] },
];

const zodiacSymbols: Record<string, string> = {
  Aries: "♈", Taurus: "♉", Gemini: "♊", Cancer: "♋", Leo: "♌", Virgo: "♍",
  Libra: "♎", Scorpio: "♏", Sagittarius: "♐", Capricorn: "♑", Aquarius: "♒", Pisces: "♓",
};

const zodiacKorean: Record<string, string> = {
  Aries: "양자리",
  Taurus: "황소자리",
  Gemini: "쌍둥이자리",
  Cancer: "게자리",
  Leo: "사자자리",
  Virgo: "처녀자리",
  Libra: "천칭자리",
  Scorpio: "전갈자리",
  Sagittarius: "사수자리",
  Capricorn: "염소자리",
  Aquarius: "물병자리",
  Pisces: "물고기자리",
};

const zodiacElement: Record<string, "fire" | "earth" | "air" | "water"> = {
  Aries: "fire", Leo: "fire", Sagittarius: "fire",
  Taurus: "earth", Virgo: "earth", Capricorn: "earth",
  Gemini: "air", Libra: "air", Aquarius: "air",
  Cancer: "water", Scorpio: "water", Pisces: "water",
};

const elementFill: Record<string, string> = {
  fire: "#FDE2E4",
  earth: "#E6F4EA",
  air: "#E3F2FD",
  water: "#EDE7F6",
};

const elementStroke: Record<string, string> = {
  fire: "#F4A5AE",
  earth: "#A8D5BA",
  air: "#9BC7F2",
  water: "#C5B3E6",
};

const bodyGlyph: Record<string, string> = {
  sun: "☉", moon: "☽", mercury: "☿", venus: "♀", mars: "♂", jupiter: "♃", saturn: "♄", uranus: "♅", neptune: "♆", pluto: "♇",
  chiron: "⚷", ceres: "⚳", pallas: "⚴", north_node_true: "☊", north_node_mean: "☊", lilith_mean: "⚸", lilith_true: "⚸", fortune: "⊗", vertex: "Vx",
  asc: "ASC", mc: "MC",
};

function normalizeLon(lon: number) {
  let value = lon % 360;
  if (value < 0) value += 360;
  return value;
}

function polarRelative(lon: number, anchorLon: number, radius: number, center = 180) {
  const delta = normalizeLon(lon - anchorLon);
  const theta = ((180 - delta) * Math.PI) / 180;
  return {
    x: center + Math.cos(theta) * radius,
    y: center + Math.sin(theta) * radius,
  };
}

function formatDeg(n: number) {
  const deg = Math.floor(n);
  const min = Math.round((n - deg) * 60);
  return `${deg}°${String(min).padStart(2, "0")}’`;
}

function signOfLon(lon: number) {
  const signs = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"];
  return signs[Math.floor(normalizeLon(lon) / 30)];
}

function formatOrdinal(value: number) {
  const mod10 = value % 10;
  const mod100 = value % 100;
  if (mod10 === 1 && mod100 !== 11) return `${value}st`;
  if (mod10 === 2 && mod100 !== 12) return `${value}nd`;
  if (mod10 === 3 && mod100 !== 13) return `${value}rd`;
  return `${value}th`;
}

function aspectLabel(aspectType: string) {
  return aspectType.charAt(0).toUpperCase() + aspectType.slice(1);
}

function markdownPointLabel(item: Body | Point | AnglePoint) {
  const overrides: Record<string, string> = {
    north_node_true: "North Node",
    north_node_mean: "North Node",
    lilith_mean: "Lilith",
    lilith_true: "Lilith",
    fortune: "Fortune",
    asc: "ASC",
    mc: "MC",
    dsc: "DSC",
    ic: "IC",
  };
  return overrides[item.id] || item.label;
}

function formatMarkdownPosition(item: Body | Point) {
  const segments = [`${markdownPointLabel(item)} in ${item.sign} ${formatDeg(item.degree)}`];
  if (item.retrograde) segments.push("Retrograde");
  if (item.house) segments.push(`in ${formatOrdinal(item.house)} House`);
  return segments.join(", ");
}

function buildChartMarkdown(chart: NatalChartRecord) {
  const lookup = new Map<string, string>();
  [...chart.bodies, ...chart.points].forEach((item) => {
    lookup.set(item.id, markdownPointLabel(item));
  });
  lookup.set("asc", "ASC");
  lookup.set("mc", "MC");
  lookup.set("dsc", "DSC");
  lookup.set("ic", "IC");

  const positions = [...chart.bodies, ...chart.points].map(formatMarkdownPosition);
  const angles = [chart.angles.asc, chart.angles.mc].map((angle) => `${markdownPointLabel(angle)} in ${angle.sign} ${formatDeg(angle.degree)}`);
  const houses = chart.houses.map((house) => `${formatOrdinal(house.house)} House in ${house.sign} ${formatDeg(house.degree)}`);
  const aspects = chart.aspects.map((aspect) => {
    const pointA = lookup.get(aspect.point_a) || aspect.point_a;
    const pointB = lookup.get(aspect.point_b) || aspect.point_b;
    return `${pointA} ${aspectLabel(aspect.aspect_type)} ${pointB} (Orb: ${aspect.orb_text})`;
  });

  return [...positions, "", ...angles, "", ...houses, "", ...aspects].join("\n");
}

function serializeChartSvg(container: HTMLDivElement | null) {
  const svg = container?.querySelector("svg");
  if (!svg) return null;
  const serializer = new XMLSerializer();
  const source = serializer.serializeToString(svg);
  if (!source) return null;
  return source.includes("xmlns=")
    ? source
    : source.replace("<svg", '<svg xmlns="http://www.w3.org/2000/svg"');
}

function normalizeText(value: string) {
  return value.trim().toLowerCase().replace(/\s+/g, " ");
}

function scoreCityMatch(query: string, city: CitySuggestion) {
  const normalizedQuery = normalizeText(query);
  const corpus = [
    city.label,
    city.local_label || "",
    ...(city.aliases || []),
  ]
    .map(normalizeText)
    .join(" ");

  if (!normalizedQuery) return 0;
  if (corpus.startsWith(normalizedQuery)) return 300 + (city.priority || 0);
  if (corpus.includes(normalizedQuery)) return 200 + (city.priority || 0);
  return 0;
}

function midpointLon(startLon: number, endLon: number) {
  return normalizeLon(startLon + normalizeLon(endLon - startLon) / 2);
}

function getTodayLocalDate() {
  const now = new Date();
  const yyyy = now.getFullYear();
  const mm = String(now.getMonth() + 1).padStart(2, "0");
  const dd = String(now.getDate()).padStart(2, "0");
  return `${yyyy}-${mm}-${dd}`;
}

function getCurrentLocalTime() {
  const now = new Date();
  const hh = String(now.getHours()).padStart(2, "0");
  const mm = String(now.getMinutes()).padStart(2, "0");
  return `${hh}:${mm}`;
}

function titleCaseToken(value: string) {
  if (!value) return "";
  if (value.toLowerCase() === "usa") return "USA";
  return value.charAt(0).toUpperCase() + value.slice(1).toLowerCase();
}

function recoverBirthPlaceName(placeName?: string | null, createdAt?: string | null) {
  const candidate = String(placeName || "").trim();
  if (candidate && !candidate.includes("GMT") && !candidate.startsWith("Sat ")) {
    return candidate;
  }

  const source = String(createdAt || "").trim();
  const match = source.match(/^\d{4}-\d{2}-\d{2}(?:[T-]\d{2}:\d{2}(?::\d{2}(?:\.\d+)?)?Z?)?-(.+)$/);
  if (!match) return "";

  const parts = match[1]
    .split("_")
    .map((part) => part.trim())
    .filter(Boolean);

  if (!parts.length) return "";

  if (parts.length >= 2 && parts.slice(-2).join("_").toLowerCase() === "south_korea") {
    const city = parts.slice(0, -2).map(titleCaseToken).join(" ");
    return city ? `${city}, South Korea` : "South Korea";
  }

  return parts.map(titleCaseToken).join(" ");
}

function normalizeStoredBirthDate(value: string) {
  const raw = String(value || "").trim();
  const match = raw.match(/^(\d{4}-\d{2}-\d{2})/);
  return match?.[1] || raw || "날짜 없음";
}

function normalizeStoredBirthTime(item: RemoteStoredChart) {
  const dateMatch = String(item.birth_date || "").match(/^\d{4}-\d{2}-\d{2}\s+(\d{2}:\d{2})/);
  if (dateMatch?.[1]) return dateMatch[1];
  return String(item.birth_time_local || "").trim() || "--:--";
}

function relativeChartAngle(lon: number, anchorLon: number) {
  return normalizeLon(lon - anchorLon);
}

function buildCollisionLayout(points: Body[], anchorLon: number) {
  const sorted = [...points]
    .map((point) => ({
      point,
      relativeLon: relativeChartAngle(point.lon, anchorLon),
    }))
    .sort((a, b) => a.relativeLon - b.relativeLon);

  const placements = new Map<string, { radialOffset: number; tangentialOffset: number; degreeOffset: number }>();
  const groups: typeof sorted[] = [];
  let current: typeof sorted = [];

  for (const item of sorted) {
    const prev = current[current.length - 1];
    if (!prev || item.relativeLon - prev.relativeLon <= 8) {
      current.push(item);
    } else {
      groups.push(current);
      current = [item];
    }
  }
  if (current.length) groups.push(current);

  for (const group of groups) {
    const count = group.length;
    group.forEach((entry, index) => {
      const centerOffset = index - (count - 1) / 2;
      const ringIndex = Math.abs(centerOffset) % 3;
      placements.set(entry.point.id, {
        radialOffset: ringIndex * 10 + (entry.point.classification === "mathematical_point" ? 6 : 0),
        tangentialOffset: centerOffset * 8,
        degreeOffset: centerOffset * 2.5,
      });
    });
  }

  return placements;
}

function getApiBase() {
  if (typeof window !== "undefined" && (window as any).__ASTRO_API_BASE__) {
    return (window as any).__ASTRO_API_BASE__ as string;
  }
  return "/api/chart";
}

function getApiRoot() {
  return getApiBase().replace(/\/api\/chart$/, "");
}

function getInternalAccessPassword() {
  if (typeof window !== "undefined" && (window as any).__ASTRO_PREVIEW_PASSWORD__) {
    return String((window as any).__ASTRO_PREVIEW_PASSWORD__);
  }
  return "7009";
}

const REPORT_PRESET_OPTIONS: Array<{ value: ReportPreset; label: string; note: string }> = [
  { value: "core_snapshot", label: "코어 스냅샷", note: "핵심 포인트만 간단히 보는 요약형" },
  { value: "core_report", label: "기본 보고서", note: "핵심 성향과 기본 흐름을 보는 표준형" },
  { value: "adult_deep_blueprint", label: "어른 심층", note: "성인용 심층 해석과 통합 패턴" },
  { value: "teen_growth_report", label: "청소년 성장", note: "학습, 진로, 부모 가이드 중심" },
  { value: "child_parenting_report", label: "유아·양육", note: "기질, 반응 패턴, 양육 코칭 중심" },
];

function reportPresetLabel(value: string) {
  return REPORT_PRESET_OPTIONS.find((item) => item.value === value)?.label || value;
}

const signTraitText: Record<string, string> = {
  Aries: "먼저 움직이며 직접 부딪혀 보는 힘이 비교적 빠르게 살아날 수 있습니다.",
  Taurus: "안정감과 감각적인 확실함을 차분하게 쌓아가는 방향이 중심에서 작동할 수 있습니다.",
  Gemini: "관심을 넓게 연결하고 빠르게 이해해 보려는 흐름이 자연스럽게 살아날 수 있습니다.",
  Cancer: "정서적 안전감과 가까운 관계를 살피는 감각이 중요한 바탕으로 작동할 수 있습니다.",
  Leo: "자신의 빛과 존재감을 따뜻하게 드러내고 싶어지는 에너지가 중심에서 살아날 수 있습니다.",
  Virgo: "섬세하게 정리하고 실제로 도움이 되는 방향을 찾으려는 감각이 강하게 작동할 수 있습니다.",
  Libra: "조화와 균형을 살피며 관계 안에서 아름다운 흐름을 만들려는 경향이 있습니다.",
  Scorpio: "깊이 있게 느끼고 본질을 놓치지 않으려는 집중력이 내면에서 강하게 작동할 수 있습니다.",
  Sagittarius: "넓게 보고 탐색하며 가능성을 향해 움직이려는 에너지가 중심에서 살아날 수 있습니다.",
  Capricorn: "현실적인 목표를 세우고 차근차근 성취해 가려는 힘이 안정적으로 작동할 수 있습니다.",
  Aquarius: "자기만의 관점으로 새롭게 바라보며 독립적으로 움직이려는 흐름이 살아날 수 있습니다.",
  Pisces: "직감과 공감의 흐름을 따라가며 섬세하게 분위기를 읽는 감각이 자연스럽게 작동할 수 있습니다.",
};

const houseThemeText: Record<number, string> = {
  1: "자기표현과 첫인상, 삶을 시작하는 태도에서 특히 두드러질 가능성이 있습니다.",
  2: "가치관과 안정감, 자신만의 리듬을 만들어 가는 영역에서 힘을 발휘할 수 있습니다.",
  3: "말과 배움, 일상적인 소통 방식 안에서 자주 드러날 가능성이 있습니다.",
  4: "내면의 안정과 가족, 편안함을 느끼는 기반에서 중요하게 작동할 수 있습니다.",
  5: "즐거움과 창조성, 표현의 기쁨을 살리는 장면에서 잘 살아날 수 있습니다.",
  6: "생활 습관과 실무 감각, 꾸준함이 필요한 자리에서 드러날 가능성이 있습니다.",
  7: "관계와 협력, 타인과의 균형을 맞추는 과정에서 크게 느껴질 수 있습니다.",
  8: "깊은 감정 교류와 변화, 몰입의 장면에서 강하게 작동할 수 있습니다.",
  9: "시야를 넓히고 배우며 삶의 의미를 찾아가는 흐름에서 살아날 수 있습니다.",
  10: "사회적 역할과 목표, 바깥에서 보이는 방향감에 연결될 가능성이 있습니다.",
  11: "친구와 네트워크, 미래 비전을 함께 그리는 장면에서 드러날 수 있습니다.",
  12: "혼자 정리하고 회복하는 내면의 공간에서 조용히 그러나 깊게 작동할 수 있습니다.",
};

async function fetchCitySuggestions(query: string): Promise<CitySuggestion[]> {
  const q = query.trim().toLowerCase();
  if (!q) return [];

  const presetMatches = KOREA_CITY_PRESETS
    .map((city) => ({ city, score: scoreCityMatch(query, city) }))
    .filter((entry) => entry.score > 0)
    .sort((a, b) => b.score - a.score)
    .map((entry) => entry.city);

  try {
    const res = await fetch(`${getApiRoot()}/api/geo/autocomplete?q=${encodeURIComponent(query)}`);
    if (!res.ok) throw new Error("autocomplete unavailable");
    const data = await res.json();
    const apiItems: CitySuggestion[] = (data.items || []).map((item: any) => ({
      label: item.label,
      local_label: item.local_label,
      country_code: item.country_code || "KR",
      timezone: item.timezone || "Asia/Seoul",
      latitude: Number(item.latitude),
      longitude: Number(item.longitude),
      source: "api",
      priority: item.country_code === "KR" ? 80 : 40,
      aliases: item.aliases || [],
    }));
    const merged = [...presetMatches];
    for (const item of apiItems) {
      if (!merged.some((m) => m.label.toLowerCase() === item.label.toLowerCase())) merged.push(item);
    }
    return merged
      .sort((a, b) => (b.priority || 0) - (a.priority || 0) || a.label.localeCompare(b.label))
      .slice(0, 10);
  } catch {
    return presetMatches.slice(0, 10);
  }
}

const sampleChart: NatalChartRecord = {
  metadata: { chart_id: "preview-19831126-0710", engine_name: "swiss_ephemeris", status: "ready", warnings: [] },
  input: {
    person_name: "김대한",
    birth_date: "2026-01-01",
    birth_time_local: "07:10",
    timezone: "Asia/Seoul",
    birth_place_name: "Seoul, South Korea",
    country_code: "KR",
    latitude: 37.5665,
    longitude: 126.978,
  },
  settings: { zodiac_type: "tropical", house_system: "placidus", node_mode: "true", lilith_mode: "mean_apogee" },
  angles: {
    asc: { id: "asc", label: "Ascendant", sign: "Scorpio", degree: 29.6333, formatted: "Scorpio 29°38’", lon: 239.6333 },
    mc: { id: "mc", label: "Midheaven", sign: "Virgo", degree: 12.3833, formatted: "Virgo 12°23’", lon: 162.3833 },
    dsc: { id: "dsc", label: "Descendant", sign: "Taurus", degree: 29.6333, formatted: "Taurus 29°38’", lon: 59.6333 },
    ic: { id: "ic", label: "Imum Coeli", sign: "Pisces", degree: 12.3833, formatted: "Pisces 12°23’", lon: 342.3833 },
  },
  houses: [
    { house: 1, sign: "Scorpio", degree: 29.6333, formatted: "Scorpio 29°38’", lon: 239.6333 },
    { house: 2, sign: "Capricorn", degree: 0.7, formatted: "Capricorn 0°42’", lon: 270.7 },
    { house: 3, sign: "Aquarius", degree: 6.35, formatted: "Aquarius 6°21’", lon: 306.35 },
    { house: 4, sign: "Pisces", degree: 12.3833, formatted: "Pisces 12°23’", lon: 342.3833 },
    { house: 5, sign: "Aries", degree: 13.4667, formatted: "Aries 13°28’", lon: 13.4667 },
    { house: 6, sign: "Taurus", degree: 8.5667, formatted: "Taurus 8°34’", lon: 38.5667 },
    { house: 7, sign: "Taurus", degree: 29.6333, formatted: "Taurus 29°38’", lon: 59.6333 },
    { house: 8, sign: "Cancer", degree: 0.7, formatted: "Cancer 0°42’", lon: 90.7 },
    { house: 9, sign: "Leo", degree: 6.35, formatted: "Leo 6°21’", lon: 126.35 },
    { house: 10, sign: "Virgo", degree: 12.3833, formatted: "Virgo 12°23’", lon: 162.3833 },
    { house: 11, sign: "Libra", degree: 13.4667, formatted: "Libra 13°28’", lon: 193.4667 },
    { house: 12, sign: "Scorpio", degree: 8.5667, formatted: "Scorpio 8°34’", lon: 218.5667 },
  ],
  bodies: [
    { id: "sun", label: "Sun", classification: "planet", sign: "Sagittarius", degree: 3.0667, formatted: "Sagittarius 3°04’", lon: 243.0667, house: 1 },
    { id: "moon", label: "Moon", classification: "planet", sign: "Leo", degree: 12.9, formatted: "Leo 12°54’", lon: 132.9, house: 9 },
    { id: "mercury", label: "Mercury", classification: "planet", sign: "Sagittarius", degree: 17.55, formatted: "Sagittarius 17°33’", lon: 257.55, house: 1 },
    { id: "venus", label: "Venus", classification: "planet", sign: "Libra", degree: 17.7667, formatted: "Libra 17°46’", lon: 197.7667, house: 11 },
    { id: "mars", label: "Mars", classification: "planet", sign: "Libra", degree: 4.3833, formatted: "Libra 4°23’", lon: 184.3833, house: 10 },
    { id: "jupiter", label: "Jupiter", classification: "planet", sign: "Sagittarius", degree: 17.75, formatted: "Sagittarius 17°45’", lon: 257.75, house: 1 },
    { id: "saturn", label: "Saturn", classification: "planet", sign: "Scorpio", degree: 10.2667, formatted: "Scorpio 10°16’", lon: 220.2667, house: 12 },
    { id: "uranus", label: "Uranus", classification: "planet", sign: "Sagittarius", degree: 8.9667, formatted: "Sagittarius 8°58’", lon: 248.9667, house: 1 },
    { id: "neptune", label: "Neptune", classification: "planet", sign: "Sagittarius", degree: 28, formatted: "Sagittarius 28°00’", lon: 268, house: 1 },
    { id: "pluto", label: "Pluto", classification: "planet", sign: "Scorpio", degree: 0.75, formatted: "Scorpio 0°45’", lon: 210.75, house: 11 },
  ],
  points: [
    { id: "north_node_true", label: "True Node", classification: "mathematical_point", definition: "true_node", sign: "Gemini", degree: 16.4333, formatted: "Gemini 16°26’", lon: 76.4333, house: 7, retrograde: true },
    { id: "lilith_mean", label: "Lilith", classification: "mathematical_point", definition: "mean_apogee", sign: "Aquarius", degree: 28.15, formatted: "Aquarius 28°09’", lon: 328.15, house: 3 },
    { id: "chiron", label: "Chiron", classification: "asteroid", definition: "chiron", sign: "Gemini", degree: 0.1833, formatted: "Gemini 0°11’", lon: 60.1833, house: 7, retrograde: true },
    { id: "ceres", label: "Ceres", classification: "asteroid", definition: "ceres", sign: "Virgo", degree: 8.25, formatted: "Virgo 8°15’", lon: 158.25, house: 10, retrograde: false },
    { id: "pallas", label: "Pallas Athena", classification: "asteroid", definition: "pallas", sign: "Aries", degree: 14.1, formatted: "Aries 14°06’", lon: 14.1, house: 5, retrograde: false },
    { id: "fortune", label: "Part of Fortune", classification: "mathematical_point", definition: "day_night_formula", sign: "Pisces", degree: 19.7833, formatted: "Pisces 19°47’", lon: 349.7833, house: 4 },
    { id: "vertex", label: "Vertex", classification: "mathematical_point", definition: "vertex", sign: "Cancer", degree: 15.1833, formatted: "Cancer 15°11’", lon: 105.1833, house: 8 },
  ],
  aspects: [
    { id: "asp_001", point_a: "sun", point_b: "moon", aspect_type: "trine", orb_text: "9°50’" },
    { id: "asp_002", point_a: "sun", point_b: "mars", aspect_type: "sextile", orb_text: "1°19’" },
    { id: "asp_003", point_a: "mercury", point_b: "jupiter", aspect_type: "conjunction", orb_text: "0°12’" },
    { id: "asp_004", point_a: "moon", point_b: "saturn", aspect_type: "square", orb_text: "2°38’" },
  ],
  availability: { core_complete: true, soft_missing: [] },
};

function JsonBlock({ value }: { value: unknown }) {
  return (
    <pre className="rounded-2xl bg-slate-950 text-slate-100 text-xs p-4 overflow-auto h-[420px] leading-6">
      {JSON.stringify(value, null, 2)}
    </pre>
  );
}

export default function AstroChartExtractorPreview() {
  const counselorCodeFromUrl = useMemo(() => {
    if (typeof window === "undefined") return "";
    return new URLSearchParams(window.location.search).get("counselor_code")?.trim().toUpperCase() || "";
  }, []);
  const testerLocalIdFromUrl = useMemo(() => {
    if (typeof window === "undefined") return "";
    return new URLSearchParams(window.location.search).get("tester_local_id")?.trim() || "";
  }, []);
  const defaultBirthDate = getTodayLocalDate();
  const defaultBirthTime = getCurrentLocalTime();
  const [form, setForm] = useState({
    person_name: "김대한",
    phone: "",
    email: "",
    consentPersonalInfo: true,
    birth_date: defaultBirthDate,
    birth_time_local: defaultBirthTime,
    timezone: "Asia/Seoul",
    birth_place_name: "Seoul, South Korea",
    country_code: "KR",
    latitude: "37.5665",
    longitude: "126.978",
    zodiac_type: "tropical",
    house_system: "placidus",
    node_mode: "true",
    lilith_mode: "mean_apogee",
    include_chiron: true,
    include_juno: true,
    include_vesta: true,
    include_ceres: true,
    include_pallas: true,
    include_vulcan: false,
    include_vertex: true,
    include_fortune: true,
    report_preset: "core_report" as ReportPreset,
    report_viewer_code: "",
  });
  const [chart, setChart] = useState<NatalChartRecord>(sampleChart);
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState("");
  const [internalStatusDetail, setInternalStatusDetail] = useState("");
  const [cityQuery, setCityQuery] = useState("Seoul, South Korea");
  const [citySuggestions, setCitySuggestions] = useState<CitySuggestion[]>([]);
  const [cityLoading, setCityLoading] = useState(false);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [workspaceMode, setWorkspaceMode] = useState<WorkspaceMode>("public");
  const [hasChartResult, setHasChartResult] = useState(false);
  const [accessPanelOpen, setAccessPanelOpen] = useState(false);
  const [passwordInput, setPasswordInput] = useState("");
  const [accessMessage, setAccessMessage] = useState("");
  const [savedLeads, setSavedLeads] = useState<SavedLead[]>([]);
  const [remoteStoredCharts, setRemoteStoredCharts] = useState<RemoteStoredChart[]>([]);
  const [remoteChartsLoading, setRemoteChartsLoading] = useState(false);
  const [adminSearchQuery, setAdminSearchQuery] = useState("");
  const [selectedLeadId, setSelectedLeadId] = useState("");
  const [show64Key, setShow64Key] = useState(false);
  const [jsonPanelOpen, setJsonPanelOpen] = useState(false);
  const [markdownCopyMessage, setMarkdownCopyMessage] = useState("");
  const [pendingArtworkRecordId, setPendingArtworkRecordId] = useState("");
  const cityBoxRef = useRef<HTMLDivElement | null>(null);
  const chartCardRef = useRef<HTMLDivElement | null>(null);

  const isInternalView = workspaceMode === "internal";
  const visiblePoints = useMemo(
    () => (isInternalView ? chart.points : chart.points.filter((point) => !chart.availability.soft_missing.includes(point.id))),
    [chart, isInternalView]
  );
  const softMissingLabels = useMemo(() => {
    const lookup = new Map([...chart.bodies, ...chart.points].map((item) => [item.id, item.label]));
    return chart.availability.soft_missing.map((id) => lookup.get(id) || id);
  }, [chart]);
  const savedLeadGroups = useMemo(() => {
    const grouped = new Map<string, SavedLead[]>();
    for (const lead of savedLeads) {
      const key = lead.form.birth_date || "날짜 없음";
      const bucket = grouped.get(key) || [];
      bucket.push(lead);
      grouped.set(key, bucket);
    }
    return Array.from(grouped.entries())
      .sort((a, b) => b[0].localeCompare(a[0]))
      .map(([date, leads]) => ({
        date,
        leads: [...leads].sort((a, b) => (a.form.person_name || "").localeCompare(b.form.person_name || "")),
      }));
  }, [savedLeads]);
  const remoteStoredChartGroups = useMemo<RemoteStoredChartGroup[]>(() => {
    const grouped = new Map<string, RemoteStoredChart[]>();
    for (const item of remoteStoredCharts) {
      const normalizedItem = {
        ...item,
        birth_date: normalizeStoredBirthDate(item.birth_date),
        birth_time_local: normalizeStoredBirthTime(item),
        birth_place_name: recoverBirthPlaceName(item.birth_place_name, item.created_at),
      };
      const bucket = grouped.get(normalizedItem.birth_date) || [];
      bucket.push(normalizedItem);
      grouped.set(normalizedItem.birth_date, bucket);
    }

    return Array.from(grouped.entries())
      .sort((a, b) => b[0].localeCompare(a[0]))
      .map(([date, items]) => ({
        date,
        items: [...items].sort((a, b) => String(a.person_name || "").localeCompare(String(b.person_name || ""))),
      }));
  }, [remoteStoredCharts]);
  const filteredSavedLeadGroups = useMemo(() => {
    const query = normalizeText(adminSearchQuery);
    if (!query) return savedLeadGroups;

    return savedLeadGroups
      .map((group) => ({
        ...group,
        leads: group.leads.filter((lead) =>
          normalizeText(
            [
              group.date,
              lead.id,
              lead.form.person_name,
              lead.form.birth_date,
              lead.form.birth_time_local,
              lead.form.birth_place_name,
              lead.form.report_preset,
              lead.form.report_viewer_code,
              lead.email,
            ].join(" ")
          ).includes(query)
        ),
      }))
      .filter((group) => group.leads.length > 0);
  }, [adminSearchQuery, savedLeadGroups]);
  const filteredRemoteStoredChartGroups = useMemo(() => {
    const query = normalizeText(adminSearchQuery);
    if (!query) return remoteStoredChartGroups;

    return remoteStoredChartGroups
      .map((group) => ({
        ...group,
        items: group.items.filter((item) =>
          normalizeText(
            [
              group.date,
              item.record_id,
              item.person_name,
              item.birth_date,
              item.birth_time_local,
              item.birth_place_name,
              item.phone,
              item.email,
              item.report_preset,
              item.report_product_code,
              item.report_viewer_code,
              item.report_payment_status,
            ].join(" ")
          ).includes(query)
        ),
      }))
      .filter((group) => group.items.length > 0);
  }, [adminSearchQuery, remoteStoredChartGroups]);
  const visibleRemoteChartCount = useMemo(
    () => filteredRemoteStoredChartGroups.reduce((sum, group) => sum + group.items.length, 0),
    [filteredRemoteStoredChartGroups]
  );
  const visibleSavedLeadCount = useMemo(
    () => filteredSavedLeadGroups.reduce((sum, group) => sum + group.leads.length, 0),
    [filteredSavedLeadGroups]
  );
  const chartMarkdown = useMemo(() => buildChartMarkdown(chart), [chart]);
  const sunBody = useMemo(() => chart.bodies.find((b) => b.id === "sun"), [chart]);
  const moonBody = useMemo(() => chart.bodies.find((b) => b.id === "moon"), [chart]);
  const internalSummary = useMemo(
    () => ({
      warnings: chart.metadata.warnings?.length || 0,
      optionalMissing: chart.availability.soft_missing.length,
      aspects: chart.aspects.length,
      points: visiblePoints.length,
    }),
    [chart, visiblePoints]
  );
  const cityContextLabel = useMemo(() => {
    const parts = [form.birth_place_name, form.timezone, form.country_code].filter(Boolean);
    return parts.join(" · ");
  }, [form.birth_place_name, form.timezone, form.country_code]);
  const publicBriefReading = useMemo<Array<{ key: string; lead: string; text: string; tone: string }>>(() => {
    const sunSignLabel = zodiacKorean[sunBody?.sign || ""] || sunBody?.sign || "태양 자리";
    const moonSignLabel = zodiacKorean[moonBody?.sign || ""] || moonBody?.sign || "달 자리";
    const ascSignLabel = zodiacKorean[chart.angles.asc.sign] || chart.angles.asc.sign;

    return [
      {
        key: "sun-sign",
        lead: "태양",
        tone: "text-amber-700",
        text: `이 ${sunSignLabel}에 있으면 ${signTraitText[sunBody?.sign || ""] || "자기 자신을 표현하는 방식에 고유한 결이 살아날 수 있습니다."}`,
      },
      {
        key: "sun-house",
        lead: "태양",
        tone: "text-amber-700",
        text: `이 ${sunBody?.house || "?"}하우스에 있으면 ${houseThemeText[sunBody?.house || 0] || "삶의 중요한 장면에서 자기표현의 방향이 드러날 수 있습니다."}`,
      },
      {
        key: "moon-sign",
        lead: "달",
        tone: "text-sky-700",
        text: `이 ${moonSignLabel}에 있으면 ${signTraitText[moonBody?.sign || ""] || "정서적 반응과 안정 욕구에 고유한 결이 나타날 수 있습니다."}`,
      },
      {
        key: "moon-house",
        lead: "달",
        tone: "text-sky-700",
        text: `이 ${moonBody?.house || "?"}하우스에 있으면 ${houseThemeText[moonBody?.house || 0] || "감정이 머무는 생활 장면에서 중요한 힌트를 줄 수 있습니다."}`,
      },
      {
        key: "asc-sign",
        lead: "어센던트",
        tone: "text-violet-700",
        text: `가 ${ascSignLabel}에 있으면 ${signTraitText[chart.angles.asc.sign] || "사람들과 처음 만나는 태도와 첫인상에 고유한 분위기가 나타날 수 있습니다."}`,
      },
    ];
  }, [chart.angles.asc.sign, moonBody?.house, moonBody?.sign, sunBody?.house, sunBody?.sign]);
  const publicBriefReadingPayload = useMemo(() => {
    const intro = "태양 사인은 자기 자신을, 어센던트는 당신이 세상에 보여주고 사람들과 만나는 방식을, 달 사인은 무의식의 당신을 말해주는 경향이 있습니다. 각 하우스는 관심이 머무는 영역이자 삶의 무대로 볼 수 있습니다.";
    const lines = publicBriefReading.map((item) => ({
      key: item.key,
      lead: item.lead,
      text: `${item.lead}${item.text}`,
      tone: item.tone,
    }));
    const outro = "당신의 더 많은 가능성을 심층보고서를 통해 알아보세요.";
    return {
      intro,
      lines,
      outro,
      text: [intro, ...lines.map((item) => item.text), outro].join("\n\n"),
    };
  }, [publicBriefReading]);

  useEffect(() => {
    if (typeof window === "undefined") return;
    try {
      const raw = window.localStorage.getItem("astro-saved-leads");
      if (!raw) return;
      const parsed = JSON.parse(raw) as SavedLead[];
      if (Array.isArray(parsed) && parsed.length) {
        setSavedLeads(parsed);
        setSelectedLeadId(parsed[0].id);
      }
    } catch {
      // ignore local storage parsing failures in the browser cache
    }
  }, []);

  useEffect(() => {
    if (!isInternalView) return;
    let cancelled = false;
    const run = async () => {
      setRemoteChartsLoading(true);
      try {
        const res = await fetch(`${getApiBase()}/stored-charts?limit=100`);
        if (!res.ok) throw new Error("stored charts unavailable");
        const data = await res.json();
        if (!cancelled) {
          setRemoteStoredCharts(Array.isArray(data.items) ? data.items : []);
        }
      } catch {
        if (!cancelled) setRemoteStoredCharts([]);
      } finally {
        if (!cancelled) setRemoteChartsLoading(false);
      }
    };
    run();
    return () => {
      cancelled = true;
    };
  }, [isInternalView]);

  useEffect(() => {
    if (!markdownCopyMessage) return;
    const timeout = window.setTimeout(() => setMarkdownCopyMessage(""), 1800);
    return () => window.clearTimeout(timeout);
  }, [markdownCopyMessage]);

  useEffect(() => {
    if (!pendingArtworkRecordId) return;
    let cancelled = false;

    const run = async () => {
      await new Promise((resolve) => window.setTimeout(resolve, 80));
      if (cancelled) return;
      const chartSvg = serializeChartSvg(chartCardRef.current);
      if (!chartSvg) {
        setPendingArtworkRecordId("");
        return;
      }

      try {
        await fetch(`${getApiBase()}/stored-charts/${encodeURIComponent(pendingArtworkRecordId)}/chart-art`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            chart_svg: chartSvg,
            chart_svg_updated_at: new Date().toISOString(),
          }),
        });
      } catch {
        // 차트 저장 본 흐름이 우선이라 SVG 동기화는 조용히 지나간다.
      } finally {
        if (!cancelled) setPendingArtworkRecordId("");
      }
    };

    run();
    return () => {
      cancelled = true;
    };
  }, [chart, pendingArtworkRecordId]);

  useEffect(() => {
    const q = cityQuery.trim();
    if (!q) {
      setCitySuggestions([]);
      return;
    }
    const timer = setTimeout(async () => {
      setCityLoading(true);
      const items = await fetchCitySuggestions(q);
      setCitySuggestions(items);
      setCityLoading(false);
    }, 200);
    return () => clearTimeout(timer);
  }, [cityQuery]);

  useEffect(() => {
    const onDocClick = (e: MouseEvent) => {
      if (cityBoxRef.current && !cityBoxRef.current.contains(e.target as Node)) setShowSuggestions(false);
    };
    document.addEventListener("mousedown", onDocClick);
    return () => document.removeEventListener("mousedown", onDocClick);
  }, []);

  function applyCitySuggestion(city: CitySuggestion) {
    setCityQuery(city.label);
    setShowSuggestions(false);
    setForm((prev) => ({
      ...prev,
      birth_place_name: city.label,
      country_code: city.country_code,
      timezone: city.timezone,
      latitude: String(city.latitude),
      longitude: String(city.longitude),
    }));
  }

  function persistLead(nextChart: NatalChartRecord) {
    if (typeof window === "undefined") return;

    const lead: SavedLead = {
      id: nextChart.metadata.chart_id,
      label: `${form.person_name || "이름 없음"} · ${form.birth_date}`,
      email: form.email,
      birth_place_name: form.birth_place_name,
      created_at: new Date().toISOString(),
      form: {
        person_name: form.person_name,
        phone: form.phone,
        email: form.email,
        counselor_code: counselorCodeFromUrl || null,
        tester_local_id: testerLocalIdFromUrl || null,
        birth_date: form.birth_date,
        birth_time_local: form.birth_time_local,
        timezone: form.timezone,
        birth_place_name: form.birth_place_name,
        country_code: form.country_code,
        latitude: form.latitude,
        longitude: form.longitude,
        report_preset: form.report_preset,
        report_viewer_code: form.report_viewer_code,
      },
      chart: nextChart,
    };

    setSavedLeads((prev) => {
      const deduped = [lead, ...prev.filter((item) => item.id !== lead.id)].slice(0, 20);
      window.localStorage.setItem("astro-saved-leads", JSON.stringify(deduped));
      return deduped;
    });
    setSelectedLeadId(lead.id);
  }

  function loadSavedLead(leadId: string) {
    const lead = savedLeads.find((item) => item.id === leadId);
    if (!lead) return;

    setSelectedLeadId(lead.id);
    setChart(lead.chart);
    setHasChartResult(true);
    setCityQuery(lead.form.birth_place_name);
    setForm((prev) => ({
      ...prev,
      ...lead.form,
    }));
    setStatus(`${lead.form.person_name} 저장 차트를 불러왔어요.`);
  }

  async function loadRemoteStoredChart(item: RemoteStoredChart) {
    setSelectedLeadId(item.record_id);
    if (!item.chart) {
      try {
        const res = await fetch(`${getApiBase()}/stored-charts/${encodeURIComponent(item.record_id)}`);
        if (res.ok) {
          const data = await res.json();
          if (data?.item) item = data.item;
        }
      } catch {
        // fall back to form-only restore below
      }
    }
    if (item.chart) {
      setChart(item.chart);
      setHasChartResult(true);
      setCityQuery(item.chart.input.birth_place_name);
      setForm((prev) => ({
        ...prev,
        person_name: item.chart?.input.person_name || prev.person_name,
        birth_date: item.chart.input.birth_date,
        birth_time_local: item.chart.input.birth_time_local,
        timezone: item.chart.input.timezone,
        birth_place_name: item.chart.input.birth_place_name,
        country_code: item.chart.input.country_code || prev.country_code,
        latitude: String(item.chart.input.latitude),
        longitude: String(item.chart.input.longitude),
        phone: item.phone || prev.phone,
        email: item.email || prev.email,
        report_preset: (item.report_preset as ReportPreset) || prev.report_preset,
        report_viewer_code: item.report_viewer_code || prev.report_viewer_code,
      }));
      setStatus(`${item.person_name || "저장된 차트"} 차트를 불러왔어요.`);
      return;
    }

    const birthDateMatch = String(item.birth_date || "").match(/^(\d{4}-\d{2}-\d{2})(?:\s+(\d{2}:\d{2}))?(?:\s+\(([^)]+)\))?/);
    const normalizedPlaceName = recoverBirthPlaceName(item.birth_place_name, item.created_at);
    setForm((prev) => ({
      ...prev,
      person_name: item.person_name || prev.person_name,
      phone: item.phone || prev.phone,
      email: item.email || prev.email,
      birth_date: birthDateMatch?.[1] || prev.birth_date,
      birth_time_local: birthDateMatch?.[2] || item.birth_time_local || prev.birth_time_local,
      timezone: birthDateMatch?.[3] || prev.timezone,
      birth_place_name: normalizedPlaceName || prev.birth_place_name,
      report_preset: (item.report_preset as ReportPreset) || prev.report_preset,
      report_viewer_code: item.report_viewer_code || prev.report_viewer_code,
    }));
    if (normalizedPlaceName) {
      setCityQuery(normalizedPlaceName);
    }
    setStatus(`${item.person_name || "저장된 기록"} 정보를 불러왔어요. 차트를 다시 계산하면 최신 휠로 열립니다.`);
  }

  async function handleCalculate() {
    if (!form.consentPersonalInfo) {
      setStatus("개인정보 수집 및 이용 동의가 필요합니다.");
      return;
    }

    setLoading(true);
    setStatus("무료 네이탈 차트를 계산하고 있어요...");
    setInternalStatusDetail("");
    if (!/^\d{4}$/.test(form.report_viewer_code)) {
      setLoading(false);
      setStatus("리포트 확인 코드 4자리를 입력해 주세요.");
      return;
    }
    try {
      const payload = {
        person_name: form.person_name,
        phone: form.phone,
        email: form.email,
        birth_date: form.birth_date,
        birth_time_local: form.birth_time_local,
        timezone: form.timezone,
        birth_place_name: form.birth_place_name,
        country_code: form.country_code,
        latitude: Number(form.latitude),
        longitude: Number(form.longitude),
        zodiac_type: form.zodiac_type,
        house_system: form.house_system,
        node_mode: form.node_mode,
        lilith_mode: form.lilith_mode,
        fortune_formula: "day_night",
        include_chiron: form.include_chiron,
        include_juno: form.include_juno,
        include_vesta: form.include_vesta,
        include_ceres: form.include_ceres,
        include_pallas: form.include_pallas,
        include_vulcan: form.include_vulcan,
        include_vertex: form.include_vertex,
        include_fortune: form.include_fortune,
        report_preset: form.report_preset,
        report_addons: [],
        report_id: "",
        report_viewer_code: form.report_viewer_code || null,
        report_product_code: form.report_preset,
        report_payment_status: "pending",
      };

      const res = await fetch(`${getApiBase()}/extract-and-store`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (!res.ok) {
        const text = await res.text();
        throw new Error(text || "실제 계산 API가 아직 연결되지 않았어요");
      }

      const data = await res.json();
      const nextChart = data.chart ?? data;
      setChart(nextChart);
      setHasChartResult(true);
      persistLead(nextChart);
      if (data.storage?.stored) {
        setStatus("차트가 준비되었어요.");
        if (data.storage?.record_id) {
          setPendingArtworkRecordId(data.storage.record_id);
        }
        const storageBits = [
          data.storage.row_appended ? "row appended" : "",
          data.storage.row_updated ? "row updated" : "",
          data.storage.row_number ? `row ${data.storage.row_number}` : "",
          data.storage.record_id ? `record ${data.storage.record_id}` : "",
        ].filter(Boolean).join(" · ");
        setInternalStatusDetail(
          [`stored to ${data.storage.destination}`, storageBits].filter(Boolean).join(" · ")
        );
      } else if (data.storage?.attempted) {
        setStatus("차트 계산이 완료되었어요.");
        setInternalStatusDetail(data.storage?.message || "storage attempt failed");
      } else {
        setStatus("차트 계산이 완료되었어요.");
        setInternalStatusDetail(data.storage?.message || "storage not configured");
      }
    } catch (e: any) {
      setHasChartResult(false);
      setStatus("아직 새로운 차트 해석을 불러오지 못했습니다. 잠시 후 다시 시도해 주세요.");
      setInternalStatusDetail(e?.message || "backend unavailable");
    } finally {
      setLoading(false);
    }
  }

  function handleInternalAccess() {
    if (passwordInput === getInternalAccessPassword()) {
      setWorkspaceMode("internal");
      setAccessMessage("");
      setAccessPanelOpen(false);
      setPasswordInput("");
      return;
    }
    setAccessMessage("비밀번호가 맞지 않습니다.");
  }

  function handleDownloadChart() {
    const source = serializeChartSvg(chartCardRef.current);
    if (!source) return;
    const blob = new Blob([source], { type: "image/svg+xml;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `${chart.metadata.chart_id || "natal-chart"}.svg`;
    document.body.appendChild(link);
    link.click();
    link.remove();
    URL.revokeObjectURL(url);
  }

  async function handleCopyChartMarkdown() {
    try {
      await navigator.clipboard.writeText(chartMarkdown);
      setMarkdownCopyMessage("복사 완료");
    } catch {
      setMarkdownCopyMessage("복사 실패");
    }
  }

  return (
    <div className="min-h-screen bg-[radial-gradient(circle_at_14%_16%,rgba(183,211,196,0.36),transparent_22%),radial-gradient(circle_at_84%_14%,rgba(234,198,163,0.34),transparent_24%),linear-gradient(180deg,#f6f2ea_0%,#eef3ed_44%,#f5efe6_100%)] text-slate-900 p-4 md:p-6">
      <div className="mx-auto max-w-7xl space-y-6">
        <div className="rounded-[2.25rem] border border-[rgba(120,137,128,0.14)] bg-[rgba(255,251,245,0.84)] p-6 shadow-[0_24px_80px_rgba(65,72,82,0.10)] backdrop-blur">
          <div className="flex items-start justify-between gap-4">
            <div className="mx-auto max-w-4xl text-center">
              <div className="inline-flex rounded-full border border-[rgba(190,123,71,0.20)] bg-[rgba(255,248,240,0.88)] px-3 py-1 text-xs font-medium uppercase tracking-[0.25em] text-[#9a6540]">
                natal.kr
              </div>
              <h1 className="mt-5 text-4xl font-semibold tracking-tight text-slate-900 md:text-6xl">
                당신의 차트를, 읽을 수 있는 보고서로.
              </h1>
              <p className="mx-auto mt-5 max-w-2xl text-base leading-8 text-slate-600 md:text-xl">
                출생 데이터를 바탕으로 차트를 계산하고, 먼저 호로스코프 휠을 확인할 수 있도록 구성했습니다. 이 화면은 차트 계산과 기본 확인에 집중하고, 보고서 안내와 운영 흐름은 별도 페이지에서 이어집니다.
              </p>
              <div className="mt-8 flex flex-wrap justify-center gap-3">
                <a href="#apply" className="rounded-full border border-[rgba(124,141,132,0.14)] bg-[rgba(255,255,255,0.82)] px-6 py-3 text-sm font-medium text-slate-800 shadow-[0_12px_28px_rgba(84,90,99,0.08)] transition hover:-translate-y-[1px]">
                  내 네이탈 차트 확인하기
                </a>
              </div>
            </div>
            <div className="flex items-center gap-2">
              {workspaceMode === "internal" && (
                <button
                  onClick={() => setWorkspaceMode("public")}
                  className="rounded-full border border-[rgba(124,141,132,0.14)] bg-white px-4 py-2 text-sm font-medium text-slate-600 shadow-sm transition hover:border-[rgba(190,123,71,0.24)] hover:text-slate-900"
                >
                  Public 보기
                </button>
              )}
              <button
                onClick={() => setAccessPanelOpen((prev) => !prev)}
                className="flex h-11 w-11 items-center justify-center rounded-full border border-[rgba(124,141,132,0.14)] bg-white text-slate-700 shadow-sm transition hover:border-[rgba(190,123,71,0.24)] hover:text-slate-900"
                aria-label="관리 화면 열기"
              >
                <span className="text-xl leading-none">⚙</span>
              </button>
            </div>
          </div>

          {accessPanelOpen && (
            <div className="mt-5 rounded-[1.5rem] border border-slate-200 bg-slate-50/80 p-4">
              <div className="text-sm font-semibold text-slate-800">비밀번호를 입력하세요</div>
              <div className="mt-3 flex gap-3">
                <input
                  type="password"
                  value={passwordInput}
                  onChange={(e) => setPasswordInput(e.target.value)}
                  placeholder="관리 비밀번호"
                  className="flex-1 rounded-2xl border border-slate-200 bg-white px-4 py-3"
                />
                <button onClick={handleInternalAccess} className="rounded-2xl bg-slate-900 px-4 py-3 text-sm font-medium text-white">
                  입장
                </button>
              </div>
              {accessMessage && <div className="mt-3 text-sm text-rose-600">{accessMessage}</div>}
            </div>
          )}
        </div>

        {workspaceMode === "public" ? (
          <>
            <div className="grid gap-8 xl:grid-cols-[minmax(0,1fr)_420px]">
              <div className="space-y-6">
                <div ref={chartCardRef} className="rounded-[2.1rem] border border-[rgba(120,137,128,0.14)] bg-[rgba(255,252,247,0.88)] p-6 shadow-[0_24px_60px_rgba(65,72,82,0.08)]">
                  <div className="flex flex-wrap items-center justify-between gap-3">
                    <div>
                      <div className="text-xs font-semibold uppercase tracking-[0.24em] text-slate-400">Horoscope</div>
                      <h2 className="mt-2 text-3xl font-semibold">Your Horoscope Chart</h2>
                      <p className="mt-2 text-sm leading-7 text-slate-500">입력한 출생 정보 기준으로 호로스코프 휠과 핵심 위치를 함께 확인합니다.</p>
                    </div>
                    <div className="flex flex-wrap items-center gap-2">
                      <label className="flex items-center gap-2 rounded-2xl border border-[rgba(124,141,132,0.14)] bg-white px-3 py-2 text-sm font-medium text-slate-700">
                        <input
                          type="checkbox"
                          className="h-4 w-4 accent-slate-900"
                          checked={show64Key}
                          onChange={(e) => setShow64Key(e.target.checked)}
                        />
                        고급 64key 보기
                      </label>
                      <button onClick={handleDownloadChart} disabled={!hasChartResult} className="rounded-2xl border border-[rgba(124,141,132,0.14)] bg-white px-4 py-3 text-sm font-medium text-slate-700 disabled:opacity-50">
                        다운로드
                      </button>

                    </div>
                  </div>

                  <div className="mt-6 rounded-[2rem] border border-[rgba(142,156,147,0.16)] bg-[radial-gradient(circle_at_center,#ffffff_0%,#f7f3eb_54%,#ebf1ea_100%)] p-4">
                    <div className="mx-auto aspect-square max-w-[880px]">
                      <NCWheel chart={chart} size={880} hexagramCsvText={hexagramCsvText} show64Key={show64Key} className="h-full w-full" />
                    </div>
                  </div>

                  <div className="mt-5 rounded-[1.5rem] border border-dashed border-[rgba(142,156,147,0.18)] bg-[rgba(255,255,255,0.72)] px-4 py-4 text-sm leading-7 text-slate-500">
                    64key 보기는 기본 차트 해석보다 한 단계 더 깊은 비교용 보기입니다. 먼저 기본 휠을 확인한 뒤 필요할 때만 켜는 흐름을 권장합니다.
                  </div>
                </div>
              </div>

              <div id="apply" className="rounded-[2.1rem] border border-[rgba(120,137,128,0.14)] bg-[rgba(255,252,247,0.86)] p-6 shadow-[0_24px_60px_rgba(65,72,82,0.08)]">
                <div>
                  <div className="text-xs font-semibold uppercase tracking-[0.24em] text-slate-400">Input</div>
                  <h2 className="mt-2 text-3xl font-semibold">기본 정보 입력</h2>
                  <p className="mt-2 text-sm leading-7 text-slate-500">
                    이름과 연락처를 남기고 출생 정보를 입력하면, 왼쪽에서 바로 호로스코프 휠을 확인할 수 있습니다.
                  </p>
                </div>

                <div className="mt-6 grid grid-cols-1 gap-4 text-sm md:grid-cols-2">
                  <label className="space-y-1 md:col-span-2">
                    <span className="text-slate-600">이름</span>
                    <input className="w-full rounded-2xl border border-[rgba(124,141,132,0.14)] bg-white/86 px-4 py-3" value={form.person_name} onChange={(e) => setForm((prev) => ({ ...prev, person_name: e.target.value }))} />
                  </label>

                  <label className="space-y-1">
                    <span className="text-slate-600">생년월일</span>
                    <input type="date" className="w-full rounded-2xl border border-[rgba(124,141,132,0.14)] bg-white/86 px-4 py-3" value={form.birth_date} onChange={(e) => setForm((prev) => ({ ...prev, birth_date: e.target.value }))} />
                  </label>

                  <label className="space-y-1">
                    <span className="text-slate-600">출생 시간</span>
                    <input type="time" className="w-full rounded-2xl border border-[rgba(124,141,132,0.14)] bg-white/86 px-4 py-3" value={form.birth_time_local} onChange={(e) => setForm((prev) => ({ ...prev, birth_time_local: e.target.value }))} />
                  </label>

                  <div className="space-y-1 md:col-span-2" ref={cityBoxRef}>
                    <span className="text-slate-600">지역 선택</span>
                    <div className="relative">
                      <input
                        className="w-full rounded-2xl border border-[rgba(124,141,132,0.14)] bg-white/86 px-4 py-3"
                        value={cityQuery}
                        onFocus={() => setShowSuggestions(true)}
                        onChange={(e) => {
                          const next = e.target.value;
                          setCityQuery(next);
                          setShowSuggestions(true);
                          setForm((prev) => ({ ...prev, birth_place_name: next }));
                        }}
                        placeholder="서울, 안양, 구리, Daejeon"
                      />
                      {showSuggestions && (cityLoading || citySuggestions.length > 0) && (
                        <div className="absolute z-20 mt-2 w-full overflow-hidden rounded-2xl border border-[rgba(124,141,132,0.14)] bg-white shadow-lg">
                          {cityLoading && <div className="px-3 py-2 text-sm text-slate-500">검색 중...</div>}
                          {!cityLoading && citySuggestions.map((city) => (
                            <button key={`${city.label}-${city.source}`} onClick={() => applyCitySuggestion(city)} className="w-full border-t border-slate-100 px-3 py-3 text-left first:border-t-0 hover:bg-slate-50">
                              <div className="flex items-center justify-between gap-3">
                                <div>
                                  <div className="text-sm font-medium">{city.local_label ? `${city.local_label} · ${city.label}` : city.label}</div>
                                  <div className="text-xs text-slate-500">{city.timezone} · {city.latitude}, {city.longitude}</div>
                                </div>
                                {city.country_code === "KR" && <span className="rounded-full bg-rose-50 px-2 py-1 text-[11px] font-medium text-rose-700">Korea first</span>}
                              </div>
                            </button>
                          ))}
                        </div>
                      )}
                    </div>
                    <div className="text-xs text-slate-500">한글/영문 도시명 모두 검색하고, 한국 도시는 우선 제안합니다.</div>
                  </div>

                  <div className="md:col-span-2 rounded-[1.5rem] border border-[rgba(124,141,132,0.14)] bg-[rgba(243,245,239,0.82)] px-4 py-4">
                    <div className="flex flex-wrap items-center justify-between gap-2">
                      <div>
                        <div className="text-sm font-medium text-slate-800">자동 설정된 위치 정보</div>
                        <div className="mt-1 text-xs leading-5 text-slate-500">
                          도시 선택 시 시간대와 국가 코드가 자동으로 채워집니다. 필요할 때만 수정하세요.
                        </div>
                      </div>
                      <div className="rounded-full bg-white px-3 py-1 text-xs font-medium text-slate-600">
                        {cityContextLabel || "위치 정보 없음"}
                      </div>
                    </div>
                    <div className="mt-4 grid grid-cols-2 gap-3">
                      <label className="space-y-1">
                        <span className="text-slate-600">Timezone</span>
                        <input className="w-full rounded-2xl border border-[rgba(124,141,132,0.14)] bg-white px-4 py-3" value={form.timezone} onChange={(e) => setForm((prev) => ({ ...prev, timezone: e.target.value }))} />
                      </label>

                      <label className="space-y-1">
                        <span className="text-slate-600">국가 코드</span>
                        <input className="w-full rounded-2xl border border-[rgba(124,141,132,0.14)] bg-white px-4 py-3" value={form.country_code} onChange={(e) => setForm((prev) => ({ ...prev, country_code: e.target.value }))} />
                      </label>
                    </div>
                  </div>

                  <label className="space-y-1 md:col-span-2">
                    <span className="text-slate-600">연락처</span>
                    <input className="w-full rounded-2xl border border-[rgba(124,141,132,0.14)] bg-white/86 px-4 py-3" value={form.phone} onChange={(e) => setForm((prev) => ({ ...prev, phone: e.target.value }))} placeholder="010-1234-5678" />
                  </label>

                  <label className="space-y-1 md:col-span-2">
                    <span className="text-slate-600">이메일 주소</span>
                    <input type="email" className="w-full rounded-2xl border border-[rgba(124,141,132,0.14)] bg-white/86 px-4 py-3" value={form.email} onChange={(e) => setForm((prev) => ({ ...prev, email: e.target.value }))} />
                  </label>

                  <label className="space-y-1 md:col-span-2">
                    <span className="text-slate-600">리포트 확인 코드(4자리)</span>
                    <input
                      inputMode="numeric"
                      maxLength={4}
                      className="w-full rounded-2xl border border-[rgba(124,141,132,0.14)] bg-white/86 px-4 py-3 tracking-[0.35em]"
                      value={form.report_viewer_code}
                      onChange={(e) => setForm((prev) => ({ ...prev, report_viewer_code: e.target.value.replace(/[^0-9]/g, "").slice(0, 4) }))}
                      placeholder="4자리 숫자"
                    />
                    <div className="text-xs text-slate-500">
                      이 코드는 나중에 본인 확인용으로 사용됩니다. 신청 정보와 함께 안전하게 보관해 주세요.
                    </div>
                  </label>
                </div>
                <label className="mt-6 flex items-start gap-3 rounded-[1.5rem] border border-[rgba(124,141,132,0.14)] bg-[rgba(243,245,239,0.76)] px-4 py-4 text-sm leading-6 text-slate-600">
                  <input
                    type="checkbox"
                    className="mt-1 h-4 w-4 shrink-0 accent-slate-900"
                    checked={form.consentPersonalInfo}
                    onChange={(e) => setForm((prev) => ({ ...prev, consentPersonalInfo: e.target.checked }))}
                  />
                  <span>
                    개인정보는 3개월간 보관되며, 차트분석 전달 및 마케팅에만 사용됩니다.
                  </span>
                </label>

                <div className="mt-6 flex gap-3">
                  <button onClick={handleCalculate} disabled={loading} className="flex-1 rounded-2xl bg-[linear-gradient(180deg,#d6c8a8_0%,#c7b48c_100%)] px-4 py-3 font-medium text-[#22312e] shadow-[0_14px_30px_rgba(157,136,96,0.18)] disabled:opacity-60">
                    {loading ? "차트 계산 중..." : "내 네이탈 차트 확인하기"}
                  </button>
                </div>

                {status && (
                  <div className="mt-5 rounded-[1.5rem] border border-[rgba(124,141,132,0.14)] bg-[rgba(243,245,239,0.76)] p-4 text-sm text-slate-600">
                    <div>{status}</div>
                  </div>
                )}
              </div>
            </div>

            {hasChartResult && (
              <div className="mt-10 rounded-[2rem] border border-[rgba(120,137,128,0.10)] bg-transparent p-2">
                <div className="text-xs uppercase tracking-[0.22em] text-slate-400">Short Reading</div>
                <div className="mt-5 max-w-5xl text-[20px] leading-[1.95] text-slate-600 md:text-[25px]">
                  {publicBriefReadingPayload.intro}
                </div>
                <div className="mt-4 max-w-5xl text-[20px] leading-[1.95] text-slate-700 md:text-[25px]">
                  {publicBriefReading.map((item) => (
                    <p key={item.key} className="m-0">
                      <span className={`font-semibold ${item.tone}`}>{item.lead}</span>
                      {item.text}
                    </p>
                  ))}
                </div>
                <div className="mt-6 max-w-5xl text-[20px] font-medium leading-[1.9] text-slate-900 md:text-[25px]">
                  {publicBriefReadingPayload.outro}
                </div>
              </div>
            )}
          </>
        ) : (
          <>
            <div className="rounded-[2rem] border border-slate-200 bg-white/90 p-5 text-sm leading-7">
              <div className="font-semibold mb-2">저장된 차트 목록</div>
              <div className="mb-3 flex flex-col gap-3 md:flex-row md:items-center">
                <input
                  value={adminSearchQuery}
                  onChange={(e) => setAdminSearchQuery(e.target.value)}
                  placeholder="이름, 날짜, 시간, 지역, record_id 검색"
                  className="w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-700 outline-none transition placeholder:text-slate-400 focus:border-slate-400 md:flex-1"
                />
                <div className="text-xs text-slate-500">
                  {remoteStoredCharts.length ? `${visibleRemoteChartCount}건 표시` : `${visibleSavedLeadCount}건 표시`}
                </div>
              </div>
              <div className="rounded-[1.25rem] border border-slate-200 bg-slate-50 px-4 py-4 font-mono text-[13px] leading-7 text-slate-700">
                {remoteChartsLoading ? (
                  <div>- 저장소 목록을 불러오는 중입니다.</div>
                ) : filteredRemoteStoredChartGroups.length ? (
                  filteredRemoteStoredChartGroups.map((group) => (
                    <div key={group.date} className="mb-3 last:mb-0">
                      <div># {group.date}</div>
                      {group.items.map((item) => (
                        <button
                          key={item.record_id}
                          type="button"
                          onClick={() => { void loadRemoteStoredChart(item); }}
                          className={`mt-2 block w-full rounded-2xl border px-4 py-3 text-left font-sans transition ${
                            selectedLeadId === item.record_id
                              ? "border-slate-900 bg-slate-100 shadow-sm"
                              : "border-slate-200 bg-white hover:border-slate-300 hover:bg-slate-50"
                          }`}
                        >
                          <div className="flex flex-wrap items-center justify-between gap-2">
                            <div className="text-sm font-semibold text-slate-900">
                              {item.person_name || "이름 없음"}
                            </div>
                            <div className="text-[11px] uppercase tracking-[0.18em] text-slate-400">
                              {item.record_id}
                            </div>
                          </div>
                          <div className="text-sm text-slate-600">
                            {group.date} · {item.birth_time_local || "--:--"} · {item.birth_place_name || "지역 없음"}
                          </div>
                          <div className="mt-2 flex flex-wrap gap-2 text-[11px] font-medium text-slate-500">
                            {item.report_preset && <span className="rounded-full bg-slate-100 px-2 py-1">{reportPresetLabel(item.report_preset)}</span>}
                            {item.report_payment_status && <span className="rounded-full bg-amber-50 px-2 py-1 text-amber-700">{item.report_payment_status}</span>}
                            {item.report_viewer_code && <span className="rounded-full bg-emerald-50 px-2 py-1 text-emerald-700">열람 코드 {item.report_viewer_code}</span>}
                          </div>
                        </button>
                      ))}
                    </div>
                  ))
                ) : filteredSavedLeadGroups.length ? (
                  filteredSavedLeadGroups.map((group) => (
                    <div key={group.date} className="mb-3 last:mb-0">
                      <div># {group.date}</div>
                      {group.leads.map((lead) => (
                        <button
                          key={lead.id}
                          type="button"
                          onClick={() => loadSavedLead(lead.id)}
                          className={`mt-2 block w-full rounded-2xl border px-4 py-3 text-left font-sans transition ${
                            selectedLeadId === lead.id
                              ? "border-slate-900 bg-slate-100 shadow-sm"
                              : "border-slate-200 bg-white hover:border-slate-300 hover:bg-slate-50"
                          }`}
                        >
                          <div className="flex flex-wrap items-center justify-between gap-2">
                            <div className="text-sm font-semibold text-slate-900">
                              {lead.form.person_name || "이름 없음"}
                            </div>
                            <div className="text-[11px] uppercase tracking-[0.18em] text-slate-400">
                              local
                            </div>
                          </div>
                          <div className="text-sm text-slate-600">
                            {group.date} · {lead.form.birth_time_local || "--:--"} · {lead.form.birth_place_name || "지역 없음"}
                          </div>
                        </button>
                      ))}
                    </div>
                  ))
                ) : adminSearchQuery.trim() ? (
                  <div>- 검색 결과가 없습니다.</div>
                ) : (
                  <div>- 저장된 차트가 아직 없습니다.</div>
                )}
              </div>
            </div>

            <div className="space-y-6">
              <div ref={chartCardRef} className="rounded-[2rem] border border-white/70 bg-white/95 p-6 shadow-sm">
                <div className="flex flex-wrap items-start justify-between gap-4">
                  <div>
                    <h2 className="text-2xl font-semibold">정교한 호로스코프 휠</h2>
                    <p className="mt-1 text-sm text-slate-500">ASC 9시 기준 · 반시계 진행 · 내부 상세 검토 화면</p>
                  </div>
                  <div className="flex flex-wrap items-center gap-2">
                    <label className="flex items-center gap-2 rounded-full bg-white px-3 py-1 text-sm shadow">
                      <input
                        type="checkbox"
                        className="h-4 w-4 accent-slate-900"
                        checked={show64Key}
                        onChange={(e) => setShow64Key(e.target.checked)}
                      />
                      64key 보기
                    </label>
                    <span className="rounded-full bg-white px-3 py-1 text-sm shadow">{chart.settings.zodiac_type}</span>
                    <span className="rounded-full bg-white px-3 py-1 text-sm shadow">{chart.settings.house_system}</span>
                    <span className="rounded-full bg-white px-3 py-1 text-sm shadow">{chart.settings.node_mode} node</span>
                    <span className={`rounded-full px-3 py-1 text-sm shadow ${chart.availability.core_complete ? "bg-emerald-50 text-emerald-700" : "bg-amber-50 text-amber-700"}`}>
                      {chart.availability.core_complete ? "Core complete" : "Needs review"}
                    </span>
                  </div>
                </div>

                <div className="mt-5 rounded-[2rem] border border-stone-200 bg-[radial-gradient(circle_at_center,#ffffff_0%,#f8fafc_52%,#f3eadc_100%)] p-4">
                  <div className="mx-auto aspect-square max-w-[960px]">
                    <NCWheel chart={chart} size={960} hexagramCsvText={hexagramCsvText} show64Key={show64Key} className="h-full w-full" />
                  </div>
                </div>

                <div className="mt-5 grid gap-4 lg:grid-cols-4">
                  <div className="rounded-[1.5rem] border border-emerald-100 bg-emerald-50 px-4 py-4">
                    <div className="text-sm text-emerald-700">검토 상태</div>
                    <div className="mt-2 text-2xl font-semibold text-emerald-950">{chart.availability.core_complete ? "Ready" : "Check"}</div>
                    <div className="mt-2 text-xs leading-5 text-emerald-800/80">
                      {chart.availability.core_complete ? "핵심 천체와 각도가 계산되어 바로 검토할 수 있습니다." : "핵심 결과에 누락이 있어 재확인이 필요합니다."}
                    </div>
                  </div>
                  <div className="rounded-[1.5rem] border border-slate-200 bg-slate-50 px-4 py-4">
                    <div className="text-sm text-slate-500">경고 / 선택 누락</div>
                    <div className="mt-2 text-2xl font-semibold text-slate-900">{internalSummary.warnings} / {internalSummary.optionalMissing}</div>
                    <div className="mt-2 text-xs leading-5 text-slate-500">
                      warnings {internalSummary.warnings}, optional missing {internalSummary.optionalMissing}
                    </div>
                  </div>
                  <div className="rounded-[1.5rem] border border-slate-200 bg-slate-50 px-4 py-4">
                    <div className="text-sm text-slate-500">표시 포인트</div>
                    <div className="mt-2 text-2xl font-semibold text-slate-900">{internalSummary.points}</div>
                    <div className="mt-2 text-xs leading-5 text-slate-500">
                      aspects {internalSummary.aspects}개와 함께 점검 중입니다.
                    </div>
                  </div>
                  <div className="rounded-[1.5rem] border border-slate-200 bg-slate-50 px-4 py-4">
                    <div className="text-sm text-slate-500">저장 소스</div>
                    <div className="mt-2 text-sm font-medium leading-6 text-slate-900">{internalStatusDetail || status}</div>
                  </div>
                </div>

                <div className="mt-4 grid gap-4 lg:grid-cols-3">
                  <div className="rounded-[1.5rem] border border-slate-200 bg-slate-50 px-4 py-4">
                    <div className="text-sm text-slate-500">저장 명단</div>
                    <select value={selectedLeadId} onChange={(e) => loadSavedLead(e.target.value)} className="mt-3 w-full rounded-2xl border border-slate-200 bg-white px-3 py-3">
                      <option value="">저장된 리드 선택</option>
                      {savedLeads.map((lead) => (
                        <option key={lead.id} value={lead.id}>
                          {lead.label}
                        </option>
                      ))}
                    </select>
                  </div>
                  <div className="rounded-[1.5rem] border border-slate-200 bg-slate-50 px-4 py-4">
                    <div className="text-sm text-slate-500">현재 상태</div>
                    <div className="mt-3 text-sm font-medium leading-6">{status}</div>
                  </div>
                  <div className="rounded-[1.5rem] border border-slate-200 bg-slate-50 px-4 py-4">
                    <div className="text-sm text-slate-500">다음 액션</div>
                    <div className="mt-3 text-sm font-medium leading-6">
                      {internalSummary.warnings || internalSummary.optionalMissing
                        ? "Warnings와 optional missing을 먼저 확인한 뒤 차트를 검토하세요."
                        : "행성표와 aspect 표를 빠르게 확인한 뒤 저장 상태만 마무리하면 됩니다."}
                    </div>
                  </div>
                </div>
              </div>

              <div className="rounded-[2rem] border border-slate-200 bg-white/95 p-5 shadow-sm">
                <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
                  <div>
                    <h3 className="text-lg font-semibold">Copy-ready chart text</h3>
                    <div className="mt-1 text-sm text-slate-500">
                      선택한 이름과 생일 기준으로 바로 복붙할 수 있는 텍스트입니다.
                    </div>
                    <div className="mt-2 text-xs text-slate-400">
                      {chart.input.person_name || "이름 없음"} · {chart.input.birth_date} {chart.input.birth_time_local}
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    {markdownCopyMessage && <span className="text-sm text-slate-500">{markdownCopyMessage}</span>}
                    <button
                      type="button"
                      onClick={() => { void handleCopyChartMarkdown(); }}
                      className="rounded-2xl border border-slate-200 bg-white px-4 py-2 text-sm font-medium text-slate-700 transition hover:border-slate-300 hover:text-slate-900"
                    >
                      텍스트 복사
                    </button>
                  </div>
                </div>
                <textarea
                  readOnly
                  value={chartMarkdown}
                  className="mt-4 h-[360px] w-full rounded-[1.5rem] border border-slate-200 bg-slate-50 px-4 py-4 font-mono text-[13px] leading-6 text-slate-700 outline-none"
                />
              </div>

              <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
                <div className="bg-white/95 rounded-3xl shadow-sm p-5 border border-white/60">
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="text-lg font-semibold">Planetary positions</h3>
                    <span className="text-xs px-2 py-1 rounded-full bg-slate-100">bodies</span>
                  </div>
                  <div className="overflow-hidden rounded-2xl border border-slate-200">
                    <table className="w-full text-sm">
                      <thead className="bg-slate-50 text-slate-600">
                        <tr>
                          <th className="text-left px-4 py-3">Body</th>
                          <th className="text-left px-4 py-3">Sign</th>
                          <th className="text-left px-4 py-3">House</th>
                        </tr>
                      </thead>
                      <tbody>
                        {chart.bodies.map((b) => (
                          <tr key={b.id} className="border-t border-slate-100">
                            <td className="px-4 py-3 font-medium">{bodyGlyph[b.id] || "•"} {b.label}</td>
                            <td className="px-4 py-3">{zodiacSymbols[b.sign]} {b.formatted.split(" ")[1]}</td>
                            <td className="px-4 py-3">
                              <div className="flex items-center gap-2">
                                <span>{b.house ? `House ${b.house}` : "-"}</span>
                                {b.retrograde && <span className="rounded-full bg-slate-100 px-2 py-0.5 text-[11px] text-slate-600">Rx</span>}
                              </div>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>

                <div className="bg-white/95 rounded-3xl shadow-sm p-5 border border-white/60">
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="text-lg font-semibold">Points & markers</h3>
                    <span className="text-xs px-2 py-1 rounded-full bg-slate-100">points</span>
                  </div>
                  <div className="space-y-3">
                    {visiblePoints.map((p) => (
                      <div key={p.id} className="rounded-2xl border border-slate-200 px-4 py-3 flex items-center justify-between">
                        <div>
                          <div className="font-medium flex items-center gap-2">
                            <span>{bodyGlyph[p.id] || "•"} {p.label}</span>
                            {chart.availability.soft_missing.includes(p.id) && (
                              <span className="rounded-full bg-amber-50 px-2 py-0.5 text-[11px] text-amber-700">optional missing</span>
                            )}
                          </div>
                          <div className="text-sm text-slate-500">{zodiacSymbols[p.sign]} {p.formatted.split(" ")[1]}</div>
                        </div>
                        <div className="text-sm text-slate-600">{p.house ? `House ${p.house}` : "-"}</div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>

              <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
                <div className="xl:col-span-1 bg-white/95 rounded-3xl shadow-sm p-5 border border-white/60">
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="text-lg font-semibold">House cusps</h3>
                    <span className="text-xs px-2 py-1 rounded-full bg-slate-100">houses</span>
                  </div>
                  <div className="space-y-2 text-sm">
                    {chart.houses.map((h) => (
                      <div key={h.house} className="rounded-2xl border border-slate-200 px-3 py-2 flex items-center justify-between">
                        <span>{h.house}H</span>
                        <span>{zodiacSymbols[h.sign]} {formatDeg(h.degree)}</span>
                      </div>
                    ))}
                  </div>
                </div>

                <div className="xl:col-span-1 bg-white/95 rounded-3xl shadow-sm p-5 border border-white/60">
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="text-lg font-semibold">Major aspects</h3>
                    <span className="text-xs px-2 py-1 rounded-full bg-slate-100">aspects</span>
                  </div>
                  <div className="overflow-hidden rounded-2xl border border-slate-200">
                    <table className="w-full text-sm">
                      <thead className="bg-slate-50 text-slate-600">
                        <tr>
                          <th className="text-left px-3 py-3">A</th>
                          <th className="text-left px-3 py-3">B</th>
                          <th className="text-left px-3 py-3">Type</th>
                          <th className="text-left px-3 py-3">Orb</th>
                        </tr>
                      </thead>
                      <tbody>
                        {chart.aspects.map((a) => (
                          <tr key={a.id} className="border-t border-slate-100">
                            <td className="px-3 py-3">{a.point_a}</td>
                            <td className="px-3 py-3">{a.point_b}</td>
                            <td className="px-3 py-3 capitalize">{a.aspect_type}</td>
                            <td className="px-3 py-3">{a.orb_text}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>

                <div className="xl:col-span-1 bg-white/95 rounded-3xl shadow-sm p-5 border border-white/60">
                  <button
                    type="button"
                    onClick={() => setJsonPanelOpen((prev) => !prev)}
                    className="flex w-full items-center justify-between text-left"
                  >
                    <div>
                      <h3 className="text-lg font-semibold">Raw JSON</h3>
                      <div className="mt-1 text-sm text-slate-500">필요할 때만 여는 디버그용 상세 데이터</div>
                    </div>
                    <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-medium text-slate-600">
                      {jsonPanelOpen ? "접기" : "열기"}
                    </span>
                  </button>
                  {jsonPanelOpen ? (
                    <div className="mt-4">
                      <JsonBlock value={chart} />
                    </div>
                  ) : (
                    <div className="mt-4 rounded-2xl border border-dashed border-slate-200 px-4 py-6 text-sm text-slate-500">
                      운영 검토에서는 위 요약 카드와 표를 먼저 보고, 필요할 때만 JSON을 확인하는 흐름을 권장합니다.
                    </div>
                  )}
                </div>
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
