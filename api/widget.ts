export default function handler(req: any, res: any) {
    // Handle OPTIONS preflight requests
    if (req.method === "OPTIONS") {
        res.setHeader("Access-Control-Allow-Origin", "*");
        res.setHeader("Access-Control-Allow-Methods", "GET, OPTIONS");
        res.status(200).end();
        return;
    }

    const { username = "Leon" } = req.query;

    // Create SVG string
    const svg = `
    <svg xmlns="http://www.w3.org/2000/svg" width="400" height="120">
      <rect width="400" height="120" fill="#222" />
      <text x="40" y="70" font-family="Helvetica" font-size="24" fill="#0f0">
        Hello, ${username}!
      </text>
    </svg>
  `;

    // Send response
    res.setHeader("Content-Type", "image/svg+xml");
    res.setHeader("Access-Control-Allow-Origin", "*");
    res.setHeader("Access-Control-Allow-Methods", "GET, OPTIONS");
    res.setHeader("Cache-Control", "public, max-age=3600");
    res.send(svg);
}
