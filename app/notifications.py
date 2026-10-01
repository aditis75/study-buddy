from flask import Blueprint, render_template, jsonify
from flask_login import login_required, current_user
from . import db
from .models import Notification

bp = Blueprint("notifications", __name__)

@bp.route("/notifications")
@login_required
def list_notifications():
    notifications = Notification.query.filter_by(
        student_id=current_user.id
    ).order_by(Notification.created_at.desc()).all()

    for n in notifications:
        n.is_read = True
    db.session.commit()

    return render_template("notifications.html", notifications=notifications)

@bp.route("/notifications/count")
@login_required
def count():
    unread = Notification.query.filter_by(
        student_id=current_user.id,
        is_read=False
    ).count()
    return jsonify({"count": unread})
