import * as fs from "fs";
import * as path from "path";

export default function handler(req: any, res: any) {
    if (req.method === "OPTIONS") {
        res.setHeader("Access-Control-Allow-Origin", "*");
        res.setHeader("Access-Control-Allow-Methods", "GET, OPTIONS");
        res.status(200).end();
        return;
    }

    //const { username = "Léon" } = req.query;
    const { theme = "light" } = req.query;
    const { bruh = "" } = req.query;
    let filePath: string;
    if ( theme === "dark" ) {
        filePath = path.join(process.cwd(), "resources/svg", "test_dark.svg");
    } else if ( theme === "light" ) {
        filePath = path.join(process.cwd(), "resources/svg", "test_light.svg");
    } else {
        filePath = path.join(process.cwd(), "resources/svg", "test_light.svg");
    }
    const svg = fs.readFileSync(filePath, "utf8");

    res.setHeader("Content-Type", "image/svg+xml");
    res.setHeader("Access-Control-Allow-Origin", "*");
    res.setHeader("Access-Control-Allow-Methods", "GET, OPTIONS");
    res.setHeader("Cache-Control", "public, max-age=3600");
    res.send(svg);

    if (bruh == 'really?') {
        console.log('Why are you doing this?');
    }
}