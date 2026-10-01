from . import db
from .models import Notification

def notify(user_id, message, type_="general", link=None):
    db.session.add(Notification(
        student_id=user_id,
        message=message,
        type=type_,
        link=link
    ))
