
from flask import (
    Blueprint,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

from werkzeug.security import (
    check_password_hash,
    generate_password_hash,
)

from app import db
from app.models.user import User


auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template("register.html")

    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "")
    confirm_password = request.form.get("confirm_password", "")

    if not email or not password or not confirm_password:
        flash("Please complete all fields.")
        return redirect(url_for("auth.register"))

    if password != confirm_password:
        flash("The passwords do not match.")
        return redirect(url_for("auth.register"))

    if len(password) < 8:
        flash("Your password must contain at least 8 characters.")
        return redirect(url_for("auth.register"))

    existing_user = User.query.filter_by(email=email).first()

    if existing_user is not None:
        flash("An account with this email already exists.")
        return redirect(url_for("auth.register"))

    user = User(
        email=email,
        password_hash=generate_password_hash(password),
    )

    try:
        db.session.add(user)
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise

    flash("Account created successfully. You can now log in.")
    return redirect(url_for("auth.login"))


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")

    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "")

    user = User.query.filter_by(email=email).first()

    if user is None or not check_password_hash(
        user.password_hash, password
    ):
        flash("Invalid email or password.")
        return redirect(url_for("auth.login"))

    session.clear()
    session["user_id"] = user.id

    return redirect(url_for("dashboard.dashboard"))


@auth_bp.route("/logout", methods=["POST"])
def logout():
    session.clear()
    flash("You have been logged out.")
    return redirect(url_for("auth.login"))
