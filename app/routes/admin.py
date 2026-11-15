
from flask import (
    Blueprint, render_template, abort,
    request, redirect, url_for, flash
)
from flask_login import login_required, current_user
from extensions import get_db_connection

admin_bp = Blueprint("admin", __name__)


# Admin Permission Check
def admin_required():
    if (current_user.role or "").strip().lower() != "admin":
        abort(403)


# ==========================================
# ADMIN DASHBOARD
# ==========================================

@admin_bp.route("/admin/dashboard")
@login_required
def admin_dashboard():

    admin_required()

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        statistics = {}

        tables = {
            "users": "users",
            "services": "services",
            "locations": "locations",
            "complaints": "complaints",
            "donors": "blood_donors",
            "feedback": "feedback"
        }

        for key, table in tables.items():
            cursor.execute(
                f"SELECT COUNT(*) AS total FROM {table}"
            )
            statistics[key] = cursor.fetchone()["total"]

        cursor.execute("""
            SELECT status, COUNT(*) AS total
            FROM complaints
            GROUP BY status
        """)

        complaint_status = cursor.fetchall()

    finally:
        cursor.close()
        connection.close()

    return render_template(
        "admin/dashboard.html",
        statistics=statistics,
        complaint_status=complaint_status
    )


# ==========================================
# USER MANAGEMENT
# ==========================================

@admin_bp.route("/admin/users")
@login_required
def user_management():

    admin_required()

    search = request.args.get("search", "").strip()

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        cursor.execute("""
            SELECT COUNT(*) AS total
            FROM users
        """)
        total_users = cursor.fetchone()["total"]

        cursor.execute("""
            SELECT COUNT(*) AS total
            FROM users
            WHERE is_active = TRUE
        """)
        active_users = cursor.fetchone()["total"]

        cursor.execute("""
            SELECT COUNT(*) AS total
            FROM users
            WHERE is_active = FALSE
        """)
        inactive_users = cursor.fetchone()["total"]

        if search:
            cursor.execute("""
                SELECT user_id, full_name, email, phone,
                       user_role, is_active, created_at
                FROM users
                WHERE full_name LIKE %s
                   OR email LIKE %s
                ORDER BY user_id DESC
            """, (f"%{search}%", f"%{search}%"))
        else:
            cursor.execute("""
                SELECT user_id, full_name, email, phone,
                       user_role, is_active, created_at
                FROM users
                ORDER BY user_id DESC
            """)

        users = cursor.fetchall()

    finally:
        cursor.close()
        connection.close()

    return render_template(
        "admin/users.html",
        users=users,
        search=search,
        total_users=total_users,
        active_users=active_users,
        inactive_users=inactive_users
    )


# ==========================================
# ACTIVATE / DEACTIVATE USER
# ==========================================

@admin_bp.route("/admin/users/toggle/<int:user_id>", methods=["POST"])
@login_required
def toggle_user_status(user_id):

    admin_required()

    # Admin cannot change their own account status
    if user_id == int(current_user.id):
        flash("You cannot deactivate your own account.", "error")
        return redirect(url_for("admin.user_management"))

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        cursor.execute("""
            SELECT user_id, user_role, is_active
            FROM users
            WHERE user_id = %s
        """, (user_id,))

        user = cursor.fetchone()

        if not user:
            flash("User not found.", "error")

        elif (user["user_role"] or "").strip().lower() == "admin":
            flash("Admin accounts cannot be modified here.", "error")

        else:
            new_status = not bool(user["is_active"])

            cursor.execute("""
                UPDATE users
                SET is_active = %s
                WHERE user_id = %s
            """, (new_status, user_id))

            connection.commit()

            if new_status:
                flash("User activated successfully.", "success")
            else:
                flash("User deactivated successfully.", "success")

    except Exception:
        connection.rollback()
        raise

    finally:
        cursor.close()
        connection.close()

    return redirect(url_for("admin.user_management"))
