from functools import wraps

from flask import (Flask, flash, redirect, render_template, request,
                   session, url_for)
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash, generate_password_hash

app = Flask(__name__)
app.secret_key = "change-this-to-a-long-random-string"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///hostel3.db"
db = SQLAlchemy(app)

HOSTELS = ["Girls Hostel", "Boys Hostel"]
GIRLS_BLOCKS = ["Krishnaveni", "Bhima", "Tungabhadra", "Munneru", "Ghataprabha"]
CATEGORIES = {
    "Food": "🍜",
    "Toiletries": "🧴",
    "Stationery": "✏️",
    "Medicine": "💊",
    "Other": "📦",
}


# ---------------------------------------------------------------- models

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80))
    room_no = db.Column(db.String(20))
    hostel_name = db.Column(db.String(80))
    block = db.Column(db.String(80))
    email = db.Column(db.String(120), unique=True)
    password_hash = db.Column(db.String(200))


class Item(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120))
    category = db.Column(db.String(40))
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))


# --------------------------------------------------------------- helpers

def current_user():
    user_id = session.get("user_id")
    return db.session.get(User, user_id) if user_id else None


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not current_user():
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    return wrapped


@app.context_processor
def inject_globals():
    return {"me": current_user()}


def other_hostel_of(hostel_name):
    return "Boys Hostel" if hostel_name == "Girls Hostel" else "Girls Hostel"


# ------------------------------------------------------------------ auth

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if current_user():
        return redirect(url_for("dashboard"))

    error = None
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        hostel = request.form.get("hostel_name", "")
        block = request.form.get("block", "").strip()
        room_no = request.form.get("room_no", "").strip()

        if not name or not room_no or not email:
            error = "Please fill in your name, room number and email."
        elif hostel not in HOSTELS:
            error = "Please choose your hostel."
        elif len(password) < 6:
            error = "Password must be at least 6 characters."
        elif User.query.filter_by(email=email).first():
            error = "An account with this email already exists."

        if not error:
            user = User(
                name=name, room_no=room_no, hostel_name=hostel, block=block,
                email=email, password_hash=generate_password_hash(password),
            )
            db.session.add(user)
            db.session.commit()
            session["user_id"] = user.id
            flash("Welcome aboard! Your profile is ready.")
            return redirect(url_for("dashboard"))

    return render_template("signup.html", error=error, form=request.form,
                           hostels=HOSTELS, blocks=GIRLS_BLOCKS)


@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user():
        return redirect(url_for("dashboard"))

    error = None
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password_hash, request.form.get("password", "")):
            session["user_id"] = user.id
            return redirect(url_for("dashboard"))
        error = "Wrong email or password."

    return render_template("login.html", error=error, form=request.form)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# ------------------------------------------------------------- dashboard

@app.route("/")
@login_required
def dashboard():
    user = current_user()
    q = request.args.get("q", "").strip()
    category = request.args.get("category", "").strip()
    searching = bool(q or category)

    base = db.session.query(Item, User).join(User, Item.user_id == User.id)
    same_hostel = base.filter(User.hostel_name == user.hostel_name,
                              User.id != user.id)
    other_hostel = base.filter(User.hostel_name != user.hostel_name)

    results, recent, other_hostel_has = [], [], False

    if searching:
        if q:
            same_hostel = same_hostel.filter(Item.name.ilike(f"%{q}%"))
            other_hostel = other_hostel.filter(Item.name.ilike(f"%{q}%"))
        if category in CATEGORIES:
            same_hostel = same_hostel.filter(Item.category == category)
            other_hostel = other_hostel.filter(Item.category == category)
        results = same_hostel.order_by(Item.id.desc()).all()
        # Only tells whether the other hostel has it. Never who.
        other_hostel_has = other_hostel.first() is not None
    else:
        recent = same_hostel.order_by(Item.id.desc()).limit(8).all()

    my_items = (Item.query.filter_by(user_id=user.id)
                .order_by(Item.id.desc()).all())

    return render_template(
        "dashboard.html", user=user, q=q, category=category,
        searching=searching, results=results, recent=recent,
        other_hostel_has=other_hostel_has,
        other_hostel_name=other_hostel_of(user.hostel_name),
        my_items=my_items, categories=CATEGORIES,
    )


@app.route("/add", methods=["POST"])
@login_required
def add_item():
    user = current_user()
    name = request.form.get("name", "").strip()[:80]
    category = request.form.get("category", "Other")
    if category not in CATEGORIES:
        category = "Other"

    if not name:
        flash("Please type what you have.")
    else:
        db.session.add(Item(name=name, category=category, user_id=user.id))
        db.session.commit()
        flash(f"\"{name}\" is now on the shelf.")
    return redirect(url_for("dashboard"))


@app.route("/delete/<int:item_id>", methods=["POST"])
@login_required
def delete_item(item_id):
    item = db.session.get(Item, item_id)
    if item and item.user_id == current_user().id:
        db.session.delete(item)
        db.session.commit()
        flash("Item removed.")
    return redirect(url_for("dashboard"))


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
