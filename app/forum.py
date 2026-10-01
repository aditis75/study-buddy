from flask import Blueprint
from flask_login import login_required

bp = Blueprint("forum", __name__)

@bp.route("/forum")
@login_required
def list_posts():
    return "Forum - Person B module coming soon"
