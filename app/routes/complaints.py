
import os
import uuid

from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    current_app,
    abort,
    send_from_directory
)

from flask_login import login_required, current_user
from werkzeug.utils import secure_filename

from extensions import get_db_connection


complaints_bp = Blueprint("complaints", __name__)

ALLOWED_EXTENSIONS = {"pdf", "png", "jpg", "jpeg", "doc", "docx"}

MAX_FILE_SIZE = 5 * 1024 * 1024


# --------------------------------------------------
# HELPER FUNCTIONS
# --------------------------------------------------

def allowed_file(filename):
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS
    )


def admin_required():
    if (current_user.role or "").strip().lower() != "admin":
        abort(403)


def get_upload_folder():
    return os.path.abspath(
        os.path.join(
            current_app.root_path,
            "..",
            "uploads",
            "complaints"
        )
    )


# --------------------------------------------------
# 1. VIEW MY COMPLAINTS
# --------------------------------------------------

@complaints_bp.route("/complaints")
@login_required
def my_complaints():

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        cursor.execute(
            """
            SELECT complaint_id, tracking_id, subject,
                   location, status, created_at
            FROM complaints
            WHERE user_id = %s
            ORDER BY created_at DESC
            """,
            (current_user.id,)
        )

        complaints = cursor.fetchall()

    finally:
        cursor.close()
        connection.close()

    return render_template(
        "complaints/list.html",
        complaints=complaints
    )


# --------------------------------------------------
# 2. SUBMIT COMPLAINT
# --------------------------------------------------

@complaints_bp.route("/complaints/submit", methods=["GET", "POST"])
@login_required
def submit_complaint():

    if request.method == "POST":

        subject = request.form.get("subject", "").strip()
        description = request.form.get("description", "").strip()
        location = request.form.get("location", "").strip()
        uploaded_file = request.files.get("attachment")

        if not subject or not description:
            flash("Subject and description are required.", "danger")
            return redirect(url_for("complaints.submit_complaint"))

        has_file = uploaded_file and uploaded_file.filename

        if has_file:

            if not allowed_file(uploaded_file.filename):
                flash("Invalid file type.", "danger")
                return redirect(url_for("complaints.submit_complaint"))

            uploaded_file.seek(0, os.SEEK_END)
            file_size = uploaded_file.tell()
            uploaded_file.seek(0)

            if file_size > MAX_FILE_SIZE:
                flash("File size must not exceed 5 MB.", "danger")
                return redirect(url_for("complaints.submit_complaint"))

        else:
            file_size = None

        original_filename = None
        stored_filename = None
        saved_file_path = None

        tracking_id = "CIV-" + uuid.uuid4().hex[:10].upper()

        connection = get_db_connection()
        cursor = connection.cursor()

        try:

            # Insert complaint
            cursor.execute(
                """
                INSERT INTO complaints
                (tracking_id, user_id, subject, description, location, status)
                VALUES (%s, %s, %s, %s, %s, 'Pending')
                """,
                (
                    tracking_id,
                    current_user.id,
                    subject,
                    description,
                    location or None
                )
            )

            complaint_id = cursor.lastrowid

            # Save attachment
            if has_file:

                original_filename = secure_filename(
                    uploaded_file.filename
                )

                if not original_filename or "." not in original_filename:
                    abort(400)

                extension = original_filename.rsplit(".", 1)[1].lower()

                stored_filename = (
                    f"{uuid.uuid4().hex}.{extension}"
                )

                upload_folder = get_upload_folder()
                os.makedirs(upload_folder, exist_ok=True)

                saved_file_path = os.path.join(
                    upload_folder,
                    stored_filename
                )

                uploaded_file.save(saved_file_path)

                cursor.execute(
                    """
                    INSERT INTO complaint_attachments
                    (complaint_id, original_filename, stored_filename,
                     file_type, file_size)
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    (
                        complaint_id,
                        original_filename,
                        stored_filename,
                        uploaded_file.mimetype,
                        file_size
                    )
                )

            # Insert initial complaint history
            cursor.execute(
                """
                INSERT INTO complaint_history
                (complaint_id, previous_status, new_status,
                 remarks, changed_by)
                VALUES (%s, NULL, 'Pending', %s, %s)
                """,
                (
                    complaint_id,
                    "Complaint submitted",
                    current_user.id
                )
            )

            # Create submission notification
            cursor.execute(
                """
                INSERT INTO notifications
                (user_id, complaint_id, title, message,
                 notification_type, is_read)
                VALUES (%s, %s, %s, %s, %s, FALSE)
                """,
                (
                    current_user.id,
                    complaint_id,
                    "Complaint Submitted",
                    (
                        f"Your complaint '{subject}' has been "
                        f"submitted successfully. Tracking ID: {tracking_id}"
                    ),
                    "Complaint"
                )
            )

            connection.commit()

            flash(
                f"Complaint submitted successfully! Tracking ID: {tracking_id}",
                "success"
            )

        except Exception:
            connection.rollback()

            # Remove uploaded file if database operation fails
            if saved_file_path and os.path.exists(saved_file_path):
                try:
                    os.remove(saved_file_path)
                except OSError:
                    current_app.logger.exception(
                        "Could not remove failed complaint attachment."
                    )

            raise

        finally:
            cursor.close()
            connection.close()

        return redirect(url_for("complaints.my_complaints"))

    return render_template("complaints/submit.html")


# --------------------------------------------------
# 3. TRACK COMPLAINT
# --------------------------------------------------

@complaints_bp.route("/complaints/track", methods=["GET", "POST"])
@login_required
def track_complaint():

    if request.method == "POST":

        tracking_id = request.form.get(
            "tracking_id", ""
        ).strip().upper()

        if not tracking_id:
            flash("Please enter a tracking ID.", "danger")
            return redirect(url_for("complaints.track_complaint"))

        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        try:
            cursor.execute(
                """
                SELECT complaint_id
                FROM complaints
                WHERE tracking_id = %s AND user_id = %s
                """,
                (tracking_id, current_user.id)
            )

            complaint = cursor.fetchone()

        finally:
            cursor.close()
            connection.close()

        if complaint:
            return redirect(
                url_for(
                    "complaints.complaint_details",
                    complaint_id=complaint["complaint_id"]
                )
            )

        flash(
            "Complaint not found. Check your tracking ID.",
            "danger"
        )

    return render_template("complaints/track.html")


# --------------------------------------------------
# 4. COMPLAINT DETAILS AND HISTORY
# --------------------------------------------------

@complaints_bp.route("/complaints/details/<int:complaint_id>")
@login_required
def complaint_details(complaint_id):

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    try:

        # Get complaint details
        cursor.execute(
            """
            SELECT complaint_id, tracking_id, subject, description,
                   location, status, created_at, updated_at
            FROM complaints
            WHERE complaint_id = %s AND user_id = %s
            """,
            (complaint_id, current_user.id)
        )

        complaint = cursor.fetchone()

        if not complaint:
            abort(404)

        # Get complaint history
        cursor.execute(
            """
            SELECT previous_status, new_status, remarks,
                   changed_at
            FROM complaint_history
            WHERE complaint_id = %s
            ORDER BY changed_at DESC, history_id DESC
            """,
            (complaint_id,)
        )

        history = cursor.fetchall()

        # Get complaint attachments
        cursor.execute(
            """
            SELECT attachment_id, original_filename,
                   stored_filename, file_type, file_size
            FROM complaint_attachments
            WHERE complaint_id = %s
            ORDER BY attachment_id DESC
            """,
            (complaint_id,)
        )

        attachments = cursor.fetchall()

    finally:
        cursor.close()
        connection.close()

    return render_template(
        "complaints/details.html",
        complaint=complaint,
        history=history,
        attachments=attachments
    )


# --------------------------------------------------
# 5. ADMIN VIEW COMPLAINTS
# --------------------------------------------------

@complaints_bp.route("/admin/complaints")
@login_required
def admin_complaints():

    admin_required()

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        cursor.execute(
            """
            SELECT c.complaint_id, c.tracking_id, c.subject,
                   c.location, c.status, c.created_at,
                   u.full_name, u.email
            FROM complaints c
            JOIN users u ON c.user_id = u.user_id
            ORDER BY c.created_at DESC
            """
        )

        complaints = cursor.fetchall()

    finally:
        cursor.close()
        connection.close()

    return render_template(
        "complaints/admin_list.html",
        complaints=complaints
    )


# --------------------------------------------------
# 6. ADMIN UPDATE COMPLAINT STATUS
# --------------------------------------------------

@complaints_bp.route(
    "/admin/complaints/update/<int:complaint_id>",
    methods=["POST"]
)
@login_required
def update_complaint_status(complaint_id):

    admin_required()

    new_status = request.form.get("status", "").strip()
    remarks = request.form.get("remarks", "").strip()

    allowed_statuses = {
        "Pending",
        "In Progress",
        "Resolved"
    }

    if new_status not in allowed_statuses:
        abort(400)

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    try:

        # Get complaint owner and current status
        cursor.execute(
            """
            SELECT user_id, status
            FROM complaints
            WHERE complaint_id = %s
            FOR UPDATE
            """,
            (complaint_id,)
        )

        complaint = cursor.fetchone()

        if not complaint:
            abort(404)

        previous_status = complaint["status"]
        complaint_user_id = complaint["user_id"]

        # Update complaint status
        cursor.execute(
            """
            UPDATE complaints
            SET status = %s
            WHERE complaint_id = %s
            """,
            (new_status, complaint_id)
        )

        # Insert status history
        cursor.execute(
            """
            INSERT INTO complaint_history
            (complaint_id, previous_status, new_status,
             remarks, changed_by)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (
                complaint_id,
                previous_status,
                new_status,
                remarks or None,
                current_user.id
            )
        )

        # Create notification when status changes
        if previous_status != new_status:

            cursor.execute(
                """
                INSERT INTO notifications
                (user_id, complaint_id, title, message,
                 notification_type, is_read)
                VALUES (%s, %s, %s, %s, %s, FALSE)
                """,
                (
                    complaint_user_id,
                    complaint_id,
                    "Complaint Status Updated",
                    (
                        f"Your complaint status has changed "
                        f"from {previous_status} to {new_status}."
                    ),
                    "Status Update"
                )
            )

        connection.commit()

        flash(
            "Complaint status updated successfully.",
            "success"
        )

    except Exception:
        connection.rollback()
        raise

    finally:
        cursor.close()
        connection.close()

    return redirect(url_for("complaints.admin_complaints"))


# --------------------------------------------------
# 7. SECURE COMPLAINT ATTACHMENT DOWNLOAD
# --------------------------------------------------

@complaints_bp.route(
    "/complaints/attachment/<int:attachment_id>"
)
@login_required
def download_attachment(attachment_id):

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    try:

        cursor.execute(
            """
            SELECT
                a.original_filename,
                a.stored_filename,
                c.user_id
            FROM complaint_attachments a
            JOIN complaints c
                ON a.complaint_id = c.complaint_id
            WHERE a.attachment_id = %s
            """,
            (attachment_id,)
        )

        attachment = cursor.fetchone()

    finally:
        cursor.close()
        connection.close()

    if not attachment:
        abort(404)

    # Only complaint owner or admin can download
    if (
        attachment["user_id"] != current_user.id
        and (current_user.role or "").strip().lower() != "admin"
    ):
        abort(403)

    upload_folder = get_upload_folder()

    return send_from_directory(
        upload_folder,
        attachment["stored_filename"],
        as_attachment=True,
        download_name=attachment["original_filename"]
    )
