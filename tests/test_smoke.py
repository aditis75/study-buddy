from app import create_app
import io


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


def test_dashboard_access(client, app):
    from app.models import User
    from app import db

    with app.app_context():
        user = User(
            name="Dashboard Student",
            email="dashboard@mitwpu.edu.in",
            department="CSE",
            year=3,
            is_verified=True,
        )
        user.set_password("Valid@123")

        db.session.add(user)
        db.session.commit()

    client.post(
        "/login",
        data={
            "email": "dashboard@mitwpu.edu.in",
            "password": "Valid@123",
        },
    )

    response = client.get("/")

    assert response.status_code == 200
    assert b"Dashboard Student" in response.data


def test_buddy_search(client, app):
    from app.models import User
    from app import db

    with app.app_context():
        user1 = User(
            name="Buddy Searcher",
            email="buddysearcher@mitwpu.edu.in",
            department="CSE",
            year=3,
            subjects="DBMS, AI",
            is_verified=True,
        )
        user1.set_password("Valid@123")

        user2 = User(
            name="Database Buddy",
            email="databasebuddy@mitwpu.edu.in",
            department="CSE",
            year=3,
            subjects="DBMS",
            is_verified=True,
        )
        user2.set_password("Valid@123")

        db.session.add_all([user1, user2])
        db.session.commit()

    client.post(
        "/login",
        data={
            "email": "buddysearcher@mitwpu.edu.in",
            "password": "Valid@123",
        },
    )

    response = client.get(
        "/buddies?department=CSE&year=3&subject=DBMS"
    )

    assert response.status_code == 200
    assert b"Database Buddy" in response.data


def test_send_buddy_request(client, app):
    from app.models import User, StudyRequest, Notification
    from app import db

    with app.app_context():
        sender = User(
            name="Request Sender",
            email="requestsender@mitwpu.edu.in",
            is_verified=True,
        )
        sender.set_password("Valid@123")

        receiver = User(
            name="Request Receiver",
            email="requestreceiver@mitwpu.edu.in",
            is_verified=True,
        )
        receiver.set_password("Valid@123")

        db.session.add_all([sender, receiver])
        db.session.commit()

        sender_id = sender.id
        receiver_id = receiver.id

    client.post(
        "/login",
        data={
            "email": "requestsender@mitwpu.edu.in",
            "password": "Valid@123",
        },
    )

    response = client.post(
        f"/buddies/request/{receiver_id}",
        follow_redirects=False,
    )

    assert response.status_code == 302

    with app.app_context():
        study_request = StudyRequest.query.filter_by(
            sender_id=sender_id,
            receiver_id=receiver_id,
        ).first()

        assert study_request is not None
        assert study_request.status == "pending"

        notification = Notification.query.filter_by(
            student_id=receiver_id,
            type="buddy",
        ).first()

        assert notification is not None


def test_accept_buddy_request(client, app):
    from app.models import User, StudyRequest
    from app import db

    with app.app_context():
        sender = User(
            name="Buddy Sender",
            email="buddysender@mitwpu.edu.in",
            is_verified=True,
        )
        sender.set_password("Valid@123")

        receiver = User(
            name="Buddy Receiver",
            email="buddyreceiver@mitwpu.edu.in",
            is_verified=True,
        )
        receiver.set_password("Valid@123")

        db.session.add_all([sender, receiver])
        db.session.commit()

        study_request = StudyRequest(
            sender_id=sender.id,
            receiver_id=receiver.id,
            status="pending",
        )

        db.session.add(study_request)
        db.session.commit()

        request_id = study_request.id

    client.post(
        "/login",
        data={
            "email": "buddyreceiver@mitwpu.edu.in",
            "password": "Valid@123",
        },
    )

    response = client.post(
        f"/buddies/request/{request_id}/accept",
        follow_redirects=False,
    )

    assert response.status_code == 302

    with app.app_context():
        updated_request = db.session.get(
            StudyRequest,
            request_id,
        )

        assert updated_request.status == "accepted"


def test_reject_buddy_request(client, app):
    from app.models import User, StudyRequest
    from app import db

    with app.app_context():
        sender = User(
            name="Rejected Sender",
            email="rejectsender@mitwpu.edu.in",
            is_verified=True,
        )
        sender.set_password("Valid@123")

        receiver = User(
            name="Rejecting Receiver",
            email="rejectreceiver@mitwpu.edu.in",
            is_verified=True,
        )
        receiver.set_password("Valid@123")

        db.session.add_all([sender, receiver])
        db.session.commit()

        study_request = StudyRequest(
            sender_id=sender.id,
            receiver_id=receiver.id,
            status="pending",
        )

        db.session.add(study_request)
        db.session.commit()

        request_id = study_request.id

    client.post(
        "/login",
        data={
            "email": "rejectreceiver@mitwpu.edu.in",
            "password": "Valid@123",
        },
    )

    response = client.post(
        f"/buddies/request/{request_id}/reject",
        follow_redirects=False,
    )

    assert response.status_code == 302

    with app.app_context():
        updated_request = db.session.get(
            StudyRequest,
            request_id,
        )

        assert updated_request.status == "rejected"


def test_create_forum_post(client, app):
    from app.models import User, DiscussionPost
    from app import db

    with app.app_context():
        user = User(
            name="Forum Student",
            email="forumstudent@mitwpu.edu.in",
            is_verified=True,
        )
        user.set_password("Valid@123")

        db.session.add(user)
        db.session.commit()

        user_id = user.id

    client.post(
        "/login",
        data={
            "email": "forumstudent@mitwpu.edu.in",
            "password": "Valid@123",
        },
    )

    response = client.post(
        "/forum/new",
        data={
            "title": "Need help with DBMS",
            "content": "Can someone explain normalization?",
        },
        follow_redirects=False,
    )

    assert response.status_code == 302

    with app.app_context():
        post = DiscussionPost.query.filter_by(
            user_id=user_id,
            title="Need help with DBMS",
        ).first()

        assert post is not None
        assert "normalization" in post.content


def test_add_forum_comment(client, app):
    from app.models import User, DiscussionPost, Comment
    from app import db

    with app.app_context():
        author = User(
            name="Post Author",
            email="postauthor@mitwpu.edu.in",
            is_verified=True,
        )
        author.set_password("Valid@123")

        commenter = User(
            name="Forum Commenter",
            email="forumcommenter@mitwpu.edu.in",
            is_verified=True,
        )
        commenter.set_password("Valid@123")

        db.session.add_all([author, commenter])
        db.session.commit()

        post = DiscussionPost(
            user_id=author.id,
            title="Dynamic Programming",
            content="How does dynamic programming work?",
        )

        db.session.add(post)
        db.session.commit()

        post_id = post.id
        commenter_id = commenter.id

    client.post(
        "/login",
        data={
            "email": "forumcommenter@mitwpu.edu.in",
            "password": "Valid@123",
        },
    )

    response = client.post(
        f"/forum/{post_id}/comment",
        data={
            "content": "It stores solutions to repeated subproblems."
        },
        follow_redirects=False,
    )

    assert response.status_code == 302

    with app.app_context():
        comment = Comment.query.filter_by(
            post_id=post_id,
            user_id=commenter_id,
        ).first()

        assert comment is not None
        assert "repeated subproblems" in comment.content


def test_resource_upload_and_download(client, app, tmp_path):
    from app.models import User, Resource
    from app import db

    app.config["UPLOAD_FOLDER"] = str(tmp_path)

    with app.app_context():
        user = User(
            name="Resource Student",
            email="resource@mitwpu.edu.in",
            is_verified=True,
        )
        user.set_password("Valid@123")

        db.session.add(user)
        db.session.commit()

        user_id = user.id

    client.post(
        "/login",
        data={
            "email": "resource@mitwpu.edu.in",
            "password": "Valid@123",
        },
    )

    response = client.post(
        "/resources/upload",
        data={
            "title": "DBMS Test Notes",
            "subject": "DBMS",
            "description": "Normalization notes",
            "file": (
                io.BytesIO(b"Test DBMS resource content"),
                "dbms_notes.txt",
            ),
        },
        content_type="multipart/form-data",
        follow_redirects=False,
    )

    assert response.status_code == 302

    with app.app_context():
        resource = Resource.query.filter_by(
            user_id=user_id,
            title="DBMS Test Notes",
        ).first()

        assert resource is not None
        resource_id = resource.id

    response = client.get(
        f"/resources/download/{resource_id}"
    )

    assert response.status_code == 200
    assert b"Test DBMS resource content" in response.data


def test_student_cannot_access_admin(client, app):
    from app.models import User
    from app import db

    with app.app_context():
        student = User(
            name="Normal Student",
            email="normalstudent@mitwpu.edu.in",
            role="student",
            is_verified=True,
        )
        student.set_password("Valid@123")

        db.session.add(student)
        db.session.commit()

    client.post(
        "/login",
        data={
            "email": "normalstudent@mitwpu.edu.in",
            "password": "Valid@123",
        },
    )

    response = client.get("/admin")

    assert response.status_code == 403


def test_admin_can_access_panel(client, app):
    from app.models import User
    from app import db

    with app.app_context():
        admin = User(
            name="Test Admin",
            email="testadmin@mitwpu.edu.in",
            role="admin",
            is_verified=True,
        )
        admin.set_password("Admin@123")

        db.session.add(admin)
        db.session.commit()

    client.post(
        "/login",
        data={
            "email": "testadmin@mitwpu.edu.in",
            "password": "Admin@123",
        },
    )

    response = client.get("/admin")

    assert response.status_code == 200
    assert b"Admin Control Center" in response.data


def test_admin_suspend_and_unsuspend_user(client, app):
    from app.models import User
    from app import db

    with app.app_context():
        admin = User(
            name="Admin User",
            email="adminuser@mitwpu.edu.in",
            role="admin",
            is_verified=True,
        )
        admin.set_password("Admin@123")

        student = User(
            name="Student User",
            email="studentuser@mitwpu.edu.in",
            role="student",
            is_verified=True,
        )
        student.set_password("Valid@123")

        db.session.add_all([admin, student])
        db.session.commit()

        student_id = student.id

    client.post(
        "/login",
        data={
            "email": "adminuser@mitwpu.edu.in",
            "password": "Admin@123",
        },
    )

    response = client.post(
        f"/admin/suspend/{student_id}",
        follow_redirects=False,
    )

    assert response.status_code == 302

    with app.app_context():
        student = db.session.get(User, student_id)
        assert student.is_suspended is True

    response = client.post(
        f"/admin/unsuspend/{student_id}",
        follow_redirects=False,
    )

    assert response.status_code == 302

    with app.app_context():
        student = db.session.get(User, student_id)
        assert student.is_suspended is False


def test_admin_verify_user(client, app):
    from app.models import User
    from app import db

    with app.app_context():
        admin = User(
            name="Verification Admin",
            email="verificationadmin@mitwpu.edu.in",
            role="admin",
            is_verified=True,
        )
        admin.set_password("Admin@123")

        student = User(
            name="Unverified User",
            email="verifyme@mitwpu.edu.in",
            role="student",
            is_verified=False,
        )
        student.set_password("Valid@123")

        db.session.add_all([admin, student])
        db.session.commit()

        student_id = student.id

    client.post(
        "/login",
        data={
            "email": "verificationadmin@mitwpu.edu.in",
            "password": "Admin@123",
        },
    )

    response = client.post(
        f"/admin/verify/{student_id}",
        follow_redirects=False,
    )

    assert response.status_code == 302

    with app.app_context():
        student = db.session.get(User, student_id)
        assert student.is_verified is True