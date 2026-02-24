from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional
from functools import wraps

from flask import Flask, render_template, request, abort, url_for, redirect, session
from pathlib import Path
import json

from validation import (
    validate_payment_form,
    is_account_locked,
    register_failed_attempt,
    register_successful_login,
    has_role,                 # ✅ RBAC
)

app = Flask(__name__)
app.config["TEMPLATES_AUTO_RELOAD"] = True
app.secret_key = "dev-secret-change-me"


BASE_DIR = Path(__file__).resolve().parent
EVENTS_PATH = BASE_DIR / "data" / "events.json"
USERS_PATH = BASE_DIR / "data" / "users.json"
ORDERS_PATH = BASE_DIR / "data" / "orders.json"

CATEGORIES = ["All", "Music", "Tech", "Sports", "Business"]
CITIES = ["Any", "New York", "San Francisco", "Berlin", "London", "Oakland", "San Jose"]


# ==================================================
# AUTH DECORATORS
# ==================================================

def get_current_user() -> Optional[dict]:
    email = session.get("user_email")
    if not email:
        return None
    return find_user_by_email(email)


def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not get_current_user():
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return wrapper


def admin_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        user = get_current_user()
        if not user or not has_role(user, "admin"):
            abort(403)
        return f(*args, **kwargs)
    return wrapper


# ==================================================
# MODELO EVENTO
# ==================================================

@dataclass(frozen=True)
class Event:
    id: int
    title: str
    category: str
    city: str
    venue: str
    start: datetime
    end: datetime
    price_usd: float
    available_tickets: int
    banner_url: str
    description: str


# ==================================================
# DATA ACCESS
# ==================================================

def load_events() -> List[Event]:
    data = json.loads(EVENTS_PATH.read_text(encoding="utf-8"))
    return [
        Event(
            id=int(e["id"]),
            title=e["title"],
            category=e["category"],
            city=e["city"],
            venue=e["venue"],
            start=datetime.fromisoformat(e["start"]),
            end=datetime.fromisoformat(e["end"]),
            price_usd=float(e["price_usd"]),
            available_tickets=int(e["available_tickets"]),
            banner_url=e.get("banner_url", ""),
            description=e.get("description", ""),
        )
        for e in data
    ]


def load_users() -> list[dict]:
    if not USERS_PATH.exists():
        USERS_PATH.parent.mkdir(parents=True, exist_ok=True)
        USERS_PATH.write_text("[]", encoding="utf-8")
    return json.loads(USERS_PATH.read_text(encoding="utf-8"))


def save_users(users: list[dict]) -> None:
    USERS_PATH.write_text(json.dumps(users, indent=2), encoding="utf-8")


def find_user_by_email(email: str) -> Optional[dict]:
    users = load_users()
    email_norm = (email or "").strip().lower()
    for u in users:
        if (u.get("email", "") or "").strip().lower() == email_norm:
            return u
    return None


def load_orders() -> list[dict]:
    if not ORDERS_PATH.exists():
        ORDERS_PATH.parent.mkdir(parents=True, exist_ok=True)
        ORDERS_PATH.write_text("[]", encoding="utf-8")
    return json.loads(ORDERS_PATH.read_text(encoding="utf-8"))


def save_orders(orders: list[dict]) -> None:
    ORDERS_PATH.write_text(json.dumps(orders, indent=2), encoding="utf-8")


def next_order_id(orders: list[dict]) -> int:
    return max([o.get("id", 0) for o in orders], default=0) + 1


# ==================================================
# ROUTES
# ==================================================

@app.get("/")
def index():
    events = load_events()
    return render_template("index.html", events=events)


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")

    email = request.form.get("email", "")
    password = request.form.get("password", "")

    email_norm = email.strip().lower()

    locked, seconds = is_account_locked(email_norm)
    if locked:
        return render_template(
            "login.html",
            error=f"Account locked. Try again in {seconds} seconds."
        ), 403

    user = find_user_by_email(email)
    if not user or user.get("password") != password:
        register_failed_attempt(email_norm)
        return render_template(
            "login.html",
            error="Invalid credentials."
        ), 401

    register_successful_login(email_norm)
    session["user_email"] = email_norm

    return redirect(url_for("dashboard"))


@app.get("/dashboard")
@login_required
def dashboard():
    user = get_current_user()
    return render_template("dashboard.html", user_name=user.get("full_name"))


@app.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    user = get_current_user()
    return render_template("profile.html", user=user)


@app.route("/checkout/<int:event_id>", methods=["GET", "POST"])
@login_required
def checkout(event_id: int):
    events = load_events()
    event = next((e for e in events if e.id == event_id), None)
    if not event:
        abort(404)

    if request.method == "POST":
        clean, errors = validate_payment_form(
            request.form.get("card_number", ""),
            request.form.get("exp_date", ""),
            request.form.get("cvv", ""),
            request.form.get("name_on_card", ""),
            request.form.get("billing_email", "")
        )

        if errors:
            return render_template("checkout.html", errors=errors), 400

        orders = load_orders()
        orders.append({
            "id": next_order_id(orders),
            "user_email": get_current_user()["email"],
            "event_id": event.id,
            "status": "PAID",
            "created_at": datetime.utcnow().isoformat(),
        })
        save_orders(orders)

        return redirect(url_for("dashboard"))

    return render_template("checkout.html", event=event)


# ==================================================
# ADMIN ROUTES (PROTECTED)
# ==================================================

@app.get("/admin/users")
@admin_required
def admin_users():
    users = load_users()
    return render_template("admin_users.html", users=users)


@app.post("/admin/users/<int:user_id>/toggle")
@admin_required
def admin_toggle_user(user_id: int):
    users = load_users()
    for u in users:
        if int(u.get("id", 0)) == user_id:
            u.setdefault("status", "active")
            u["status"] = "disabled" if u["status"] == "active" else "active"
            break
    save_users(users)
    return redirect(url_for("admin_users"))


@app.post("/admin/users/<int:user_id>/role")
@admin_required
def admin_change_role(user_id: int):
    new_role = request.form.get("role", "user")
    users = load_users()
    for u in users:
        if int(u.get("id", 0)) == user_id:
            u["role"] = new_role
            break
    save_users(users)
    return redirect(url_for("admin_users"))


if __name__ == "__main__":
    app.run(debug=True)