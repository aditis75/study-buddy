from app import create_app


def test_app_starts(app):
    assert app is not None


def test_auth_routes_exist(client):
    assert client.get("/login").status_code == 200
    assert client.get("/register").status_code == 200


def test_register_rejects_non_college_email(client):

    response = client.post(
        "/register",
        data={
            "name": "Test Student",
            "email": "student@gmail.com",
            "department": "CSE",
            "year": "3",
            "password": "Test@123",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"mitwpu.edu.in" in response.data


def test_register_rejects_weak_password(client):

    response = client.post(
        "/register",
        data={
            "name": "Test Student",
            "email": "testweak@mitwpu.edu.in",
            "department": "CSE",
            "year": "3",
            "password": "password",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Password" in response.data


def test_successful_registration(client):
    response = client.post(
        "/register",
        data={
            "name": "Test Student",
            "email": "validuser@mitwpu.edu.in",
            "department": "CSE",
            "year": "3",
            "password": "Valid@123",
        },
        follow_redirects=False,
    )

    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_unverified_user_cannot_login(client):

    client.post(
        "/register",
        data={
            "name": "Unverified Student",
            "email": "unverified@mitwpu.edu.in",
            "department": "CSE",
            "year": "3",
            "password": "Valid@123",
        },
    )

    response = client.post(
        "/login",
        data={
            "email": "unverified@mitwpu.edu.in",
            "password": "Valid@123",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"verify" in response.data.lower()


def test_profile_update(client, app):

    # Register user
    client.post(
        "/register",
        data={
            "name": "Profile Student",
            "email": "profiletest@mitwpu.edu.in",
            "department": "CSE",
            "year": "3",
            "password": "Valid@123",
        },
    )

    from app.models import User
    from app import db

    # Verify account
    with app.app_context():
        user = User.query.filter_by(
            email="profiletest@mitwpu.edu.in"
        ).first()

        assert user is not None

        user.is_verified = True
        db.session.commit()

    # Login
    client.post(
        "/login",
        data={
            "email": "profiletest@mitwpu.edu.in",
            "password": "Valid@123",
        },
    )

    # Update profile
    response = client.post(
        "/profile",
        data={
            "name": "Updated Student",
            "department": "CSE",
            "year": "3",
            "subjects": "DAA, DBMS, AI",
            "study_preferences": "Group study",
            "availability": "Evenings",
            "interests": "Python, AI",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Profile updated" in response.data


def test_create_study_session(client, app):
    from app.models import User, StudySession

    # Create a verified user
    with app.app_context():
        user = User(
            name="Session Creator",
            email="sessioncreator@mitwpu.edu.in",
            department="CSE",
            year=3,
            is_verified=True,
        )
        user.set_password("Valid@123")

        from app import db
        db.session.add(user)
        db.session.commit()

    # Login
    client.post(
        "/login",
        data={
            "email": "sessioncreator@mitwpu.edu.in",
            "password": "Valid@123",
        },
    )

    # Create study session
    response = client.post(
        "/sessions/new",
        data={
            "subject": "Data Structures",
            "date": "2026-10-10",
            "time": "18:00",
            "venue": "Library",
            "max_participants": "5",
        },
        follow_redirects=False,
    )

    assert response.status_code == 302
    assert "/sessions/" in response.headers["Location"]

    # Verify session was actually stored
    with app.app_context():
        session = StudySession.query.filter_by(
            subject="Data Structures"
        ).first()

        assert session is not None
        assert session.venue == "Library"
        assert session.max_participants == 5
        assert session.status == "active"

def test_join_study_session(client, app):
    from app.models import User, StudySession, SessionParticipant
    from app import db

    with app.app_context():
        creator = User(
            name="Session Creator",
            email="joincreator@mitwpu.edu.in",
            department="CSE",
            year=3,
            is_verified=True,
        )
        creator.set_password("Valid@123")

        student = User(
            name="Joining Student",
            email="joiningstudent@mitwpu.edu.in",
            department="CSE",
            year=3,
            is_verified=True,
        )
        student.set_password("Valid@123")

        db.session.add_all([creator, student])
        db.session.commit()

        session = StudySession(
            subject="DBMS",
            date="2026-10-11",
            time="17:00",
            venue="Library",
            max_participants=5,
            creator_id=creator.id,
        )

        db.session.add(session)
        db.session.commit()

        session_id = session.id
        student_id = student.id

    # Login as the student who wants to join
    client.post(
        "/login",
        data={
            "email": "joiningstudent@mitwpu.edu.in",
            "password": "Valid@123",
        },
    )

    response = client.post(
        f"/sessions/{session_id}/join",
        follow_redirects=False,
    )

    assert response.status_code == 302
    assert f"/sessions/{session_id}" in response.headers["Location"]

    # Verify that the student was added
    with app.app_context():
        participant = SessionParticipant.query.filter_by(
            session_id=session_id,
            user_id=student_id,
        ).first()

        assert participant is not None


def test_leave_study_session(client, app):
    from app.models import User, StudySession, SessionParticipant
    from app import db

    with app.app_context():
        user = User(
            name="Leaving Student",
            email="leavingstudent@mitwpu.edu.in",
            department="CSE",
            year=3,
            is_verified=True,
        )
        user.set_password("Valid@123")

        db.session.add(user)
        db.session.commit()

        user_id = user.id

        session = StudySession(
            subject="Algorithms",
            date="2026-10-12",
            time="18:00",
            venue="Library",
            max_participants=5,
            creator_id=user_id,
        )

        db.session.add(session)
        db.session.commit()

        session_id = session.id

        participant = SessionParticipant(
            session_id=session_id,
            user_id=user_id,
        )

        db.session.add(participant)
        db.session.commit()

    # Login
    client.post(
        "/login",
        data={
            "email": "leavingstudent@mitwpu.edu.in",
            "password": "Valid@123",
        },
    )

    # Leave the session
    response = client.post(
        f"/sessions/{session_id}/leave",
        follow_redirects=False,
    )

    assert response.status_code == 302
    assert f"/sessions/{session_id}" in response.headers["Location"]

    # Verify participant was removed
    with app.app_context():
        participant = SessionParticipant.query.filter_by(
            session_id=session_id,
            user_id=user_id,
        ).first()

        assert participant is None


def test_cancel_study_session(client, app):
    from app.models import User, StudySession
    from app import db

    with app.app_context():
        user = User(
            name="Session Owner",
            email="cancelowner@mitwpu.edu.in",
            department="CSE",
            year=3,
            is_verified=True,
        )
        user.set_password("Valid@123")

        db.session.add(user)
        db.session.commit()

        user_id = user.id

        session = StudySession(
            subject="Operating Systems",
            date="2026-10-13",
            time="17:00",
            venue="Library",
            max_participants=5,
            creator_id=user_id,
        )

        db.session.add(session)
        db.session.commit()

        session_id = session.id

    # Login as session owner
    client.post(
        "/login",
        data={
            "email": "cancelowner@mitwpu.edu.in",
            "password": "Valid@123",
        },
    )

    # Cancel session
    response = client.post(
        f"/sessions/{session_id}/cancel",
        follow_redirects=False,
    )

    assert response.status_code == 302
    assert "/sessions/" in response.headers["Location"]

    # Verify session is cancelled
    with app.app_context():
        cancelled_session = db.session.get(
            StudySession,
            session_id,
        )

        assert cancelled_session is not None
        assert cancelled_session.status == "cancelled"


def test_raise_sos(client, app):
    from app.models import User, StudySession, SessionParticipant, SOSRequest
    from app import db

    with app.app_context():
        # Create student
        user = User(
            name="SOS Student",
            email="sosstudent@mitwpu.edu.in",
            department="CSE",
            year=3,
            is_verified=True,
        )
        user.set_password("Valid@123")

        db.session.add(user)
        db.session.commit()

        user_id = user.id

        # Create study session
        session = StudySession(
            subject="DAA",
            date="2026-10-14",
            time="18:00",
            venue="Library",
            max_participants=5,
            creator_id=user_id,
        )

        db.session.add(session)
        db.session.commit()

        session_id = session.id

        # Add student as participant
        participant = SessionParticipant(
            session_id=session_id,
            user_id=user_id,
        )

        db.session.add(participant)
        db.session.commit()

    # Login as participant
    client.post(
        "/login",
        data={
            "email": "sosstudent@mitwpu.edu.in",
            "password": "Valid@123",
        },
    )

    # Raise SOS
    response = client.post(
        f"/sos/raise/{session_id}",
        data={
            "message": "I need help understanding dynamic programming."
        },
        follow_redirects=False,
    )

    assert response.status_code == 302
    assert f"/sessions/{session_id}" in response.headers["Location"]

    # Verify SOS was stored
    with app.app_context():
        sos = SOSRequest.query.filter_by(
            session_id=session_id,
            requester_id=user_id,
        ).first()

        assert sos is not None
        assert sos.message == "I need help understanding dynamic programming."
        assert sos.status == "open"
        assert sos.helper_id is None


def test_help_sos_request(client, app):
    from app.models import User, StudySession, SessionParticipant, SOSRequest, Notification
    from app import db

    with app.app_context():
        # Create two verified students
        requester = User(
            name="SOS Requester",
            email="requester@mitwpu.edu.in",
            is_verified=True,
        )
        requester.set_password("Valid@123")

        helper = User(
            name="SOS Helper",
            email="helper@mitwpu.edu.in",
            is_verified=True,
        )
        helper.set_password("Valid@123")

        db.session.add_all([requester, helper])
        db.session.commit()

        requester_id = requester.id
        helper_id = helper.id

        # Create a study session
        session = StudySession(
            subject="DBMS",
            date="2026-10-15",
            time="17:00",
            venue="Library",
            max_participants=5,
            creator_id=requester_id,
        )

        db.session.add(session)
        db.session.commit()

        session_id = session.id

        # Both students participate
        db.session.add_all([
            SessionParticipant(
                session_id=session_id,
                user_id=requester_id,
            ),
            SessionParticipant(
                session_id=session_id,
                user_id=helper_id,
            ),
        ])

        # Create an open SOS request
        sos = SOSRequest(
            session_id=session_id,
            requester_id=requester_id,
            message="Please help me understand SQL joins.",
            status="open",
        )

        db.session.add(sos)
        db.session.commit()

        sos_id = sos.id

    # Login as the helper
    client.post(
        "/login",
        data={
            "email": "helper@mitwpu.edu.in",
            "password": "Valid@123",
        },
    )

    # Click "I Can Help"
    response = client.post(
        f"/sos/{sos_id}/help",
        follow_redirects=False,
    )

    assert response.status_code == 302
    assert f"/sessions/{session_id}" in response.headers["Location"]

    # Verify helper assignment and notification
    with app.app_context():
        updated_sos = db.session.get(SOSRequest, sos_id)

        assert updated_sos.helper_id == helper_id

        notification = Notification.query.filter_by(
            student_id=requester_id,
            type="sos",
        ).first()

        assert notification is not None
        assert "can help" in notification.message


def test_resolve_sos_request(client, app):
    from app.models import User, StudySession, SessionParticipant, SOSRequest, Notification
    from app import db

    with app.app_context():
        # Create requester
        requester = User(
            name="SOS Requester",
            email="resolver@mitwpu.edu.in",
            is_verified=True,
        )
        requester.set_password("Valid@123")

        # Create helper
        helper = User(
            name="SOS Helper",
            email="resolvehelper@mitwpu.edu.in",
            is_verified=True,
        )
        helper.set_password("Valid@123")

        db.session.add_all([requester, helper])
        db.session.commit()

        requester_id = requester.id
        helper_id = helper.id

        # Create study session
        session = StudySession(
            subject="Artificial Intelligence",
            date="2026-10-16",
            time="18:00",
            venue="Library",
            max_participants=5,
            creator_id=requester_id,
        )

        db.session.add(session)
        db.session.commit()

        session_id = session.id

        # Add both students as participants
        db.session.add_all([
            SessionParticipant(
                session_id=session_id,
                user_id=requester_id,
            ),
            SessionParticipant(
                session_id=session_id,
                user_id=helper_id,
            ),
        ])

        # Create SOS with helper already assigned
        sos = SOSRequest(
            session_id=session_id,
            requester_id=requester_id,
            message="Need help with minimax algorithm.",
            helper_id=helper_id,
            status="open",
        )

        db.session.add(sos)
        db.session.commit()

        sos_id = sos.id

    # Login as SOS requester
    client.post(
        "/login",
        data={
            "email": "resolver@mitwpu.edu.in",
            "password": "Valid@123",
        },
    )

    # Mark SOS as resolved
    response = client.post(
        f"/sos/{sos_id}/resolve",
        follow_redirects=False,
    )

    assert response.status_code == 302
    assert f"/sessions/{session_id}" in response.headers["Location"]

    # Verify SOS status and helper notification
    with app.app_context():
        resolved_sos = db.session.get(SOSRequest, sos_id)

        assert resolved_sos.status == "resolved"

        notification = Notification.query.filter_by(
            student_id=helper_id,
            type="sos",
        ).first()

        assert notification is not None
        assert "marked resolved" in notification.message