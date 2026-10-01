from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from . import db
from .models import StudySession, SessionParticipant, Notification, SOSRequest
from .utils import notify

bp = Blueprint("study_sessions", __name__, url_prefix="/sessions")

@bp.route("/")
@login_required
def list_sessions():
    sessions = StudySession.query.filter_by(status="active").order_by(StudySession.id.desc()).all()
    return render_template("sessions.html", sessions=sessions)

@bp.route("/new", methods=["GET", "POST"])
@login_required
def create():
    if request.method == "POST":
        session = StudySession(
            subject=request.form.get("subject", "").strip(),
            date=request.form.get("date", "").strip(),
            time=request.form.get("time", "").strip(),
            venue=request.form.get("venue", "").strip(),
            max_participants=request.form.get("max_participants", type=int) or 5,
            creator_id=current_user.id
        )
        db.session.add(session)
        db.session.flush()
        db.session.add(SessionParticipant(session_id=session.id, user_id=current_user.id))
        db.session.commit()
        flash("Study session created.", "success")
        return redirect(url_for("study_sessions.detail", sid=session.id))
    return render_template("session_form.html")

@bp.route("/<int:sid>")
@login_required
def detail(sid):
    session = db.session.get(StudySession, sid)

    if not session:
        return "Session not found", 404

    participants = SessionParticipant.query.filter_by(
        session_id=sid
    ).all()

    sos_requests = SOSRequest.query.filter_by(
        session_id=sid
    ).order_by(SOSRequest.created_at.desc()).all()

    return render_template(
        "session_detail.html",
        session=session,
        participants=participants,
        sos_requests=sos_requests
    )

@bp.route("/<int:sid>/join", methods=["POST"])
@login_required
def join(sid):
    session = db.session.get(StudySession, sid)
    if not session or session.status != "active":
        flash("Session is unavailable.", "danger")
        return redirect(url_for("study_sessions.list_sessions"))

    existing = SessionParticipant.query.filter_by(session_id=sid, user_id=current_user.id).first()
    count = SessionParticipant.query.filter_by(session_id=sid).count()
    if existing:
        flash("You already joined this session.", "info")
    elif count >= session.max_participants:
        flash("Session is full.", "danger")
    else:
        db.session.add(SessionParticipant(session_id=sid, user_id=current_user.id))
        notify(session.creator_id, f"{current_user.name} joined your study session.", "session")
        db.session.commit()
        flash("You joined the session.", "success")
    return redirect(url_for("study_sessions.detail", sid=sid))

@bp.route("/<int:sid>/leave", methods=["POST"])
@login_required
def leave(sid):
    participant = SessionParticipant.query.filter_by(session_id=sid, user_id=current_user.id).first()
    if participant:
        db.session.delete(participant)
        db.session.commit()
        flash("You left the session.", "success")
    return redirect(url_for("study_sessions.detail", sid=sid))

@bp.route("/<int:sid>/edit", methods=["GET", "POST"])
@login_required
def edit(sid):
    session = db.session.get(StudySession, sid)
    if not session or session.creator_id != current_user.id:
        return "Unauthorized", 403
    if request.method == "POST":
        session.subject = request.form.get("subject", "").strip()
        session.date = request.form.get("date", "").strip()
        session.time = request.form.get("time", "").strip()
        session.venue = request.form.get("venue", "").strip()
        session.max_participants = request.form.get("max_participants", type=int) or 5
        db.session.commit()
        flash("Session updated.", "success")
        return redirect(url_for("study_sessions.detail", sid=sid))
    return render_template("session_form.html", session=session)

@bp.route("/<int:sid>/cancel", methods=["POST"])
@login_required
def cancel(sid):
    session = db.session.get(StudySession, sid)
    if not session or session.creator_id != current_user.id:
        return "Unauthorized", 403
    session.status = "cancelled"
    for p in SessionParticipant.query.filter_by(session_id=sid).all():
        if p.user_id != current_user.id:
            notify(p.user_id, f"Study session '{session.subject}' was cancelled.", "session")
    db.session.commit()
    flash("Session cancelled.", "success")
    return redirect(url_for("study_sessions.list_sessions"))
