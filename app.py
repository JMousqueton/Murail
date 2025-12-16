#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations
import io
import os
import re
import threading
import time
from datetime import datetime, date, timedelta
import pytz
from typing import List, Dict, Any, Optional

from dateutil import parser as dtparser
from dateutil.tz import gettz
from flask import (
    Flask, render_template, request, redirect, url_for, flash, send_file,
    session, make_response
)

from unidecode import unidecode
import pandas as pd

from dotenv import load_dotenv
from werkzeug.utils import secure_filename

from pathlib import Path
from functools import lru_cache
from flask import g
import json


load_dotenv()


# ROLES will be populated dynamically from CHRONOGRAMME after loading
ROLES: List[str] = []

PMS = os.environ.get("PMS_FILE", os.path.join("Sample", "pms.xlsx"))
CHRONOGRAMME = os.environ.get("CHRONOGRAMME_FILE", os.path.join("Sample", "chronogramme.xlsx"))
ADMIN_PASSWORD     = os.environ.get("ADMIN_PASSWORD", "changeme_admin")
ANIMATOR_PASSWORD  = os.environ.get("ANIMATOR_PASSWORD", "changeme_animator")
OBSERVER_PASSWORD  = os.environ.get("OBSERVER_PASSWORD", "changeme_observer")
APP_ID             = os.environ.get("APP_ID", "REMPAR-DEMO-LOCAL")
TRACKING           = os.environ.get("TRACKING", "")
DEBUG           = os.environ.get("DEBUG", "False")
ENABLE_PMS = os.environ.get("ENABLE_PMS", "false").strip().lower() in ("1", "true", "yes", "on")
TZ = os.getenv("TZ", "Europe/Paris")
APP_TZ = gettz(TZ)

UPLOAD_FOLDER = os.path.join("static", "images")
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif"}

DEMO = os.environ.get("DEMO", "false").strip().lower() in ("1", "true", "yes", "on")

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET", "dev-secret-change-me")

STATE_LOCK = threading.Lock()
TWEETS: List[Dict[str, Any]] = []
MESSAGES: List[Dict[str, Any]] = []
SENT_TWEET_IDS: set[str] = set()
SENT_MESSAGE_IDS: set[str] = set()
RAW_ROWS: List[Dict[str, Any]] = []

# NEW: store parsed "decompte" windows
DECOMPTE_EVENTS: List[Dict[str, Any]] = []  # {start: datetime, end: datetime, minutes: int}

I18N_DIR = Path(__file__).parent / "i18n"
SUPPORTED_LANGS = {"fr", "en"}
DEFAULT_LANG = os.getenv("LANG", "fr").lower()

def detect_lang_from_header() -> str:
    header = (request.headers.get("Accept-Language") or "").lower()
    if header.startswith("en"):
        return "en"
    return DEFAULT_LANG

def get_lang() -> str:
    lang = session.get("language") or request.cookies.get("language")
    if lang in SUPPORTED_LANGS:
        return lang
    return detect_lang_from_header()

# --- File loading with mtime-aware cache (auto reloads when files change) ---
@lru_cache(maxsize=None)
def _read_translation(lang: str, mtime: float) -> dict:
    path = I18N_DIR / f"{lang}.json"
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)

def load_translation(lang: str) -> dict:
    lang = lang if lang in SUPPORTED_LANGS else DEFAULT_LANG
    path = I18N_DIR / f"{lang}.json"
    if not path.exists():
        lang = DEFAULT_LANG
    path = I18N_DIR / f"{lang}.json"
    mtime = path.stat().st_mtime
    return _read_translation(lang, mtime)

@app.before_request
def before_request():
    g.lang = get_lang()
    g.tdict = load_translation(g.lang)

@app.context_processor
def inject_translator():
    def t(key: str, **kwargs):
        text = g.tdict.get(key, key)
        try:
            return text.format(**kwargs) if kwargs else text
        except Exception:
            return text  # don't crash on bad placeholders
    return {
        "t": t,
        "current_lang": lambda: g.lang,
        "now_year": datetime.now().year
    }

@app.route("/set-lang/<lang>")
def set_lang(lang):
    if lang not in SUPPORTED_LANGS:
        lang = DEFAULT_LANG
    session.permanent = True
    session["language"] = lang
    resp = make_response(redirect(request.referrer or url_for("index")))
    resp.set_cookie("language", lang, max_age=60*60*24*365, samesite="Lax")
    return resp





# Make TZ available in all templates
@app.context_processor
def inject_globals():
    return dict(TZ=TZ)

@app.after_request
def add_no_cache_headers(response):
    """Add no-cache headers to all responses."""
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response

def get_active_decompte_end(now: Optional[datetime] = None) -> Optional[datetime]:
    """If a decompte is active (start <= now < end) return its end datetime, else None."""
    if now is None:
        now = datetime.now(tz=APP_TZ)
    with STATE_LOCK:
        for ev in DECOMPTE_EVENTS:
            if ev["start"] <= now < ev["end"]:
                return ev["end"]
    return None

# --- NEW: small helper to format the SSE event for current décompte state
def _sse_decompte_event():
    """
    Returns (event_name, data_str) for SSE:
      - ("decompte", {"target_iso": ...}) when a countdown is active
      - ("decompte_end", {}) when no countdown is active
    """
    end_dt = get_active_decompte_end()
    if end_dt:
        payload = app.json.dumps({"target_iso": end_dt.astimezone(APP_TZ).isoformat()})
        return ("decompte", payload)
    else:
        return ("decompte_end", app.json.dumps({}))

def norm(s: Optional[str]) -> str:
    if s is None:
        return ""
    return unidecode(str(s)).strip()

def parse_horaire(val) -> datetime:
    """
    Parse an Excel 'horaire' cell into a timezone-aware datetime in APP_TZ.

    Accepts:
      - strings like "HH:MM", "HH:MM:SS", "02:15:00 PM"
      - pandas/py datetime objects
      - Excel serial numbers (including time-only fractions)
    For time-only inputs, the date defaults to today (local).
    """
    today = date.today()
    default_dt = datetime.combine(today, datetime.min.time())

    # 1) Pandas/py datetime-like
    if isinstance(val, (datetime, pd.Timestamp)):
        dt = pd.to_datetime(val).to_pydatetime()

    # 2) Excel serials (date+time as days since 1899-12-30; time-only as fraction of a day)
    elif isinstance(val, (int, float)) and not pd.isna(val):
        try:
            # This handles both whole days and fractions (time-only)
            dt = pd.to_datetime(val, unit="D", origin="1899-12-30").to_pydatetime()
        except Exception:
            # Fallback: treat as fraction of day
            secs = int(round(float(val) * 86400)) % 86400
            dt = default_dt + timedelta(seconds=secs)

    # 3) Strings (HH:MM, HH:MM:SS, with/without AM/PM, etc.)
    else:
        txt = str(val).strip()
        if not txt:
            raise ValueError("horaire manquant")

        # dateutil will respect the provided default for missing Y/M/D.
        # dayfirst=True is harmless for time-only; fuzzy helps with stray spaces.
        dt = dtparser.parse(
            txt,
            dayfirst=True,
            default=default_dt,
            fuzzy=True
        )

        # If the parsed date looks like an Excel epoch artifact (e.g., year < 1970)
        # and the input had no explicit date, pin to today but keep time.
        if dt.year < 1970 and not re.search(r"\d{4}-\d{1,2}-\d{1,2}|\d{1,2}/\d{1,2}/\d{2,4}", txt):
            dt = default_dt.replace(hour=dt.hour, minute=dt.minute, second=dt.second, microsecond=dt.microsecond)

    # Ensure timezone-aware in APP_TZ
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=APP_TZ)
    else:
        dt = dt.astimezone(APP_TZ)

    return dt


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route("/upload_image", methods=["POST"])
def upload_image():
    if "image" not in request.files:
        flash("Aucun fichier sélectionné")
        return redirect(url_for("admin"))

    file = request.files["image"]
    if file.filename == "":
        flash("Nom de fichier vide")
        return redirect(url_for("admin"))

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(path)
        flash(f"Image '{filename}' uploadée avec succès.")
    else:
        flash("Format non autorisé. Extensions acceptées : png, jpg, jpeg, gif.")
    return redirect(url_for("admin"))

@app.context_processor
def inject_tracking():
    return dict(TRACKING=TRACKING)

def extract_roles_from_messages() -> None:
    """Extract unique, non-empty destinataires from MESSAGES and sort alphabetically."""
    global ROLES
    with STATE_LOCK:
        roles_set = set()
        for m in MESSAGES:
            dest = m.get("destinataire", "").strip()
            if dest:
                # Split by newline and add each as a separate role
                for role in dest.split('\n'):
                    role = role.strip()
                    if role and role.lower() != "tous":  # Exclude empty and "tous" (broadcast)
                        roles_set.add(role)
        ROLES = sorted(list(roles_set))
    app.logger.info(f"ROLES extracted: {ROLES} ({len(ROLES)} roles found)")

@app.context_processor
def inject_tracking():
    return dict(TRACKING=TRACKING)

def load_pms(file_like) -> None:
    """Load tweets from PMS file."""
    df = pd.read_excel(file_like, engine="openpyxl")
    if df.empty:
        raise ValueError("Fichier PMS vide")

    cols = {unidecode(c).strip().lower(): c for c in df.columns}
    required = ["horaire", "emetteur", "stimuli"]
    missing = [k for k in required if k not in cols]
    if missing:
        raise ValueError(f"Colonnes manquantes dans DPS: {', '.join(missing)}")

    tweets: List[Dict[str, Any]] = []

    for idx, row in df.iterrows():
        try:
            when = parse_horaire(row[cols["horaire"]])
            emet = row[cols["emetteur"]]
            stim = row[cols["stimuli"]]

            tid = f"tw-{int(when.timestamp())}-{idx}"
            tweets.append({
                "id": tid,
                "at": when,
                "emetteur": str(emet).strip() if pd.notna(emet) else "Anonyme",
                "texte": str(stim).strip() if pd.notna(stim) else "",
            })

        except Exception as e:
            raise ValueError(f"PMS Ligne {idx+2}: {e}")

    tweets.sort(key=lambda r: r["at"])

    with STATE_LOCK:
        TWEETS.clear(); TWEETS.extend(tweets)
        SENT_TWEET_IDS.clear()

def load_excel(file_like) -> None:
    """Load Chronogramme (messages, decompte, raw events)."""
    df = pd.read_excel(file_like, engine="openpyxl")
    if df.empty:
        raise ValueError("Fichier Excel vide")

    cols = {unidecode(c).strip().lower(): c for c in df.columns}
    required = ["horaire", "type", "emetteur", "stimuli"]
    missing = [k for k in required if k not in cols]
    if missing:
        raise ValueError(f"Colonnes manquantes: {', '.join(missing)}")

    messages: List[Dict[str, Any]] = []
    raw_rows: List[Dict[str, Any]] = []
    decompte_events: List[Dict[str, Any]] = []

    for idx, row in df.iterrows():
        try:
            typ = norm(row[cols["type"]]).lower()
            # Accept 'message', 'decompte' (skip 'tweet')
            if typ not in {"message", "decompte"}:
                continue

            when = parse_horaire(row[cols["horaire"]])
            emet = row[cols["emetteur"]]
            stim = row[cols["stimuli"]]

            # Keep raw row for animator
            raw = {
                "id": (str(int(row[cols["id"]])).strip() if "id" in cols and pd.notna(row[cols["id"]]) else ""),
                "horaire": row[cols["horaire"]],
                "type": typ,
                "Emetteur": (str(emet).strip() if pd.notna(emet) else ""),
                "Destinataire": (str(row[cols["destinataire"]]).strip() if "destinataire" in cols and pd.notna(row[cols["destinataire"]]) else ""),
                "stimuli": (str(stim).strip() if pd.notna(stim) else ""),
                "reaction attendue": (str(row[cols["reaction attendue"]]).strip() if "reaction attendue" in cols and pd.notna(row[cols["reaction attendue"]]) else ""),
                "commentaire": (str(row[cols["commentaire"]]).strip() if "commentaire" in cols and pd.notna(row[cols["commentaire"]]) else ""),
                "livrable": (str(row[cols["livrable"]]).strip() if "livrable" in cols and pd.notna(row[cols["livrable"]]) else ""),
                "_at": when,
            }
            raw_rows.append(raw)

            if typ == "message":
                mid = raw["id"] or f"msg-{int(when.timestamp())}-{idx}"
                dest = raw["Destinataire"]
                if not dest:
                    raise ValueError("Destinataire manquant pour message")
                messages.append({
                    "id": mid,
                    "at": when,
                    "emetteur": str(emet).strip() if pd.notna(emet) else "",
                    "destinataire": dest,
                    "stimuli": str(stim).strip() if pd.notna(stim) else "",
                })
                continue

            if typ == "decompte":
                # stimuli must contain an integer (minutes)
                stim_txt = str(stim).strip() if pd.notna(stim) else ""
                m = re.search(r"(\d+)", stim_txt)
                if not m:
                    raise ValueError("décompte: 'stimuli' doit contenir le nombre de minutes (ex: 15)")
                minutes = int(m.group(1))
                if minutes <= 0:
                    raise ValueError("décompte: minutes doit être > 0")
                start = when
                end = start + timedelta(minutes=minutes)
                decompte_events.append({
                    "start": start,
                    "end": end,
                    "minutes": minutes
                })
                continue

        except Exception as e:
            raise ValueError(f"Ligne {idx+2}: {e}")

    messages.sort(key=lambda r: r["at"])
    raw_rows.sort(key=lambda r: r["_at"])
    decompte_events.sort(key=lambda r: r["start"])

    with STATE_LOCK:
        MESSAGES.clear(); MESSAGES.extend(messages)
        RAW_ROWS.clear(); RAW_ROWS.extend(raw_rows)
        DECOMPTE_EVENTS.clear(); DECOMPTE_EVENTS.extend(decompte_events)
        SENT_MESSAGE_IDS.clear()

@app.route("/animateur", methods=["GET", "POST"])
def animateur():
    if not session.get("is_animator"):
        if request.method == "POST":
            pwd = request.form.get("password")
            if pwd == ANIMATOR_PASSWORD:
                session["is_animator"] = True
                return redirect(url_for("animateur"))
            else:
                flash("Mot de passe incorrect")
                return redirect(url_for("animateur"))
        return render_template(
            "admin_login.html",
            action=url_for("animateur"),
            prefill_password=(ANIMATOR_PASSWORD if DEMO else "")
        )

    with STATE_LOCK:
        n_tw = len(TWEETS)
        n_msg = len(MESSAGES)

        # méta pour afficher réaction attendue / commentaire par ID
        meta_by_id = {}
        for r in RAW_ROWS:
            if r.get("type") == "message":
                rid = r.get("id", "")
                if rid:
                    meta_by_id[rid] = {
                        "reaction": r.get("reaction attendue", "") or "",
                        "commentaire": r.get("commentaire", "") or "",
                    }

        # timeline = messages uniquement (inclure emetteur/destinataire/stimuli)  # CHANGED
        events = []
        for m in MESSAGES:
            events.append({
                "at": m["at"],  # datetime TZ-aware
                "type": "message",
                "label": f"Message à {m['destinataire']} (de {m['emetteur']})",
                "msg_id": m["id"],
                "emetteur": m.get("emetteur", ""),
                "destinataire": m.get("destinataire", ""),
                "stimuli": m.get("stimuli", ""),
            })
        events.sort(key=lambda e: e["at"])

    # séparation passé / futur
    now = datetime.now(tz=APP_TZ)
    past = [e for e in events if e["at"] < now]
    future = [e for e in events if e["at"] >= now]
    past5 = past[-5:]
    next1 = future[0] if future else None
    next2 = future[1] if len(future) > 1 else None

    # packer au format déjà “digeste” pour le front (ISO + at_ms + champs utiles)  # NEW
    def pack(e):
        if not e:
            return None
        return {
            "id": e["msg_id"],
            "label": e["label"],
            "at": e["at"].isoformat(),
            "at_ms": int(e["at"].timestamp() * 1000),
            "emetteur": e.get("emetteur", ""),
            "destinataire": e.get("destinataire", ""),
            "stimuli": e.get("stimuli", ""),
        }

    past5 = [pack(e) for e in past5]
    next1 = pack(next1)
    next2 = pack(next2)

    return render_template(
        "animateur.html",
        n_tweets=n_tw, n_messages=n_msg,
        past5=past5, next1=next1, next2=next2,
        meta_by_id=meta_by_id,
    )



@app.route("/reset", methods=["GET", "POST"])
def reset():
    if request.method == "POST":
        action = request.form.get("action")
        if action == "yes":
            session.clear()
            resp = make_response(redirect(url_for("index")))
            session_cookie = app.config.get("SESSION_COOKIE_NAME", "session")
            resp.delete_cookie(session_cookie, path='/', samesite='Lax')
            flash("Session réinitialisée.")
            return resp
        else:
            return redirect(url_for("index"))
    return render_template("reset_confirm.html")

@app.route("/")
def index():
    # If a decompte is active, show countdown instead of normal index
    end_dt = get_active_decompte_end()
    if end_dt:
        return render_template("countdown.html", target_iso=end_dt.astimezone(APP_TZ).isoformat())

    with STATE_LOCK:
        n_tw = len(TWEETS)
        n_msg = len(MESSAGES)
        events = [
            {"at": m["at"], "type": "message",
             "label": f"Message à {m['destinataire']} (de {m['emetteur']})"}
            for m in MESSAGES
        ]
        events.sort(key=lambda e: e["at"])

    now = datetime.now(tz=APP_TZ)
    past = [e for e in events if e["at"] < now]
    past5 = past[-5:]

    return render_template(
        "index.html",
        n_tweets=n_tw, n_messages=n_msg,
        past5=past5,
        enable_pms=ENABLE_PMS
    )

@app.route("/admin", methods=["GET", "POST"])
def admin():
    if not session.get("is_admin"):
        if request.method == "POST":
            pwd = request.form.get("password")
            if pwd == ADMIN_PASSWORD:
                session["is_admin"] = True
                return redirect(url_for("admin"))
            else:
                flash("Mot de passe incorrect")
                return redirect(url_for("admin"))
        return render_template("admin_login.html")

    if request.method == "POST":
        # Handle Chronogramme upload
        f = request.files.get("file")
        if f and f.filename and f.filename.lower().endswith((".xlsx", ".xls")):
            try:
                load_excel(f)
                extract_roles_from_messages()  # Extract roles after loading
                flash("Chronogramme chargé avec succès.")
            except Exception as e:
                flash(f"Erreur de chargement Chronogramme: {e}")
            return redirect(url_for("admin"))
        
        # Handle PMS upload
        pms_f = request.files.get("pms_file")
        if pms_f and pms_f.filename and pms_f.filename.lower().endswith((".xlsx", ".xls")):
            try:
                load_pms(pms_f)
                flash("PMS chargé avec succès.")
            except Exception as e:
                flash(f"Erreur de chargement PMS: {e}")
            return redirect(url_for("admin"))
        
        flash("Veuillez sélectionner un fichier Excel (.xlsx/.xls)")
        return redirect(url_for("admin"))

    with STATE_LOCK:
        n_tw = len(TWEETS)
        n_msg = len(MESSAGES)
        events = []
        for t in TWEETS:
            events.append({"at": t["at"], "type": "tweet", "label": f"Tweet de {t['emetteur']}"})
        for m in MESSAGES:
            events.append({"at": m["at"], "type": "message", "label": f"Message à {m['destinataire']} (de {m['emetteur']})"})
        events.sort(key=lambda e: e["at"])

    now = datetime.now(tz=APP_TZ)
    past = [e for e in events if e["at"] < now]
    future = [e for e in events if e["at"] >= now]
    past5 = past[-5:]
    next1 = future[0] if future else None
    next2 = future[1] if len(future) > 1 else None

    return render_template("admin.html",
                           n_tweets=n_tw, n_messages=n_msg,
                           past5=past5, next1=next1, next2=next2,
                           enable_pms=ENABLE_PMS)

@app.route("/socialmedia")
def socialmedia():
    # Force countdown if active
    end_dt = get_active_decompte_end()
    if end_dt:
        return render_template("countdown.html", target_iso=end_dt.astimezone(APP_TZ).isoformat())
    return render_template("socialmedia.html")

@app.route("/messagerie", methods=["GET", "POST"])
def messagerie():
    # Force countdown if active
    end_dt = get_active_decompte_end()
    if end_dt:
        return render_template("countdown.html", target_iso=end_dt.astimezone(APP_TZ).isoformat())

    if request.method == "POST":
        role = request.form.get("role")
        if role not in ROLES:
            flash("Rôle invalide")
            return redirect(url_for("messagerie"))
        session['role'] = role
        return redirect(url_for("messagerie"))
    role = session.get('role')
    return render_template("messagerie.html", roles=ROLES, selected_role=role)

@app.route("/animateur_upcoming")
def animateur_upcoming():
    """
    Return the next upcoming messages (not yet due), regardless of time.
    Query params:
      - limit (int, default 3): how many future items to return
    """
    try:
        limit = int(request.args.get("limit", "3"))
    except ValueError:
        limit = 3

    now = datetime.now(tz=APP_TZ)
    out = []
    with STATE_LOCK:
        # build meta map once
        meta = {}
        for r in RAW_ROWS:
            if r.get("type") == "message":
                rid = r.get("id", "")
                if rid:
                    meta[rid] = {
                        "reaction": r.get("reaction attendue", "") or "",
                        "commentaire": r.get("commentaire", "") or "",
                    }

        future = [m for m in MESSAGES if m["at"] >= now]
        future.sort(key=lambda m: m["at"])
        for m in future[:max(1, limit)]:
            mm = meta.get(m["id"], {"reaction": "", "commentaire": ""})
            out.append({
                "id": m["id"],
                "label": f"Message à {m.get('destinataire','')} (de {m.get('emetteur','')})",
                "at": m["at"].isoformat(),
                "at_ms": int(m["at"].timestamp() * 1000),
                "emetteur": m.get("emetteur", ""),          # NEW
                "destinataire": m.get("destinataire", ""),  # NEW
                "stimuli": m.get("stimuli", ""),            # NEW
                "reaction": mm["reaction"],
                "commentaire": mm["commentaire"],
            })

    return app.response_class(app.json.dumps(out), mimetype="application/json")

@app.route("/stream_animateur")
def stream_animateur():
    """
    Streams *messages only* (stimuli) for the animator timeline, with metadata.
    On connect: sends all past-due messages (once).
    Then: streams each message at its due time.
    """
    def build_meta_by_id():
        meta = {}
        # Build once per emission window to avoid holding the lock too long
        with STATE_LOCK:
            for r in RAW_ROWS:
                if r.get("type") == "message":
                    rid = r.get("id", "")
                    if rid:
                        meta[rid] = {
                            "reaction": r.get("reaction attendue", "") or "",
                            "commentaire": r.get("commentaire", "") or "",
                        }
        return meta

    def gen():
        yield "event: ping\ndata: {}\n\n"
        sent_ids = set()
        meta_by_id = build_meta_by_id()

        # 1) Send all past-due messages on connect
        now = datetime.now(tz=APP_TZ)
        due = []
        with STATE_LOCK:
            for m in MESSAGES:
                if m["id"] in sent_ids:
                    continue
                if m["at"] <= now:
                    meta = meta_by_id.get(m["id"], {"reaction": "", "commentaire": ""})
                    due.append({
                        "id": m["id"],
                        "label": f"Message à {m.get('destinataire','')} (de {m.get('emetteur','')})",
                        "at": m["at"].isoformat(),
                        "at_ms": int(m["at"].timestamp() * 1000),
                        "emetteur": m.get("emetteur",""),          # NEW
                        "destinataire": m.get("destinataire",""),  # NEW
                        "stimuli": m.get("stimuli",""),            # NEW
                        "reaction": meta.get("reaction",""),
                        "commentaire": meta.get("commentaire",""),
                    })
                    sent_ids.add(m["id"])
        if due:
            payload = app.json.dumps(due)
            yield f"event: animateur\ndata: {payload}\n\n"

        # 2) Stream new messages as they become due
        while True:
            now = datetime.now(tz=APP_TZ)
            due = []
            meta_by_id = build_meta_by_id()
            with STATE_LOCK:
                for m in MESSAGES:
                    if m["id"] in sent_ids:
                        continue
                    if m["at"] <= now:
                        meta = meta_by_id.get(m["id"], {"reaction": "", "commentaire": ""})
                        due.append({
                            "id": m["id"],
                            "label": f"Message à {m.get('destinataire','')} (de {m.get('emetteur','')})",
                            "at": m["at"].isoformat(),
                            "at_ms": int(m["at"].timestamp() * 1000),
                            "emetteur": m.get("emetteur",""),          # NEW
                            "destinataire": m.get("destinataire",""),  # NEW
                            "stimuli": m.get("stimuli",""),            # NEW
                            "reaction": meta.get("reaction",""),
                            "commentaire": meta.get("commentaire",""),
                        })
                        sent_ids.add(m["id"])
            if due:
                payload = app.json.dumps(due)
                yield f"event: animateur\ndata: {payload}\n\n"
            time.sleep(1)

    return app.response_class(gen(), mimetype="text/event-stream")

@app.route("/stream_tweets")
def stream_tweets():
    def gen():
        yield "event: ping\ndata: {}\n\n"

        # Send decompte state on connect
        ev, data = _sse_decompte_event()
        yield f"event: {ev}\ndata: {data}\n\n"

        sent_ids = set()
        last_decompte_key = None  # track state changes

        # Send past tweets
        now = datetime.now(tz=APP_TZ)
        due = []
        with STATE_LOCK:
            for t in TWEETS:
                if t["id"] in sent_ids:
                    continue
                if t["at"] <= now:
                    due.append({
                        "id": t["id"],
                        "emetteur": t["emetteur"],
                        "texte": t["texte"],
                        "at": t["at"].isoformat(),
                        "at_ms": int(t["at"].timestamp() * 1000),
                    })
                    sent_ids.add(t["id"])
        if due:
            payload = app.json.dumps(due)
            yield f"event: tweet\ndata: {payload}\n\n"

        # Stream new tweets + decompte state changes
        while True:
            # Emit decompte updates if changed
            end_dt = get_active_decompte_end()
            key = end_dt.isoformat() if end_dt else "none"
            if key != last_decompte_key:
                last_decompte_key = key
                ev, data = _sse_decompte_event()
                yield f"event: {ev}\ndata: {data}\n\n"

            now = datetime.now(tz=APP_TZ)
            due = []
            with STATE_LOCK:
                for t in TWEETS:
                    if t["id"] in sent_ids:
                        continue
                    if t["at"] <= now:
                        due.append({
                            "id": t["id"],
                            "emetteur": t["emetteur"],
                            "texte": t["texte"],
                            "at": t["at"].isoformat(),
                            "at_ms": int(t["at"].timestamp() * 1000),
                        })
                        sent_ids.add(t["id"])
            if due:
                payload = app.json.dumps(due)
                yield f"event: tweet\ndata: {payload}\n\n"
            time.sleep(1)
    return app.response_class(gen(), mimetype="text/event-stream")

@app.route("/stream_messages")
def stream_messages():
    role = request.args.get('role')

    def is_for_role(m, role):
        dest = (m.get("destinataire") or "").strip()
        if not role:
            return True
        if dest.casefold() == "tous":
            return True
        # Handle multiple destinataires separated by newline
        for d in dest.split('\n'):
            d = d.strip()
            if d == role:
                return True
        return False

    def gen():
        yield "event: ping\ndata: {}\n\n"

        # Send decompte state on connect
        ev, data = _sse_decompte_event()
        yield f"event: {ev}\ndata: {data}\n\n"

        sent_ids = set()
        last_decompte_key = None

        # past messages
        now = datetime.now(tz=APP_TZ)
        due = []
        with STATE_LOCK:
            for m in MESSAGES:
                if m["id"] in sent_ids:
                    continue
                if m["at"] <= now and is_for_role(m, role):
                    due.append({
                        "id": m["id"],
                        "emetteur": m["emetteur"],
                        "destinataire": m.get("destinataire", ""),
                        "stimuli": m["stimuli"],
                        "at": m["at"].isoformat(),
                        "at_ms": int(m["at"].timestamp()*1000),
                    })
                    sent_ids.add(m["id"])
        if due:
            payload = app.json.dumps(due)
            yield f"event: message\ndata: {payload}\n\n"

        # new messages + decompte changes
        while True:
            # Emit decompte updates if changed
            end_dt = get_active_decompte_end()
            key = end_dt.isoformat() if end_dt else "none"
            if key != last_decompte_key:
                last_decompte_key = key
                ev, data = _sse_decompte_event()
                yield f"event: {ev}\ndata: {data}\n\n"

            now = datetime.now(tz=APP_TZ)
            due = []
            with STATE_LOCK:
                for m in MESSAGES:
                    if m["id"] in sent_ids:
                        continue
                    if m["at"] <= now and is_for_role(m, role):
                        due.append({
                            "id": m["id"],
                            "emetteur": m["emetteur"],
                            "destinataire": m.get("destinataire", ""),
                            "stimuli": m["stimuli"],
                            "at": m["at"].isoformat(),
                            "at_ms": int(m["at"].timestamp()*1000),
                        })
                        sent_ids.add(m["id"])
            if due:
                payload = app.json.dumps(due)
                yield f"event: message\ndata: {payload}\n\n"
            time.sleep(1)
    return app.response_class(gen(), mimetype='text/event-stream')


@app.route("/observateur", methods=["GET", "POST"])
def observateur():
    # Gate with password unless already authenticated in this session
    if not session.get("is_observer"):
        if request.method == "POST":
            pwd = request.form.get("password", "")
            if pwd == OBSERVER_PASSWORD:
                session["is_observer"] = True
                return redirect(url_for("observateur"))
            else:
                flash("Mot de passe incorrect")
                return redirect(url_for("observateur"))
        # GET: show login, prefill password in demo mode
        return render_template(
            "admin_login.html",
            action=url_for("observateur"),
            prefill_password=(OBSERVER_PASSWORD if DEMO else "")
        )

    # ---- authenticated: render your observateur page (notes) ----
    # Build the same context you already use (past3/next1/next2/APP_ID, etc.)
    # Example skeleton:
    now = datetime.now(tz=APP_TZ)
    with STATE_LOCK:
        future_msgs = sorted([m for m in MESSAGES if m["at"] >= now], key=lambda m: m["at"])
        past_msgs   = sorted([m for m in MESSAGES if m["at"] <  now], key=lambda m: m["at"])

    past3 = [
        {
            "id": m["id"],
            "at": m["at"].isoformat(),
            "at_ms": int(m["at"].timestamp() * 1000),
            "emetteur": m.get("emetteur",""),
            "destinataire": m.get("destinataire",""),
            "stimuli": m.get("stimuli",""),
            "label": f"Message à {m.get('destinataire','')} (de {m.get('emetteur','')})",
        }
        # for m in past_msgs[-3:]
        for m in past_msgs
    ]
    next1 = None
    next2 = None
    if future_msgs:
        m0 = future_msgs[0]
        next1 = {
            "id": m0["id"],
            "at": m0["at"].isoformat(),
            "at_ms": int(m0["at"].timestamp() * 1000),
            "emetteur": m0.get("emetteur",""),
            "destinataire": m0.get("destinataire",""),
            "stimuli": m0.get("stimuli",""),
            "label": f"Message à {m0.get('destinataire','')} (de {m0.get('emetteur','')})",
        }
        if len(future_msgs) > 1:
            m1 = future_msgs[1]
            next2 = {
                "id": m1["id"],
                "at": m1["at"].isoformat(),
                "at_ms": int(m1["at"].timestamp() * 1000),
                "emetteur": m1.get("emetteur",""),
                "destinataire": m1.get("destinataire",""),
                "stimuli": m1.get("stimuli",""),
                "label": f"Message à {m1.get('destinataire','')} (de {m1.get('emetteur','')})",
            }

    return render_template(
        "observateur.html",
        past3=past3,
        next1=next1,
        next2=next2,
        APP_ID=APP_ID,
    )


@app.route("/messagerie/change", methods=["POST", "GET"])
def messagerie_change():
    session.pop("role", None)
    return redirect(url_for("messagerie"))

os.makedirs(os.path.dirname(CHRONOGRAMME), exist_ok=True)
if ENABLE_PMS:
    os.makedirs(os.path.dirname(PMS), exist_ok=True)

# Load Chronogramme (messages, decompte, raw events)
if os.path.exists(CHRONOGRAMME):
    try:
        with open(CHRONOGRAMME, 'rb') as f:
            load_excel(f)
        extract_roles_from_messages()  # Extract roles after loading
    except Exception as e:
        app.logger.warning(f"Impossible de charger {CHRONOGRAMME}: {e}")

# Load PMS (tweets) - only if ENABLE_PMS is True
if ENABLE_PMS and os.path.exists(PMS):
    try:
        with open(PMS, 'rb') as f:
            load_pms(f)
    except Exception as e:
        app.logger.warning(f"Impossible de charger {PMS}: {e}")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=DEBUG)
