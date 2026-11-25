# Github-Widgets

Animated SVG widgets for a GitHub profile README, served as Vercel Serverless Functions from `api/`.

## Endpoints

| Endpoint      | What it returns                                                              | Query parameters        |
|---------------|------------------------------------------------------------------------------|-------------------------|
| `/api/widget` | The hand-drawn signature (`resources/svg/test_*.svg`)                        | `theme`                 |
| `/api/stats`  | Profile stats card: contributions per week, totals, streak and top languages | `theme`, `hide`, `demo` |
| `/api/train`  | Looping pixel-art banner: Series 0 Shinkansen on a viaduct below Mt Fuji (`resources/svg/train_*.svg`) | `theme`                 |

Every endpoint responds with `Content-Type: image/svg+xml`.

### Query parameters

- `theme`: `dark` or `light`, default `light`. Widget and stats card: darkred on `#0d1117` / blue on `#ffffff`.
  Train banner: moonlit night / dusk.
- `hide`: languages to leave out of the top languages, comma-separated and case-insensitive,
  e.g. `hide=css,jupyter%20notebook`. Applies to `/api/stats` only.
- `demo`: `demo=1` renders the stats card with sample data and doesn't call GitHub. Useful for checking the layout.

If `/api/stats` can't load data (no token, bad token, GitHub API error), it returns an error card with
status 200 and a 5-minute cache instead of a 500. The image in your profile then shows the reason
instead of a broken icon.

## Environment variables

| Variable          | Required | Default        | Purpose                                                                                    |
|-------------------|----------|----------------|--------------------------------------------------------------------------------------------|
| `GITHUB_TOKEN`    | yes      | none           | Token for the GitHub GraphQL API (classic PAT with `read:user`, or fine-grained read-only) |
| `GITHUB_USER`     | no       | `brodbeckleon` | Account whose stats are shown                                                              |
| `INCLUDE_PRIVATE` | no       | `false`        | `true` counts private repos (stars, languages) and private contributions. The token needs access to private repos (`repo` scope) |

For local development, put them in `.env.local`. That file is gitignored: never commit it.
On Vercel, set them under Project → Settings → Environment Variables.

## Embedding in your profile

`<picture>` picks the variant that matches the viewer's GitHub theme:

```html
<picture>
  <source media="(prefers-color-scheme: dark)" srcset="https://<your-deployment>.vercel.app/api/stats?theme=dark&hide=css">
  <img alt="GitHub stats" src="https://<your-deployment>.vercel.app/api/stats?theme=light&hide=css">
</picture>

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="https://<your-deployment>.vercel.app/api/train?theme=dark">
  <img alt="Pixel train" src="https://<your-deployment>.vercel.app/api/train?theme=light">
</picture>
```

GitHub caches images through its camo proxy. The stats card is cached for 6 hours at the edge and then
revalidated in the background.

## Development

```sh
npm install
npm run typecheck   # tsc --noEmit
npm run preview     # writes preview/stats_dark.svg and preview/stats_light.svg from demo data
npm run train       # regenerates resources/svg/train_*.svg (needs python3, no extra packages)
npx vercel dev      # serves api/ locally on http://localhost:3000 (needs a Vercel login)
```
