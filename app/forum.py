from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user

from . import db
from .models import DiscussionPost, Comment, User


bp = Blueprint("forum", __name__)


@bp.route("/forum")
@login_required
def list_posts():
    posts = DiscussionPost.query.order_by(
        DiscussionPost.created_at.desc()
    ).all()

    users = {
        user.id: user
        for user in User.query.all()
    }

    return render_template(
        "forum.html",
        posts=posts,
        users=users,
    )


@bp.route("/forum/new", methods=["GET", "POST"])
@login_required
def create_post():
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        content = request.form.get("content", "").strip()

        if not title or not content:
            flash(
                "Title and discussion content are required.",
                "danger",
            )
            return render_template("forum_post_form.html")

        post = DiscussionPost(
            user_id=current_user.id,
            title=title,
            content=content,
        )

        db.session.add(post)
        db.session.commit()

        flash(
            "Discussion post created successfully.",
            "success",
        )

        return redirect(
            url_for("forum.view_post", post_id=post.id)
        )

    return render_template("forum_post_form.html")


@bp.route("/forum/<int:post_id>")
@login_required
def view_post(post_id):
    post = db.session.get(DiscussionPost, post_id)

    if not post:
        return "Discussion post not found.", 404

    author = db.session.get(User, post.user_id)

    comments = Comment.query.filter_by(
        post_id=post_id
    ).order_by(Comment.created_at.asc()).all()

    users = {
        user.id: user
        for user in User.query.all()
    }

    return render_template(
        "forum_post_detail.html",
        post=post,
        author=author,
        comments=comments,
        users=users,
    )


@bp.route("/forum/<int:post_id>/comment", methods=["POST"])
@login_required
def add_comment(post_id):
    post = db.session.get(DiscussionPost, post_id)

    if not post:
        return "Discussion post not found.", 404

    content = request.form.get("content", "").strip()

    if not content:
        flash(
            "Comment cannot be empty.",
            "danger",
        )

        return redirect(
            url_for("forum.view_post", post_id=post_id)
        )

    comment = Comment(
        post_id=post_id,
        user_id=current_user.id,
        content=content,
    )

    db.session.add(comment)
    db.session.commit()

    flash(
        "Comment added successfully.",
        "success",
    )

    return redirect(
        url_for("forum.view_post", post_id=post_id)
    )