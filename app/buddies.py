from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user

from . import db
from .models import User, StudyRequest
from .utils import notify


bp = Blueprint("buddies", __name__)


@bp.route("/buddies")
@login_required
def find():
    department = request.args.get("department", "").strip()
    year = request.args.get("year", type=int)
    subject = request.args.get("subject", "").strip()

    query = User.query.filter(
    User.id != current_user.id,
    User.role == "student",
    User.is_verified.is_(True),
    User.is_suspended.is_(False),
)

    if department:
        query = query.filter(
            User.department.ilike(f"%{department}%")
        )

    if year:
        query = query.filter(
            User.year == year
        )

    if subject:
        query = query.filter(
            User.subjects.ilike(f"%{subject}%")
        )

    buddies = query.order_by(User.name.asc()).all()

    # Existing requests involving logged-in student
    sent_requests = StudyRequest.query.filter_by(
        sender_id=current_user.id
    ).all()

    request_status = {
        study_request.receiver_id: study_request.status
        for study_request in sent_requests
    }

    return render_template(
        "buddies.html",
        buddies=buddies,
        department=department,
        year=year,
        subject=subject,
        request_status=request_status,
    )


@bp.route("/buddies/request/<int:user_id>", methods=["POST"])
@login_required
def send_request(user_id):
    receiver = db.session.get(User, user_id)

    if not receiver:
        flash("Student not found.", "danger")
        return redirect(url_for("buddies.find"))

    if receiver.role != "student":
        flash("Study requests can only be sent to student accounts.", "danger")
        return redirect(url_for("buddies.find"))

    if receiver.id == current_user.id:
        flash("You cannot send a request to yourself.", "danger")
        return redirect(url_for("buddies.find"))

    existing = StudyRequest.query.filter_by(
        sender_id=current_user.id,
        receiver_id=receiver.id,
    ).first()

    if existing:
        flash("You have already sent a study request to this student.", "info")
        return redirect(url_for("buddies.find"))

    study_request = StudyRequest(
        sender_id=current_user.id,
        receiver_id=receiver.id,
        status="pending",
    )

    db.session.add(study_request)

    notify(
        receiver.id,
        f"{current_user.name} sent you a study buddy request.",
        "buddy",
        url_for("buddies.requests"),
    )

    db.session.commit()

    flash("Study buddy request sent.", "success")

    return redirect(url_for("buddies.find"))


@bp.route("/buddies/requests")
@login_required
def requests():
    incoming = StudyRequest.query.filter_by(
        receiver_id=current_user.id
    ).order_by(StudyRequest.created_at.desc()).all()

    outgoing = StudyRequest.query.filter_by(
        sender_id=current_user.id
    ).order_by(StudyRequest.created_at.desc()).all()

    users = {
        user.id: user
        for user in User.query.all()
    }

    return render_template(
        "buddy_requests.html",
        incoming=incoming,
        outgoing=outgoing,
        users=users,
    )


@bp.route("/buddies/request/<int:request_id>/accept", methods=["POST"])
@login_required
def accept_request(request_id):
    study_request = db.session.get(StudyRequest, request_id)

    if not study_request or study_request.receiver_id != current_user.id:
        return "Unauthorized", 403

    if study_request.status != "pending":
        flash("This request has already been processed.", "info")
        return redirect(url_for("buddies.requests"))

    study_request.status = "accepted"

    notify(
        study_request.sender_id,
        f"{current_user.name} accepted your study buddy request.",
        "buddy",
    )

    db.session.commit()

    flash("Study buddy request accepted.", "success")

    return redirect(url_for("buddies.requests"))


@bp.route("/buddies/request/<int:request_id>/reject", methods=["POST"])
@login_required
def reject_request(request_id):
    study_request = db.session.get(StudyRequest, request_id)

    if not study_request or study_request.receiver_id != current_user.id:
        return "Unauthorized", 403

    if study_request.status != "pending":
        flash("This request has already been processed.", "info")
        return redirect(url_for("buddies.requests"))

    study_request.status = "rejected"

    notify(
        study_request.sender_id,
        f"{current_user.name} declined your study buddy request.",
        "buddy",
    )

    db.session.commit()

    flash("Study buddy request declined.", "success")

    return redirect(url_for("buddies.requests"))