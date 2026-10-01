from flask import Blueprint
from flask_login import login_required

bp = Blueprint("admin", __name__)

@bp.route("/admin")
@login_required
def panel():
    return "Admin - Person B module coming soon"
