
from flask import Blueprint, render_template, request, redirect, url_for, flash

from werkzeug.security import generate_password_hash, check_password_hash

from flask_login import (
    login_user,
    logout_user,
    current_user,
    login_required
)

from extensions import get_db_connection
from app.models import User

auth = Blueprint("auth", __name__)


@auth.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        full_name = request.form.get("full_name", "").strip()
        email = request.form.get("email", "").strip().lower()
        phone = request.form.get("phone", "").strip()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        # Validate fields
        if not all([full_name, email, phone, password, confirm_password]):
            flash("Please fill in all fields.", "error")
            return redirect(url_for("auth.register"))

        if password != confirm_password:
            flash("Passwords do not match.", "error")
            return redirect(url_for("auth.register"))

        if len(password) < 8:
            flash("Password must contain at least 8 characters.", "error")
            return redirect(url_for("auth.register"))

        connection = None
        cursor = None

        try:
            connection = get_db_connection()
            cursor = connection.cursor()

            # Check existing email
            cursor.execute(
                "SELECT user_id FROM users WHERE email = %s",
                (email,)
            )

            if cursor.fetchone():
                flash("This email is already registered.", "error")
                return redirect(url_for("auth.register"))

            # Hash password
            password_hash = generate_password_hash(password)

            # Insert citizen
            cursor.execute(
                """
                INSERT INTO users
                (full_name, email, phone, password_hash, user_role)
                VALUES (%s, %s, %s, %s, 'citizen')
                """,
                (full_name, email, phone, password_hash)
            )

            connection.commit()

            flash("Registration successful! You can now log in.", "success")
            return redirect(url_for("auth.login"))

        except Exception:
            if connection:
                connection.rollback()

            flash("Registration failed. Please try again.", "error")

        finally:
            if cursor:
                cursor.close()
            if connection and connection.is_connected():
                connection.close()

    return render_template("auth/register.html")

@auth.route("/login", methods=["GET", "POST"])
def login():

    if current_user.is_authenticated:
        return redirect(url_for("home"))

    if request.method == "POST":

        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        if not email or not password:
            flash("Please enter your email and password.", "error")
            return redirect(url_for("auth.login"))

        connection = None
        cursor = None

        try:
            connection = get_db_connection()
            cursor = connection.cursor(dictionary=True)

            cursor.execute(
                """
                SELECT user_id, full_name, email, phone,
                       password_hash, user_role
                FROM users
                WHERE email = %s AND is_active = TRUE
                """,
                (email,)
            )

            user_data = cursor.fetchone()

            if user_data and check_password_hash(
                user_data["password_hash"], password
            ):
                user = User(
                    user_data["user_id"],
                    user_data["full_name"],
                    user_data["email"],
                    user_data["phone"],
                    user_data["password_hash"],
                    user_data["user_role"]
                )

                login_user(user)
                flash("Welcome back!", "success")
                return redirect(url_for("home"))

            flash("Invalid email or password.", "error")

        except Exception:
            flash("Login failed. Please try again.", "error")

        finally:
            if cursor:
                cursor.close()
            if connection and connection.is_connected():
                connection.close()

    return render_template("auth/login.html")


@auth.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have logged out successfully.", "success")
    return redirect(url_for("auth.login"))
