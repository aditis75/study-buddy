import os
from uuid import uuid4

from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    current_app,
    send_from_directory,
)
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename

from . import db
from .models import Resource, User


bp = Blueprint("resources", __name__)


ALLOWED_EXTENSIONS = {
    "pdf",
    "doc",
    "docx",
    "ppt",
    "pptx",
    "txt",
}


def allowed_file(filename):
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS
    )


@bp.route("/resources")
@login_required
def list_notes():
    subject = request.args.get("subject", "").strip()

    query = Resource.query

    if subject:
        query = query.filter(
            Resource.subject.ilike(f"%{subject}%")
        )

    resources = query.order_by(
        Resource.created_at.desc()
    ).all()

    users = {
        user.id: user
        for user in User.query.all()
    }

    return render_template(
        "resources.html",
        resources=resources,
        users=users,
        subject=subject,
    )


@bp.route("/resources/upload", methods=["GET", "POST"])
@login_required
def upload():
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        description = request.form.get(
            "description", ""
        ).strip()
        subject = request.form.get("subject", "").strip()

        file = request.files.get("file")

        if not title or not subject:
            flash(
                "Title and subject are required.",
                "danger",
            )
            return render_template("resource_upload.html")

        if not file or file.filename == "":
            flash(
                "Please select a file.",
                "danger",
            )
            return render_template("resource_upload.html")

        if not allowed_file(file.filename):
            flash(
                "Only PDF, DOC, DOCX, PPT, PPTX and TXT files are allowed.",
                "danger",
            )
            return render_template("resource_upload.html")

        original_name = secure_filename(file.filename)

        unique_name = (
            f"{uuid4().hex}_{original_name}"
        )

        upload_folder = current_app.config[
            "UPLOAD_FOLDER"
        ]

        os.makedirs(
            upload_folder,
            exist_ok=True,
        )

        file.save(
            os.path.join(
                upload_folder,
                unique_name,
            )
        )

        resource = Resource(
            title=title,
            description=description,
            subject=subject,
            file_path=unique_name,
            user_id=current_user.id,
        )

        db.session.add(resource)
        db.session.commit()

        flash(
            "Resource uploaded successfully.",
            "success",
        )

        return redirect(
            url_for("resources.list_notes")
        )

    return render_template(
        "resource_upload.html"
    )


@bp.route("/resources/download/<int:resource_id>")
@login_required
def download(resource_id):
    resource = db.session.get(
        Resource,
        resource_id,
    )

    if not resource:
        return "Resource not found.", 404

    upload_folder = current_app.config[
        "UPLOAD_FOLDER"
    ]

    return send_from_directory(
        upload_folder,
        resource.file_path,
        as_attachment=True,
    )