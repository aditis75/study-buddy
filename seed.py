from app import create_app, db
from app.models import User

app = create_app()

with app.app_context():
    if not User.query.filter_by(email="admin@mitwpu.edu.in").first():
        admin = User(name="Admin", email="admin@mitwpu.edu.in", department="CSE", year=3, role="admin")
        admin.set_password("Admin@123")
        admin.is_verified = True
        db.session.add(admin)
        db.session.commit()
        print("Seeded admin: admin@mitwpu.edu.in / Admin@123")
    else:
        print("Seed data already exists.")
