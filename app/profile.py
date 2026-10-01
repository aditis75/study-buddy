from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from . import db

bp = Blueprint("profile", __name__)

@bp.route("/profile", methods=["GET", "POST"])
@login_required
def edit():
    if request.method == "POST":
        current_user.name = request.form.get("name", "").strip()
        current_user.department = request.form.get("department", "").strip()
        current_user.year = request.form.get("year", type=int)
        current_user.subjects = request.form.get("subjects", "").strip()
        current_user.study_preferences = request.form.get("study_preferences", "").strip()
        current_user.availability = request.form.get("availability", "").strip()
        current_user.interests = request.form.get("interests", "").strip()
        db.session.commit()
        flash("Profile updated.", "success")
        return redirect(url_for("profile.edit"))

    return render_template("profile.html")
