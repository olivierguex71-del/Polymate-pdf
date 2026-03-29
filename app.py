#!/usr/bin/env python3
import json
import os
from http.server import HTTPServer, BaseHTTPRequestHandler

from jinja2 import Template
from weasyprint import HTML

THEMES = {
    "cabinet": {
        "name": "Cabinet",
        "accent": "#8FC819",
    }
}

PDF_TEMPLATE = Template("""
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
body { font-family: Arial, sans-serif; font-size: 12px; }
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

def build_pdf(payload):
    theme = THEMES.get(payload.get("theme", "cabinet"), THEMES["cabinet"])
    html = PDF_TEMPLATE.render(
        theme=theme,
        meta=payload.get("meta", {}),
        scores=payload.get("scores", {}),
        summary_html=payload.get("summary_html") or payload.get("summary", "")
    )
    return HTML(string=html).write_pdf()

class Handler(BaseHTTPRequestHandler):
    def _set_cors_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")

    def do_OPTIONS(self):
        self.send_response(204)
        self._set_cors_headers()
        self.end_headers()

    def do_GET(self):
        if self.path == "/":
            self.send_response(200)
            self._set_cors_headers()
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.end_headers()
            self.wfile.write(b"Polymate PDF server running")
            return

        self.send_response(404)
        self._set_cors_headers()
        self.end_headers()

    def do_POST(self):
        if self.path != "/generate-pdf":
            self.send_response(404)
            self._set_cors_headers()
            self.end_headers()
            return

        try:
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length)
            payload = json.loads(body.decode("utf-8"))
            pdf = build_pdf(payload)

            self.send_response(200)
            self._set_cors_headers()
            self.send_header("Content-Type", "application/pdf")
            self.send_header("Content-Disposition", 'attachment; filename="rapport.pdf"')
            self.send_header("Content-Length", str(len(pdf)))
            self.end_headers()
            self.wfile.write(pdf)

        except Exception as e:
            error_payload = json.dumps({"error": str(e)}).encode("utf-8")
            self.send_response(500)
            self._set_cors_headers()
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(error_payload)))
            self.end_headers()
            self.wfile.write(error_payload)

if __name__ == "__main__":
    host = "0.0.0.0"
    port = int(os.environ.get("PORT", 8767))
    print(f"Server running on {host}:{port}")
    HTTPServer((host, port), Handler).serve_forever()