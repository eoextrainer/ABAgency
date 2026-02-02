from __future__ import annotations

import json
import os
import smtplib
from email.message import EmailMessage
from datetime import date, timedelta
from pathlib import Path
from typing import Any, Dict, List

from flask import Flask, jsonify, request, send_from_directory

BASE_DIR = Path(__file__).resolve().parent
ASSET_DIR = BASE_DIR / "assets"

app = Flask(__name__, static_folder="static", template_folder="templates")

VIDEO_CATEGORIES = [
    "events",
    "backstage",
    "classes",
    "artists",
]
IMAGE_CATEGORIES = [
    "events",
    "backstage",
    "classes",
    "artists",
]


def _title_from_filename(name: str) -> str:
    cleaned = name.replace("-", " ").replace("_", " ")
    cleaned = cleaned.replace(".mp4", "").replace(".jpg", "").replace(".jpeg", "")
    return " ".join([part.capitalize() for part in cleaned.split() if part])


def scan_assets() -> List[Dict[str, Any]]:
    assets: List[Dict[str, Any]] = []
    if not ASSET_DIR.exists():
        return assets

    files = sorted([p for p in ASSET_DIR.iterdir() if p.is_file()])
    for idx, path in enumerate(files, start=1):
        ext = path.suffix.lower()
        asset_type = "video" if ext in {".mp4", ".webm", ".mov"} else "image"
        if asset_type == "video":
            category = VIDEO_CATEGORIES[idx % len(VIDEO_CATEGORIES)]
        else:
            category = IMAGE_CATEGORIES[idx % len(IMAGE_CATEGORIES)]

        assets.append(
            {
                "id": idx,
                "filename": path.name,
                "filepath": f"/assets/{path.name}",
                "asset_type": asset_type,
                "category": category,
                "title": _title_from_filename(path.stem),
                "metadata": {
                    "size_bytes": path.stat().st_size,
                    "extension": ext.replace(".", ""),
                },
            }
        )
    return assets


def _db_connection():
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        return None
    try:
        import psycopg2

        return psycopg2.connect(db_url)
    except Exception:
        return None


def _send_inquiry_email(payload: Dict[str, Any]) -> None:
    smtp_host = os.getenv("SMTP_HOST")
    if not smtp_host:
        return

    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_user = os.getenv("SMTP_USERNAME", "")
    smtp_pass = os.getenv("SMTP_PASSWORD", "")
    smtp_use_tls = os.getenv("SMTP_USE_TLS", "true").lower() in {"1", "true", "yes"}
    smtp_from = os.getenv("SMTP_FROM", smtp_user or "no-reply@abagency.local")
    smtp_to = os.getenv("SMTP_TO", "roum1990@hotmail.fr")

    message = EmailMessage()
    message["Subject"] = "Nouvelle demande – AB AGENCY"
    message["From"] = smtp_from
    message["To"] = smtp_to
    message.set_content(
        "\n".join(
            [
                "Nouvelle demande via le formulaire:",
                f"Nom: {payload.get('client_name')}",
                f"Email: {payload.get('email')}",
                f"Type d'événement: {payload.get('event_type')}",
                f"Date souhaitée: {payload.get('event_date')}",
                "Message:",
                payload.get("message", ""),
            ]
        )
    )

    try:
        with smtplib.SMTP(smtp_host, smtp_port, timeout=10) as server:
            if smtp_use_tls:
                server.starttls()
            if smtp_user and smtp_pass:
                server.login(smtp_user, smtp_pass)
            server.send_message(message)
    except Exception as exc:
        print(f"Email send failed: {exc}")


@app.route("/")
def index():
    return send_from_directory(app.template_folder, "index.html")


@app.route("/test")
def test():
    return send_from_directory(BASE_DIR, "test_media.html")


@app.route("/assets")
def assets():
    return jsonify({"assets": scan_assets()})


@app.route("/assets/<path:filename>")
def asset_file(filename: str):
    return send_from_directory(ASSET_DIR, filename)


@app.route("/milestones")
def milestones():
    assets = scan_assets()
    asset_ids = [asset["id"] for asset in assets]
    milestones_data = [
        {
            "id": 1,
            "year": 2008,
            "title": "Premiers grands spectacles",
            "description": "Débuts professionnels entre danse urbaine et scène contemporaine.",
            "discipline": "dance",
            "media_assets": asset_ids[:2],
        },
        {
            "id": 2,
            "year": 2012,
            "title": "Accrobaties et tournées européennes",
            "description": "Intégration d'acrobaties aériennes et collaborations internationales.",
            "discipline": "acrobatics",
            "media_assets": asset_ids[2:4],
        },
        {
            "id": 3,
            "year": 2016,
            "title": "Cascadeur et direction artistique",
            "description": "Participation à des productions scéniques et télévisées.",
            "discipline": "stunts",
            "media_assets": asset_ids[4:6],
        },
        {
            "id": 4,
            "year": 2020,
            "title": "Transmission et coaching",
            "description": "Coaching chorégraphique et ateliers pour équipes créatives.",
            "discipline": "teaching",
            "media_assets": asset_ids[6:8],
        },
        {
            "id": 5,
            "year": 2024,
            "title": "Lancement de l'agence événementielle",
            "description": "Création d'expériences immersives pour marques et événements.",
            "discipline": "event",
            "media_assets": asset_ids[8:10],
        },
    ]
    return jsonify({"milestones": milestones_data})


@app.route("/inquiry", methods=["POST"])
def inquiry():
    payload = request.get_json(silent=True) or request.form.to_dict()
    required_fields = ["client_name", "email", "event_type", "event_date", "message"]
    missing = [field for field in required_fields if not payload.get(field)]
    if missing:
        return jsonify({"status": "error", "missing": missing}), 400

    conn = _db_connection()
    if conn:
        try:
            with conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        INSERT INTO inquiries (client_name, email, event_type, event_date, message)
                        VALUES (%s, %s, %s, %s, %s)
                        """,
                        (
                            payload["client_name"],
                            payload["email"],
                            payload["event_type"],
                            payload["event_date"],
                            payload["message"],
                        ),
                    )
        except Exception:
            pass
        finally:
            conn.close()
    else:
        log_path = BASE_DIR / "inquiries.jsonl"
        with log_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, ensure_ascii=False) + "\n")

    _send_inquiry_email(payload)

    return jsonify({"status": "ok"})


@app.route("/booking/availability")
def booking_availability():
    today = date.today()
    availability = []
    for offset in range(1, 45):
        day = today + timedelta(days=offset)
        if day.weekday() in {1, 3, 5}:
            availability.append({"date": day.isoformat(), "status": "available"})
        else:
            availability.append({"date": day.isoformat(), "status": "limited"})
    return jsonify({"availability": availability})


if __name__ == "__main__":
    port = int(os.getenv("PORT", "5000"))
    app.run(host="0.0.0.0", port=port, debug=True)
