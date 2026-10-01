from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from . import db
from .models import StudySession, SessionParticipant, SOSRequest
from .utils import notify

bp = Blueprint("sos", __name__, url_prefix="/sos")

@bp.route("/raise/<int:sid>", methods=["POST"])
@login_required
def raise_sos(sid):
    session = db.session.get(StudySession, sid)
    participant = SessionParticipant.query.filter_by(
        session_id=sid, user_id=current_user.id
    ).first()

    if not session or not participant:
        return "You must be a participant to raise SOS.", 403

    message = request.form.get("message", "").strip()
    if not message:
        flash("Please describe your doubt.", "danger")
        return redirect(url_for("study_sessions.detail", sid=sid))

    sos = SOSRequest(
        session_id=sid,
        requester_id=current_user.id,
        message=message
    )
    db.session.add(sos)
    db.session.flush()

    participants = SessionParticipant.query.filter_by(session_id=sid).all()
    for p in participants:
        if p.user_id != current_user.id:
            notify(
                p.user_id,
                f"Urgent SOS from {current_user.name}: {message}",
                "sos",
                url_for("study_sessions.detail", sid=sid)
            )

    db.session.commit()
    flash("SOS raised. Other participants have been notified.", "success")
    return redirect(url_for("study_sessions.detail", sid=sid))

@bp.route("/<int:rid>/help", methods=["POST"])
@login_required
def help_request(rid):
    sos = db.session.get(SOSRequest, rid)
    if not sos or sos.status != "open":
        return "SOS is unavailable.", 404

    participant = SessionParticipant.query.filter_by(
        session_id=sos.session_id, user_id=current_user.id
    ).first()

    if not participant or sos.requester_id == current_user.id:
        return "Not allowed.", 403

    sos.helper_id = current_user.id
    notify(
        sos.requester_id,
        f"{current_user.name} can help with your SOS.",
        "sos"
    )
    db.session.commit()
    flash("The requester has been notified that you can help.", "success")
    return redirect(url_for("study_sessions.detail", sid=sos.session_id))

@bp.route("/<int:rid>/resolve", methods=["POST"])
@login_required
def resolve(rid):
    sos = db.session.get(SOSRequest, rid)
    if not sos or sos.requester_id != current_user.id:
        return "Unauthorized", 403

    sos.status = "resolved"
    if sos.helper_id:
        notify(sos.helper_id, "The SOS request was marked resolved.", "sos")
    db.session.commit()
    flash("SOS resolved.", "success")
    return redirect(url_for("study_sessions.detail", sid=sos.session_id))
