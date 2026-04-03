import fs from "fs";
import path from "path";

const ROOT = path.resolve(path.dirname(new URL(import.meta.url).pathname), "..");
const OUT_DIR = path.join(ROOT, "src", "data", "interpretations");

const SIGNS = [
  "aries",
  "taurus",
  "gemini",
  "cancer",
  "leo",
  "virgo",
  "libra",
  "scorpio",
  "sagittarius",
  "capricorn",
  "aquarius",
  "pisces",
];

const HOUSES = Array.from({ length: 12 }, (_, index) => index + 1);

const PLANETS = [
  "sun",
  "moon",
  "mercury",
  "venus",
  "mars",
  "jupiter",
  "saturn",
  "uranus",
  "neptune",
  "pluto",
  "node_north",
  "node_south",
  "chiron",
];

const RULER_PLANETS = [
  "sun",
  "moon",
  "mercury",
  "venus",
  "mars",
  "jupiter",
  "saturn",
  "uranus",
  "neptune",
  "pluto",
];

const HOUSE_POINTS = ["asc", "mc"];

const planetMeta = {
  sun: {
    ko: "태양",
    subject: "삶의 중심이",
    object: "삶의 중심과 정체성",
    keywords: ["정체성", "주도성", "존재감"],
  },
  moon: {
    ko: "달",
    subject: "감정의 반응이",
    object: "감정과 정서 반응",
    keywords: ["감정", "안정", "정서"],
  },
  mercury: {
    ko: "수성",
    subject: "사고와 표현이",
    object: "사고와 표현 방식",
    keywords: ["사고", "표현", "소통"],
  },
  venus: {
    ko: "금성",
    subject: "관계와 가치 판단이",
    object: "관계와 가치, 끌림",
    keywords: ["관계", "가치", "매력"],
  },
  mars: {
    ko: "화성",
    subject: "행동과 추진력이",
    object: "행동과 추진력",
    keywords: ["행동", "추진력", "결단"],
  },
  jupiter: {
    ko: "목성",
    subject: "확장과 믿음이",
    object: "확장과 기회, 믿음",
    keywords: ["확장", "기회", "신념"],
  },
  saturn: {
    ko: "토성",
    subject: "책임감과 기준이",
    object: "구조와 책임, 제한",
    keywords: ["책임", "기준", "구조"],
  },
  uranus: {
    ko: "천왕성",
    subject: "변화 욕구와 독립성이",
    object: "변화와 각성, 탈피",
    keywords: ["변화", "독립", "각성"],
  },
  neptune: {
    ko: "해왕성",
    subject: "감수성과 직관이",
    object: "감수성과 직관, 흐름",
    keywords: ["감수성", "직관", "상상력"],
  },
  pluto: {
    ko: "명왕성",
    subject: "깊은 변화의 힘이",
    object: "깊은 변화와 재생",
    keywords: ["변화", "재생", "집중"],
  },
  node_north: {
    ko: "북노드",
    subject: "성장 방향이",
    object: "성장 방향",
    keywords: ["성장", "확장", "방향"],
  },
  node_south: {
    ko: "남노드",
    subject: "익숙한 패턴이",
    object: "익숙한 패턴",
    keywords: ["습관", "익숙함", "반복"],
  },
  chiron: {
    ko: "카이런",
    subject: "상처를 다루는 방식이",
    object: "상처와 치유",
    keywords: ["상처", "치유", "민감성"],
  },
};

const signMeta = {
  aries: {
    ko: "양",
    keywords: ["주도성", "직진", "속도", "결단"],
    style: "직설적이고 선도적인 방식으로",
    outward: "빠르고 분명한 인상",
    approach: "먼저 움직이며 흐름을 주도하는 편입니다.",
    support: "망설이기보다 직접 시도할 때 감각이 살아납니다.",
  },
  taurus: {
    ko: "황소",
    keywords: ["안정", "지속성", "감각", "현실성"],
    style: "안정적이고 꾸준한 방식으로",
    outward: "차분하고 믿음직한 인상",
    approach: "서두르기보다 익숙한 리듬을 지키는 편입니다.",
    support: "시간을 들여 쌓아 갈수록 힘이 단단해집니다.",
  },
  gemini: {
    ko: "쌍둥이",
    keywords: ["호기심", "소통", "유연성", "기민함"],
    style: "가볍고 유연한 방식으로",
    outward: "경쾌하고 빠른 인상",
    approach: "질문하고 연결하며 상황을 넓게 보는 편입니다.",
    support: "대화를 나누고 정보를 순환시킬 때 흐름이 좋아집니다.",
  },
  cancer: {
    ko: "게",
    keywords: ["보호", "정서", "돌봄", "안정"],
    style: "조심스럽고 보호적인 방식으로",
    outward: "부드럽고 배려 깊은 인상",
    approach: "안전하다고 느껴질 때 비로소 속도를 내는 편입니다.",
    support: "정서적 기반이 갖춰질수록 힘을 자연스럽게 씁니다.",
  },
  leo: {
    ko: "사자",
    keywords: ["표현", "자신감", "창조성", "존재감"],
    style: "당당하고 표현적인 방식으로",
    outward: "밝고 존재감 있는 인상",
    approach: "자신의 색을 분명히 드러내며 움직이는 편입니다.",
    support: "마음을 담아 표현할수록 에너지가 커집니다.",
  },
  virgo: {
    ko: "처녀",
    keywords: ["정교함", "실용성", "분석", "정리"],
    style: "세심하고 실용적인 방식으로",
    outward: "단정하고 정확한 인상",
    approach: "흐름을 정리하고 작은 차이를 살피는 편입니다.",
    support: "구체적으로 개선할수록 안정감이 높아집니다.",
  },
  libra: {
    ko: "천칭",
    keywords: ["균형", "관계", "조화", "감각"],
    style: "균형 있고 세련된 방식으로",
    outward: "부드럽고 조화로운 인상",
    approach: "상대의 반응을 살피며 균형점을 찾는 편입니다.",
    support: "관계의 흐름을 다듬을수록 감각이 살아납니다.",
  },
  scorpio: {
    ko: "전갈",
    keywords: ["집중", "깊이", "통찰", "강도"],
    style: "깊고 강하게 몰입하는 방식으로",
    outward: "조용하지만 밀도 있는 인상",
    approach: "겉보다 본질을 읽으며 깊게 파고드는 편입니다.",
    support: "표면을 넘어서 핵심에 닿을 때 힘이 커집니다.",
  },
  sagittarius: {
    ko: "사수",
    keywords: ["확장", "비전", "자유", "탐색"],
    style: "넓고 개방적인 방식으로",
    outward: "자유롭고 시원한 인상",
    approach: "큰 그림을 보며 앞으로 뻗어 가는 편입니다.",
    support: "배우고 움직일수록 시야와 에너지가 함께 커집니다.",
  },
  capricorn: {
    ko: "염소",
    keywords: ["책임감", "현실성", "구조", "성취"],
    style: "현실적이고 구조적인 방식으로",
    outward: "차분하고 신뢰를 주는 인상",
    approach: "목표를 세우고 단계적으로 쌓아 가는 편입니다.",
    support: "오래 가는 결과를 만들 때 자신감이 안정됩니다.",
  },
  aquarius: {
    ko: "물병",
    keywords: ["독립성", "새로움", "객관성", "개혁"],
    style: "독립적이고 새로운 방식으로",
    outward: "담백하고 독특한 인상",
    approach: "익숙한 틀을 한 번 더 의심해 보는 편입니다.",
    support: "거리감을 확보할수록 더 선명한 판단이 나옵니다.",
  },
  pisces: {
    ko: "물고기",
    keywords: ["공감", "직관", "유연성", "상상력"],
    style: "유연하고 감응적인 방식으로",
    outward: "부드럽고 열린 인상",
    approach: "분위기와 흐름을 읽으며 자연스럽게 반응하는 편입니다.",
    support: "억지로 밀어붙이기보다 감각을 믿을 때 길이 열립니다.",
  },
};

const houseMeta = {
  1: {
    keywords: ["자기표현", "존재감", "주도성", "시작"],
    area: "자기표현과 존재감의 영역",
    support: "스스로 나서고 직접 움직일 때 에너지가 가장 잘 살아납니다.",
  },
  2: {
    keywords: ["가치", "자원", "안정", "현실감"],
    area: "가치와 자원을 다루는 영역",
    support: "무엇을 지키고 쌓을지 분명해질수록 안정감이 커집니다.",
  },
  3: {
    keywords: ["소통", "학습", "일상", "연결"],
    area: "소통과 학습, 일상의 영역",
    support: "가볍게 주고받고 자주 움직일수록 흐름이 좋아집니다.",
  },
  4: {
    keywords: ["가정", "내면", "기반", "안정"],
    area: "가정과 내적 기반의 영역",
    support: "밖의 성과보다 안쪽의 안정이 먼저 갖춰질 때 힘이 납니다.",
  },
  5: {
    keywords: ["창조성", "즐거움", "표현", "자기색"],
    area: "창조성과 즐거움의 영역",
    support: "재미와 몰입이 살아날수록 자기다움도 함께 선명해집니다.",
  },
  6: {
    keywords: ["일상관리", "실무", "건강", "정비"],
    area: "일상 관리와 실무의 영역",
    support: "작은 루틴을 정돈할수록 전체 흐름이 안정됩니다.",
  },
  7: {
    keywords: ["관계", "협력", "조율", "거울"],
    area: "관계와 협력의 영역",
    support: "타인과의 조율 속에서 자신에게 필요한 기준도 선명해집니다.",
  },
  8: {
    keywords: ["심층", "공유", "변화", "회복"],
    area: "깊은 교류와 변화의 영역",
    support: "겉으로 넘기지 않고 깊이 다룰수록 전환의 힘이 생깁니다.",
  },
  9: {
    keywords: ["확장", "철학", "배움", "시야"],
    area: "시야 확장과 배움의 영역",
    support: "멀리 보고 새로운 관점을 받아들일수록 길이 넓어집니다.",
  },
  10: {
    keywords: ["커리어", "목표", "책임", "성과"],
    area: "사회적 역할과 목표의 영역",
    support: "밖에서 맡은 책임을 다룰수록 방향감이 분명해집니다.",
  },
  11: {
    keywords: ["네트워크", "비전", "협업", "확장"],
    area: "네트워크와 미래 비전의 영역",
    support: "같은 방향을 보는 사람들과 연결될수록 가능성이 커집니다.",
  },
  12: {
    keywords: ["내면", "회복", "정리", "무의식"],
    area: "내면 정리와 회복의 영역",
    support: "혼자 정리하고 쉬는 시간이 있어야 흐름이 다시 맑아집니다.",
  },
};

const pointMeta = {
  asc: {
    ko: "ASC",
    label: "ASC 룰러",
    direction: "삶의 방향",
    area: "자기 전개와 삶의 방향",
    keywords: ["방향성", "자기전개"],
  },
  mc: {
    ko: "MC",
    label: "MC 룰러",
    direction: "사회적 목표",
    area: "일과 사회적 역할",
    keywords: ["사회적목표", "커리어"],
  },
};

function csvEscape(value) {
  const text = String(value ?? "");
  if (text.includes(",") || text.includes('"') || text.includes("\n")) {
    return `"${text.replace(/"/g, '""')}"`;
  }
  return text;
}

function writeCsv(filePath, header, rows) {
  const lines = [header.join(",")];
  rows.forEach((row) => {
    lines.push(header.map((column) => csvEscape(row[column])).join(","));
  });
  fs.writeFileSync(filePath, `${lines.join("\n")}\n`, "utf8");
}

function uniqueKeywords(...groups) {
  const list = [];
  groups.flat().forEach((item) => {
    if (item && !list.includes(item)) list.push(item);
  });
  return list.slice(0, 4);
}

function formatKeywords(list) {
  return uniqueKeywords(list).join("|");
}

function subjectParticle(word) {
  const lastChar = word[word.length - 1];
  const code = lastChar.charCodeAt(0);
  if (code < 0xac00 || code > 0xd7a3) return `${word}이`;
  const hasBatchim = (code - 0xac00) % 28 !== 0;
  return `${word}${hasBatchim ? "이" : "가"}`;
}

function assertShort(text) {
  if (!text.trim().endsWith(".")) {
    throw new Error(`short must end with a period: ${text}`);
  }
  const sentenceCount = text.split(".").filter(Boolean).length;
  if (sentenceCount !== 1) {
    throw new Error(`short must be one sentence: ${text}`);
  }
}

function assertSummary(text) {
  const sentenceCount = text.split(".").filter(Boolean).length;
  if (sentenceCount < 1 || sentenceCount > 2) {
    throw new Error(`summary must be 1-2 sentences: ${text}`);
  }
}

function signTitle(sign) {
  return `${signMeta[sign].ko}자리`;
}

function buildPlanetInSignRows() {
  const rows = [];
  PLANETS.forEach((planet) => {
    SIGNS.forEach((sign) => {
      const p = planetMeta[planet];
      const s = signMeta[sign];
      const key = `${planet}_${sign}`;
      const short = `${p.subject} ${s.style} 드러납니다.`;
      const summary = `${subjectParticle(p.ko)} ${signTitle(sign)}에 있으면 ${p.object}은 ${s.style} 표현됩니다. ${s.support}`;
      rows.push({
        category: "planet_in_sign",
        planet,
        sign,
        key,
        title: `${p.ko} in ${signTitle(sign)}`,
        keywords: formatKeywords([...p.keywords, ...s.keywords]),
        short,
        summary,
      });
    });
  });
  return rows;
}

function buildPlanetInHouseRows() {
  const rows = [];
  PLANETS.forEach((planet) => {
    HOUSES.forEach((house) => {
      const p = planetMeta[planet];
      const h = houseMeta[house];
      const key = `${planet}_house_${house}`;
      const short = `${p.subject} ${h.area}에서 두드러집니다.`;
      const summary = `${subjectParticle(p.ko)} ${house}하우스에 있으면 ${p.object}은 ${h.area}에서 강하게 드러납니다. ${h.support}`;
      rows.push({
        category: "planet_in_house",
        planet,
        house,
        key,
        title: `${p.ko} in ${house}하우스`,
        keywords: formatKeywords([...p.keywords, ...h.keywords]),
        short,
        summary,
      });
    });
  });
  return rows;
}

function buildAscRows() {
  return SIGNS.map((sign) => {
    const s = signMeta[sign];
    const short = `첫인상과 외부 태도가 ${s.style} 드러나는 편입니다.`;
    const summary = `어센던트가 ${signTitle(sign)}에 있으면 타인에게 ${s.outward}을 주기 쉽습니다. 새로운 상황에서는 ${s.approach}`;
    return {
      category: "asc_in_sign",
      point: "asc",
      sign,
      key: `asc_${sign}`,
      title: `ASC in ${signTitle(sign)}`,
      keywords: formatKeywords(["첫인상", ...s.keywords]),
      short,
      summary,
    };
  });
}

function buildRulerRows() {
  const rows = [];
  HOUSE_POINTS.forEach((housePoint) => {
    const point = pointMeta[housePoint];
    RULER_PLANETS.forEach((ruler) => {
      const planet = planetMeta[ruler];
      SIGNS.forEach((sign) => {
        const s = signMeta[sign];
        rows.push({
          category: "ruler_placement",
          house_point: housePoint,
          ruler,
          placement_type: "sign",
          placement_value: sign,
          key: `${housePoint}_ruler_${ruler}_${sign}`,
          title: `${point.label} ${planet.ko} in ${signTitle(sign)}`,
          keywords: formatKeywords([...point.keywords, ...planet.keywords, ...s.keywords]),
          short: `${point.direction}이 ${planet.object}을 통해 ${s.style} 전개됩니다.`,
          summary: `${point.ko} 룰러인 ${subjectParticle(planet.ko)} ${signTitle(sign)}에 있으면 ${point.area}은 ${planet.object}을 통해 ${s.style} 전개됩니다. ${s.support}`,
        });
      });
      HOUSES.forEach((house) => {
        const h = houseMeta[house];
        rows.push({
          category: "ruler_placement",
          house_point: housePoint,
          ruler,
          placement_type: "house",
          placement_value: house,
          key: `${housePoint}_ruler_${ruler}_house_${house}`,
          title: `${point.label} ${planet.ko} in ${house}하우스`,
          keywords: formatKeywords([...point.keywords, ...planet.keywords, ...h.keywords]),
          short: `${point.direction}이 ${h.area}과 강하게 연결됩니다.`,
          summary: `${point.ko} 룰러인 ${planet.ko}이 ${house}하우스에 있으면 ${point.area}은 ${h.area}과 직접 연결됩니다. ${h.support}`,
        });
      });
    });
  });
  return rows;
}

function buildNodeChironRows() {
  const rows = [];
  [
    { point: "node_north", typeLabel: "성장 방향", caution: "낯설더라도 이 방향으로 움직일수록 성장이 커집니다." },
    { point: "node_south", typeLabel: "익숙한 패턴", caution: "익숙해서 편하지만 여기에만 머물면 시야가 좁아질 수 있습니다." },
    { point: "chiron", typeLabel: "상처와 치유의 감각", caution: "이 민감함을 외면하지 않고 다루는 과정이 회복의 핵심이 됩니다." },
  ].forEach(({ point, typeLabel, caution }) => {
    const meta = planetMeta[point];
    SIGNS.forEach((sign) => {
      const s = signMeta[sign];
      rows.push({
        category: "node_chiron",
        point,
        placement_type: "sign",
        placement_value: sign,
        key: `${point}_${sign}`,
        title: `${meta.ko} in ${signTitle(sign)}`,
        keywords: formatKeywords([...meta.keywords, ...s.keywords]),
        short: `${typeLabel}이 ${s.style} 드러납니다.`,
        summary: `${subjectParticle(meta.ko)} ${signTitle(sign)}에 있으면 ${typeLabel}은 ${s.style} 나타납니다. ${caution}`,
      });
    });
    HOUSES.forEach((house) => {
      const h = houseMeta[house];
      rows.push({
        category: "node_chiron",
        point,
        placement_type: "house",
        placement_value: house,
        key: `${point}_house_${house}`,
        title: `${meta.ko} in ${house}하우스`,
        keywords: formatKeywords([...meta.keywords, ...h.keywords]),
        short: `${typeLabel}이 ${h.area}에서 드러납니다.`,
        summary: `${subjectParticle(meta.ko)} ${house}하우스에 있으면 ${typeLabel}은 ${h.area}에서 반복되거나 성장 과제로 떠오릅니다. ${caution}`,
      });
    });
  });
  return rows;
}

function validateRows(rows, expectedCount) {
  const keys = new Set();
  rows.forEach((row) => {
    if (keys.has(row.key)) {
      throw new Error(`duplicated key: ${row.key}`);
    }
    keys.add(row.key);

    const keywordCount = row.keywords.split("|").filter(Boolean).length;
    if (keywordCount < 3 || keywordCount > 4) {
      throw new Error(`keywords count must be 3~4: ${row.key}`);
    }
    assertShort(row.short);
    assertSummary(row.summary);
  });
  if (rows.length !== expectedCount) {
    throw new Error(`expected ${expectedCount} rows, got ${rows.length}`);
  }
}

function nestRows(allRows) {
  const out = {
    meta: {
      generated_at: new Date().toISOString(),
      categories: {},
    },
    planet_in_sign: {},
    planet_in_house: {},
    asc_in_sign: {},
    ruler_placement: {},
    node_chiron: {},
  };

  allRows.planet_in_sign.forEach((row) => {
    out.planet_in_sign[row.planet] ??= {};
    out.planet_in_sign[row.planet][row.sign] = row;
  });

  allRows.planet_in_house.forEach((row) => {
    out.planet_in_house[row.planet] ??= {};
    out.planet_in_house[row.planet][String(row.house)] = row;
  });

  allRows.asc_in_sign.forEach((row) => {
    out.asc_in_sign[row.sign] = row;
  });

  allRows.ruler_placement.forEach((row) => {
    out.ruler_placement[row.house_point] ??= {};
    out.ruler_placement[row.house_point][row.ruler] ??= { sign: {}, house: {} };
    out.ruler_placement[row.house_point][row.ruler][row.placement_type][String(row.placement_value)] = row;
  });

  allRows.node_chiron.forEach((row) => {
    out.node_chiron[row.point] ??= { sign: {}, house: {} };
    out.node_chiron[row.point][row.placement_type][String(row.placement_value)] = row;
  });

  Object.entries(allRows).forEach(([category, rows]) => {
    out.meta.categories[category] = rows.length;
  });

  return out;
}

fs.mkdirSync(OUT_DIR, { recursive: true });

const allRows = {
  planet_in_sign: buildPlanetInSignRows(),
  planet_in_house: buildPlanetInHouseRows(),
  asc_in_sign: buildAscRows(),
  ruler_placement: buildRulerRows(),
  node_chiron: buildNodeChironRows(),
};

validateRows(allRows.planet_in_sign, PLANETS.length * SIGNS.length);
validateRows(allRows.planet_in_house, PLANETS.length * HOUSES.length);
validateRows(allRows.asc_in_sign, SIGNS.length);
validateRows(allRows.ruler_placement, HOUSE_POINTS.length * RULER_PLANETS.length * (SIGNS.length + HOUSES.length));
validateRows(allRows.node_chiron, 3 * (SIGNS.length + HOUSES.length));

writeCsv(
  path.join(OUT_DIR, "planet_in_sign.csv"),
  ["category", "planet", "sign", "key", "title", "keywords", "short", "summary"],
  allRows.planet_in_sign,
);
writeCsv(
  path.join(OUT_DIR, "planet_in_house.csv"),
  ["category", "planet", "house", "key", "title", "keywords", "short", "summary"],
  allRows.planet_in_house,
);
writeCsv(
  path.join(OUT_DIR, "asc_in_sign.csv"),
  ["category", "point", "sign", "key", "title", "keywords", "short", "summary"],
  allRows.asc_in_sign,
);
writeCsv(
  path.join(OUT_DIR, "ruler_placement.csv"),
  ["category", "house_point", "ruler", "placement_type", "placement_value", "key", "title", "keywords", "short", "summary"],
  allRows.ruler_placement,
);
writeCsv(
  path.join(OUT_DIR, "node_chiron.csv"),
  ["category", "point", "placement_type", "placement_value", "key", "title", "keywords", "short", "summary"],
  allRows.node_chiron,
);

fs.writeFileSync(path.join(OUT_DIR, "interpretations.json"), `${JSON.stringify(nestRows(allRows), null, 2)}\n`, "utf8");
fs.writeFileSync(
  path.join(OUT_DIR, "manifest.json"),
  `${JSON.stringify(
    {
      generated_at: new Date().toISOString(),
      batches: {
        "1": ["sun", "moon"],
        "2": ["mercury", "venus", "mars"],
        "3": ["jupiter", "saturn"],
        "4": ["uranus", "neptune", "pluto"],
        "5": ["node_north", "node_south", "chiron"],
      },
      totals: {
        planet_in_sign: allRows.planet_in_sign.length,
        planet_in_house: allRows.planet_in_house.length,
        asc_in_sign: allRows.asc_in_sign.length,
        ruler_placement: allRows.ruler_placement.length,
        node_chiron: allRows.node_chiron.length,
      },
    },
    null,
    2,
  )}\n`,
  "utf8",
);

console.log(`Generated astrology interpretation datasets in ${OUT_DIR}`);
