from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required
from . import db
from .models import User

bp = Blueprint("auth", __name__)


def valid_password(password):
    return (
        len(password) >= 8
        and any(c.islower() for c in password)
        and any(c.isupper() for c in password)
        and any(c.isdigit() for c in password)
        and any(not c.isalnum() for c in password)
    )


@bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        department = request.form.get("department", "").strip()
        year = request.form.get("year", type=int)
        password = request.form.get("password", "")

        # College email validation
        if not email.endswith("@mitwpu.edu.in"):
            flash("Use your @mitwpu.edu.in college email.", "danger")
            return render_template("register.html")

        # Password validation
        if not valid_password(password):
            flash(
                "Password must contain 8+ characters, uppercase, "
                "lowercase, number and special character.",
                "danger"
            )
            return render_template("register.html")

        # Check existing account
        if User.query.filter_by(email=email).first():
            flash("Email already registered.", "warning")
            return render_template("register.html")

        # Create user
        user = User(
            name=name,
            email=email,
            department=department,
            year=year
        )
        user.set_password(password)

        db.session.add(user)
        db.session.commit()

        # Development verification link
        verification_link = url_for(
            "auth.verify",
            user_id=user.id,
            _external=True
        )

        print("\n" + "=" * 60)
        print("VERIFICATION LINK:")
        print(verification_link)
        print("=" * 60 + "\n")

        flash(
            "Registration successful. Check the terminal "
            "for your verification link.",
            "success"
        )

        return redirect(url_for("auth.login"))

    # IMPORTANT: response for normal GET request
    return render_template("register.html")


@bp.route("/verify/<int:user_id>")
def verify(user_id):
    user = db.session.get(User, user_id)

    if not user:
        flash("Invalid verification link.", "danger")
        return redirect(url_for("auth.login"))

    if user.is_verified:
        flash("Your account is already verified.", "info")
        return redirect(url_for("auth.login"))

    user.is_verified = True
    db.session.commit()

    flash(
        "Your account has been verified. You can now log in.",
        "success"
    )

    return redirect(url_for("auth.login"))


@bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        user = User.query.filter_by(email=email).first()

        if not user or not user.check_password(password):
            flash("Invalid email or password.", "danger")

        elif not user.is_verified:
            flash(
                "Please verify your account before logging in.",
                "warning"
            )

        elif user.is_suspended:
            flash("Your account is suspended.", "danger")

        else:
            login_user(user)
            return redirect(url_for("profile.edit"))

    return render_template("login.html")


@bp.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("auth.login"))