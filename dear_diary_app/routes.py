# dear_diary_app/routes.py
from datetime import datetime, date
from calendar import monthrange

from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_user, logout_user, login_required, current_user
from sqlalchemy import extract
from dear_diary_app import db
from dear_diary_app.models import User, Diary

# Blueprint define (MUST be before decorators)
main = Blueprint("main", __name__)

# ── HOME ──────────────────────────────────────────
@main.route("/")
def home():
    # simple landing page
    return render_template("home.html")

# ── AUTH ──────────────────────────────────────────
@main.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        u = request.form["username"].lower().strip()
        p = request.form["password"]
        if User.query.filter_by(username=u).first():
            flash("Username already exists", "error")
        else:
            user = User(username=u)
            user.set_pw(p)
            db.session.add(user)
            db.session.commit()
            login_user(user)
            return redirect(url_for("main.home"))
    return render_template("signup.html")


@main.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        u = request.form["username"].lower().strip()
        p = request.form["password"]
        user = User.query.filter_by(username=u).first()
        if user and user.check_pw(p):
            login_user(user)
            return redirect(url_for("main.home"))
        flash("Bad credentials", "error")
    return render_template("login.html")


@main.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("main.login"))

# ── WRITE ENTRY ───────────────────────────────────
@main.route("/write", methods=["GET", "POST"])
@login_required
def write():
    if request.method == "POST":
        body = request.form.get("body", "").strip()
        pub  = bool(request.form.get("is_public"))
        if body:
            db.session.add(Diary(body=body, is_public=pub, user_id=current_user.id))
            db.session.commit()
            flash("Diary saved!", "success")
            return redirect(url_for("main.entries"))
    return render_template("write.html", now=datetime.now())

# ── ENTRIES ───────────────────────────────────────
@main.route("/entries")
@login_required
def entries():
    friend_ids = [f.id for f in current_user.friends]
    q = Diary.query.filter(
        (Diary.user_id == current_user.id) |
        ((Diary.user_id.in_(friend_ids)) & (Diary.is_public == True))
    ).order_by(Diary.timestamp.desc())
    return render_template("entries.html", entries=q.all(), friend=None)

@main.route("/entries/<username>")
@login_required
def friend_entries(username):
    friend = User.query.filter_by(username=username.lower()).first_or_404()
    if friend not in current_user.friends:
        flash("Not your friend", "error")
        return redirect(url_for("main.entries"))
    q = Diary.query.filter_by(user_id=friend.id, is_public=True)\
                   .order_by(Diary.timestamp.desc())
    return render_template("entries.html", entries=q.all(), friend=friend)

# ── FRIENDS ───────────────────────────────────────
@main.route("/friends")
@login_required
def friends():
    return render_template("friends.html", friends=current_user.friends)

@main.route("/add_friend", methods=["GET", "POST"])
@login_required
def add_friend():
    if request.method == "POST":
        uname = request.form.get("username", "").lower().strip()
        pal = User.query.filter_by(username=uname).first()
        if not pal:
            flash("User not found", "error")
        elif pal == current_user or pal in current_user.friends:
            flash("Already friends / same user", "error")
        else:
            current_user.friends.append(pal)
            db.session.commit()
            flash("Friend added", "success")
            return redirect(url_for("main.friends"))
    return render_template("add_friend.html")

# ── CALENDAR ──────────────────────────────────────
@main.route("/calendar")
@main.route("/calendar/")
@login_required
def calendar_view():
    y = request.args.get("y", date.today().year, int)
    m = request.args.get("m", date.today().month, int)
    search = request.args.get("q", "").lower()

    base = Diary.query.filter_by(user_id=current_user.id)\
           .filter(extract("year", Diary.timestamp)==y)\
           .filter(extract("month", Diary.timestamp)==m)

    entries = [e for e in base if search in e.body.lower()] if search else list(base)

    grouped, marked = {}, set()
    for e in entries:
        d = e.timestamp.date()
        grouped.setdefault(d, []).append(e)
        marked.add(d.day)

    return render_template("calendar.html",
                           year=y, month=m,
                           days=monthrange(y, m)[1],
                           marked=marked,
                           calendar_entries=grouped,
                           search=search)
