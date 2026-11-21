#!/usr/bin/env python3
"""Local download page for the built question bank.

  /          landing page with a real download button
  /download  jac_pyqs.html sent as an attachment
  /view      jac_pyqs.html served inline, to read in the browser

    python3 tools/serve.py [port]        (default 8081)
"""
import http.server
import os
import shutil
import socketserver
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FILE = "jac_pyqs.html"
SIZE = os.path.getsize(os.path.join(ROOT, FILE))

LANDING = """<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Download - JAC PYQ Question Bank</title>
<style>
 :root{color-scheme:dark}
 *{box-sizing:border-box}
 body{margin:0;min-height:100vh;display:grid;place-items:center;padding:24px;
      font:16px/1.55 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;
      background:radial-gradient(120% 90% at 50% 0%,#1b2330 0%,#0d1219 60%);color:#e8edf5}
 .card{width:100%;max-width:560px;background:#141b25;border:1px solid #253041;
       border-radius:18px;padding:30px 28px;box-shadow:0 24px 60px rgba(0,0,0,.5)}
 h1{margin:0 0 6px;font-size:23px;letter-spacing:-.2px}
 p.sub{margin:0 0 22px;color:#93a0b4;font-size:14px}
 dl{display:grid;grid-template-columns:auto 1fr;gap:9px 16px;margin:0 0 24px;
    font-size:14px;border-top:1px solid #232d3d;padding-top:18px}
 dt{color:#8190a5}
 dd{margin:0;font-variant-numeric:tabular-nums}
 .btn{display:block;text-align:center;text-decoration:none;font-weight:650;font-size:16px;
      padding:15px 20px;border-radius:12px;background:linear-gradient(180deg,#3b82f6,#2563eb);
      color:#fff;box-shadow:0 8px 22px rgba(37,99,235,.35);transition:transform .12s,filter .12s}
 .btn:hover{filter:brightness(1.08)} .btn:active{transform:translateY(1px)}
 .alt{display:block;text-align:center;margin-top:12px;color:#8fa1ba;font-size:13.5px;
      text-decoration:none;padding:10px;border:1px solid #253041;border-radius:11px}
 .alt:hover{border-color:#3a4a63;color:#c7d3e4}
 code{background:#0e141c;padding:2px 6px;border-radius:5px;font-size:12.5px;color:#9fc4ef}
 .note{margin:18px 0 0;font-size:12.5px;color:#75859b;line-height:1.5}
</style></head><body>
<div class="card">
  <h1>JAC PYQ Question Bank</h1>
  <p class="sub">Class 12 &middot; 56 papers &middot; 2,187 solved questions</p>
  <dl>
    <dt>File</dt><dd><code>JAC-PYQ-Question-Bank.html</code></dd>
    <dt>Size</dt><dd>__SIZE__</dd>
    <dt>Physics</dt><dd>14 papers &middot; 530 questions</dd>
    <dt>Chemistry</dt><dd>13 papers &middot; 510 questions</dd>
    <dt>Mathematics</dt><dd>13 papers &middot; 506 questions</dd>
    <dt>English Core</dt><dd>16 papers &middot; 641 questions</dd>
    <dt>Works offline</dt><dd>yes &mdash; nothing loads from the internet</dd>
  </dl>
  <a class="btn" href="/download" download="JAC-PYQ-Question-Bank.html">Download HTML file</a>
  <a class="alt" href="/view">or open it in the browser first &rsaquo;</a>
  <p class="note">One self-contained file: save it anywhere and double-click it. Works on
  phone and laptop, no internet needed after download. If the browser opens it instead of
  saving, right-click the button and choose &ldquo;Save link as&hellip;&rdquo;.</p>
</div></body></html>
"""


class Handler(http.server.BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def do_GET(self):
        path = self.path.split("?")[0]
        if path in ("/download", "/download/", "/download.html"):
            self._send_file(attachment=True)
        elif path in ("/view", "/view/"):
            self._send_file(attachment=False)
        elif path in ("/", "/index.html"):
            body = LANDING.replace("__SIZE__", "%.1f MB" % (SIZE / 1048576)).encode()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)
        else:
            self.send_error(404, "Not found")

    def _send_file(self, attachment):
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        if attachment:
            self.send_header("Content-Disposition",
                             'attachment; filename="JAC-PYQ-Question-Bank.html"')
        self.send_header("Content-Length", str(SIZE))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        with open(os.path.join(ROOT, FILE), "rb") as fh:
            shutil.copyfileobj(fh, self.wfile)

    def log_message(self, fmt, *args):
        print("%s - %s" % (self.address_string(), fmt % args), flush=True)


class Server(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    daemon_threads = True


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8081
    with Server(("0.0.0.0", port), Handler) as httpd:
        print("download page on 0.0.0.0:%d" % port, flush=True)
        httpd.serve_forever()
