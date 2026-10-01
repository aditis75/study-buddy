from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required, current_user

from . import db
from .models import User


bp = Blueprint("admin", __name__)


def is_admin():
    return current_user.is_authenticated and current_user.role == "admin"


@bp.route("/admin")
@login_required
def panel():
    if not is_admin():
        return "Unauthorized - Admin access only.", 403

    users = User.query.order_by(User.created_at.desc()).all()

    total_users = User.query.count()

    verified_users = User.query.filter_by(
        is_verified=True
    ).count()

    unverified_users = User.query.filter_by(
        is_verified=False
    ).count()

    suspended_users = User.query.filter_by(
        is_suspended=True
    ).count()

    return render_template(
        "admin.html",
        users=users,
        total_users=total_users,
        verified_users=verified_users,
        unverified_users=unverified_users,
        suspended_users=suspended_users,
    )


@bp.route("/admin/verify/<int:user_id>", methods=["POST"])
@login_required
def verify_user(user_id):
    if not is_admin():
        return "Unauthorized - Admin access only.", 403

    user = db.session.get(User, user_id)

    if not user:
        return "User not found.", 404

    user.is_verified = True
    db.session.commit()

    flash(
        f"{user.name}'s account has been verified.",
        "success",
    )

    return redirect(url_for("admin.panel"))


@bp.route("/admin/suspend/<int:user_id>", methods=["POST"])
@login_required
def suspend_user(user_id):
    if not is_admin():
        return "Unauthorized - Admin access only.", 403

    user = db.session.get(User, user_id)

    if not user:
        return "User not found.", 404

    if user.id == current_user.id:
        flash(
            "You cannot suspend your own admin account.",
            "danger",
        )
        return redirect(url_for("admin.panel"))

    user.is_suspended = True
    db.session.commit()

    flash(
        f"{user.name}'s account has been suspended.",
        "warning",
    )

    return redirect(url_for("admin.panel"))


@bp.route("/admin/unsuspend/<int:user_id>", methods=["POST"])
@login_required
def unsuspend_user(user_id):
    if not is_admin():
        return "Unauthorized - Admin access only.", 403

    user = db.session.get(User, user_id)

    if not user:
        return "User not found.", 404

    user.is_suspended = False
    db.session.commit()

    flash(
        f"{user.name}'s account has been reactivated.",
        "success",
    )

    return redirect(url_for("admin.panel"))