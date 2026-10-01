from flask import Blueprint
from flask_login import login_required

bp = Blueprint("buddies", __name__)

@bp.route("/buddies")
@login_required
def find():
    return "Buddies - Person B module coming soon"
