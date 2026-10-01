from flask import Blueprint
from flask_login import login_required

bp = Blueprint("resources", __name__)

@bp.route("/resources")
@login_required
def list_notes():
    return "Resources - Person B module coming soon"
