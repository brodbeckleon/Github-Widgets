import { createCanvas } from "canvas";

export default async function handler(req: any, res: any) {
    // Handle OPTIONS preflight requests
    if (req.method === "OPTIONS") {
        res.setHeader("Access-Control-Allow-Origin", "*");
        res.setHeader("Access-Control-Allow-Methods", "GET, OPTIONS");
        res.status(200).end();
        return;
    }

    const { username = "Leon" } = req.query;
    const canvas = createCanvas(400, 120);
    const ctx = canvas.getContext("2d");

    ctx.fillStyle = "#222";
    ctx.fillRect(0, 0, 400, 120);

    ctx.fillStyle = "#0f0";
    ctx.font = "Helvetica";
    ctx.fillText(`Hello, there!`, 40, 70);

    res.setHeader("Content-Type", "image/png");
    res.setHeader("Access-Control-Allow-Origin", "*");
    res.setHeader("Access-Control-Allow-Methods", "GET, OPTIONS");
    res.setHeader("Cache-Control", "public, max-age=3600");
    const buffer = canvas.toBuffer("image/png");
    res.send(buffer);
}
