import type { Stats } from "./github";

// Same look as the hand-drawn widget: strokes draw themselves in, darkred on dark, blue on light.
type Theme = { bg: string; fg: string; muted: string; accent: string; track: string };

const THEMES: Record<string, Theme> = {
    dark: { bg: "#0d1117", fg: "#e6edf3", muted: "#8b949e", accent: "darkred", track: "#21262d" },
    light: { bg: "#ffffff", fg: "#1f2328", muted: "#656d76", accent: "blue", track: "#eaeef2" },
};

export function getTheme(name: string): Theme {
    return THEMES[name] ?? THEMES.light;
}

const W = 840;
const H = 340;
const FONT = "'JetBrains Mono', ui-monospace, SFMono-Regular, Menlo, Consolas, monospace";

const esc = (s: string) =>
    s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");

const fmt = (n: number) =>
    n >= 10000 ? `${Math.round(n / 1000)}k` : n >= 1000 ? `${(n / 1000).toFixed(1)}k` : `${n}`;

function frame(t: Theme, body: string): string {
    return `<svg xmlns="http://www.w3.org/2000/svg" width="${W}" height="${H}" viewBox="0 0 ${W} ${H}" font-family="${FONT}">
<style>
  .draw { fill: none; stroke: ${t.accent}; stroke-linecap: round; stroke-linejoin: round;
          stroke-dasharray: 1; stroke-dashoffset: 1; animation: draw 1.6s ease forwards; animation-delay: var(--d, 0s); }
  .fade { opacity: 0; animation: fade .7s ease forwards; animation-delay: var(--d, 0s); }
  .rough { filter: url(#rough); }
  @keyframes draw { to { stroke-dashoffset: 0; } }
  @keyframes fade { to { opacity: 1; } }
  @media (prefers-reduced-motion: reduce) {
    .draw { animation: none; stroke-dashoffset: 0; }
    .fade { animation: none; opacity: 1; }
  }
</style>
<defs>
  <filter id="rough" filterUnits="userSpaceOnUse" x="0" y="0" width="${W}" height="${H}">
    <feTurbulence type="fractalNoise" baseFrequency="0.035" numOctaves="2" seed="4" result="noise"/>
    <feDisplacementMap in="SourceGraphic" in2="noise" scale="3"/>
  </filter>
</defs>
<rect width="100%" height="100%" fill="${t.bg}"/>
${body}
</svg>`;
}

export function renderStatsCard(s: Stats, themeName: string): string {
    const t = getTheme(themeName);
    const parts: string[] = [];

    // Header
    parts.push(`<text class="fade" x="32" y="44" font-size="20" font-weight="700" fill="${t.fg}">${esc(s.login)}</text>`);
    parts.push(`<path class="draw rough" pathLength="1" stroke-width="3" d="M32 56 C 90 52, 150 60, ${32 + s.login.length * 12.5} 54"/>`);
    parts.push(`<text class="fade" style="--d:.3s" x="${W - 32}" y="44" font-size="13" text-anchor="end" fill="${t.muted}">` +
        `<tspan fill="${t.fg}" font-weight="700">${fmt(s.totalContributions)}</tspan> contributions in the last year</text>`);

    // Contribution line (weekly sums)
    const x0 = 32, x1 = W - 32, yTop = 82, yBase = 168;
    const weekly = s.weekly.length ? s.weekly : [0];
    const max = Math.max(1, ...weekly);
    const step = (x1 - x0) / Math.max(1, weekly.length - 1);
    const pts = weekly.map((v, i) => [x0 + i * step, yBase - (v / max) * (yBase - yTop)]);
    const line = pts.map((p, i) => `${i ? "L" : "M"}${p[0].toFixed(1)} ${p[1].toFixed(1)}`).join(" ");
    const area = `${line} L${x1} ${yBase} L${x0} ${yBase} Z`;
    // Brand-new account (all zeros): max is clamped to 1, so fall back to the last point.
    const peak = pts[weekly.indexOf(max)] ?? pts[pts.length - 1];

    parts.push(`<path class="draw rough" pathLength="1" stroke="${t.track}" stroke-width="2" style="stroke:${t.track};--d:.2s" d="M${x0} ${yBase} L${x1} ${yBase}"/>`);
    parts.push(`<path class="fade" style="--d:1.4s" fill="${t.accent}" fill-opacity=".12" d="${area}"/>`);
    parts.push(`<path class="draw rough" pathLength="1" stroke-width="2.5" style="--d:.4s;animation-duration:2.4s" d="${line}"/>`);
    parts.push(`<g class="fade" style="--d:2.4s">
  <circle cx="${peak[0].toFixed(1)}" cy="${peak[1].toFixed(1)}" r="4.5" fill="${t.bg}" stroke="${t.accent}" stroke-width="2.5"/>
  <text x="${peak[0].toFixed(1)}" y="${(peak[1] - 11).toFixed(1)}" font-size="11" text-anchor="middle" fill="${t.muted}">peak ${Math.max(...weekly)}/week</text>
</g>`);
    parts.push(`<text class="fade" style="--d:.6s" x="${x0}" y="${yBase + 18}" font-size="11" fill="${t.muted}">12 months ago</text>`);
    parts.push(`<text class="fade" style="--d:.6s" x="${x1}" y="${yBase + 18}" font-size="11" text-anchor="end" fill="${t.muted}">now</text>`);

    // Numbers grid (3 x 2)
    const cells: [string, string][] = [
        [fmt(s.commits), "commits"],
        [fmt(s.prs), "pull requests"],
        [fmt(s.issues), "issues"],
        [fmt(s.stars), "stars earned"],
        [fmt(s.contributedTo), "repos contributed"],
        [`${s.currentStreak}d`, `streak · best ${s.longestStreak}d`],
    ];
    cells.forEach(([value, label], i) => {
        const cx = 32 + (i % 3) * 132;
        const cy = 236 + Math.floor(i / 3) * 56;
        const d = (0.9 + i * 0.12).toFixed(2);
        parts.push(`<g class="fade" style="--d:${d}s">
  <text x="${cx}" y="${cy}" font-size="22" font-weight="700" fill="${t.fg}">${esc(value)}</text>
  <text x="${cx}" y="${cy + 17}" font-size="11" fill="${t.muted}">${esc(label)}</text>
</g>`);
    });

    // Vertical divider
    parts.push(`<path class="draw rough" pathLength="1" stroke-width="2" style="stroke:${t.track};--d:.8s" d="M434 212 L436 300"/>`);

    // Languages
    const lx = 466, barX = 580, barMax = W - 32 - 52 - barX;
    parts.push(`<text class="fade" style="--d:1s" x="${lx}" y="216" font-size="11" fill="${t.muted}">top languages</text>`);
    const topPct = Math.max(1, ...s.languages.map(l => l.percent));
    s.languages.forEach((l, i) => {
        const y = 240 + i * 17;
        const len = Math.max(4, (l.percent / topPct) * barMax);
        const d = (1.1 + i * 0.15).toFixed(2);
        parts.push(`<text class="fade" style="--d:${d}s" x="${lx}" y="${y + 4}" font-size="12" fill="${t.fg}">${esc(l.name)}</text>`);
        parts.push(`<path class="draw" pathLength="1" stroke-width="7" style="stroke:${t.track};--d:${d}s" d="M${barX} ${y} L${barX + barMax} ${y}"/>`);
        parts.push(`<path class="draw" pathLength="1" stroke-width="7" style="--d:${d}s" d="M${barX} ${y} L${(barX + len).toFixed(1)} ${y}"/>`);
        parts.push(`<text class="fade" style="--d:${d}s" x="${W - 32}" y="${y + 4}" font-size="11" text-anchor="end" fill="${t.muted}">${l.percent.toFixed(1)}%</text>`);
    });

    return frame(t, parts.join("\n"));
}

export function renderErrorCard(message: string, themeName: string): string {
    const t = getTheme(themeName);
    return frame(t, `<text x="32" y="60" font-size="16" font-weight="700" fill="${t.fg}">stats are taking a break</text>
<path class="draw rough" pathLength="1" stroke-width="3" d="M32 72 C 120 68, 200 76, 290 70"/>
<text x="32" y="104" font-size="12" fill="${t.muted}">${esc(message)}</text>`);
}
