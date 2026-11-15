from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from extensions import get_db_connection

notifications_bp = Blueprint("notifications", __name__)


@notifications_bp.route("/notifications")
@login_required
def notification_list():

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    cursor.execute(
        """
        SELECT notification_id, complaint_id, title, message,
               notification_type, is_read, created_at
        FROM notifications
        WHERE user_id = %s
        ORDER BY created_at DESC
        """,
        (current_user.id,)
    )

    notifications = cursor.fetchall()

    cursor.execute(
        """
        SELECT COUNT(*) AS unread_count
        FROM notifications
        WHERE user_id = %s AND is_read = FALSE
        """,
        (current_user.id,)
    )

    unread_count = cursor.fetchone()["unread_count"]

    cursor.close()
    connection.close()

    return render_template(
        "notifications/list.html",
        notifications=notifications,
        unread_count=unread_count
    )


@notifications_bp.route("/notifications/open/<int:notification_id>")
@login_required
def open_notification(notification_id):

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    cursor.execute(
        """
        SELECT notification_id, complaint_id
        FROM notifications
        WHERE notification_id = %s AND user_id = %s
        """,
        (notification_id, current_user.id)
    )

    notification = cursor.fetchone()

    if notification:
        cursor.execute(
            """
            UPDATE notifications
            SET is_read = TRUE
            WHERE notification_id = %s AND user_id = %s
            """,
            (notification_id, current_user.id)
        )
        connection.commit()

    cursor.close()
    connection.close()

    if not notification:
        flash("Notification not found.", "error")
        return redirect(url_for("notifications.notification_list"))

    if notification["complaint_id"]:
        return redirect(
            url_for(
                "complaints.complaint_details",
                complaint_id=notification["complaint_id"]
            )
        )

    return redirect(url_for("notifications.notification_list"))