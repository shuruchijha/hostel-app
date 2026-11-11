from urllib.parse import quote
import secrets
from datetime import datetime
from functools import wraps

from flask import (Flask, abort, flash, redirect, render_template,
                   request, session, url_for)
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash, generate_password_hash

app = Flask(__name__, static_folder="static")
app.secret_key = "change-this-to-a-long-random-string-in-production"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///hostel3.db"
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_size": 10,
    "pool_timeout": 30,
    "pool_recycle": 300,
    "max_overflow": 20,
}
app.config["SEND_FILE_MAX_AGE_DEFAULT"] = 86400  # Cache static files 24h
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
CONDITIONS = {
    "new_packed": ("New / Packed", "🏷️"),
    "used":       ("Used", "♻️"),
    "free":       ("Free", "🎁"),
}
URGENCIES = {
    "urgent":  ("🚨 Urgent (Need ASAP)", "badge-danger"),
    "tonight": ("🌙 Tonight", "badge-amber"),
    "anytime": ("📦 Anytime", "badge-muted"),
}


# ════════════════════════════════════════════
#  MODELS
# ════════════════════════════════════════════

class User(db.Model):
    id            = db.Column(db.Integer, primary_key=True)
    name          = db.Column(db.String(80),  nullable=False)
    room_no       = db.Column(db.String(20),  nullable=False)   # Protected room number
    hostel_name   = db.Column(db.String(80))
    block         = db.Column(db.String(80))
    email         = db.Column(db.String(120), unique=True)
    password_hash = db.Column(db.String(200))
    upi_id        = db.Column(db.String(100), nullable=True)    # optional UPI ID (e.g. name@upi)
    phone_number  = db.Column(db.String(20),  nullable=True)    # optional phone number for GPay/PhonePe/Paytm


class Message(db.Model):
    id          = db.Column(db.Integer, primary_key=True)
    sender_id   = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    item_id     = db.Column(db.Integer, db.ForeignKey("item.id"), nullable=True)
    text        = db.Column(db.Text, nullable=False)
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)
    is_read     = db.Column(db.Boolean, default=False)

    sender   = db.relationship("User", foreign_keys=[sender_id], backref="sent_messages")
    receiver = db.relationship("User", foreign_keys=[receiver_id], backref="received_messages")
    item     = db.relationship("Item", backref="chat_messages")


class Item(db.Model):
    id           = db.Column(db.Integer, primary_key=True)
    name         = db.Column(db.String(120))
    category     = db.Column(db.String(40))
    user_id      = db.Column(db.Integer, db.ForeignKey("user.id"))
    condition    = db.Column(db.String(20), default="used")  # new_packed | used | free
    price        = db.Column(db.Float,   default=0.0)
    payment_mode = db.Column(db.String(30), default="both")  # upi | cash | both | free
    is_taken     = db.Column(db.Boolean, default=False)
    created_at   = db.Column(db.DateTime, default=datetime.utcnow)


class ItemRequest(db.Model):
    id           = db.Column(db.Integer, primary_key=True)
    user_id      = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    name         = db.Column(db.String(120), nullable=False)
    category     = db.Column(db.String(40), default="Other")
    urgency      = db.Column(db.String(20), default="tonight") # urgent | tonight | anytime
    price_offer  = db.Column(db.Float, default=0.0)             # willing to pay in INR
    note         = db.Column(db.String(200), nullable=True)     # optional note
    is_fulfilled = db.Column(db.Boolean, default=False)
    created_at   = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("User", backref="item_requests")


class Community(db.Model):
    id          = db.Column(db.Integer, primary_key=True)
    name        = db.Column(db.String(100), nullable=False)
    creator_id  = db.Column(db.Integer, db.ForeignKey("user.id"))
    invite_code = db.Column(db.String(16), unique=True)
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)

    creator = db.relationship("User", backref="created_communities", foreign_keys=[creator_id])
    members = db.relationship("CommunityMember", backref="community", cascade="all, delete-orphan")


class CommunityMember(db.Model):
    id           = db.Column(db.Integer, primary_key=True)
    community_id = db.Column(db.Integer, db.ForeignKey("community.id", ondelete="CASCADE"))
    user_id      = db.Column(db.Integer, db.ForeignKey("user.id"))
    joined_at    = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (db.UniqueConstraint("community_id", "user_id"),)
    user = db.relationship("User", backref="memberships")


# ════════════════════════════════════════════
#  HELPERS
# ════════════════════════════════════════════

def current_user():
    uid = session.get("user_id")
    return db.session.get(User, uid) if uid else None


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not current_user():
            session["after_login"] = request.url   # redirect back after login
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    return wrapped


@app.context_processor
def inject_globals():
    user = current_user()
    comm_count = 0
    unread_chat_count = 0
    if user:
        comm_count = CommunityMember.query.filter_by(user_id=user.id).count()
        unread_chat_count = Message.query.filter_by(receiver_id=user.id, is_read=False).count()
    return {
        "me": user,
        "comm_count": comm_count,
        "unread_chat_count": unread_chat_count,
        "conditions": CONDITIONS,
    }


def other_hostel_of(h):
    return "Boys Hostel" if h == "Girls Hostel" else "Girls Hostel"


def _shared_community(a: User, b: User) -> bool:
    """True if users a and b are both members of at least one community."""
    ids_a = {m.community_id for m in a.memberships}
    ids_b = {m.community_id for m in b.memberships}
    return bool(ids_a & ids_b)


def can_see_profile(viewer: User, target: User) -> bool:
    """Profile is visible only to same-hostel students or shared-community members."""
    if viewer.id == target.id:
        return True
    if viewer.hostel_name == target.hostel_name:
        return True
    return _shared_community(viewer, target)


def can_see_room_no(viewer: User, target: User) -> bool:
    """Room no is visible only to people within the same hostel (e.g. Girls Hostel sees Girls Hostel rooms,
       boys or outsiders cannot see girls' room numbers)."""
    if not viewer or not target:
        return False
    if viewer.id == target.id:
        return True
    if target.hostel_name == "Girls Hostel":
        return viewer.hostel_name == "Girls Hostel"
    if target.hostel_name == "Boys Hostel":
        return viewer.hostel_name == "Boys Hostel"
    return False


def seller_payment_vpa(seller: User) -> str:
    """Returns the primary UPI handle or phone VPA for payments."""
    if not seller:
        return ""
    if seller.upi_id:
        return seller.upi_id.strip()
    if seller.phone_number:
        clean = seller.phone_number.replace("+91", "").replace(" ", "").replace("-", "").strip()
        if clean:
            return f"{clean}@upi"
    return ""


def fmt_price(item) -> str:
    if item.condition == "free":
        return "Free 🎁"
    if item.price and item.price > 0:
        return f"₹{int(item.price)}"
    return "Negotiable"


def upi_intent_url(upi_id_or_phone: str, seller_name: str, price: float, item_name: str = "") -> str:
    vpa = (upi_id_or_phone or "").strip()
    if vpa and "@" not in vpa and vpa.replace("+", "").replace(" ", "").replace("-", "").isdigit():
        clean_num = vpa.replace("+91", "").replace(" ", "").replace("-", "").strip()
        vpa = f"{clean_num}@upi"
    if not vpa:
        return ""
    pn = quote(seller_name or "HostelMate")
    tn = quote(f"Midnight Pantry - {item_name}"[:40])
    am = f"{price:.2f}" if price and price > 0 else ""
    am_param = f"&am={am}" if am else ""
    return f"upi://pay?pa={vpa}&pn={pn}{am_param}&cu=INR&tn={tn}"


app.jinja_env.globals["fmt_price"] = fmt_price
app.jinja_env.globals["upi_intent_url"] = upi_intent_url
app.jinja_env.globals["can_see_room_no"] = can_see_room_no
app.jinja_env.globals["seller_payment_vpa"] = seller_payment_vpa


# ════════════════════════════════════════════
#  AUTH
# ════════════════════════════════════════════

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if current_user():
        return redirect(url_for("dashboard"))

    error = None
    if request.method == "POST":
        name     = request.form.get("name", "").strip()
        email    = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")
        hostel   = request.form.get("hostel_name", "")
        block    = request.form.get("block", "").strip()
        room_no  = request.form.get("room_no", "").strip()

        if not name or not room_no or not email:
            error = "Please fill in your name, room number and email."
        elif hostel not in HOSTELS:
            error = "Please choose your hostel."
        elif len(password) < 6:
            error = "Password must be at least 6 characters."
        elif confirm_password and password != confirm_password:
            error = "Passwords do not match. Please check and re-type."
        elif User.query.filter_by(email=email).first():
            error = "An account with this email already exists."

        if not error:
            user = User(
                name=name, room_no=room_no, hostel_name=hostel,
                block=block, email=email,
                password_hash=generate_password_hash(password),
            )
            db.session.add(user)
            db.session.commit()
            session["user_id"] = user.id
            flash("Welcome aboard! Your profile is ready. 🎉")
            after = session.pop("after_login", None)
            return redirect(after or url_for("dashboard"))

    return render_template("signup.html", error=error, form=request.form,
                           hostels=HOSTELS, blocks=GIRLS_BLOCKS)


@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user():
        return redirect(url_for("dashboard"))

    error = None
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        user  = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password_hash, request.form.get("password", "")):
            session["user_id"] = user.id
            after = session.pop("after_login", None)
            return redirect(after or url_for("dashboard"))
        error = "Wrong email or password."

    return render_template("login.html", error=error, form=request.form)


@app.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    if current_user():
        return redirect(url_for("dashboard"))

    error = None
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        hostel = request.form.get("hostel_name", "").strip()
        room_no = request.form.get("room_no", "").strip()
        new_password = request.form.get("new_password", "")
        confirm_password = request.form.get("confirm_password", "")

        user = User.query.filter_by(email=email).first()
        if not email or not room_no or not hostel:
            error = "Please provide your email, hostel, and room number."
        elif not user:
            error = "No account found with this college email."
        elif user.hostel_name != hostel or user.room_no.strip().lower() != room_no.lower():
            error = "Security verification failed: Hostel or Room Number does not match our records."
        elif len(new_password) < 6:
            error = "New password must be at least 6 characters long."
        elif new_password != confirm_password:
            error = "Passwords do not match. Please re-enter."
        else:
            user.password_hash = generate_password_hash(new_password)
            db.session.commit()
            flash("Password reset successfully! You can now log in with your new password. ✓")
            return redirect(url_for("login"))

    return render_template("forgot_password.html", error=error, hostels=HOSTELS, form=request.form)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# ════════════════════════════════════════════
#  DASHBOARD
# ════════════════════════════════════════════

@app.route("/")
@login_required
def dashboard():
    user      = current_user()
    q         = request.args.get("q", "").strip()
    category  = request.args.get("category", "").strip()
    tab       = request.args.get("tab", "shelf").strip() # "shelf" or "requests"
    searching = bool(q or category)

    # 1. Available Items on Shelf
    base = db.session.query(Item, User).join(User, Item.user_id == User.id)

    same = base.filter(
        User.hostel_name == user.hostel_name,
        User.id != user.id,
        Item.is_taken == False,          # only available items
    )
    other = base.filter(
        User.hostel_name != user.hostel_name,
        Item.is_taken == False,
    )

    results, recent, other_hostel_has = [], [], False

    if searching:
        if q:
            same  = same.filter(Item.name.ilike(f"%{q}%"))
            other = other.filter(Item.name.ilike(f"%{q}%"))
        if category in CATEGORIES:
            same  = same.filter(Item.category == category)
            other = other.filter(Item.category == category)
        results = same.order_by(Item.id.desc()).all()
        other_hostel_has = other.first() is not None   # hint only — never who
    else:
        recent = same.order_by(Item.id.desc()).limit(8).all()

    my_items = Item.query.filter_by(user_id=user.id).order_by(Item.id.desc()).all()

    # 2. Student Requests ("Who is looking for what")
    req_base = (db.session.query(ItemRequest, User)
                .join(User, ItemRequest.user_id == User.id)
                .filter(User.hostel_name == user.hostel_name, ItemRequest.is_fulfilled == False))

    if searching:
        if q:
            req_base = req_base.filter(ItemRequest.name.ilike(f"%{q}%"))
        if category in CATEGORIES:
            req_base = req_base.filter(ItemRequest.category == category)

    active_requests = req_base.order_by(ItemRequest.created_at.desc()).all()
    my_requests = ItemRequest.query.filter_by(user_id=user.id).order_by(ItemRequest.created_at.desc()).all()

    return render_template(
        "dashboard.html", user=user, q=q, category=category, tab=tab,
        searching=searching, results=results, recent=recent,
        other_hostel_has=other_hostel_has,
        other_hostel_name=other_hostel_of(user.hostel_name),
        my_items=my_items, active_requests=active_requests, my_requests=my_requests,
        categories=CATEGORIES, urgencies=URGENCIES,
    )


# ════════════════════════════════════════════
#  ITEM REQUESTS — "Who is looking for what"
# ════════════════════════════════════════════

@app.route("/request/add", methods=["POST"])
@login_required
def add_request():
    user        = current_user()
    name        = request.form.get("name", "").strip()[:100]
    category    = request.form.get("category", "Other")
    urgency     = request.form.get("urgency", "tonight")
    price_str   = request.form.get("price_offer", "0").strip()
    note        = request.form.get("note", "").strip()[:200]

    if category not in CATEGORIES:
        category = "Other"
    if urgency not in ("urgent", "tonight", "anytime"):
        urgency = "tonight"

    try:
        price_offer = max(0.0, float(price_str))
    except (ValueError, TypeError):
        price_offer = 0.0

    if not name:
        flash("Please type what you are looking for.")
    else:
        req = ItemRequest(
            user_id=user.id,
            name=name,
            category=category,
            urgency=urgency,
            price_offer=price_offer,
            note=note
        )
        db.session.add(req)
        db.session.commit()
        flash(f'Your request for "{name}" is now live! Friends nearby can see and help you. 📢')
    return redirect(url_for("dashboard", tab="requests"))


@app.route("/request/<int:req_id>/fulfill", methods=["POST"])
@login_required
def fulfill_request(req_id):
    user = current_user()
    req = db.session.get(ItemRequest, req_id)
    if not req or req.user_id != user.id:
        abort(403)
    req.is_fulfilled = True
    db.session.commit()
    flash(f'Marked "{req.name}" as fulfilled / received! ✓')
    return redirect(request.referrer or url_for("dashboard", tab="requests"))


@app.route("/request/<int:req_id>/delete", methods=["POST"])
@login_required
def delete_request(req_id):
    user = current_user()
    req = db.session.get(ItemRequest, req_id)
    if not req or req.user_id != user.id:
        abort(403)
    db.session.delete(req)
    db.session.commit()
    flash("Request removed.")
    return redirect(request.referrer or url_for("dashboard", tab="requests"))


# ════════════════════════════════════════════
#  ITEMS — add / delete / mark taken
# ════════════════════════════════════════════

@app.route("/add", methods=["POST"])
@login_required
def add_item():
    user         = current_user()
    name         = request.form.get("name", "").strip()[:80]
    category     = request.form.get("category", "Other")
    condition    = request.form.get("condition", "used")
    price_str    = request.form.get("price", "0").strip()
    payment_mode = request.form.get("payment_mode", "both")

    if category not in CATEGORIES:
        category = "Other"
    if condition not in CONDITIONS:
        condition = "used"
    if payment_mode not in ("upi", "cash", "both"):
        payment_mode = "both"

    try:
        price = max(0.0, float(price_str))
    except (ValueError, TypeError):
        price = 0.0

    if condition == "free":
        price = 0.0
        payment_mode = "free"

    if not name:
        flash("Please type what you have.")
    else:
        db.session.add(Item(
            name=name, category=category, user_id=user.id,
            condition=condition, price=price, payment_mode=payment_mode,
        ))
        db.session.commit()
        flash(f'"{name}" is now on the shelf! ✓')
    return redirect(url_for("dashboard"))


@app.route("/delete/<int:item_id>", methods=["POST"])
@login_required
def delete_item(item_id):
    item = db.session.get(Item, item_id)
    if item and item.user_id == current_user().id:
        db.session.delete(item)
        db.session.commit()
        flash("Item removed from shelf.")
    return redirect(request.referrer or url_for("dashboard"))


@app.route("/item/<int:item_id>/taken", methods=["POST"])
@login_required
def mark_taken(item_id):
    item = db.session.get(Item, item_id)
    if not item:
        abort(404)
    if item.user_id != current_user().id:
        abort(403)
    item.is_taken = True
    db.session.commit()
    flash(f'"{item.name}" marked as given — it won\'t appear in searches.')
    return redirect(request.referrer or url_for("dashboard"))


@app.route("/item/<int:item_id>/available", methods=["POST"])
@login_required
def mark_available(item_id):
    item = db.session.get(Item, item_id)
    if not item:
        abort(404)
    if item.user_id != current_user().id:
        abort(403)
    item.is_taken = False
    db.session.commit()
    flash(f'"{item.name}" is available again.')
    return redirect(request.referrer or url_for("dashboard"))


# ════════════════════════════════════════════
#  PROFILE  (private — same hostel or shared community only)
# ════════════════════════════════════════════

@app.route("/profile/<int:user_id>")
@login_required
def profile(user_id):
    viewer = current_user()
    target = db.session.get(User, user_id)
    if not target:
        abort(404)

    is_own = (viewer.id == user_id)

    if not is_own and not can_see_profile(viewer, target):
        flash("You can only view profiles of people in your hostel or a shared community.")
        return redirect(url_for("dashboard"))

    all_items       = Item.query.filter_by(user_id=target.id).order_by(Item.id.desc()).all()
    available_items = [i for i in all_items if not i.is_taken]
    given_items     = [i for i in all_items if i.is_taken]

    # UPI visible only to same-hostel/community members (never strangers)
    show_upi = is_own or can_see_profile(viewer, target)

    return render_template(
        "profile.html",
        target=target, available_items=available_items,
        given_items=given_items, is_own=is_own,
        show_upi=show_upi, categories=CATEGORIES,
    )


# ════════════════════════════════════════════
#  SETTINGS  (UPI ID, etc.)
# ════════════════════════════════════════════

@app.route("/settings", methods=["GET", "POST"])
@login_required
def settings():
    user = current_user()
    if request.method == "POST":
        name     = request.form.get("name", "").strip()[:80]
        hostel   = request.form.get("hostel_name", "").strip()
        block    = request.form.get("block", "").strip()[:80]
        room_no  = request.form.get("room_no", "").strip()[:20]
        phone    = request.form.get("phone_number", "").strip()[:20]
        upi          = request.form.get("upi_id", "").strip()[:100]
        current_pass = request.form.get("current_password", "").strip()
        new_pass     = request.form.get("new_password", "").strip()
        confirm_pass = request.form.get("confirm_password", "").strip()

        if not name or not room_no:
            flash("Name and room number cannot be empty.")
            return redirect(url_for("settings"))
        if hostel not in HOSTELS:
            flash("Please choose a valid hostel.")
            return redirect(url_for("settings"))
        if upi and "@" not in upi:
            flash("UPI ID should look like yourname@upi or 9876543210@paytm.")
            return redirect(url_for("settings"))

        user.name = name
        user.hostel_name = hostel
        user.block = block
        user.room_no = room_no
        user.phone_number = phone if phone else None
        user.upi_id = upi if upi else None

        if new_pass:
            if user.password_hash and not check_password_hash(user.password_hash, current_pass):
                flash("Current password is incorrect. Could not update password.")
                return redirect(url_for("settings"))
            if len(new_pass) < 6:
                flash("New password must be at least 6 characters.")
                return redirect(url_for("settings"))
            if new_pass != confirm_pass:
                flash("New password and confirmation do not match.")
                return redirect(url_for("settings"))
            user.password_hash = generate_password_hash(new_pass)
            flash("Password updated successfully! ✓")

        db.session.commit()
        flash("Personal profile and payment details updated successfully! ✓")
        return redirect(url_for("settings"))

    return render_template("settings.html", user=user, hostels=HOSTELS, blocks=GIRLS_BLOCKS)


# ════════════════════════════════════════════
#  CHAT & MESSAGING
# ════════════════════════════════════════════

@app.route("/chat")
@login_required
def chat_inbox():
    user = current_user()

    # Find all conversations user is part of
    all_msgs = (Message.query
                .filter((Message.sender_id == user.id) | (Message.receiver_id == user.id))
                .order_by(Message.created_at.desc())
                .all())

    partners = {}
    for m in all_msgs:
        partner_id = m.receiver_id if m.sender_id == user.id else m.sender_id
        if partner_id not in partners:
            partner = db.session.get(User, partner_id)
            if partner:
                unread = Message.query.filter_by(
                    sender_id=partner_id, receiver_id=user.id, is_read=False
                ).count()
                partners[partner_id] = {
                    "partner": partner,
                    "last_message": m,
                    "unread_count": unread
                }

    # Available contacts: people in same hostel + shared communities
    same_hostel_students = User.query.filter(
        User.hostel_name == user.hostel_name,
        User.id != user.id
    ).order_by(User.name.asc()).all()

    comm_memberships = CommunityMember.query.filter_by(user_id=user.id).all()
    comm_ids = [c.community_id for c in comm_memberships]
    comm_user_ids = set()
    if comm_ids:
        other_members = CommunityMember.query.filter(
            CommunityMember.community_id.in_(comm_ids),
            CommunityMember.user_id != user.id
        ).all()
        comm_user_ids = {m.user_id for m in other_members}

    comm_students = User.query.filter(User.id.in_(comm_user_ids)).all() if comm_user_ids else []

    contacts_dict = {u.id: u for u in same_hostel_students}
    for u in comm_students:
        contacts_dict[u.id] = u

    # Quick contacts who don't have an active chat yet
    quick_contacts = [u for uid, u in contacts_dict.items() if uid not in partners]

    return render_template(
        "chat_inbox.html",
        conversations=list(partners.values()),
        quick_contacts=quick_contacts,
        user=user
    )


@app.route("/chat/<int:target_id>", methods=["GET", "POST"])
@login_required
def chat_detail(target_id):
    user = current_user()
    if user.id == target_id:
        flash("You cannot chat with yourself.")
        return redirect(url_for("chat_inbox"))

    target = db.session.get(User, target_id)
    if not target:
        abort(404)

    if not can_see_profile(user, target):
        flash("You can only chat with students in your hostel or a shared community.")
        return redirect(url_for("chat_inbox"))

    item_id = request.args.get("item_id", type=int)
    item = db.session.get(Item, item_id) if item_id else None
    request_item = request.args.get("request_item", "").strip()[:100]

    if request.method == "POST":
        text_content = request.form.get("text", "").strip()
        if text_content:
            msg = Message(
                sender_id=user.id,
                receiver_id=target.id,
                item_id=item.id if item else None,
                text=text_content
            )
            db.session.add(msg)
            db.session.commit()
        return redirect(url_for("chat_detail", target_id=target.id, item_id=item_id if item else None, request_item=request_item if request_item else None))

    # Mark incoming unread messages as read
    Message.query.filter_by(sender_id=target.id, receiver_id=user.id, is_read=False).update({"is_read": True})
    db.session.commit()

    messages = (Message.query
                .filter(
                    ((Message.sender_id == user.id) & (Message.receiver_id == target.id)) |
                    ((Message.sender_id == target.id) & (Message.receiver_id == user.id))
                )
                .order_by(Message.created_at.asc())
                .all())

    return render_template(
        "chat_detail.html",
        target=target,
        messages=messages,
        item=item,
        request_item=request_item,
        user=user
    )


# ════════════════════════════════════════════
#  COMMUNITY
# ════════════════════════════════════════════

@app.route("/community")
@login_required
def community():
    user = current_user()
    memberships = CommunityMember.query.filter_by(user_id=user.id).all()
    comm_ids    = [m.community_id for m in memberships]
    communities = []
    if comm_ids:
        communities = (Community.query
                       .filter(Community.id.in_(comm_ids))
                       .order_by(Community.created_at.desc())
                       .all())
    return render_template("community.html", communities=communities, user=user)


@app.route("/community/create", methods=["GET", "POST"])
@login_required
def create_community():
    user = current_user()
    if request.method == "POST":
        name = request.form.get("name", "").strip()[:100]
        if not name:
            flash("Give your community a name.")
            return redirect(url_for("create_community"))

        # Unique 16-char hex invite code
        code = secrets.token_hex(8)
        while Community.query.filter_by(invite_code=code).first():
            code = secrets.token_hex(8)

        comm = Community(name=name, creator_id=user.id, invite_code=code)
        db.session.add(comm)
        db.session.flush()                      # get id before commit
        db.session.add(CommunityMember(community_id=comm.id, user_id=user.id))
        db.session.commit()

        flash(f'"{name}" created! Share the invite link with your friends.')
        return redirect(url_for("community_detail", comm_id=comm.id))

    return render_template("create_community.html")


@app.route("/community/<int:comm_id>")
@login_required
def community_detail(comm_id):
    user = current_user()
    comm = db.session.get(Community, comm_id)
    if not comm:
        abort(404)

    if not CommunityMember.query.filter_by(community_id=comm_id, user_id=user.id).first():
        flash("You're not a member of this community.")
        return redirect(url_for("community"))

    members = (db.session.query(CommunityMember, User)
               .join(User, CommunityMember.user_id == User.id)
               .filter(CommunityMember.community_id == comm_id)
               .all())

    invite_url = url_for("join_community", code=comm.invite_code, _external=True)
    is_creator = (comm.creator_id == user.id)

    return render_template(
        "community_detail.html",
        comm=comm, members=members,
        invite_url=invite_url, is_creator=is_creator, user=user,
    )


@app.route("/community/join/<code>", methods=["GET", "POST"])
def join_community(code):
    comm = Community.query.filter_by(invite_code=code).first()
    if not comm:
        flash("Invalid or expired invite link.")
        return redirect(url_for("login"))

    user = current_user()
    if not user:
        session["after_login"] = url_for("join_community", code=code)
        flash(f'Create an account or log in to join "{comm.name}".')
        return redirect(url_for("signup"))

    existing = CommunityMember.query.filter_by(community_id=comm.id, user_id=user.id).first()
    if existing:
        flash(f'You\'re already in "{comm.name}"!')
        return redirect(url_for("community_detail", comm_id=comm.id))

    if request.method == "POST":
        db.session.add(CommunityMember(community_id=comm.id, user_id=user.id))
        db.session.commit()
        flash(f'You joined "{comm.name}"! 🎉')
        return redirect(url_for("community_detail", comm_id=comm.id))

    member_count = CommunityMember.query.filter_by(community_id=comm.id).count()
    return render_template("join_community.html", comm=comm, member_count=member_count)


@app.route("/community/<int:comm_id>/leave", methods=["POST"])
@login_required
def leave_community(comm_id):
    user = current_user()
    comm = db.session.get(Community, comm_id)
    if not comm:
        abort(404)
    if comm.creator_id == user.id:
        flash("You created this community — delete it instead if you no longer need it.")
        return redirect(url_for("community_detail", comm_id=comm_id))
    m = CommunityMember.query.filter_by(community_id=comm_id, user_id=user.id).first()
    if m:
        db.session.delete(m)
        db.session.commit()
        flash(f'You left "{comm.name}".')
    return redirect(url_for("community"))


@app.route("/community/<int:comm_id>/delete", methods=["POST"])
@login_required
def delete_community(comm_id):
    user = current_user()
    comm = db.session.get(Community, comm_id)
    if not comm or comm.creator_id != user.id:
        abort(403)
    name = comm.name
    db.session.delete(comm)
    db.session.commit()
    flash(f'Community "{name}" deleted.')
    return redirect(url_for("community"))


# ════════════════════════════════════════════
#  BOOTSTRAP  (auto-migrate existing DB)
# ════════════════════════════════════════════

# ════════════════════════════════════════════
#  DATABASE INIT & MIGRATION ON STARTUP
# ════════════════════════════════════════════
with app.app_context():
    db.create_all()     # creates any missing tables
    try:
        from sqlalchemy import inspect as sa_inspect, text
        insp = sa_inspect(db.engine)
        tables = insp.get_table_names()
        if "item" in tables:
            item_cols = {c["name"] for c in insp.get_columns("item")}
            with db.engine.begin() as conn:
                if "condition"  not in item_cols:
                    conn.execute(text("ALTER TABLE item ADD COLUMN condition  VARCHAR(20) DEFAULT 'used'"))
                if "price"        not in item_cols:
                    conn.execute(text("ALTER TABLE item ADD COLUMN price        FLOAT       DEFAULT 0.0"))
                if "payment_mode" not in item_cols:
                    conn.execute(text("ALTER TABLE item ADD COLUMN payment_mode VARCHAR(30) DEFAULT 'both'"))
                if "is_taken"     not in item_cols:
                    conn.execute(text("ALTER TABLE item ADD COLUMN is_taken   BOOLEAN     DEFAULT 0"))
                if "created_at" not in item_cols:
                    conn.execute(text("ALTER TABLE item ADD COLUMN created_at DATETIME"))
        if "user" in tables:
            user_cols = {c["name"] for c in insp.get_columns("user")}
            with db.engine.begin() as conn:
                if "upi_id"       not in user_cols:
                    conn.execute(text("ALTER TABLE user ADD COLUMN upi_id       VARCHAR(100)"))
                if "phone_number" not in user_cols:
                    conn.execute(text("ALTER TABLE user ADD COLUMN phone_number VARCHAR(20)"))
    except Exception as e:
        print(f"Migration note: {e}")


if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
