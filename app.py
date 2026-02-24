from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional, Dict

from flask import Flask, render_template, request, abort, url_for, redirect, session
from pathlib import Path
import json

from validation import (
    validate_payment_form,
    validate_full_name,
    validate_email,
    validate_phone,
    validate_password,
    validate_password_confirmation,
    validate_login_input,
    is_account_locked,
    register_failed_attempt,
    register_successful_login,
    has_role
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


def _user_with_defaults(u: dict) -> dict:
    u = dict(u)
    u.setdefault("role", "user")      
    u.setdefault("status", "active")  
    u.setdefault("locked_until", "") 
    return u


def get_current_user() -> Optional[dict]:
    email = session.get("user_email")
    if not email:
        return None
    return find_user_by_email(email)


# ==================================================
# USERS
# ==================================================

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


def user_exists(email: str) -> bool:
    return find_user_by_email(email) is not None


# ==================================================
# LOGIN
# ==================================================

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        registered = request.args.get("registered")
        msg = "Account created successfully. Please sign in." if registered == "1" else None
        return render_template("login.html", info_message=msg)

    email = request.form.get("email", "")
    password = request.form.get("password", "")

    clean, errors = validate_login_input(email, password)

    if errors:
        return render_template(
            "login.html",
            error="Invalid credentials.",
            field_errors={"email": " ", "password": " "},
            form={"email": email},
        ), 400

    email_norm = clean["email"]

    locked, seconds = is_account_locked(email_norm)
    if locked:
        return render_template(
            "login.html",
            error=f"Account locked. Try again in {seconds} seconds.",
            field_errors={"email": " ", "password": " "},
            form={"email": email},
        ), 403

    user = find_user_by_email(email_norm)

    if not user or user.get("password") != password:
        register_failed_attempt(email_norm)
        return render_template(
            "login.html",
            error="Invalid credentials.",
            field_errors={"email": " ", "password": " "},
            form={"email": email},
        ), 401

    register_successful_login(email_norm)
    session["user_email"] = email_norm

    return redirect(url_for("dashboard"))


# ==================================================
# REGISTER 
# ==================================================

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template("register.html")

    full_name = request.form.get("full_name", "")
    email = request.form.get("email", "")
    phone = request.form.get("phone", "")
    password = request.form.get("password", "")
    confirm_password = request.form.get("confirm_password", "")

    field_errors = {}

    name_clean, err = validate_full_name(full_name)
    if err:
        field_errors["full_name"] = err

    email_clean, err = validate_email(email)
    if err:
        field_errors["email"] = err
    elif user_exists(email_clean):
        field_errors["email"] = "Email already registered."

    phone_clean, err = validate_phone(phone)
    if err:
        field_errors["phone"] = err

    password_clean, err = validate_password(password, email_clean if not err else "")
    if err:
        field_errors["password"] = err

    _, err = validate_password_confirmation(password, confirm_password)
    if err:
        field_errors["confirm_password"] = err

    if field_errors:
        return render_template(
            "register.html",
            field_errors=field_errors,
            form=request.form
        ), 400

    users = load_users()
    next_id = (max([u.get("id", 0) for u in users], default=0) + 1)

    users.append({
        "id": next_id,
        "full_name": name_clean,
        "email": email_clean,
        "phone": phone_clean,
        "password": password_clean,
        "role": "user",
        "status": "active",
    })

    save_users(users)

    return redirect(url_for("login", registered="1"))


# ==================================================
# AUTORIZACIÓN CORREGIDA 
# ==================================================

@app.get("/dashboard")
def dashboard():
    user = get_current_user()
    if not user:
        abort(403)

    paid = request.args.get("paid") == "1"
    return render_template("dashboard.html", user_name=user.get("full_name", "User"), paid=paid)


@app.route("/profile", methods=["GET", "POST"])
def profile():
    user = get_current_user()
    if not user:
        abort(403)

    return render_template("profile.html")
if __name__ == "__main__":
    app.run(debug=True)
