// Renders the stats card with demo data into preview/ (run: npx tsx scripts/preview-stats.ts)
import * as fs from "fs";
import { demoStats } from "../lib/github";
import { renderStatsCard } from "../lib/statsCard";

fs.mkdirSync("preview", { recursive: true });
for (const theme of ["dark", "light"]) {
    fs.writeFileSync(`preview/stats_${theme}.svg`, renderStatsCard(demoStats(), theme));
}
console.log("wrote preview/stats_dark.svg and preview/stats_light.svg");
