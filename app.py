from __future__ import annotations

import json
import mimetypes
import secrets
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import pandas as pd

from duplicate_detector import analyze_dataframe, save_outputs

BASE_DIR = Path(__file__).resolve().parent
WEB_DIR = BASE_DIR / "web"
OUTPUT_DIR = BASE_DIR / "outputs"
HOST = "127.0.0.1"
PORT = 8000

SESSIONS: dict[str, dict] = {}


def json_response(handler, payload, status=200):
    body = json.dumps(payload, ensure_ascii=False, default=str).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(body)))
    handler.send_header("Cache-Control", "no-store")
    handler.end_headers()
    handler.wfile.write(body)


def html_response(handler, path: Path):
    body = path.read_bytes()
    handler.send_response(200)
    handler.send_header("Content-Type", "text/html; charset=utf-8")
    handler.send_header("Content-Length", str(len(body)))
    handler.end_headers()
    handler.wfile.write(body)


class Handler(BaseHTTPRequestHandler):
    server_version = "MatchLens/1.0"

    def log_message(self, fmt, *args):
        print(f"[MatchLens] {self.address_string()} - {fmt % args}")

    def do_GET(self):
        parsed = urlparse(self.path)

        if parsed.path in ("/", "/index.html"):
            return html_response(self, WEB_DIR / "index.html")

        if parsed.path == "/api/health":
            return json_response(self, {"ok": True, "service": "MatchLens Duplicate Record Detection System"})

        if parsed.path.startswith("/download/"):
            name = Path(parsed.path.split("/download/", 1)[1]).name
            path = OUTPUT_DIR / name
            if not path.exists() or path.suffix.lower() != ".csv":
                return json_response(self, {"error": "File not found."}, 404)
            body = path.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "text/csv; charset=utf-8")
            self.send_header("Content-Disposition", f'attachment; filename="{name}"')
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return

        # Static assets
        safe = (WEB_DIR / parsed.path.lstrip("/")).resolve()
        if WEB_DIR.resolve() in safe.parents and safe.is_file():
            mime = mimetypes.guess_type(str(safe))[0] or "application/octet-stream"
            body = safe.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", mime)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return

        self.send_error(404, "Not found")

    def do_POST(self):
        parsed = urlparse(self.path)
        if parsed.path != "/api/analyze":
            return json_response(self, {"error": "Endpoint not found."}, 404)

        try:
            length = int(self.headers.get("Content-Length", "0"))
            if length > 8 * 1024 * 1024:
                return json_response(self, {"error": "Upload is limited to 8 MB for this local demo."}, 413)
            raw = self.rfile.read(length)
            payload = json.loads(raw.decode("utf-8"))
            csv_text = payload.get("csv", "")
            fields = payload.get("fields", [])
            threshold = float(payload.get("threshold", 0.82))

            if not csv_text.strip():
                return json_response(self, {"error": "Please choose a CSV file."}, 400)

            # Keep CSV parsing deterministic and safe.
            from io import StringIO
            df = pd.read_csv(StringIO(csv_text))
            if df.empty:
                return json_response(self, {"error": "The CSV contains no records."}, 400)

            # Clean duplicate column names and whitespace.
            df.columns = [str(c).strip() for c in df.columns]
            df = df.loc[:, ~df.columns.duplicated()]

            if not 0.50 <= threshold <= 0.99:
                return json_response(self, {"error": "Threshold must be between 50% and 99%."}, 400)

            result = analyze_dataframe(df, list(fields), threshold)
            files = save_outputs(result, OUTPUT_DIR)

            session_id = secrets.token_hex(8)
            SESSIONS[session_id] = {"files": files}

            def records(frame, limit=100):
                if frame.empty:
                    return []
                return frame.head(limit).where(pd.notna(frame.head(limit)), None).to_dict(orient="records")

            response = {
                "session_id": session_id,
                "filename": payload.get("filename", "uploaded.csv"),
                "rows": result["rows"],
                "columns": result["columns"],
                "fields": result["fields"],
                "threshold": result["threshold"],
                "exact_pair_count": result["exact_pair_count"],
                "potential_pair_count": result["potential_pair_count"],
                "removed_exact_rows": result["removed_exact_rows"],
                "exact": records(result["exact"]),
                "potential": records(result["potential"]),
                "preview": records(df),
                "cleaned_preview": records(result["cleaned"]),
                "downloads": {
                    "exact": f"/download/{files['exact']}",
                    "potential": f"/download/{files['potential']}",
                    "cleaned": f"/download/{files['cleaned']}",
                },
            }
            return json_response(self, response)

        except pd.errors.ParserError as exc:
            return json_response(self, {"error": f"CSV parsing error: {exc}"}, 400)
        except UnicodeDecodeError:
            return json_response(self, {"error": "Please save the CSV as UTF-8 and try again."}, 400)
        except ValueError as exc:
            return json_response(self, {"error": str(exc)}, 400)
        except Exception as exc:
            print("ERROR:", repr(exc))
            return json_response(self, {"error": "Unexpected error while analyzing the file. Check the terminal for details."}, 500)


def main():
    OUTPUT_DIR.mkdir(exist_ok=True)
    print("\nMatchLens — Duplicate Record Detection System")
    print(f"Open: http://{HOST}:{PORT}")
    print("Press Ctrl+C to stop the server.\n")
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped.")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
