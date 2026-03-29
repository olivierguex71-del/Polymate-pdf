#!/usr/bin/env python3
import json
import math
import os
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlparse

from jinja2 import Template
from weasyprint import HTML

ROOT = Path(__file__).resolve().parent
INDEX = ROOT / "index.html"

THEMES = {
    "cabinet": {
        "name": "Cabinet",
        "accent": "#8FC819",
        "accent2": "#68B5FF",
        "soft": "#F7F9FC",
        "ink": "#132033",
        "cover_grad": "linear-gradient(180deg,#ffffff 0%,#f7f9fc 100%)",
    },
    "graphite": {
        "name": "Graphite",
        "accent": "#67758E",
        "accent2": "#9CB0C8",
        "soft": "#F5F6F8",
        "ink": "#1E2836",
        "cover_grad": "linear-gradient(180deg,#ffffff 0%,#f5f6f8 100%)",
    },
    "executive": {
        "name": "Executive",
        "accent": "#1F6FFF",
        "accent2": "#8EC5FF",
        "soft": "#F4F8FF",
        "ink": "#13254A",
        "cover_grad": "linear-gradient(180deg,#ffffff 0%,#f4f8ff 100%)",
    },
    "impact": {
        "name": "Impact",
        "accent": "#00B894",
        "accent2": "#7CE8D1",
        "soft": "#F3FFFB",
        "ink": "#12362F",
        "cover_grad": "linear-gradient(180deg,#ffffff 0%,#f3fffb 100%)",
    },
}

PDF_TEMPLATE = Template(r"""
<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="utf-8">
<title>Rapport Polymate</title>
<style>
  @page {
    size: A4;
    margin: 13mm;
    @bottom-left {
      content: "Polymate — Diagnostic de prise en charge";
      color: #6b778c;
      font-size: 9px;
    }
    @bottom-right {
      content: "Réf. {{ meta.reference }}";
      color: #6b778c;
      font-size: 9px;
    }
  }
  :root{
    --accent: {{ theme.accent }};
    --accent2: {{ theme.accent2 }};
    --soft: {{ theme.soft }};
    --ink: {{ theme.ink }};
    --line: #dfe5ef;
    --muted: #5d6b84;
    --paper: #ffffff;
  }
  * { box-sizing: border-box; }
  body {
    margin: 0;
    color: #142033;
    font-family: Arial, Helvetica, sans-serif;
    font-size: 11px;
    line-height: 1.55;
    background: white;
  }
  .page {
    page-break-after: always;
    min-height: 258mm;
  }
  .page:last-child { page-break-after: auto; }
  .avoid-break { break-inside: avoid; page-break-inside: avoid; }
  .cover {
    background:
      radial-gradient(circle at top right, color-mix(in srgb, var(--accent) 18%, transparent), transparent 24%),
      {{ theme.cover_grad }};
    border: 1px solid var(--line);
    padding: 15mm;
  }
  .badge{
    display:inline-block;
    padding:6px 10px;
    border-radius:999px;
    border:1px solid var(--line);
    background:#fff;
    color:#4f5e77;
    font-size:10px;
    font-weight:700;
    letter-spacing:.08em;
    text-transform:uppercase;
  }
  .title{
    margin:14px 0 10px 0;
    font-size: 54px;
    line-height: .92;
    letter-spacing: -1.9px;
    color: var(--accent);
    font-weight: 800;
  }
  .subtitle{
    font-size:14px;
    line-height:1.75;
    color:#55647d;
    max-width:125mm;
  }
  .grid-2{
    display:grid;
    grid-template-columns: 1.08fr .92fr;
    gap: 9mm;
  }
  .card, .block{
    border:1px solid var(--line);
    border-radius:16px;
    background:#fff;
    padding:12px;
  }
  .card.hero-card{
    border-top:4px solid var(--accent);
    box-shadow: 0 8px 24px rgba(0,0,0,.03);
  }
  .label{
    font-size:10px;
    text-transform:uppercase;
    color:#66758d;
    letter-spacing:.08em;
    margin-bottom:6px;
  }
  .score{
    font-size:22px;
    font-weight:800;
    color:var(--ink);
    margin:0 0 4px 0;
  }
  .tiny{ font-size:10px; color:#6b778c; line-height:1.55; }
  .meter{
    height:7px;
    background:#edf1f6;
    border-radius:999px;
    overflow:hidden;
    border:1px solid #e5ebf2;
    margin:6px 0 2px 0;
  }
  .meter > span{
    display:block;
    height:100%;
  }
  .meter.maturity > span{
    background: linear-gradient(90deg, #ff6675, #ffb84d, var(--accent2), var(--accent));
    width: {{ scores.maturity }}%;
  }
  .meter.urgency > span{
    background: linear-gradient(90deg, #34d399, #ffb84d, #ff6675);
    width: {{ scores.urgency }}%;
  }
  .meter.completion > span{
    background: linear-gradient(90deg, var(--accent2), var(--accent));
    width: {{ scores.completion }}%;
  }
  .score-stack{ display:grid; gap:8px; }
  .meta-grid{
    display:grid;
    grid-template-columns:1fr 1fr;
    gap:8px;
    margin-top:9mm;
  }
  .meta{
    border:1px solid var(--line);
    border-radius:12px;
    padding:10px 12px;
    background:#fff;
  }
  .meta .k{
    color:#66758d;
    font-size:10px;
    text-transform:uppercase;
    letter-spacing:.08em;
  }
  .meta .v{
    margin-top:4px;
    font-size:13px;
    font-weight:700;
    color:#1f2b3f;
  }
  .chip{
    display:inline-block;
    margin:4px 6px 0 0;
    padding:7px 9px;
    font-size:10px;
    border-radius:999px;
    border:1px solid color-mix(in srgb, var(--accent) 20%, var(--line));
    background:#fff;
    color:#31415d;
  }
  .recommendation{
    display:inline-block;
    margin-top:8px;
    padding:9px 12px;
    border-radius:999px;
    border:1px solid color-mix(in srgb, var(--accent) 25%, var(--line));
    background:#fff;
    color:#23314a;
    font-size:11px;
    font-weight:700;
  }
  .cover-bottom{
    margin-top:10mm;
    display:grid;
    grid-template-columns: 1fr auto;
    gap:8mm;
    align-items:end;
  }
  .section-title{
    font-size:24px;
    font-weight:800;
    color:var(--ink);
    letter-spacing:-.03em;
    margin:0 0 2px 0;
  }
  .section-sub{
    color:#66758d;
    font-size:11px;
    margin:0 0 8mm 0;
  }
  .summary-hero{
    display:grid;
    grid-template-columns: 1.12fr .88fr;
    gap: 8mm;
    margin-bottom:8mm;
  }
  .hero-box{
    border:1px solid var(--line);
    border-radius:16px;
    background:#fff;
    padding:14px;
  }
  .hero-box.primary{
    border-top:4px solid var(--accent);
  }
  .hero-name{
    font-size:30px;
    line-height:1;
    color:var(--accent);
    font-weight:800;
    margin-bottom:8px;
  }
  .hero-text{ font-size:12px; line-height:1.68; }
  .score-grid{
    display:grid;
    grid-template-columns:1fr;
    gap:8px;
  }
  .scorebox{
    border:1px solid var(--line);
    border-radius:14px;
    background:#fff;
    padding:11px;
  }
  .scorebox .k{
    color:#66758d;
    font-size:10px;
    text-transform:uppercase;
    letter-spacing:.08em;
  }
  .scorebox .n{
    font-size:17px;
    font-weight:800;
    margin:4px 0;
  }
  .two-col{
    display:grid;
    grid-template-columns: 1.03fr .97fr;
    gap: 8mm;
  }
  .list{ display:grid; gap:8px; }
  .item{
    border:1px solid var(--line);
    border-radius:12px;
    padding:10px;
    background:#fcfdff;
    font-size:11px;
    line-height:1.55;
  }
  .item strong{ display:block; margin-bottom:4px; }
  .radar-box{
    border:1px solid var(--line);
    border-radius:14px;
    background:#fff;
    padding:10px;
  }
  .bars{ display:grid; gap:8px; }
  .bar-row{
    display:grid;
    grid-template-columns:1fr 40px;
    gap:8px;
    align-items:center;
  }
  .bar-name{ font-size:10px; }
  .bar-track{
    height:7px;
    border-radius:999px;
    overflow:hidden;
    border:1px solid #e5ebf2;
    background:#edf1f6;
    margin-top:4px;
  }
  .bar-fill{
    display:block;
    height:100%;
    background: linear-gradient(90deg, var(--accent2), var(--accent));
  }
  .bar-score{
    text-align:right;
    color:#66758d;
    font-size:10px;
  }
  .three-col{
    display:grid;
    grid-template-columns:1fr 1fr 1fr;
    gap:8mm;
    margin-bottom:8mm;
  }
  .theme-box{
    border:1px solid var(--line);
    border-radius:12px;
    padding:9px;
    background:#fff;
    margin-top:6px;
  }
  .theme-badge{
    display:inline-block;
    padding:6px 8px;
    border-radius:999px;
    border:1px solid color-mix(in srgb, var(--accent) 25%, var(--line));
    background: var(--soft);
    font-size:10px;
    color:#30425f;
    margin-right:6px;
    margin-bottom:6px;
  }
  .footer-note{
    margin-top:8mm;
    padding-top:4mm;
    border-top:1px solid var(--line);
    color:#67758d;
    font-size:10px;
    display:flex;
    justify-content:space-between;
  }
  svg text { font-family: Arial, Helvetica, sans-serif; }
</style>
</head>
<body>
  <div class="page cover">
    <div class="badge">Polymate · Diagnostic</div>
    <div class="title">{{ recommendation.name }}</div>
    <div class="subtitle">{{ recommendation.text }}</div>

    <div class="grid-2 avoid-break" style="margin-top:9mm">
      <div class="card hero-card">
        <div class="label">Résumé exécutif</div>
        <div>{{ summary_html|safe }}</div>
      </div>
      <div class="score-stack">
        <div class="card">
          <div class="label">Maturité</div>
          <div class="score">{{ scores.maturity }}/100</div>
          <div class="meter maturity"><span></span></div>
          <div class="tiny">Niveau de structuration et de pilotabilité.</div>
        </div>
        <div class="card">
          <div class="label">Urgence</div>
          <div class="score">{{ scores.urgency }}/100</div>
          <div class="meter urgency"><span></span></div>
          <div class="tiny">Niveau de tension appelant une reprise en main.</div>
        </div>
        <div class="card">
          <div class="label">Complétude</div>
          <div class="score">{{ scores.completion }}%</div>
          <div class="meter completion"><span></span></div>
          <div class="tiny">Niveau de confiance associé à la restitution.</div>
        </div>
      </div>
    </div>

    <div class="meta-grid avoid-break">
      <div class="meta"><div class="k">Client</div><div class="v">{{ meta.client }}</div></div>
      <div class="meta"><div class="k">Date du diagnostic</div><div class="v">{{ meta.date }}</div></div>
      <div class="meta"><div class="k">Référence</div><div class="v">{{ meta.reference }}</div></div>
      <div class="meta"><div class="k">Chargé de mission</div><div class="v">{{ meta.owner }}</div></div>
    </div>

    <div class="cover-bottom avoid-break">
      <div class="tiny">
        Document de diagnostic indicatif destiné à rendre visibles les priorités, les déséquilibres et la forme d’accompagnement la plus cohérente à ce stade.
      </div>
      <div style="text-align:right">
        <div class="recommendation">Formule recommandée : {{ recommendation.name }}</div>
        <div>
          {% for tag in recommendation.tags %}
            <span class="chip">{{ tag }}</span>
          {% endfor %}
        </div>
      </div>
    </div>
  </div>

  <div class="page">
    <div class="section-title">Lecture détaillée</div>
    <div class="section-sub">Synthèse opérationnelle, priorités et cartographie des dimensions</div>

    <div class="summary-hero avoid-break">
      <div class="hero-box primary">
        <div class="label">Lecture de direction</div>
        <div class="hero-name">{{ recommendation.name }}</div>
        <div class="hero-text">{{ summary_html|safe }}</div>
        <div style="margin-top:8px">
          {% for tag in recommendation.tags %}
            <span class="chip">{{ tag }}</span>
          {% endfor %}
        </div>
      </div>
      <div class="score-grid">
        <div class="scorebox">
          <div class="k">Maturité</div>
          <div class="n">{{ scores.maturity }}/100</div>
          <div class="meter maturity"><span></span></div>
        </div>
        <div class="scorebox">
          <div class="k">Urgence</div>
          <div class="n">{{ scores.urgency }}/100</div>
          <div class="meter urgency"><span></span></div>
        </div>
        <div class="scorebox">
          <div class="k">Complétude</div>
          <div class="n">{{ scores.completion }}%</div>
          <div class="meter completion"><span></span></div>
        </div>
      </div>
    </div>

    <div class="two-col">
      <div class="list">
        <div class="block avoid-break">
          <div class="label">3 priorités d’action suggérées</div>
          <div class="list">
            {% for p in priorities %}
              <div class="item avoid-break"><strong>{{ p.title }}</strong>{{ p.text }}</div>
            {% endfor %}
          </div>
        </div>
        <div class="block avoid-break">
          <div class="label">Lecture commerciale suggérée</div>
          <div class="list">
            {% for c in commercial %}
              <div class="item avoid-break"><strong>{{ c.title }}</strong>{{ c.text }}</div>
            {% endfor %}
          </div>
        </div>
      </div>

      <div class="list">
        <div class="radar-box avoid-break">
          <div class="label">Radar des dimensions</div>
          {{ radar_svg|safe }}
        </div>
        <div class="block avoid-break">
          <div class="label">Scores par dimension</div>
          <div class="bars">
            {% for d in dimensions %}
              <div class="bar-row">
                <div>
                  <div class="bar-name">{{ d.title }}</div>
                  <div class="bar-track"><span class="bar-fill" style="width: {{ d.score_value }}%"></span></div>
                </div>
                <div class="bar-score">{{ d.score_label }}</div>
              </div>
            {% endfor %}
          </div>
        </div>
      </div>
    </div>
  </div>

  <div class="page">
    <div class="section-title">Aide à la décision</div>
    <div class="section-sub">Lecture managériale, zones d’appui, fragilités et trajectoire</div>

    <div class="three-col avoid-break">
      <div class="block">
        <div class="label">Points d’appui</div>
        <div class="list">
          {% for s in strengths %}
            <div class="item avoid-break"><strong>{{ s }}</strong>Dimension actuellement la plus porteuse ou la plus solide du profil.</div>
          {% endfor %}
        </div>
      </div>
      <div class="block">
        <div class="label">Zones de fragilité</div>
        <div class="list">
          {% for w in weaknesses %}
            <div class="item avoid-break"><strong>{{ w }}</strong>Dimension appelant une attention prioritaire ou une remise à niveau.</div>
          {% endfor %}
        </div>
      </div>
      <div class="block">
        <div class="label">Profil de cohérence</div>
        <div class="item"><strong>Indice de cohérence : {{ stability_label }}</strong>{{ stability_text }}</div>
      </div>
    </div>

    <div class="two-col">
      <div class="list">
        <div class="block avoid-break">
          <div class="label">Trajectoire recommandée</div>
          <div class="list">
            {% for t in trajectory %}
              <div class="item avoid-break"><strong>{{ t.title }}</strong>{{ t.text }}</div>
            {% endfor %}
          </div>
        </div>
        <div class="block avoid-break">
          <div class="label">Traduction en langage client</div>
          <div class="list">
            {% for c in client_language %}
              <div class="item avoid-break"><strong>{{ c.title }}</strong>{{ c.text }}</div>
            {% endfor %}
          </div>
        </div>
      </div>
      <div class="list">
        <div class="block avoid-break">
          <div class="label">Thème visuel retenu</div>
          <div class="theme-box">
            <span class="theme-badge">{{ theme.name }}</span>
            <span class="theme-badge">Accent {{ theme.accent }}</span>
            <span class="theme-badge">Secondaire {{ theme.accent2 }}</span>
          </div>
          <div style="height:4mm"></div>
          <div class="tiny">
            Ce rapport n’a pas vocation à “juger” l’entreprise. Il sert à objectiver les déséquilibres, à hiérarchiser les chantiers et à choisir le niveau d’intervention le plus juste.
          </div>
        </div>
      </div>
    </div>

    <div class="footer-note">
      <div>Polymate — Rapport d’aide à la décision</div>
      <div>Réf. {{ meta.reference }}</div>
    </div>
  </div>
</body>
</html>
""")


def radar_svg(dimensions, accent="#8FC819", accent2="#68B5FF"):
    size = 420
    cx = size / 2
    cy = size / 2
    radius = 120
    count = max(1, len(dimensions))
    parts = [f'<svg width="{size}" height="{size}" viewBox="0 0 {size} {size}" xmlns="http://www.w3.org/2000/svg">']
    parts.append(f'<rect x="0" y="0" width="{size}" height="{size}" rx="14" fill="#fbfcfe"/>')
    for layer in range(1, 5):
        r = radius * layer / 4
        pts = []
        for i in range(count):
            a = -math.pi/2 + i * 2 * math.pi / count
            x = cx + math.cos(a) * r
            y = cy + math.sin(a) * r
            pts.append(f"{x:.1f},{y:.1f}")
        parts.append(f'<polygon points="{" ".join(pts)}" fill="none" stroke="#d7deea" stroke-width="1"/>')
    for i, d in enumerate(dimensions):
        a = -math.pi/2 + i * 2 * math.pi / count
        x = cx + math.cos(a) * radius
        y = cy + math.sin(a) * radius
        parts.append(f'<line x1="{cx:.1f}" y1="{cy:.1f}" x2="{x:.1f}" y2="{y:.1f}" stroke="#d0d8e5" stroke-width="1"/>')
        lx = cx + math.cos(a) * (radius + 20)
        ly = cy + math.sin(a) * (radius + 20)
        anchor = "middle"
        if lx < cx - 5:
            anchor = "end"
        elif lx > cx + 5:
            anchor = "start"
        parts.append(f'<text x="{lx:.1f}" y="{ly:.1f}" font-size="11" fill="#66758d" text-anchor="{anchor}">{d["title"].split(" ")[0]}</text>')
    pts = []
    for i, d in enumerate(dimensions):
        val = d.get("score_value", 0) / 100
        a = -math.pi/2 + i * 2 * math.pi / count
        r = radius * val
        x = cx + math.cos(a) * r
        y = cy + math.sin(a) * r
        pts.append((x, y))
    poly = " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
    parts.append(f'<polygon points="{poly}" fill="{accent}33" stroke="{accent}" stroke-width="2.2"/>')
    for x, y in pts:
        parts.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3.5" fill="{accent}" stroke="#ffffff" stroke-width="1"/>')
    parts.append("</svg>")
    return "".join(parts)


def stability_text(stability):
    if stability is None:
        return "La stabilité inter-dimensions n’est pas encore lisible."
    if stability >= 75:
        return "Le profil paraît relativement homogène. Les écarts entre dimensions restent contenus."
    if stability >= 55:
        return "Le profil présente quelques déséquilibres notables. Certaines zones avancent plus vite que d’autres."
    return "Le profil est très contrasté. L’entreprise semble solide sur certains sujets mais nettement fragile sur d’autres."


def build_pdf(payload: dict) -> bytes:
    theme_name = payload.get("theme", "cabinet")
    theme = THEMES.get(theme_name, THEMES["cabinet"])
    meta = payload.get("meta", {})
    recommendation = payload.get("recommendation", {})
    scores = payload.get("scores", {})
    dimensions = payload.get("dimensions", [])
    priorities = payload.get("priorities", [])
    commercial = payload.get("commercial", [])
    trajectory = payload.get("trajectory", [])
    strengths = payload.get("strengths", [])
    weaknesses = payload.get("weaknesses", [])
    summary_html = payload.get("summary_html", "")
    stability = payload.get("stability")
    client_language = payload.get("client_language", [])

    rendered = PDF_TEMPLATE.render(
        theme=theme,
        meta=meta,
        recommendation=recommendation,
        scores=scores,
        dimensions=dimensions,
        priorities=priorities,
        commercial=commercial,
        trajectory=trajectory,
        strengths=strengths or ["Pas encore lisible."],
        weaknesses=weaknesses or ["Pas encore lisible."],
        summary_html=summary_html,
        radar_svg=radar_svg(dimensions, theme["accent"], theme["accent2"]),
        stability_label="—" if stability is None else f"{stability}/100",
        stability_text=stability_text(stability),
        client_language=client_language or [{"title": "Formulation possible", "text": "Le diagnostic doit encore être interprété avec prudence."}],
    )
    return HTML(string=rendered, base_url=str(ROOT)).write_pdf()


class Handler(BaseHTTPRequestHandler):
    def _send(self, code=200, ctype="text/html; charset=utf-8", data=b""):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        path = urlparse(self.path).path
        if path in ("/", "/index.html"):
            self._send(200, "text/html; charset=utf-8", INDEX.read_bytes())
            return
        self._send(404, "text/plain; charset=utf-8", b"Not found")

    def do_POST(self):
        path = urlparse(self.path).path
        if path != "/generate-pdf":
            self._send(404, "text/plain; charset=utf-8", b"Not found")
            return
        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length)
        try:
            payload = json.loads(raw.decode("utf-8"))
            pdf = build_pdf(payload)
        except Exception as e:
            self._send(500, "application/json; charset=utf-8", json.dumps({"error": str(e)}).encode("utf-8"))
            return
        filename = payload.get("meta", {}).get("reference", "POLY-DIAG").replace(" ", "_")
        self.send_response(200)
        self.send_header("Content-Type", "application/pdf")
        self.send_header("Content-Disposition", f'attachment; filename="{filename}_polymate_v12.pdf"')
        self.send_header("Content-Length", str(len(pdf)))
        self.end_headers()
        self.wfile.write(pdf)


if __name__ == "__main__":
    host = "0.0.0.0"
    port = int(os.environ.get("PORT", 8767))
    print(f"Polymate V12 server running on http://{host}:{port}")
    HTTPServer((host, port), Handler).serve_forever()
