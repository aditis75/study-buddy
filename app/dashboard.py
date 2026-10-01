from flask import Blueprint
from flask_login import login_required

bp = Blueprint("dashboard", __name__)

@bp.route("/")
@login_required
def home():
    return "Dashboard - Person B module coming soon"
