// Fetches profile stats from the GitHub GraphQL API.
// Needs a token in the GITHUB_TOKEN env var (classic PAT with read:user, or fine-grained with read access).

export type Language = { name: string; percent: number };

export type Stats = {
    login: string;
    totalContributions: number;
    commits: number;
    prs: number;
    issues: number;
    stars: number;
    contributedTo: number;
    currentStreak: number;
    longestStreak: number;
    weekly: number[];
    languages: Language[];
};

const QUERY = `
query($login: String!) {
  user(login: $login) {
    login
    pullRequests { totalCount }
    issues { totalCount }
    repositoriesContributedTo(contributionTypes: [COMMIT, PULL_REQUEST, ISSUE, REPOSITORY]) { totalCount }
    contributionsCollection {
      totalCommitContributions
      restrictedContributionsCount
      contributionCalendar {
        totalContributions
        weeks { contributionDays { contributionCount date } }
      }
    }
    repositories(first: 100, ownerAffiliations: OWNER, isFork: false, orderBy: {field: PUSHED_AT, direction: DESC}) {
      nodes {
        isPrivate
        stargazerCount
        languages(first: 10, orderBy: {field: SIZE, direction: DESC}) {
          edges { size node { name } }
        }
      }
    }
  }
}`;

export async function fetchStats(login: string, hide: string[], includePrivate: boolean): Promise<Stats> {
    const token = process.env.GITHUB_TOKEN;
    if (!token) throw new Error("GITHUB_TOKEN is not set");

    const res = await fetch("https://api.github.com/graphql", {
        method: "POST",
        headers: {
            Authorization: `bearer ${token}`,
            "Content-Type": "application/json",
            "User-Agent": "github-widgets",
        },
        body: JSON.stringify({ query: QUERY, variables: { login } }),
    });
    if (!res.ok) throw new Error(`GitHub API ${res.status}`);

    const json: any = await res.json();
    if (json.errors?.length) throw new Error(json.errors[0].message);
    const u = json.data?.user;
    if (!u) throw new Error(`User ${login} not found`);

    const cc = u.contributionsCollection;
    const days: { contributionCount: number; date: string }[] =
        cc.contributionCalendar.weeks.flatMap((w: any) => w.contributionDays);
    const weekly: number[] = cc.contributionCalendar.weeks.map((w: any) =>
        w.contributionDays.reduce((s: number, d: any) => s + d.contributionCount, 0));

    const repos = (u.repositories.nodes as any[]).filter(r => includePrivate || !r.isPrivate);
    const hidden = new Set(hide.map(h => h.trim().toLowerCase()).filter(Boolean));
    const sizes = new Map<string, number>();
    for (const r of repos) {
        for (const e of r.languages.edges) {
            const name: string = e.node.name;
            if (hidden.has(name.toLowerCase())) continue;
            sizes.set(name, (sizes.get(name) ?? 0) + e.size);
        }
    }

    return {
        login: u.login,
        totalContributions: cc.contributionCalendar.totalContributions,
        // restrictedContributionsCount = private contributions; only count them when private data is opted in.
        commits: cc.totalCommitContributions + (includePrivate ? cc.restrictedContributionsCount : 0),
        prs: u.pullRequests.totalCount,
        issues: u.issues.totalCount,
        stars: repos.reduce((s, r) => s + r.stargazerCount, 0),
        contributedTo: u.repositoriesContributedTo.totalCount,
        ...streaks(days),
        weekly,
        languages: topLanguages(sizes, 5),
    };
}

function topLanguages(sizes: Map<string, number>, n: number): Language[] {
    const total = [...sizes.values()].reduce((a, b) => a + b, 0) || 1;
    return [...sizes.entries()]
        .sort((a, b) => b[1] - a[1])
        .slice(0, n)
        .map(([name, size]) => ({ name, percent: (size / total) * 100 }));
}

function streaks(days: { contributionCount: number; date: string }[]) {
    let longest = 0, run = 0;
    for (const d of days) {
        run = d.contributionCount > 0 ? run + 1 : 0;
        longest = Math.max(longest, run);
    }
    // Current streak: count back from today; an empty "today" does not break it yet.
    let current = 0;
    let i = days.length - 1;
    if (i >= 0 && days[i].contributionCount === 0) i--;
    for (; i >= 0 && days[i].contributionCount > 0; i--) current++;
    return { currentStreak: current, longestStreak: longest };
}

// Sample data for previews (?demo=1) and local development without a token.
export function demoStats(): Stats {
    let seed = 7;
    const rnd = () => (seed = (seed * 16807) % 2147483647) / 2147483647;
    const weekly = Array.from({ length: 53 }, (_, i) =>
        Math.round(Math.max(0, 8 + 7 * Math.sin(i / 5) + 10 * rnd() + (i > 40 ? 12 : 0))));
    return {
        login: "brodbeckleon",
        totalContributions: weekly.reduce((a, b) => a + b, 0),
        commits: 742, prs: 58, issues: 21, stars: 34, contributedTo: 17,
        currentStreak: 9, longestStreak: 31,
        weekly,
        languages: [
            { name: "Python", percent: 38.2 }, { name: "TypeScript", percent: 21.5 },
            { name: "Svelte", percent: 14.1 }, { name: "Swift", percent: 11.7 },
            { name: "Java", percent: 7.3 },
        ],
    };
}
