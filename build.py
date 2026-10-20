"""Static site generator for the developer site (GitHub Pages). Python 3 standard library only.

    python build.py            build docs/ and refuse if anything required is missing
    python build.py --draft    build anyway with a visible DRAFT banner (local preview only)
    python build.py --serve    build (draft allowed) and serve http://localhost:8000

Inputs: site.json, apps/<slug>/app.json, apps/<slug>/privacy.md, apps/<slug>/assets/*, src/*.
Output: docs/ (GitHub Pages publishes this folder from the main branch).
"""
import html
import json
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "docs"
LANGS = ("fr", "en", "es")
LANG_NAMES = {"fr": "Français", "en": "English", "es": "Español"}
UI = {
    "fr": {"apps": "Applications", "privacy": "Politique de confidentialité", "contact": "Contact",
           "soon": "Bientôt sur Google Play", "get": "Disponible sur Google Play", "back": "Toutes les applications",
           "home_intro": "Des applications simples, soignées et respectueuses de votre vie privée.",
           "features": "En bref"},
    "en": {"apps": "Apps", "privacy": "Privacy policy", "contact": "Contact",
           "soon": "Coming soon to Google Play", "get": "Get it on Google Play", "back": "All apps",
           "home_intro": "Simple, polished apps that respect your privacy.", "features": "At a glance"},
    "es": {"apps": "Aplicaciones", "privacy": "Política de privacidad", "contact": "Contacto",
           "soon": "Próximamente en Google Play", "get": "Disponible en Google Play", "back": "Todas las aplicaciones",
           "home_intro": "Aplicaciones sencillas, cuidadas y respetuosas con tu privacidad.", "features": "En resumen"},
}


# ---------------------------------------------------------------- Markdown (small, documented subset)
def inline(text):
    """Escapes HTML, then renders `code`, **bold**, *italic*, [text](url) and bare https:// links."""
    codes = []

    def keep_code(m):
        codes.append("<code>" + html.escape(m.group(1)) + "</code>")
        return f"\x00{len(codes) - 1}\x00"

    text = re.sub(r"`([^`]+)`", keep_code, text)
    text = html.escape(text, quote=False)
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?!\w)", r"<em>\1</em>", text)
    text = re.sub(r"\[([^\]]+)\]\((https?://[^)\s]+|#[\w-]+|mailto:[^)\s]+)\)", r'<a href="\2">\1</a>', text)
    text = re.sub(r'(?<!["=>])(https?://[^\s<)]+[^\s<).,;:])', r'<a href="\1">\1</a>', text)
    return re.sub(r"\x00(\d+)\x00", lambda m: codes[int(m.group(1))], text)


def slugify(text):
    text = re.sub(r"[^\w\s-]", "", text.lower(), flags=re.U).strip()
    return re.sub(r"[\s_]+", "-", text)


def markdown(md):
    """Headings (#..###), paragraphs, '-' lists, '>' quotes, tables, '---'. Enough for policies."""
    out, para, lines = [], [], md.splitlines()

    def flush():
        if para:
            out.append("<p>" + inline(" ".join(para)) + "</p>")
            para.clear()

    i = 0
    while i < len(lines):
        line = lines[i].rstrip()
        if not line.strip():
            flush()
            i += 1
            continue
        m = re.match(r"^(#{1,4})\s+(.*)$", line)
        if m:
            flush()
            level = max(2, len(m.group(1)))  # the page title is the only <h1>
            out.append(f'<h{level} id="{slugify(m.group(2))}">{inline(m.group(2))}</h{level}>')
            i += 1
            continue
        if re.match(r"^-{3,}$", line.strip()):
            flush()
            out.append("<hr>")
            i += 1
            continue
        if line.lstrip().startswith("|") and i + 1 < len(lines) and re.match(r"^\s*\|[\s|:-]+\|\s*$", lines[i + 1]):
            flush()
            head = [c.strip() for c in line.strip().strip("|").split("|")]
            rows = []
            i += 2
            while i < len(lines) and lines[i].lstrip().startswith("|"):
                rows.append([c.strip() for c in lines[i].strip().strip("|").split("|")])
                i += 1
            t = ["<div class=\"table\"><table><thead><tr>"] + [f"<th>{inline(c)}</th>" for c in head] + ["</tr></thead><tbody>"]
            for r in rows:
                t.append("<tr>" + "".join(f"<td>{inline(c)}</td>" for c in r) + "</tr>")
            out.append("".join(t) + "</tbody></table></div>")
            continue
        if re.match(r"^\s*[-*]\s+", line):
            flush()
            items = []
            while i < len(lines) and (re.match(r"^\s*[-*]\s+", lines[i]) or (lines[i].startswith("  ") and items)):
                if re.match(r"^\s*[-*]\s+", lines[i]):
                    items.append(re.sub(r"^\s*[-*]\s+", "", lines[i]).strip())
                else:
                    items[-1] += " " + lines[i].strip()
                i += 1
            out.append("<ul>" + "".join(f"<li>{inline(x)}</li>" for x in items) + "</ul>")
            continue
        if line.startswith(">"):
            flush()
            quote = []
            while i < len(lines) and lines[i].startswith(">"):
                quote.append(lines[i][1:].strip())
                i += 1
            out.append("<blockquote>" + inline(" ".join(quote)) + "</blockquote>")
            continue
        para.append(line.strip())
        i += 1
    flush()
    return "\n".join(out)


# ---------------------------------------------------------------- Pages
def page(title, body, lang, depth, description="", accent="#15171A", draft=False, image=None):
    up = "../" * depth
    meta_img = f'<meta property="og:image" content="{image}">' if image else ""
    banner = '<div class="draft">BROUILLON — non publiable : informations manquantes (voir build.py)</div>' if draft else ""
    return f"""<!doctype html>
<html lang="{lang}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(title)}</title>
<meta name="description" content="{html.escape(description)}">
<meta property="og:title" content="{html.escape(title)}">
<meta property="og:description" content="{html.escape(description)}">
{meta_img}
<link rel="stylesheet" href="{up}assets/style.css">
<style>:root{{--accent:{accent}}}</style>
</head>
<body>
{banner}
<main class="wrap">
{body}
</main>
</body>
</html>
"""


def lang_switch(current, hrefs):
    links = []
    for lang in LANGS:
        cls = ' class="on" aria-current="page"' if lang == current else ""
        links.append(f'<a href="{hrefs[lang]}"{cls} lang="{lang}">{lang.upper()}</a>')
    return '<nav class="langs">' + "".join(links) + "</nav>"


def store_button(app, ui):
    if app["status"] == "published":
        url = f"https://play.google.com/store/apps/details?id={app['package']}"
        return f'<a class="btn" href="{url}">{ui["get"]}</a>'
    return f'<span class="btn ghost">{ui["soon"]}</span>'


def build_home(site, apps, draft):
    ui = UI[site["default_lang"]]
    cards = []
    for app in apps:
        cards.append(f"""<a class="card" href="{app['slug']}/">
  <img src="{app['slug']}/{app['icon']}" alt="" width="64" height="64">
  <span><strong>{html.escape(app['name'])}</strong><small>{html.escape(app['tagline'][site['default_lang']])}</small></span>
</a>""")
    body = f"""<header class="hero">
  <p class="eyebrow">{html.escape(site['github_user'])}</p>
  <h1>{ui['apps']}</h1>
  <p class="lead">{ui['home_intro']}</p>
</header>
<section class="cards">{''.join(cards)}</section>
<footer>{ui['contact']} : <a href="mailto:{site['contact_email']}">{site['contact_email']}</a></footer>"""
    (OUT / "index.html").write_text(page(f"{site['github_user']} — {ui['apps']}", body, site["default_lang"], 0,
                                         ui["home_intro"], draft=draft), encoding="utf-8")


def build_app(site, app, draft):
    slug = app["slug"]
    base = OUT / slug
    for lang in LANGS:
        ui = UI[lang]
        depth = 1 if lang == site["default_lang"] else 2
        up = "../" * depth
        target = base if depth == 1 else base / lang
        target.mkdir(parents=True, exist_ok=True)
        hrefs = {l: (f"{up}{slug}/" if l == site["default_lang"] else f"{up}{slug}/{l}/") for l in LANGS}
        features = "".join(f"<li>{html.escape(f)}</li>" for f in app["features"][lang])
        img = f"{up}{slug}/{app['feature'][lang]}"
        body = f"""{lang_switch(lang, hrefs)}
<header class="hero app">
  <img class="icon" src="{up}{slug}/{app['icon']}" alt="" width="96" height="96">
  <h1>{html.escape(app['name'])}</h1>
  <p class="lead">{html.escape(app['tagline'][lang])}</p>
  <p>{html.escape(app['summary'][lang])}</p>
  {store_button(app, ui)}
</header>
<img class="feature" src="{img}" alt="{html.escape(app['name'])} — {html.escape(app['tagline'][lang])}">
<section><h2>{ui['features']}</h2><ul class="checks">{features}</ul></section>
<footer>
  <a href="{up}{slug}/privacy/#{slugify(LANG_NAMES[lang])}">{ui['privacy']}</a> ·
  <a href="mailto:{site['contact_email']}">{ui['contact']}</a> ·
  <a href="{up}">{ui['back']}</a>
</footer>"""
        (target / "index.html").write_text(
            page(f"{app['name']} — {app['tagline'][lang]}", body, lang, depth, app["summary"][lang],
                 app["accent"], draft, f"{site['site_url']}/{slug}/{app['feature'][lang]}"),
            encoding="utf-8")

    # Privacy: one URL for Google Play, three languages on the page.
    md = (ROOT / "apps" / slug / app["privacy"]).read_text(encoding="utf-8")
    values = {
        "publisher_name": site["publisher_name"] or "[NOM DE L'ÉDITEUR À RENSEIGNER]",
        "contact_email": site["contact_email"],
        "package": app["package"],
        "app_name": app["name"],
        "effective_date": app["effective_date"],
        "updated_date": app["updated_date"],
        "site_url": site["site_url"],
    }
    md = re.sub(r"\{\{(\w+)\}\}", lambda m: values[m.group(1)], md)
    toc = " · ".join(f'<a href="#{slugify(LANG_NAMES[l])}">{LANG_NAMES[l]}</a>' for l in LANGS)
    body = f"""<header class="hero small">
  <a class="back" href="../">← {html.escape(app['name'])}</a>
  <h1>{html.escape(app['name'])} — {UI['fr']['privacy']}</h1>
  <p class="langs-inline">{toc}</p>
</header>
<article class="prose">{markdown(md)}</article>
<footer><a href="mailto:{site['contact_email']}">{site['contact_email']}</a></footer>"""
    (base / "privacy").mkdir(parents=True, exist_ok=True)
    (base / "privacy" / "index.html").write_text(
        page(f"{app['name']} — {UI['fr']['privacy']}", body, "fr", 2, f"{app['name']} privacy policy",
             app["accent"], draft), encoding="utf-8")

    shutil.copytree(ROOT / "apps" / slug / "assets", base / "assets", dirs_exist_ok=True)


def problems(site, apps):
    found = []
    if not site.get("publisher_name", "").strip():
        found.append("site.json : publisher_name est vide (nom de l'éditeur, obligatoire dans la politique).")
    if not re.match(r"[^@\s]+@[^@\s]+\.\w+$", site.get("contact_email", "")):
        found.append("site.json : contact_email invalide.")
    for pid in site.get("admob_publisher_ids", []):
        if not re.match(r"^pub-\d{16}$", pid):
            found.append(f"site.json : identifiant éditeur AdMob invalide : {pid}")
    for app in apps:
        for key in ("slug", "name", "package", "status", "effective_date", "updated_date", "icon", "privacy"):
            if not app.get(key):
                found.append(f"apps/{app.get('slug', '?')}/app.json : champ manquant « {key} ».")
        for key in ("tagline", "summary", "features", "feature"):
            missing = [l for l in LANGS if not app.get(key, {}).get(l)]
            if missing:
                found.append(f"apps/{app['slug']}/app.json : « {key} » manque pour {missing}.")
        md = (ROOT / "apps" / app["slug"] / app["privacy"]).read_text(encoding="utf-8")
        unknown = set(re.findall(r"\{\{(\w+)\}\}", md)) - {"publisher_name", "contact_email", "package", "app_name",
                                                          "effective_date", "updated_date", "site_url"}
        if unknown:
            found.append(f"apps/{app['slug']}/{app['privacy']} : variables inconnues {sorted(unknown)}.")
        if "À COMPLÉTER" in md or "TODO" in md:
            found.append(f"apps/{app['slug']}/{app['privacy']} : texte « À COMPLÉTER » restant.")
    return found


def main():
    draft_ok = "--draft" in sys.argv or "--serve" in sys.argv
    site = json.loads((ROOT / "site.json").read_text(encoding="utf-8"))
    apps = []
    for f in sorted((ROOT / "apps").glob("*/app.json")):
        if f.parent.name.startswith("_"):
            continue  # apps/_template
        apps.append(json.loads(f.read_text(encoding="utf-8")))
    issues = problems(site, apps)
    if issues and not draft_ok:
        print("Construction refusée (rien n'a été modifié) :")
        for p in issues:
            print("  -", p)
        print("Corrigez ces points, ou utilisez --draft pour un aperçu local.")
        sys.exit(1)
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir()
    shutil.copytree(ROOT / "src" / "assets", OUT / "assets")
    (OUT / ".nojekyll").write_text("", encoding="utf-8")
    (OUT / "app-ads.txt").write_text(
        "".join(f"google.com, {pid}, DIRECT, f08c47fec0942fa0\n" for pid in site["admob_publisher_ids"]),
        encoding="utf-8")
    (OUT / "404.html").write_text(page("404", '<header class="hero"><h1>404</h1><p class="lead"><a href="/">←</a></p></header>',
                                       site["default_lang"], 0), encoding="utf-8")
    draft = bool(issues)
    build_home(site, apps, draft)
    for app in apps:
        build_app(site, app, draft)
    print(f"OK : docs/ généré ({len(apps)} app(s)){' — BROUILLON' if draft else ''}.")
    for app in apps:
        print(f"  {site['site_url']}/{app['slug']}/            page de l'app")
        print(f"  {site['site_url']}/{app['slug']}/privacy/    URL à saisir dans Play Console")
    print(f"  {site['site_url']}/app-ads.txt")
    if issues:
        for p in issues:
            print("  ! ", p)
    if "--serve" in sys.argv:
        import functools
        import http.server
        handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(OUT))
        print("Aperçu : http://localhost:8000  (Ctrl+C pour arrêter)")
        http.server.ThreadingHTTPServer(("127.0.0.1", 8000), handler).serve_forever()


if __name__ == "__main__":
    main()
