
from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from flask_login import login_required, current_user
from extensions import get_db_connection

contacts_bp = Blueprint("contacts", __name__)


@contacts_bp.route("/contacts")
@login_required
def contact_list():

    search = request.args.get("search", "").strip()
    category = request.args.get("category", "").strip()

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    query = """
        SELECT contact_id, contact_name, category, phone, address
        FROM contacts
        WHERE 1=1
    """

    values = []

    if search:
        query += " AND contact_name LIKE %s"
        values.append(f"%{search}%")

    if category:
        query += " AND category = %s"
        values.append(category)

    query += " ORDER BY contact_name ASC"

    cursor.execute(query, tuple(values))
    contacts = cursor.fetchall()

    cursor.execute(
        """
        SELECT DISTINCT category
        FROM contacts
        WHERE category IS NOT NULL AND category != ''
        ORDER BY category
        """
    )

    categories = [row["category"] for row in cursor.fetchall()]

    cursor.close()
    connection.close()

    return render_template(
        "contacts/list.html",
        contacts=contacts,
        categories=categories,
        search=search,
        selected_category=category
    )


@contacts_bp.route("/admin/contacts/add", methods=["GET", "POST"])
@login_required
def add_contact():

    if current_user.user_role != "admin":
        abort(403)

    if request.method == "POST":

        name = request.form.get("contact_name", "").strip()
        category = request.form.get("category", "").strip()
        phone = request.form.get("phone", "").strip()
        address = request.form.get("address", "").strip()

        if not name or not phone:
            flash("Contact name and phone are required.", "danger")
            return redirect(url_for("contacts.add_contact"))

        if not phone.isdigit() or not 7 <= len(phone) <= 15:
            flash("Please enter a valid phone number.", "danger")
            return redirect(url_for("contacts.add_contact"))

        connection = get_db_connection()
        cursor = connection.cursor()

        try:
            cursor.execute(
                """
                INSERT INTO contacts
                (contact_name, category, phone, address)
                VALUES (%s, %s, %s, %s)
                """,
                (name, category or None, phone, address or None)
            )

            connection.commit()
            flash("Contact added successfully!", "success")

        except Exception:
            connection.rollback()
            flash("Unable to add contact.", "danger")

        finally:
            cursor.close()
            connection.close()

        return redirect(url_for("contacts.contact_list"))

    return render_template("contacts/add.html")


@contacts_bp.route("/admin/contacts/delete/<int:contact_id>", methods=["POST"])
@login_required
def delete_contact(contact_id):

    if current_user.user_role != "admin":
        abort(403)

    connection = get_db_connection()
    cursor = connection.cursor()

    try:
        cursor.execute(
            "DELETE FROM contacts WHERE contact_id = %s",
            (contact_id,)
        )

        connection.commit()

    except Exception:
        connection.rollback()
        flash("Unable to delete contact.", "danger")
        return redirect(url_for("contacts.contact_list"))

    finally:
        cursor.close()
        connection.close()

    flash("Contact deleted successfully.", "success")

    return redirect(url_for("contacts.contact_list"))
    
@contacts_bp.route("/admin/contacts/edit/<int:contact_id>", methods=["GET", "POST"])
@login_required
def edit_contact(contact_id):

    if current_user.user_role != "admin":
        abort(403)

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    cursor.execute(
        """
        SELECT contact_id, contact_name, category, phone, address
        FROM contacts
        WHERE contact_id = %s
        """,
        (contact_id,)
    )

    contact = cursor.fetchone()

    if not contact:
        cursor.close()
        connection.close()
        abort(404)

    if request.method == "POST":

        name = request.form.get("contact_name", "").strip()
        category = request.form.get("category", "").strip()
        phone = request.form.get("phone", "").strip()
        address = request.form.get("address", "").strip()

        if not name or not phone:
            flash("Contact name and phone are required.", "danger")

        elif not phone.isdigit() or not 7 <= len(phone) <= 15:
            flash("Please enter a valid phone number.", "danger")

        else:
            try:
                cursor.execute(
                    """
                    UPDATE contacts
                    SET contact_name = %s,
                        category = %s,
                        phone = %s,
                        address = %s
                    WHERE contact_id = %s
                    """,
                    (
                        name,
                        category or None,
                        phone,
                        address or None,
                        contact_id
                    )
                )

                connection.commit()
                flash("Contact updated successfully!", "success")

                cursor.close()
                connection.close()

                return redirect(url_for("contacts.contact_list"))

            except Exception:
                connection.rollback()
                flash("Unable to update contact.", "danger")

    cursor.close()
    connection.close()

    return render_template(
        "contacts/edit.html",
        contact=contact
    )

