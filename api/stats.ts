import { fetchStats, demoStats } from "../lib/github";
import { renderStatsCard, renderErrorCard } from "../lib/statsCard";
import type { VercelRequest, VercelResponse } from "@vercel/node";

// GET /api/stats?theme=dark|light&hide=css,jupyter%20notebook[&demo=1]
// Env: GITHUB_TOKEN (required), GITHUB_USER (default brodbeckleon), INCLUDE_PRIVATE=true (optional)
export default async function handler(req: VercelRequest, res: VercelResponse) {
    res.setHeader("Access-Control-Allow-Origin", "*");
    res.setHeader("Access-Control-Allow-Methods", "GET, OPTIONS");
    if (req.method === "OPTIONS") {
        res.status(200).end();
        return;
    }

    const { theme = "light", hide = "", demo } = req.query;
    const login = process.env.GITHUB_USER || "brodbeckleon";
    const includePrivate = process.env.INCLUDE_PRIVATE === "true";
    const useDemo = demo === "1" || demo === "true";

    res.setHeader("Content-Type", "image/svg+xml");
    try {
        const stats = useDemo ? demoStats() : await fetchStats(login, String(hide).split(","), includePrivate);
        // Fresh for 6 h at the edge, then served stale while revalidating.
        res.setHeader("Cache-Control", "public, max-age=3600, s-maxage=21600, stale-while-revalidate=86400");
        res.send(renderStatsCard(stats, String(theme)));
    } catch (err: any) {
        console.error(err);
        res.setHeader("Cache-Control", "public, max-age=300");
        res.send(renderErrorCard(err?.message ?? "unknown error", String(theme)));
    }
}
