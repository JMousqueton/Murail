#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations
import io
import os
import re
import threading
import time
from datetime import datetime, date, timedelta
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

load_dotenv()

APP_TZ = gettz("Europe/Paris")
ROLES = [
    "Communication", "Décision", "Informatique",
    "Juridique / Finance", "Ressources Humaines",
    "Métier"
]

DATA_PATH = os.environ.get("SCENARIO_XLSX", os.path.join("Sample", "chronogramme.xlsx"))
ADMIN_PASSWORD     = os.environ.get("ADMIN_PASSWORD", "changeme_admin")
OBSERVER_PASSWORD  = os.environ.get("OBSERVER_PASSWORD", "changeme_observer")
APP_ID             = os.environ.get("APP_ID", "REMPAR-DEMO-LOCAL")
TRACKING           = os.environ.get("TRACKING", "")

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
    if isinstance(val, (datetime, pd.Timestamp)):
        dt = pd.to_datetime(val).to_pydatetime()
    else:
        txt = str(val).strip()
        if not txt:
            raise ValueError("horaire manquant")
        dt = dtparser.parse(txt, dayfirst=True, default=datetime.combine(date.today(), datetime.min.time()))
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

def load_excel(file_like) -> None:
    df = pd.read_excel(file_like, engine="openpyxl")
    if df.empty:
        raise ValueError("Fichier Excel vide")

    cols = {unidecode(c).strip().lower(): c for c in df.columns}
    required = ["horaire", "type", "emetteur", "stimuli"]
    missing = [k for k in required if k not in cols]
    if missing:
        raise ValueError(f"Colonnes manquantes: {', '.join(missing)}")

    tweets: List[Dict[str, Any]] = []
    messages: List[Dict[str, Any]] = []
    raw_rows: List[Dict[str, Any]] = []
    decompte_events: List[Dict[str, Any]] = []  # NEW

    for idx, row in df.iterrows():
        try:
            typ = norm(row[cols["type"]]).lower()
            # Accept 'tweet', 'message', 'decompte'
            if typ not in {"tweet", "message", "decompte"}:
                continue

            when = parse_horaire(row[cols["horaire"]])
            emet = row[cols["emetteur"]]
            stim = row[cols["stimuli"]]

            # Keep raw row for observer
            raw = {
                "id": (str(row[cols["id"]]).strip() if "id" in cols and pd.notna(row[cols["id"]]) else ""),
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

            if typ == "tweet":
                tid = f"tw-{int(when.timestamp())}-{idx}"
                tweets.append({
                    "id": tid,
                    "at": when,
                    "emetteur": str(emet).strip() if pd.notna(emet) else "Anonyme",
                    "texte": str(stim).strip() if pd.notna(stim) else "",
                })
                continue

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

    tweets.sort(key=lambda r: r["at"])
    messages.sort(key=lambda r: r["at"])
    raw_rows.sort(key=lambda r: r["_at"])
    decompte_events.sort(key=lambda r: r["start"])

    with STATE_LOCK:
        TWEETS.clear(); TWEETS.extend(tweets)
        MESSAGES.clear(); MESSAGES.extend(messages)
        RAW_ROWS.clear(); RAW_ROWS.extend(raw_rows)
        DECOMPTE_EVENTS.clear(); DECOMPTE_EVENTS.extend(decompte_events)  # NEW
        SENT_TWEET_IDS.clear(); SENT_MESSAGE_IDS.clear()

@app.route("/observateur", methods=["GET", "POST"])
def observateur():
    if not session.get("is_observer"):
        if request.method == "POST":
            pwd = request.form.get("password")
            if pwd == OBSERVER_PASSWORD:
                session["is_observer"] = True
                return redirect(url_for("observateur"))
            else:
                flash("Mot de passe incorrect")
                return redirect(url_for("observateur"))
        return render_template(
            "admin_login.html",
            action=url_for("observateur"),
            prefill_password=(OBSERVER_PASSWORD if DEMO else "")
        )

    with STATE_LOCK:
        n_tw = len(TWEETS)
        n_msg = len(MESSAGES)

        meta_by_id = {}
        for r in RAW_ROWS:
            if r.get("type") == "message":
                rid = r.get("id", "")
                if rid:
                    meta_by_id[rid] = {
                        "reaction": r.get("reaction attendue", ""),
                        "commentaire": r.get("commentaire", "")
                    }

        events = []
        for m in MESSAGES:
            events.append({
                "at": m["at"],
                "type": "message",
                "label": f"Message à {m['destinataire']} (de {m['emetteur']})",
                "msg_id": m["id"],
            })
        events.sort(key=lambda e: e["at"])

    now = datetime.now(tz=APP_TZ)
    past = [e for e in events if e["at"] < now]
    future = [e for e in events if e["at"] >= now]
    past5 = past[-5:]
    next1 = future[0] if future else None
    next2 = future[1] if len(future) > 1 else None

    return render_template(
        "observateur.html",
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
        past5=past5
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
        f = request.files.get("file")
        if not f or not f.filename.lower().endswith((".xlsx", ".xls")):
            flash("Veuillez sélectionner un fichier Excel (.xlsx/.xls)")
            return redirect(url_for("admin"))
        try:
            load_excel(f)
            flash("Fichier chargé avec succès.")
        except Exception as e:
            flash(f"Erreur de chargement : {e}")
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
                           past5=past5, next1=next1, next2=next2)

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
        return (not role) or dest == role or dest.casefold() == "tous"

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

@app.route("/messagerie/change", methods=["POST", "GET"])
def messagerie_change():
    session.pop("role", None)
    return redirect(url_for("messagerie"))

os.makedirs(os.path.dirname(DATA_PATH), exist_ok=True)
if os.path.exists(DATA_PATH):
    try:
        with open(DATA_PATH, 'rb') as f:
            load_excel(f)
    except Exception as e:
        app.logger.warning(f"Impossible de charger {DATA_PATH}: {e}")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=True)
