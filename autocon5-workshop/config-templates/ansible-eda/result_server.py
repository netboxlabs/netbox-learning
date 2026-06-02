#!/usr/bin/env python3
"""Tiny result relay: EDA playbooks POST here, NetBox scripts GET here."""
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
import json
import logging
import threading

results = {}
results_lock = threading.Lock()
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
log = logging.getLogger(__name__)


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        log.info(fmt % args)

    def do_POST(self):
        job_id = self.path.strip("/")
        length = int(self.headers.get("Content-Length", 0))
        with results_lock:
            results[job_id] = json.loads(self.rfile.read(length))
        log.info("Stored result for job %s", job_id)
        self.send_response(200)
        self.end_headers()

    def do_GET(self):
        job_id = self.path.strip("/")
        with results_lock:
            if job_id in results:
                data = json.dumps(results.pop(job_id)).encode()
            else:
                data = None
        if data is not None:
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(data)
        else:
            self.send_response(404)
            self.end_headers()


if __name__ == "__main__":
    port = 5001
    log.info("Result relay server listening on port %d", port)
    ThreadingHTTPServer(("0.0.0.0", port), Handler).serve_forever()
