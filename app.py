from __future__ import annotations

import json
import json
import os
import smtplib
from email.message import EmailMessage
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List

from flask import (
    Flask,
    jsonify,
    redirect,
    render_template,
    request,
    send_from_directory,
    session,
    url_for,
)
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename
from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    MetaData,
    String,
    Table,
    Text,
    create_engine,
    select,
    text,
)
from werkzeug.security import check_password_hash
from werkzeug.utils import secure_filename

BASE_DIR = Path(__file__).resolve().parent
ASSET_DIR = BASE_DIR / "assets"
UPLOAD_DIR = BASE_DIR / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

app = Flask(__name__, static_folder="static", template_folder="templates")
app.secret_key = os.getenv("SECRET_KEY", "change-me")
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "change-me")
app.config["UPLOAD_DIR"] = str(BASE_DIR / "uploads")

os.makedirs(app.config["UPLOAD_DIR"], exist_ok=True)

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


DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR / 'app.db'}")
engine = create_engine(DATABASE_URL, future=True)
metadata = MetaData()

users = Table(
    "users",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("email", String(255), unique=True, nullable=False),
    Column("password_hash", String(255), nullable=False),
    Column("name", String(255), nullable=False),
    Column("role", String(50), nullable=False, default="user"),
    Column("hero_video_url", String(500), nullable=True),
    Column("created_at", DateTime, default=datetime.utcnow),
)

profiles = Table(
    "profiles",
    metadata,
    Column("user_id", Integer, ForeignKey("users.id"), primary_key=True),
    Column("bio", Text, nullable=True),
    Column("phone", String(50), nullable=True),
    Column("location", String(255), nullable=True),
    Column("website", String(255), nullable=True),
)

subscriptions = Table(
    "subscriptions",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("user_id", Integer, ForeignKey("users.id"), nullable=False),
    Column("plan", String(100), nullable=False),
    Column("status", String(50), nullable=False),
    Column("renewal_date", Date, nullable=True),
)

events = Table(
    "events",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("user_id", Integer, ForeignKey("users.id"), nullable=False),
    Column("title", String(255), nullable=False),
    Column("event_date", Date, nullable=False),
    Column("location", String(255), nullable=True),
)

performances = Table(
    "performances",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("user_id", Integer, ForeignKey("users.id"), nullable=False),
    Column("title", String(255), nullable=False),
    Column("performance_date", Date, nullable=False),
    Column("fee", Float, nullable=False, default=0),
)

media_assets = Table(
    "media_assets",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("user_id", Integer, ForeignKey("users.id"), nullable=False),
    Column("media_type", String(20), nullable=False),
    Column("url", String(500), nullable=False),
    Column("uploaded_at", DateTime, default=datetime.utcnow),
)

messages = Table(
    "messages",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("sender_id", Integer, ForeignKey("users.id"), nullable=False),
    Column("recipient_id", Integer, ForeignKey("users.id"), nullable=True),
    Column("body", Text, nullable=False),
    Column("created_at", DateTime, default=datetime.utcnow),
    Column("is_to_moderator", Boolean, default=False),
)

inquiries = Table(
    "inquiries",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("client_name", String(255), nullable=False),
    Column("email", String(255), nullable=False),
    Column("event_type", String(255), nullable=False),
    Column("event_date", Date, nullable=False),
    Column("message", Text, nullable=False),
    Column("created_at", DateTime, default=datetime.utcnow),
)


def init_db() -> None:
    metadata.create_all(engine)

    with engine.begin() as conn:
        _ensure_schema(conn)

        def _insert_user(email: str, password: str, name: str, role: str, hero: str) -> int | None:
            created_at = datetime.utcnow()
            if _has_column(conn, "users", "username"):
                username = email.split("@", 1)[0]
                existing_id = conn.execute(
                    text("SELECT id FROM users WHERE email = :email OR username = :username"),
                    {"email": email, "username": username},
                ).scalar_one_or_none()
                if existing_id is not None:
                    return existing_id
                result = conn.execute(
                    text(
                        """
                        INSERT INTO users (email, password_hash, name, role, hero_video_url, username, created_at)
                        VALUES (:email, :password_hash, :name, :role, :hero_video_url, :username, :created_at)
                        ON CONFLICT DO NOTHING
                        RETURNING id
                        """
                    ),
                    {
                        "email": email,
                        "password_hash": generate_password_hash(password),
                        "name": name,
                        "role": role,
                        "hero_video_url": hero,
                        "username": username,
                        "created_at": created_at,
                    },
                )
                user_id = result.scalar_one_or_none()
                if user_id is not None:
                    return user_id
                return conn.execute(
                    text("SELECT id FROM users WHERE email = :email OR username = :username"),
                    {"email": email, "username": username},
                ).scalar_one_or_none()
            existing_id = conn.execute(
                select(users.c.id).where(users.c.email == email)
            ).scalar_one_or_none()
            if existing_id is not None:
                return existing_id
            result = conn.execute(
                users.insert().values(
                    email=email,
                    password_hash=generate_password_hash(password),
                    name=name,
                    role=role,
                    hero_video_url=hero,
                    created_at=created_at,
                )
            )
            return result.inserted_primary_key[0]

        existing = conn.execute(select(users.c.id).limit(1)).first()
        if existing:
            for email, name, role, hero in (
                (
                    "admin@abagency.com",
                    "AB AGENCY Admin",
                    "admin",
                    "https://www.youtube-nocookie.com/embed/_4FGVRpNoEs",
                ),
                (
                    "moderator@abagency.com",
                    "AB AGENCY Moderator",
                    "moderator",
                    "https://www.youtube-nocookie.com/embed/Tz-khkZz_zY",
                ),
                (
                    "artist@abagency.com",
                    "Artiste Résident",
                    "community",
                    "https://www.youtube-nocookie.com/embed/7FhkTtoq9Pg",
                ),
            ):
                exists = conn.execute(
                    select(users.c.id).where(users.c.email == email)
                ).first()
                if not exists:
                    _insert_user(
                        email,
                        "Admin123!" if role == "admin" else "Mod123!" if role == "moderator" else "User123!",
                        name,
                        role,
                        hero,
                    )
            return

        admin_id = _insert_user(
            "admin@abagency.com",
            "Admin123!",
            "AB AGENCY Admin",
            "admin",
            "https://www.youtube-nocookie.com/embed/_4FGVRpNoEs",
        )
        moderator_id = _insert_user(
            "moderator@abagency.com",
            "Mod123!",
            "AB AGENCY Moderator",
            "moderator",
            "https://www.youtube-nocookie.com/embed/Tz-khkZz_zY",
        )
        user_id = _insert_user(
            "artist@abagency.com",
            "User123!",
            "Artiste Résident",
            "community",
            "https://www.youtube-nocookie.com/embed/7FhkTtoq9Pg",
        )

        conn.execute(
            profiles.insert().values(
                user_id=user_id,
                bio="Artiste pluridisciplinaire spécialisée en danse et performance scénique.",
                phone="+33 6 00 00 00 00",
                location="Paris, France",
                website="https://abagency.com",
            )
        )

        conn.execute(
            subscriptions.insert().values(
                user_id=user_id,
                plan="Premium",
                status="Active",
                renewal_date=date.today() + timedelta(days=30),
            )
        )

        conn.execute(
            events.insert().values(
                user_id=user_id,
                title="Gala Printemps",
                event_date=date.today() + timedelta(days=14),
                location="Théâtre Lumière",
            )
        )
        conn.execute(
            performances.insert().values(
                user_id=user_id,
                title="Performance Aérienne",
                performance_date=date.today() - timedelta(days=7),
                fee=850.0,
            )
        )
        conn.execute(
            messages.insert().values(
                sender_id=moderator_id,
                recipient_id=user_id,
                body="Bienvenue sur votre espace. N'hésitez pas à partager vos besoins.",
                is_to_moderator=False,
            )
        )


def _table_exists(conn, table_name: str) -> bool:
    if engine.dialect.name == "sqlite":
        result = conn.execute(
            text("SELECT name FROM sqlite_master WHERE type='table' AND name=:name"),
            {"name": table_name},
        ).first()
        return result is not None
    result = conn.execute(text("SELECT to_regclass(:name)"), {"name": table_name}).first()
    return bool(result and result[0])


def _has_column(conn, table_name: str, column_name: str) -> bool:
    if engine.dialect.name == "sqlite":
        rows = conn.execute(text(f"PRAGMA table_info({table_name})")).fetchall()
        return any(row[1] == column_name for row in rows)
    result = conn.execute(
        text(
            """
            SELECT 1 FROM information_schema.columns
            WHERE table_name = :table AND column_name = :col
            """
        ),
        {"table": table_name, "col": column_name},
    ).first()
    return result is not None


def _ensure_schema(conn) -> None:
    if _table_exists(conn, "users"):
        if not _has_column(conn, "users", "email"):
            conn.execute(text("ALTER TABLE users ADD COLUMN email TEXT"))
            conn.execute(text("UPDATE users SET email = 'user' || id || '@abagency.com' WHERE email IS NULL"))
        if not _has_column(conn, "users", "name"):
            conn.execute(text("ALTER TABLE users ADD COLUMN name TEXT"))
        if _has_column(conn, "users", "full_name"):
            conn.execute(text("UPDATE users SET name = COALESCE(name, full_name) WHERE name IS NULL"))
        if not _has_column(conn, "users", "role"):
            conn.execute(text("ALTER TABLE users ADD COLUMN role TEXT DEFAULT 'community'"))
        if not _has_column(conn, "users", "hero_video_url"):
            conn.execute(text("ALTER TABLE users ADD COLUMN hero_video_url TEXT"))
        if _has_column(conn, "users", "username"):
            conn.execute(text("ALTER TABLE users ALTER COLUMN username SET DEFAULT 'user'"))
            conn.execute(
                text(
                    """
                    UPDATE users
                    SET username = COALESCE(username, email, 'user')
                    WHERE username IS NULL
                    """
                )
            )

    if _table_exists(conn, "user_profiles") and not _table_exists(conn, "profiles"):
        conn.execute(
            text(
                """
                CREATE TABLE profiles (
                  user_id INTEGER PRIMARY KEY,
                  bio TEXT,
                  phone TEXT,
                  location TEXT,
                  website TEXT
                )
                """
            )
        )
        conn.execute(
            text(
                """
                INSERT INTO profiles (user_id, bio, phone, location, website)
                SELECT user_id, bio, phone, location, website FROM user_profiles
                """
            )
        )

    if _table_exists(conn, "user_events") and not _table_exists(conn, "events"):
        conn.execute(
            text(
                """
                CREATE TABLE events (
                  id SERIAL PRIMARY KEY,
                  user_id INTEGER,
                  title TEXT NOT NULL,
                  event_date DATE NOT NULL,
                  location TEXT
                )
                """
            )
        )
        conn.execute(
            text(
                """
                INSERT INTO events (user_id, title, event_date, location)
                SELECT user_id, title, event_date, notes FROM user_events
                """
            )
        )

    if _table_exists(conn, "user_media") and not _table_exists(conn, "media_assets"):
        conn.execute(
            text(
                """
                CREATE TABLE media_assets (
                  id SERIAL PRIMARY KEY,
                  user_id INTEGER,
                  media_type TEXT NOT NULL,
                  url TEXT NOT NULL,
                  uploaded_at TIMESTAMPTZ DEFAULT NOW()
                )
                """
            )
        )
        conn.execute(
            text(
                """
                INSERT INTO media_assets (user_id, media_type, url)
                SELECT user_id, media_type, url FROM user_media
                """
            )
        )

    if _table_exists(conn, "user_performances") and not _table_exists(conn, "performances"):
        conn.execute(
            text(
                """
                CREATE TABLE performances (
                  id SERIAL PRIMARY KEY,
                  user_id INTEGER,
                  title TEXT NOT NULL,
                  performance_date DATE NOT NULL,
                  fee NUMERIC(10,2) DEFAULT 0
                )
                """
            )
        )
        conn.execute(
            text(
                """
                INSERT INTO performances (user_id, title, performance_date, fee)
                SELECT user_id, performance_name, performance_date, fee_earned FROM user_performances
                """
            )
        )

    if _table_exists(conn, "chat_messages") and not _table_exists(conn, "messages"):
        conn.execute(
            text(
                """
                CREATE TABLE messages (
                  id SERIAL PRIMARY KEY,
                  sender_id INTEGER,
                  recipient_id INTEGER,
                  body TEXT NOT NULL,
                  created_at TIMESTAMPTZ DEFAULT NOW(),
                  is_to_moderator BOOLEAN DEFAULT FALSE
                )
                """
            )
        )
        conn.execute(
            text(
                """
                INSERT INTO messages (sender_id, recipient_id, body, created_at)
                SELECT sender_id, recipient_id, message, created_at FROM chat_messages
                """
            )
        )


def get_current_user() -> Dict[str, Any] | None:
    user_id = session.get("user_id")
    if not user_id:
        return None
    with engine.begin() as conn:
        row = conn.execute(select(users).where(users.c.id == user_id)).mappings().first()
        return dict(row) if row else None


def _sqlite_connection():
    db_path = BASE_DIR / "app.db"
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def _get_db():
    conn = _db_connection()
    if conn:
        return conn, "postgres"
    return _sqlite_connection(), "sqlite"


def _init_sqlite():
    conn, engine = _get_db()
    if engine != "sqlite":
        return
    schema_path = BASE_DIR / "schema.sql"
    if schema_path.exists():
        with conn:
            conn.executescript(schema_path.read_text(encoding="utf-8"))
    conn.close()


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
    return render_template("index.html", current_user=get_current_user())


@app.route("/test")
def test():
    return send_from_directory(BASE_DIR, "test_media.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        payload = request.form.to_dict()
        email = payload.get("email", "").strip().lower()
        password = payload.get("password", "")
        if not email or not password:
            return render_template("login.html", error="Identifiants requis")

        with engine.begin() as conn:
            row = conn.execute(select(users).where(users.c.email == email)).mappings().first()
        if not row or not check_password_hash(row["password_hash"], password):
            return render_template("login.html", error="Identifiants invalides")

        session["user_id"] = row["id"]
        return redirect(url_for("workspace"))

    return render_template("login.html", error=None)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))


@app.route("/workspace")
def workspace():
    current_user = get_current_user()
    if not current_user:
        return redirect(url_for("login"))

    with engine.begin() as conn:
        profile = conn.execute(
            select(profiles).where(profiles.c.user_id == current_user["id"])
        ).mappings().first()
        subscription = conn.execute(
            select(subscriptions).where(subscriptions.c.user_id == current_user["id"])
        ).mappings().first()
        user_events = conn.execute(
            select(events).where(events.c.user_id == current_user["id"]).order_by(events.c.event_date)
        ).mappings().all()
        user_performances = conn.execute(
            select(performances)
            .where(performances.c.user_id == current_user["id"])
            .order_by(performances.c.performance_date.desc())
        ).mappings().all()
        user_media = conn.execute(
            select(media_assets)
            .where(media_assets.c.user_id == current_user["id"])
            .order_by(media_assets.c.uploaded_at.desc())
        ).mappings().all()
        chat_messages = conn.execute(
            select(messages)
            .where(
                (messages.c.sender_id == current_user["id"]) |
                (messages.c.recipient_id == current_user["id"])
            )
            .order_by(messages.c.created_at.desc())
            .limit(50)
        ).mappings().all()

    return render_template(
        "workspace.html",
        current_user=current_user,
        profile=profile,
        subscription=subscription,
        user_events=user_events,
        user_performances=user_performances,
        user_media=user_media,
        chat_messages=chat_messages,
    )


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

    try:
        with engine.begin() as conn:
            conn.execute(
                inquiries.insert().values(
                    client_name=payload["client_name"],
                    email=payload["email"],
                    event_type=payload["event_type"],
                    event_date=payload["event_date"],
                    message=payload["message"],
                )
            )
    except Exception:
        log_path = BASE_DIR / "inquiries.jsonl"
        with log_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, ensure_ascii=False) + "\n")

    _send_inquiry_email(payload)

    return jsonify({"status": "ok"})


@app.route("/api/profile", methods=["POST"])
def update_profile():
    current_user = get_current_user()
    if not current_user:
        return jsonify({"status": "error", "message": "Unauthorized"}), 401

    payload = request.get_json(silent=True) or request.form.to_dict()
    with engine.begin() as conn:
        existing = conn.execute(
            select(profiles).where(profiles.c.user_id == current_user["id"])
        ).first()
        if existing:
            conn.execute(
                profiles.update()
                .where(profiles.c.user_id == current_user["id"])
                .values(
                    bio=payload.get("bio"),
                    phone=payload.get("phone"),
                    location=payload.get("location"),
                    website=payload.get("website"),
                )
            )
        else:
            conn.execute(
                profiles.insert().values(
                    user_id=current_user["id"],
                    bio=payload.get("bio"),
                    phone=payload.get("phone"),
                    location=payload.get("location"),
                    website=payload.get("website"),
                )
            )

    return jsonify({"status": "ok"})


@app.route("/api/events", methods=["POST"])
def add_event():
    current_user = get_current_user()
    if not current_user:
        return jsonify({"status": "error", "message": "Unauthorized"}), 401

    payload = request.get_json(silent=True) or request.form.to_dict()
    with engine.begin() as conn:
        conn.execute(
            events.insert().values(
                user_id=current_user["id"],
                title=payload.get("title", "")[:255],
                event_date=payload.get("event_date"),
                location=payload.get("location", "")[:255],
            )
        )
    return jsonify({"status": "ok"})


@app.route("/api/performances", methods=["POST"])
def add_performance():
    current_user = get_current_user()
    if not current_user:
        return jsonify({"status": "error", "message": "Unauthorized"}), 401

    payload = request.get_json(silent=True) or request.form.to_dict()
    fee_value = float(payload.get("fee", 0) or 0)
    with engine.begin() as conn:
        conn.execute(
            performances.insert().values(
                user_id=current_user["id"],
                title=payload.get("title", "")[:255],
                performance_date=payload.get("performance_date"),
                fee=fee_value,
            )
        )
    return jsonify({"status": "ok"})


@app.route("/api/media/upload", methods=["POST"])
def upload_media():
    current_user = get_current_user()
    if not current_user:
        return jsonify({"status": "error", "message": "Unauthorized"}), 401

    if "file" not in request.files:
        return jsonify({"status": "error", "message": "No file uploaded"}), 400

    file = request.files["file"]
    if not file.filename:
        return jsonify({"status": "error", "message": "Invalid filename"}), 400

    filename = secure_filename(file.filename)
    user_folder = UPLOAD_DIR / str(current_user["id"])
    user_folder.mkdir(parents=True, exist_ok=True)
    target_path = user_folder / filename
    file.save(target_path)

    media_type = "video" if filename.lower().endswith((".mp4", ".webm", ".mov")) else "image"
    url = f"/uploads/{current_user['id']}/{filename}"
    with engine.begin() as conn:
        conn.execute(
            media_assets.insert().values(
                user_id=current_user["id"],
                media_type=media_type,
                url=url,
            )
        )
    return jsonify({"status": "ok", "url": url})


@app.route("/api/media/url", methods=["POST"])
def add_media_url():
    current_user = get_current_user()
    if not current_user:
        return jsonify({"status": "error", "message": "Unauthorized"}), 401

    payload = request.get_json(silent=True) or request.form.to_dict()
    url = payload.get("url", "").strip()
    media_type = payload.get("media_type", "image")
    if not url:
        return jsonify({"status": "error", "message": "Missing URL"}), 400

    with engine.begin() as conn:
        conn.execute(
            media_assets.insert().values(
                user_id=current_user["id"],
                media_type=media_type,
                url=url,
            )
        )
    return jsonify({"status": "ok"})


@app.route("/api/messages", methods=["POST"])
def send_message():
    current_user = get_current_user()
    if not current_user:
        return jsonify({"status": "error", "message": "Unauthorized"}), 401

    payload = request.get_json(silent=True) or request.form.to_dict()
    body = payload.get("body", "").strip()
    recipient_id = payload.get("recipient_id")
    to_moderator = payload.get("to_moderator", "false") in {True, "true", "1"}
    if not body:
        return jsonify({"status": "error", "message": "Message vide"}), 400

    with engine.begin() as conn:
        conn.execute(
            messages.insert().values(
                sender_id=current_user["id"],
                recipient_id=int(recipient_id) if recipient_id else None,
                body=body,
                is_to_moderator=to_moderator,
            )
        )
    return jsonify({"status": "ok"})


@app.route("/uploads/<path:filename>")
def serve_uploads(filename: str):
    return send_from_directory(UPLOAD_DIR, filename)


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
    init_db()
    port = int(os.getenv("PORT", "5000"))
    app.run(host="0.0.0.0", port=port, debug=True)
