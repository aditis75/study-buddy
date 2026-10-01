from flask import Blueprint, render_template
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
    # Sessions joined by the logged-in student
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

    # Sessions created by the student
    created_sessions = StudySession.query.filter_by(
        creator_id=current_user.id,
        status="active",
    ).all()

    # Unread notifications
    unread_notifications = Notification.query.filter_by(
        student_id=current_user.id,
        is_read=False,
    ).count()

    # Open SOS requests created by the student
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