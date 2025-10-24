import { createCanvas } from "canvas";

export default function handler(req, res) {
    const { username = "Anonymous" } = req.query;
    const canvas = createCanvas(400, 120);
    const ctx = canvas.getContext("2d");

    ctx.fillStyle = "#222";
    ctx.fillRect(0, 0, 400, 120);

    ctx.fillStyle = "#0f0";
    ctx.font = "bold 24px Sans";
    ctx.fillText(`Hello, ${username}!`, 40, 70);

    res.setHeader("Content-Type", "image/png");
    canvas.createPNGStream(res);
    //canvas.pngStream().pipe(res);
}
