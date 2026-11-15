
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from extensions import get_db_connection

feedback_bp = Blueprint("feedback", __name__)


@feedback_bp.route("/feedback", methods=["GET", "POST"])
@login_required
def feedback_list():

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    if request.method == "POST":
        rating = request.form.get("rating", type=int)
        message = request.form.get("message", "").strip()

        if rating not in [1, 2, 3, 4, 5]:
            flash("Please select a valid rating.", "error")
        else:
            try:
                cursor.execute(
                    """
                    INSERT INTO feedback (user_id, rating, message)
                    VALUES (%s, %s, %s)
                    """,
                    (current_user.id, rating, message or None)
                )
                connection.commit()
            except Exception:
                connection.rollback()
                flash("Unable to submit feedback. Please try again.", "danger")
            finally:
                cursor.close()
                connection.close()

            flash("Thank you! Your feedback has been submitted.", "success")
            return redirect(url_for("feedback.feedback_list"))

    cursor.execute(
        """
        SELECT feedback_id, rating, message, created_at
        FROM feedback
        WHERE user_id = %s
        ORDER BY created_at DESC
        """,
        (current_user.id,)
    )

    feedbacks = cursor.fetchall()

    cursor.close()
    connection.close()

    return render_template(
        "feedback/list.html",
        feedbacks=feedbacks
    )
