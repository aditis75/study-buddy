from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
)
from flask_login import login_required, current_user

from . import db
from .models import (
    StudySession,
    SessionParticipant,
    Notification,
    SOSRequest,
    User,
)
from .utils import notify


bp = Blueprint(
    "study_sessions",
    __name__,
    url_prefix="/sessions",
)


# =========================================================
# LIST STUDY SESSIONS
# =========================================================

@bp.route("/")
@login_required
def list_sessions():

    sessions = StudySession.query.filter_by(
        status="active"
    ).order_by(
        StudySession.id.desc()
    ).all()

    return render_template(
        "sessions.html",
        sessions=sessions,
    )


# =========================================================
# CREATE STUDY SESSION
# =========================================================

@bp.route("/new", methods=["GET", "POST"])
@login_required
def create():

    if request.method == "POST":

        session = StudySession(
            subject=request.form.get(
                "subject",
                "",
            ).strip(),

            date=request.form.get(
                "date",
                "",
            ).strip(),

            time=request.form.get(
                "time",
                "",
            ).strip(),

            venue=request.form.get(
                "venue",
                "",
            ).strip(),

            max_participants=request.form.get(
                "max_participants",
                type=int,
            ) or 5,

            creator_id=current_user.id,
        )

        db.session.add(session)

        # Flush so session.id is available before commit.
        db.session.flush()

        # Creator automatically joins their own session.
        db.session.add(
            SessionParticipant(
                session_id=session.id,
                user_id=current_user.id,
            )
        )

        db.session.commit()

        flash(
            "Study session created.",
            "success",
        )

        return redirect(
            url_for(
                "study_sessions.detail",
                sid=session.id,
            )
        )

    return render_template(
        "session_form.html"
    )


# =========================================================
# SESSION DETAILS
# =========================================================

@bp.route("/<int:sid>")
@login_required
def detail(sid):

    session = db.session.get(
        StudySession,
        sid,
    )

    if not session:
        return "Session not found", 404


    # Get participant records.
    participants = SessionParticipant.query.filter_by(
        session_id=sid
    ).all()


    # -----------------------------------------------------
    # PARTICIPANT USER INFORMATION
    # -----------------------------------------------------
    # Create a dictionary:
    #
    # {
    #     user_id: User object
    # }
    #
    # This allows session_detail.html to display the
    # student's actual name, department and academic year.
    # -----------------------------------------------------

    participant_ids = [
        participant.user_id
        for participant in participants
    ]

    participant_users = {}

    if participant_ids:

        users = User.query.filter(
            User.id.in_(participant_ids)
        ).all()

        participant_users = {
            user.id: user
            for user in users
        }


    # -----------------------------------------------------
    # SOS REQUESTS
    # -----------------------------------------------------

    sos_requests = SOSRequest.query.filter_by(
        session_id=sid
    ).order_by(
        SOSRequest.created_at.desc()
    ).all()


    # Get users who created SOS requests.
    sos_user_ids = [
        sos.requester_id
        for sos in sos_requests
    ]

    sos_users = {}

    if sos_user_ids:

        users = User.query.filter(
            User.id.in_(sos_user_ids)
        ).all()

        sos_users = {
            user.id: user
            for user in users
        }


    return render_template(
        "session_detail.html",
        session=session,
        participants=participants,
        participant_users=participant_users,
        sos_requests=sos_requests,
        sos_users=sos_users,
    )


# =========================================================
# JOIN SESSION
# =========================================================

@bp.route("/<int:sid>/join", methods=["POST"])
@login_required
def join(sid):

    session = db.session.get(
        StudySession,
        sid,
    )

    if not session or session.status != "active":

        flash(
            "Session is unavailable.",
            "danger",
        )

        return redirect(
            url_for(
                "study_sessions.list_sessions"
            )
        )


    existing = SessionParticipant.query.filter_by(
        session_id=sid,
        user_id=current_user.id,
    ).first()


    count = SessionParticipant.query.filter_by(
        session_id=sid
    ).count()


    if existing:

        flash(
            "You already joined this session.",
            "info",
        )


    elif count >= session.max_participants:

        flash(
            "Session is full.",
            "danger",
        )


    else:

        db.session.add(
            SessionParticipant(
                session_id=sid,
                user_id=current_user.id,
            )
        )

        notify(
            session.creator_id,
            f"{current_user.name} joined your study session.",
            "session",
        )

        db.session.commit()

        flash(
            "You joined the session.",
            "success",
        )


    return redirect(
        url_for(
            "study_sessions.detail",
            sid=sid,
        )
    )


# =========================================================
# LEAVE SESSION
# =========================================================

@bp.route("/<int:sid>/leave", methods=["POST"])
@login_required
def leave(sid):

    participant = SessionParticipant.query.filter_by(
        session_id=sid,
        user_id=current_user.id,
    ).first()


    if participant:

        db.session.delete(
            participant
        )

        db.session.commit()

        flash(
            "You left the session.",
            "success",
        )


    return redirect(
        url_for(
            "study_sessions.detail",
            sid=sid,
        )
    )


# =========================================================
# EDIT SESSION
# =========================================================

@bp.route("/<int:sid>/edit", methods=["GET", "POST"])
@login_required
def edit(sid):

    session = db.session.get(
        StudySession,
        sid,
    )


    if (
        not session
        or session.creator_id != current_user.id
    ):
        return "Unauthorized", 403


    if request.method == "POST":

        session.subject = request.form.get(
            "subject",
            "",
        ).strip()

        session.date = request.form.get(
            "date",
            "",
        ).strip()

        session.time = request.form.get(
            "time",
            "",
        ).strip()

        session.venue = request.form.get(
            "venue",
            "",
        ).strip()

        session.max_participants = request.form.get(
            "max_participants",
            type=int,
        ) or 5


        db.session.commit()

        flash(
            "Session updated.",
            "success",
        )

        return redirect(
            url_for(
                "study_sessions.detail",
                sid=sid,
            )
        )


    return render_template(
        "session_form.html",
        session=session,
    )


# =========================================================
# CANCEL SESSION
# =========================================================

@bp.route("/<int:sid>/cancel", methods=["POST"])
@login_required
def cancel(sid):

    session = db.session.get(
        StudySession,
        sid,
    )


    if (
        not session
        or session.creator_id != current_user.id
    ):
        return "Unauthorized", 403


    session.status = "cancelled"


    participants = SessionParticipant.query.filter_by(
        session_id=sid
    ).all()


    for participant in participants:

        if participant.user_id != current_user.id:

            notify(
                participant.user_id,
                f"Study session '{session.subject}' was cancelled.",
                "session",
            )


    db.session.commit()

    flash(
        "Session cancelled.",
        "success",
    )


    return redirect(
        url_for(
            "study_sessions.list_sessions"
        )
    )