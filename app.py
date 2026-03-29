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

# =========================
# THEMES
# =========================
THEMES = {
    "cabinet": {
        "name": "Cabinet",
        "accent": "#8FC819",
        "accent2": "#68B5FF",
        "soft": "#F7F9FC",
        "ink": "#132033",
    }
}

# =========================
# TEMPLATE HTML PDF
# =========================
PDF_TEMPLATE = Template("""
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
body { font-family: Arial; font-size: 12px; }
h1 { color: {{ theme.accent }}; }
</style>
</head>
<body>
<h1>Rapport Polymate</h1>
<p><strong>Client :</strong> {{ meta.client }}</p>
<p><strong>Maturité :</strong> {{ scores.maturity }}/100</p>
<p><strong>Urgence :</strong> {{ scores.urgency }}/100</p>
<p>{{ summary_html }}</p>
</body>
</html>
""")

# =========================
# BUILD PDF
# =========================
def build_pdf(payload):
    theme = THEMES.get(payload.get("theme", "cabinet"), THEMES["cabinet"])

    html = PDF_TEMPLATE.render(
        theme=theme,
        meta=payload.get("meta", {}),
        scores=payload.get("scores", {}),
        summary_html=payload.get("summary_html", "")
    )

    return HTML(string=html).write_pdf()

# =========================
# HTTP HANDLER
# =========================
class Handler(BaseHTTPRequestHandler):

    def do_GET(self):
        if self.path == "/":
            self.send_response(200)
            self.send_header("Content-type", "text/plain")
            self.end_headers()
            self.wfile.write(b"Polymate PDF server running")
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        if self.path == "/generate-pdf":
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length)

            try:
                payload = json.loads(body.decode("utf-8"))
                pdf = build_pdf(payload)

                self.send_response(200)
                self.send_header("Content-Type", "application/pdf")
                self.send_header("Content-Disposition", "attachment; filename=rapport.pdf")
                self.end_headers()
                self.wfile.write(pdf)

            except Exception as e:
                self.send_response(500)
                self.end_headers()
                self.wfile.write(str(e).encode())

        else:
            self.send_response(404)
            self.end_headers()

# =========================
# MAIN (CRITIQUE POUR RENDER)
# =========================
if __name__ == "__main__":
    host = "0.0.0.0"
    port = int(os.environ.get("PORT", 8767))

    print(f"Server running on {host}:{port}")
    HTTPServer((host, port), Handler).serve_forever()