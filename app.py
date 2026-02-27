from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import List, Optional

from flask import Flask, render_template, request, abort, url_for, redirect, session
from pathlib import Path
import json
from time import time


SESSION_TIMEOUT = 30 

from validation import (
    validate_payment_form,
    is_account_locked,
    register_failed_attempt,
    register_successful_login,
    validate_full_name,
    validate_email,
    validate_phone,
    validate_password,
    validate_password_confirmation,
    validate_login_input,
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


EVENTS: List[Event] = load_events()


def _parse_date(date_str: str) -> Optional[datetime]:
    if not date_str:
        return None
    try:
        return datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        return None


def _safe_int(value: str, default: int = 1, min_v: int = 1, max_v: int = 10) -> int:
    try:
        n = int(value)
    except (TypeError, ValueError):
        return default
    return max(min_v, min(max_v, n))


def filter_events(
    q: str = "",
    city: str = "Any",
    date: Optional[datetime] = None,
    category: str = "All",
) -> List[Event]:
    q_norm = (q or "").strip().lower()
    city_norm = (city or "Any").strip()
    category_norm = (category or "All").strip()

    results = load_events()

    if category_norm != "All":
        results = [e for e in results if e.category == category_norm]

    if city_norm != "Any":
        results = [e for e in results if e.city == city_norm]

    if date:
        results = [e for e in results if e.start.date() == date.date()]

    if q_norm:
        results = [
            e for e in results
            if q_norm in e.title.lower() or q_norm in e.venue.lower()
        ]

    results.sort(key=lambda e: e.start)
    return results


def get_event_or_404(event_id: int) -> Event:
    for e in EVENTS:
        if e.id == event_id:
            return e
    abort(404)


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


def load_orders() -> list[dict]:
    if not ORDERS_PATH.exists():
        ORDERS_PATH.parent.mkdir(parents=True, exist_ok=True)
        ORDERS_PATH.write_text("[]", encoding="utf-8")
    return json.loads(ORDERS_PATH.read_text(encoding="utf-8"))


def save_orders(orders: list[dict]) -> None:
    ORDERS_PATH.write_text(json.dumps(orders, indent=2), encoding="utf-8")


def next_order_id(orders: list[dict]) -> int:
    return max([o.get("id", 0) for o in orders], default=0) + 1


def _field_msg(field: str) -> str:
    msgs = {
        "full_name": "Nombre inválido: 2–60 caracteres; solo letras (incluye acentos), espacios, apóstrofes y guiones.",
        "email": "Correo inválido: máximo 254 caracteres, un solo @ y dominio con al menos un punto.",
        "phone": "Teléfono inválido: solo dígitos, longitud entre 7 y 15, sin espacios ni símbolos.",
        "password": "Contraseña inválida: 8–64, con mayúscula, minúscula, número y caracter especial; sin espacios; distinta al correo.",
        "confirm_password": "La confirmación no coincide con la contraseña.",
        "current_password": "Contraseña actual incorrecta.",
        "new_password": "Nueva contraseña inválida: 8–64, con mayúscula, minúscula, número y caracter especial; sin espacios; distinta al correo.",
        "confirm_new_password": "La confirmación de la nueva contraseña no coincide.",
    }
    return msgs.get(field, "Campo inválido.")

def is_session_expired():
    login_at = session.get("login_at")
    if not login_at:
        return True
    return (time() - login_at) > SESSION_TIMEOUT

@app.before_request
def enforce_session_timeout():
    protected_paths = ("/dashboard", "/checkout", "/admin_users", "/profile", "/admin", )

    if request.path.startswith(protected_paths):
        if "user_email" not in session or is_session_expired():
            session.clear()
            return redirect(url_for("login"))


@app.get("/")
def index():
    q = request.args.get("q", "")
    city = request.args.get("city", "Any")
    date_str = request.args.get("date", "")
    category = request.args.get("category", "All")

    date = _parse_date(date_str)
    events = filter_events(q=q, city=city, date=date, category=category)

    featured = events[:3]
    upcoming = events[:6]

    return render_template(
        "index.html",
        q=q,
        city=city,
        date_str=date_str,
        category=category,
        categories=CATEGORIES,
        cities=CITIES,
        featured=featured,
        upcoming=upcoming,
    )


@app.get("/event/<int:event_id>")
def event_detail(event_id: int):
    event = next((e for e in load_events() if e.id == event_id), None)
    if not event:
        abort(404)

    similar = [e for e in EVENTS if e.category == event.category and e.id != event.id][:5]

    return render_template(
        "event_detail.html",
        event=event,
        similar=similar,
    )


@app.post("/event/<int:event_id>/buy")
def buy_ticket(event_id: int):
    event = get_event_or_404(event_id)
    qty = _safe_int(request.form.get("qty", "1"), default=1, min_v=1, max_v=8)

    if qty > event.available_tickets:
        similar = [e for e in load_events() if e.category == event.category and e.id != event.id][:5]
        return render_template(
            "event_detail.html",
            event=event,
            similar=similar,
            buy_error="Not enough tickets available for that quantity."
        ), 400

    return redirect(url_for("checkout", event_id=event.id, qty=qty))


from time import time

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        registered = request.args.get("registered")
        msg = "Cuenta creada correctamente. Inicia sesión." if registered == "1" else None
        return render_template("login.html", info_message=msg, field_errors={}, form={})

    email_raw = request.form.get("email", "")
    password_raw = request.form.get("password", "")

    clean, errors = validate_login_input(email_raw, password_raw)

    if errors:
        return render_template(
            "login.html",
            error="Credenciales inválidas.",
            field_errors={"email": " ", "password": " "},
            form={"email": email_raw},
        ), 400

    email_clean = clean["email"]

    locked, seconds = is_account_locked(email_clean)
    if locked:
        return render_template(
            "login.html",
            error=f"Cuenta bloqueada. Intenta nuevamente en {seconds} segundos.",
            field_errors={"email": " ", "password": " "},
            form={"email": email_raw},
        ), 403

    user = find_user_by_email(email_clean)
    if not user or user.get("password") != password_raw:
        register_failed_attempt(email_clean)
        return render_template(
            "login.html",
            error="Credenciales inválidas.",
            field_errors={"email": " ", "password": " "},
            form={"email": email_raw},
        ), 401

    
    register_successful_login(email_clean)

    session["user_email"] = email_clean
    session["login_at"] = time()   

    return redirect(url_for("dashboard"))

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template("register.html", field_errors={}, form={})

    full_name_raw = request.form.get("full_name", "")
    email_raw = request.form.get("email", "")
    phone_raw = request.form.get("phone", "")
    password_raw = request.form.get("password", "")
    confirm_raw = request.form.get("confirm_password", "")

    field_errors: dict[str, str] = {}
    clean: dict[str, str] = {}

    full_name_clean, err = validate_full_name(full_name_raw)
    if err:
        field_errors["full_name"] = _field_msg("full_name")
    else:
        clean["full_name"] = full_name_clean

    email_clean, err = validate_email(email_raw)
    if err:
        field_errors["email"] = _field_msg("email")
    else:
        if user_exists(email_clean):
            field_errors["email"] = "Este correo ya está registrado. Intenta iniciar sesión."
        else:
            clean["email"] = email_clean

    phone_clean, err = validate_phone(phone_raw)
    if err:
        field_errors["phone"] = _field_msg("phone")
    else:
        clean["phone"] = phone_clean

    email_for_pw = clean.get("email", "")
    password_clean, err = validate_password(password_raw, email=email_for_pw)
    if err:
        field_errors["password"] = _field_msg("password")
    else:
        clean["password"] = password_clean

    if "password" in clean:
        _, err = validate_password_confirmation(clean["password"], confirm_raw)
        if err:
            field_errors["confirm_password"] = _field_msg("confirm_password")

    if field_errors:
        return render_template(
            "register.html",
            error="Por favor corrige los campos marcados.",
            field_errors=field_errors,
            form={"full_name": full_name_raw, "email": email_raw, "phone": phone_raw},
        ), 400

    users = load_users()
    next_id = (max([u.get("id", 0) for u in users], default=0) + 1)

    users.append({
        "id": next_id,
        "full_name": clean["full_name"],
        "email": clean["email"],
        "phone": clean["phone"],
        "password": clean["password"],
        "role": "user",
        "status": "active",
        "locked_until": "",
    })

    save_users(users)
    return redirect(url_for("login", registered="1"))


@app.get("/dashboard")
def dashboard():
    paid = request.args.get("paid") == "1"
    user = get_current_user()
    return render_template("dashboard.html", user_name=(user.get("full_name") if user else "User"), paid=paid)


@app.route("/checkout/<int:event_id>", methods=["GET", "POST"])
def checkout(event_id: int):
    events = load_events()
    event = next((e for e in events if e.id == event_id), None)
    if not event:
        abort(404)

    qty = _safe_int(request.args.get("qty", "1"), default=1, min_v=1, max_v=8)

    service_fee = 5.00
    subtotal = event.price_usd * qty
    total = subtotal + service_fee

    if request.method == "GET":
        return render_template(
            "checkout.html",
            event=event,
            qty=qty,
            subtotal=subtotal,
            service_fee=service_fee,
            total=total,
            errors={},
            form_data={}
        )

    card_number = request.form.get("card_number", "")
    exp_date = request.form.get("exp_date", "")
    cvv = request.form.get("cvv", "")
    name_on_card = request.form.get("name_on_card", "")
    billing_email = request.form.get("billing_email", "")

    clean, errors = validate_payment_form(
        card_number=card_number,
        exp_date=exp_date,
        cvv=cvv,
        name_on_card=name_on_card,
        billing_email=billing_email
    )

    cn = clean.get("card_number", "")
    last4 = cn[-4:] if cn else ""
    masked_display = f"**** **** **** {last4}" if last4 else ""

    form_data = {
        "exp_date": clean.get("exp_date", ""),
        "name_on_card": clean.get("name_on_card", ""),
        "billing_email": clean.get("billing_email", ""),
        "card_number": masked_display,
    }      

    if errors:
        return render_template(
            "checkout.html",
            event=event, qty=qty, subtotal=subtotal,
            service_fee=service_fee, total=total,
            errors=errors, form_data=form_data
        ), 400

    orders = load_orders()
    order_id = next_order_id(orders)
    user = get_current_user()

    orders.append({
        "id": order_id,
        "user_email": user.get("email"),
        "event_id": event.id,
        "event_title": event.title,
        "qty": qty,
        "unit_price": event.price_usd,
        "service_fee": service_fee,
        "total": total,
        "status": "PAID",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "payment": form_data
    })

    save_orders(orders)
    del cvv # no se guarda en .json pero lo borramos por si acaso
    return redirect(url_for("dashboard", paid="1"))


@app.route("/profile", methods=["GET", "POST"])
def profile():
    user = get_current_user()
    if not user:
        session.clear()
        return redirect(url_for("login"))

    form = {
        "full_name": user.get("full_name", ""),
        "email": user.get("email", ""),
        "phone": user.get("phone", ""),
    }

    field_errors: dict[str, str] = {}
    success_msg = None

    if request.method == "POST":
        full_name_raw = request.form.get("full_name", "")
        phone_raw = request.form.get("phone", "")

        current_password = request.form.get("current_password", "")
        new_password = request.form.get("new_password", "")
        confirm_new_password = request.form.get("confirm_new_password", "")

        updates: dict[str, str] = {}

        full_name_clean, err = validate_full_name(full_name_raw)
        if err:
            field_errors["full_name"] = _field_msg("full_name")
        else:
            updates["full_name"] = full_name_clean

        phone_clean, err = validate_phone(phone_raw)
        if err:
            field_errors["phone"] = _field_msg("phone")
        else:
            updates["phone"] = phone_clean

        if current_password or new_password or confirm_new_password:
            if not current_password or current_password != (user.get("password") or ""):
                field_errors["current_password"] = _field_msg("current_password")
            else:
                email_clean = (user.get("email") or "").strip().lower()
                new_clean, err = validate_password(new_password, email=email_clean)
                if err:
                    field_errors["new_password"] = _field_msg("new_password")
                else:
                    _, err = validate_password_confirmation(new_clean, confirm_new_password)
                    if err:
                        field_errors["confirm_new_password"] = _field_msg("confirm_new_password")
                    else:
                        updates["password"] = new_clean

        if field_errors:
            form["full_name"] = full_name_raw
            form["phone"] = phone_raw
            return render_template(
                "profile.html",
                form=form,
                field_errors=field_errors,
                error="Por favor corrige los campos marcados.",
                success_message=None,
            ), 400

        users = load_users()
        email_norm = (user.get("email") or "").strip().lower()

        for u in users:
            if (u.get("email") or "").strip().lower() == email_norm:
                u["full_name"] = updates["full_name"]
                u["phone"] = updates["phone"]
                if "password" in updates:
                    u["password"] = updates["password"]
                break

        save_users(users)

        form["full_name"] = updates["full_name"]
        form["phone"] = updates["phone"]
        success_msg = "Perfil actualizado correctamente."

    return render_template(
        "profile.html",
        form=form,
        field_errors=field_errors,
        success_message=success_msg,
    )


@app.get("/admin/users")
def admin_users():
    q = (request.args.get("q") or "").strip().lower()
    role = (request.args.get("role") or "all").strip().lower()
    status = (request.args.get("status") or "all").strip().lower()
    lockout = (request.args.get("lockout") or "all").strip().lower()

    users = [_user_with_defaults(u) for u in load_users()]

    if q:
        users = [
            u for u in users
            if q in (u.get("full_name", "").lower()) or q in (u.get("email", "").lower())
        ]

    if role != "all":
        users = [u for u in users if (u.get("role", "user").lower() == role)]

    if status != "all":
        users = [u for u in users if (u.get("status", "active").lower() == status)]

    if lockout != "all":
        if lockout == "locked":
            users = [u for u in users if (u.get("locked_until") or "").strip()]
        elif lockout == "not_locked":
            users = [u for u in users if not (u.get("locked_until") or "").strip()]

    users.sort(key=lambda u: (u.get("full_name", "").lower(), u.get("id", 0)))

    return render_template(
        "admin_users.html",
        users=users,
        filters={"q": q, "role": role, "status": status, "lockout": lockout},
        total=len(users),
    )


@app.post("/admin/users/<int:user_id>/toggle")
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