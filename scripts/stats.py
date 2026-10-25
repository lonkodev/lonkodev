#!/usr/bin/env python3
"""
LonkoDev · Generador de tarjetas de stats para el perfil de GitHub.

Consulta la API GraphQL de GitHub con un token personal (incluye repos privados)
y genera dos SVG con la línea gráfica LonkoDev:

  assets/stats.svg   → contribuciones, commits, PRs, issues, repos, estrellas, rachas
  assets/langs.svg   → lenguajes más usados (por bytes, repos propios)

Uso:
  GH_TOKEN=xxxx python3 scripts/stats.py            # datos reales
  python3 scripts/stats.py --demo                   # datos de ejemplo (para probar diseño)

Sin dependencias externas (solo librería estándar).
"""

import json
import os
import sys
import urllib.request
from datetime import date, datetime, timedelta, timezone
from html import escape
from pathlib import Path

API = "https://api.github.com/graphql"
OUT_DIR = Path(__file__).resolve().parent.parent / "assets"

# ── Marca LonkoDev ────────────────────────────────────────────────
NARANJO = "#F1882D"
NEGRO = "#0D0D0D"
GRIS = "#1A1A1A"
BLANCO = "#FFFFFF"
TENUE = "#8A8A8A"
FUENTE = "'JetBrains Mono','SF Mono','Cascadia Code',Consolas,'Liberation Mono',monospace"


# ── API ───────────────────────────────────────────────────────────
def gql(token: str, query: str, variables: dict | None = None) -> dict:
    body = json.dumps({"query": query, "variables": variables or {}}).encode()
    req = urllib.request.Request(
        API,
        data=body,
        headers={
            "Authorization": f"bearer {token}",
            "Content-Type": "application/json",
            "User-Agent": "lonkodev-stats",
        },
    )
    with urllib.request.urlopen(req, timeout=60) as r:
        data = json.loads(r.read())
    if "errors" in data:
        # No se imprimen detalles: el log de Actions es público.
        raise SystemExit(f"Error de la API de GitHub ({len(data['errors'])} errores). Revisa el token.")
    return data["data"]


Q_USER = """
query {
  viewer {
    login
    name
    createdAt
    pullRequests { totalCount }
    issues { totalCount }
  }
}
"""

Q_REPOS = """
query($cursor: String) {
  viewer {
    repositories(first: 100, after: $cursor, ownerAffiliations: OWNER, isFork: false) {
      totalCount
      pageInfo { hasNextPage endCursor }
      nodes {
        stargazerCount
        languages(first: 20, orderBy: {field: SIZE, direction: DESC}) {
          edges { size node { name color } }
        }
      }
    }
  }
}
"""

Q_YEAR = """
query($from: DateTime!, $to: DateTime!) {
  viewer {
    contributionsCollection(from: $from, to: $to) {
      totalCommitContributions
      restrictedContributionsCount
      contributionCalendar {
        totalContributions
        weeks { contributionDays { date contributionCount } }
      }
    }
  }
}
"""


def collect(token: str) -> dict:
    user = gql(token, Q_USER)["viewer"]

    # Repos propios (incluye privados): estrellas + lenguajes
    stars, repos, langs, cursor = 0, 0, {}, None
    while True:
        r = gql(token, Q_REPOS, {"cursor": cursor})["viewer"]["repositories"]
        repos = r["totalCount"]
        for n in r["nodes"]:
            stars += n["stargazerCount"]
            for e in n["languages"]["edges"]:
                name = e["node"]["name"]
                entry = langs.setdefault(name, {"size": 0, "color": e["node"]["color"] or TENUE})
                entry["size"] += e["size"]
        if not r["pageInfo"]["hasNextPage"]:
            break
        cursor = r["pageInfo"]["endCursor"]

    # Contribuciones año a año (la API permite máximo 1 año por consulta)
    created = datetime.fromisoformat(user["createdAt"].replace("Z", "+00:00"))
    now = datetime.now(timezone.utc)
    days: dict[str, int] = {}
    total_contrib = 0
    commits_year = 0
    year_ago = now - timedelta(days=365)

    for y in range(created.year, now.year + 1):
        start = max(datetime(y, 1, 1, tzinfo=timezone.utc), created)
        end = min(datetime(y, 12, 31, 23, 59, 59, tzinfo=timezone.utc), now)
        c = gql(token, Q_YEAR, {"from": start.isoformat(), "to": end.isoformat()})
        cc = c["viewer"]["contributionsCollection"]
        total_contrib += cc["contributionCalendar"]["totalContributions"]
        for w in cc["contributionCalendar"]["weeks"]:
            for d in w["contributionDays"]:
                days[d["date"]] = d["contributionCount"]

    # Commits del último año (ventana móvil de 365 días)
    c = gql(token, Q_YEAR, {"from": year_ago.isoformat(), "to": now.isoformat()})
    cc = c["viewer"]["contributionsCollection"]
    commits_year = cc["totalCommitContributions"]
    contrib_year = cc["contributionCalendar"]["totalContributions"]

    current, longest = streaks(days)

    return {
        "login": user["login"],
        "name": user["name"] or user["login"],
        "since": created.year,
        "total_contrib": total_contrib,
        "contrib_year": contrib_year,
        "commits_year": commits_year,
        "prs": user["pullRequests"]["totalCount"],
        "issues": user["issues"]["totalCount"],
        "repos": repos,
        "stars": stars,
        "streak": current,
        "longest": longest,
        "langs": langs,
    }


def streaks(days: dict[str, int]) -> tuple[int, int]:
    if not days:
        return 0, 0
    ordered = sorted(days.items())
    longest = run = 0
    for _, n in ordered:
        run = run + 1 if n > 0 else 0
        longest = max(longest, run)

    # Racha actual: si hoy aún no hay contribuciones, cuenta desde ayer
    today = date.today()
    d = today if days.get(today.isoformat(), 0) > 0 else today - timedelta(days=1)
    current = 0
    while days.get(d.isoformat(), 0) > 0:
        current += 1
        d -= timedelta(days=1)
    return current, longest


def demo() -> dict:
    return {
        "login": "lonkodev", "name": "Giovanni Cáceres", "since": 2015,
        "total_contrib": 3842, "contrib_year": 912, "commits_year": 684,
        "prs": 48, "issues": 63, "repos": 71, "stars": 27,
        "streak": 12, "longest": 41,
        "langs": {
            "PHP": {"size": 9_400_000, "color": "#4F5D95"},
            "Vue": {"size": 6_100_000, "color": "#41b883"},
            "TypeScript": {"size": 4_200_000, "color": "#3178c6"},
            "JavaScript": {"size": 3_000_000, "color": "#f1e05a"},
            "Blade": {"size": 1_900_000, "color": "#f7523f"},
            "Python": {"size": 900_000, "color": "#3572A5"},
            "CSS": {"size": 600_000, "color": "#563d7c"},
        },
    }


# ── SVG ───────────────────────────────────────────────────────────
def fmt(n: int) -> str:
    return f"{n:,}".replace(",", ".")


def frame(w: int, h: int, title: str, inner: str) -> str:
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-label="{escape(title)}">
  <defs>
    <radialGradient id="g1" cx="0" cy="0" r="1"><stop offset="0" stop-color="{NARANJO}" stop-opacity=".35"/><stop offset="1" stop-color="{NARANJO}" stop-opacity="0"/></radialGradient>
    <radialGradient id="g2" cx="1" cy="1" r="1"><stop offset="0" stop-color="{NARANJO}" stop-opacity=".22"/><stop offset="1" stop-color="{NARANJO}" stop-opacity="0"/></radialGradient>
    <clipPath id="c"><rect width="{w}" height="{h}" rx="14"/></clipPath>
  </defs>
  <style>
    text {{ font-family: {FUENTE}; }}
    .t  {{ fill: {NARANJO}; font-size: 17px; font-weight: 700; }}
    .s  {{ fill: {TENUE}; font-size: 12px; }}
    .v  {{ fill: {BLANCO}; font-size: 26px; font-weight: 700; }}
    .l  {{ fill: {TENUE}; font-size: 12px; }}
    .p  {{ fill: {NARANJO}; font-size: 12px; font-weight: 700; }}
    .f  {{ opacity: 0; animation: in .6s ease forwards; }}
    @keyframes in {{ from {{ opacity: 0; transform: translateY(6px); }} to {{ opacity: 1; transform: none; }} }}
  </style>
  <g clip-path="url(#c)">
    <rect width="{w}" height="{h}" fill="{NEGRO}"/>
    <circle cx="0" cy="0" r="{h * 0.9:.0f}" fill="url(#g1)"/>
    <circle cx="{w}" cy="{h}" r="{h * 0.9:.0f}" fill="url(#g2)"/>
  </g>
  <rect x=".5" y=".5" width="{w - 1}" height="{h - 1}" rx="14" fill="none" stroke="{GRIS}"/>
{inner}
</svg>
"""


def stats_svg(d: dict) -> str:
    w, h = 860, 262
    items = [
        ("Contribuciones totales", fmt(d["total_contrib"])),
        ("Contribuciones · año", fmt(d["contrib_year"])),
        ("Commits · año", fmt(d["commits_year"])),
        ("Repos propios", fmt(d["repos"])),
        ("Pull requests", fmt(d["prs"])),
        ("Issues", fmt(d["issues"])),
        ("🔥 Racha actual", f"{fmt(d['streak'])} días"),
        ("Racha más larga", f"{fmt(d['longest'])} días"),
    ]
    cols, x0, y0, cw, rh = 4, 32, 120, 205, 74
    cells = []
    for i, (label, value) in enumerate(items):
        x = x0 + (i % cols) * cw
        y = y0 + (i // cols) * rh
        delay = 0.15 + i * 0.08
        cells.append(
            f'  <g class="f" style="animation-delay:{delay:.2f}s">'
            f'<rect x="{x - 2}" y="{y - 24}" width="3" height="46" fill="{NARANJO}" rx="1.5"/>'
            f'<text x="{x + 12}" y="{y + 2}" class="v">{escape(value)}</text>'
            f'<text x="{x + 12}" y="{y + 20}" class="l">{escape(label)}</text></g>'
        )
    head = (
        f'  <text x="32" y="44" class="t">&gt; git log --stats</text>\n'
        f'  <text x="32" y="66" class="s">{escape(d["name"])} · @{escape(d["login"])} · en GitHub desde {d["since"]} · incluye repos privados</text>\n'
        f'  <text x="{w - 32}" y="44" class="p" text-anchor="end">⭐ {fmt(d["stars"])}</text>'
    )
    foot = f'  <text x="{w - 32}" y="{h - 16}" class="s" text-anchor="end">@lonkodev · lonkodev.cl</text>'
    return frame(w, h, "Estadísticas de GitHub de LonkoDev", head + "\n" + "\n".join(cells) + "\n" + foot)


def langs_svg(d: dict, top: int = 6) -> str:
    w = 860
    ranked = sorted(d["langs"].items(), key=lambda kv: kv[1]["size"], reverse=True)
    total = sum(v["size"] for _, v in ranked) or 1
    main = ranked[:top]
    rest = sum(v["size"] for _, v in ranked[top:])
    if rest:
        main.append(("Otros", {"size": rest, "color": "#444444"}))

    rows = (len(main) + 2) // 3
    h = 128 + rows * 30
    bar_x, bar_y, bar_w = 32, 88, w - 64

    segs, x = [], bar_x
    for i, (name, v) in enumerate(main):
        sw = bar_w * v["size"] / total
        segs.append(f'<rect x="{x:.2f}" y="{bar_y}" width="{max(sw, 0.5):.2f}" height="12" fill="{v["color"]}"/>')
        x += sw
    bar = (
        f'  <clipPath id="b"><rect x="{bar_x}" y="{bar_y}" width="{bar_w}" height="12" rx="6"/></clipPath>\n'
        f'  <g clip-path="url(#b)" class="f" style="animation-delay:.15s">{"".join(segs)}</g>'
    )

    legend = []
    for i, (name, v) in enumerate(main):
        cx = 32 + (i % 3) * 270
        cy = 134 + (i // 3) * 30
        pct = 100 * v["size"] / total
        legend.append(
            f'  <g class="f" style="animation-delay:{0.3 + i * 0.07:.2f}s">'
            f'<circle cx="{cx + 5}" cy="{cy - 4}" r="5" fill="{v["color"]}"/>'
            f'<text x="{cx + 18}" y="{cy}" fill="{BLANCO}" font-size="13">{escape(name)}</text>'
            f'<text x="{cx + 230}" y="{cy}" class="l" text-anchor="end">{pct:.1f}%</text></g>'
        )
    head = (
        f'  <text x="32" y="44" class="t">&gt; cat lenguajes.log</text>\n'
        f'  <text x="32" y="66" class="s">Por tamaño de código en repos propios · incluye privados</text>'
    )
    return frame(w, h, "Lenguajes más usados", head + "\n" + bar + "\n" + "\n".join(legend))


def main() -> None:
    if "--demo" in sys.argv:
        data = demo()
    else:
        token = os.environ.get("GH_TOKEN")
        if not token:
            raise SystemExit("Falta la variable GH_TOKEN.")
        data = collect(token)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "stats.svg").write_text(stats_svg(data), encoding="utf-8")
    (OUT_DIR / "langs.svg").write_text(langs_svg(data), encoding="utf-8")
    print("Tarjetas generadas en assets/")


if __name__ == "__main__":
    main()
