from flask import Blueprint, render_template, redirect, url_for
from flask_login import login_required, current_user

from .models import (
    StudySession,
    SessionParticipant,
    Notification,
    SOSRequest,
)


bp = Blueprint("dashboard", __name__)


@bp.route("/")
@login_required
def home():

    # Admins should use the Admin Control Center,
    # not the normal student dashboard.
    if current_user.role == "admin":
        return redirect(url_for("admin.panel"))

    # Get sessions joined by the current student.
    joined_records = SessionParticipant.query.filter_by(
        user_id=current_user.id
    ).all()

    session_ids = [
        record.session_id
        for record in joined_records
    ]

    joined_sessions = []

    if session_ids:
        joined_sessions = StudySession.query.filter(
            StudySession.id.in_(session_ids),
            StudySession.status == "active",
        ).all()

    # Get active sessions created by the current student.
    created_sessions = StudySession.query.filter_by(
        creator_id=current_user.id,
        status="active",
    ).all()

    # Count unread notifications.
    unread_notifications = Notification.query.filter_by(
        student_id=current_user.id,
        is_read=False,
    ).count()

    # Count open SOS requests created by the student.
    open_sos = SOSRequest.query.filter_by(
        requester_id=current_user.id,
        status="open",
    ).count()

    return render_template(
        "dashboard.html",
        joined_sessions=joined_sessions,
        created_sessions=created_sessions,
        unread_notifications=unread_notifications,
        open_sos=open_sos,
    )