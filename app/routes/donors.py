
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from extensions import get_db_connection

donors_bp = Blueprint("donors", __name__)


@donors_bp.route("/donors")
@login_required
def donor_list():

    blood_group = request.args.get("blood_group", "").strip()
    location = request.args.get("location", "").strip()

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    query = """
        SELECT donor_id, donor_name, blood_group, location
        FROM blood_donors
        WHERE available = TRUE
          AND consent_to_contact = TRUE
    """

    values = []

    if blood_group:
        query += " AND blood_group = %s"
        values.append(blood_group)

    if location:
        query += " AND location LIKE %s"
        values.append(f"%{location}%")

    query += " ORDER BY created_at DESC"

    cursor.execute(query, tuple(values))
    donors = cursor.fetchall()

    cursor.close()
    connection.close()

    return render_template(
        "donors/list.html",
        donors=donors,
        selected_group=blood_group,
        search_location=location
    )


@donors_bp.route("/donors/register", methods=["GET", "POST"])
@login_required
def register_donor():

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    cursor.execute(
        "SELECT donor_id FROM blood_donors WHERE user_id = %s",
        (current_user.id,)
    )
    existing_donor = cursor.fetchone()

    cursor.close()
    connection.close()

    if existing_donor:
        flash("You have already registered as a blood donor.", "info")
        return redirect(url_for("donors.donor_list"))

    if request.method == "POST":

        donor_name = request.form.get("donor_name", "").strip()
        blood_group = request.form.get("blood_group", "").strip()
        phone = request.form.get("phone", "").strip()
        location = request.form.get("location", "").strip()
        consent = request.form.get("consent") == "yes"

        allowed_groups = {
            "A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"
        }

        if not donor_name or not phone or not location:
            flash("Please fill in all required fields.", "danger")
            return redirect(url_for("donors.register_donor"))

        if blood_group not in allowed_groups:
            flash("Please select a valid blood group.", "danger")
            return redirect(url_for("donors.register_donor"))

        if not phone.isdigit() or not 7 <= len(phone) <= 15:
            flash("Please enter a valid phone number.", "danger")
            return redirect(url_for("donors.register_donor"))

        if not consent:
            flash("Consent to be contacted is required for donor registration.", "danger")
            return redirect(url_for("donors.register_donor"))

        connection = get_db_connection()
        cursor = connection.cursor()

        try:
            cursor.execute(
                """
                INSERT INTO blood_donors
                (user_id, donor_name, blood_group, phone,
                 location, available, consent_to_contact)
                VALUES (%s, %s, %s, %s, %s, TRUE, TRUE)
                """,
                (
                    current_user.id,
                    donor_name,
                    blood_group,
                    phone,
                    location
                )
            )

            connection.commit()
            flash("Your blood donor registration was successful!", "success")

        except Exception:
            connection.rollback()
            flash("Unable to complete registration. Please try again.", "danger")

        finally:
            cursor.close()
            connection.close()

        return redirect(url_for("donors.donor_list"))

    return render_template("donors/register.html")
