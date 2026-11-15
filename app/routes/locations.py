
import logging

from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    abort
)

from flask_login import login_required, current_user

from extensions import get_db_connection


locations_bp = Blueprint("locations", __name__)
logger = logging.getLogger(__name__)


# =================================================
# ADMIN ACCESS
# =================================================

def admin_required():
    if (current_user.role or "").strip().lower() != "admin":
        abort(403)


# =================================================
# COORDINATE CONVERSION
# =================================================

def convert_location_coordinates(locations):
    for location in locations:
        if location.get("latitude") is not None:
            location["latitude"] = float(location["latitude"])

        if location.get("longitude") is not None:
            location["longitude"] = float(location["longitude"])

    return locations


# =================================================
# PUBLIC: COMMUNITY LOCATIONS SEARCH
# =================================================

@locations_bp.route("/locations")
def location_list():

    search = request.args.get("search", "").strip()
    district = request.args.get("district", "").strip()

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        query = """
            SELECT
                location_id,
                location_name,
                address,
                district,
                phone,
                latitude,
                longitude
            FROM locations
            WHERE is_active = 1
        """

        values = []

        if search:
            query += """
                AND (
                    location_name LIKE %s
                    OR address LIKE %s
                    OR district LIKE %s
                )
            """

            search_value = f"%{search}%"

            values.extend([
                search_value,
                search_value,
                search_value
            ])

        if district:
            query += " AND district = %s"
            values.append(district)

        query += " ORDER BY location_name ASC"

        cursor.execute(query, values)
        locations = cursor.fetchall()

        convert_location_coordinates(locations)

        cursor.execute("""
            SELECT DISTINCT district
            FROM locations
            WHERE is_active = 1
              AND district IS NOT NULL
              AND district != ''
            ORDER BY district ASC
        """)

        districts = cursor.fetchall()

    finally:
        cursor.close()
        connection.close()

    return render_template(
        "locations/list.html",
        locations=locations,
        districts=districts,
        search=search,
        selected_district=district
    )


# =================================================
# PUBLIC: REGISTERED LOCATION DETAILS
# =================================================

@locations_bp.route("/locations/<int:location_id>")
def location_details(location_id):

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        cursor.execute("""
            SELECT
                location_id,
                location_name,
                address,
                district,
                phone,
                latitude,
                longitude,
                created_at
            FROM locations
            WHERE location_id = %s
              AND is_active = 1
        """, (location_id,))

        location = cursor.fetchone()

    finally:
        cursor.close()
        connection.close()

    if not location:
        abort(404)

    if location.get("latitude") is not None:
        location["latitude"] = float(location["latitude"])

    if location.get("longitude") is not None:
        location["longitude"] = float(location["longitude"])

    return render_template(
        "locations/details.html",
        location=location
    )


# =================================================
# ADMIN: VIEW ALL LOCATIONS
# =================================================

@locations_bp.route("/admin/locations")
@login_required
def admin_location_list():

    admin_required()

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        cursor.execute("""
            SELECT
                location_id,
                location_name,
                address,
                district,
                phone,
                latitude,
                longitude,
                is_active
            FROM locations
            ORDER BY location_name ASC
        """)

        locations = cursor.fetchall()
        convert_location_coordinates(locations)

    finally:
        cursor.close()
        connection.close()

    return render_template(
        "locations/admin_list.html",
        locations=locations
    )


# =================================================
# ADMIN: ADD LOCATION
# =================================================

@locations_bp.route(
    "/admin/locations/add",
    methods=["GET", "POST"]
)
@login_required
def add_location():

    admin_required()

    if request.method == "POST":

        name = request.form.get("location_name", "").strip()
        address = request.form.get("address", "").strip()
        district = request.form.get("district", "").strip()
        phone = request.form.get("phone", "").strip()

        latitude = request.form.get("latitude", "").strip()
        longitude = request.form.get("longitude", "").strip()

        if not name:
            flash("Location name is required.", "error")
            return redirect(url_for("locations.add_location"))

        try:
            lat = float(latitude) if latitude else None
            lng = float(longitude) if longitude else None

            if lat is not None and not -90 <= lat <= 90:
                raise ValueError()

            if lng is not None and not -180 <= lng <= 180:
                raise ValueError()

            if (lat is None) != (lng is None):
                raise ValueError()

        except ValueError:
            flash(
                "Please enter valid latitude and longitude.",
                "error"
            )
            return redirect(url_for("locations.add_location"))

        connection = get_db_connection()
        cursor = connection.cursor()

        try:
            cursor.execute("""
                INSERT INTO locations (
                    location_name,
                    address,
                    district,
                    phone,
                    latitude,
                    longitude,
                    is_active
                )
                VALUES (%s, %s, %s, %s, %s, %s, 1)
            """, (
                name,
                address or None,
                district or None,
                phone or None,
                lat,
                lng
            ))

            connection.commit()

        except Exception:
            connection.rollback()
            logger.exception("Unable to add community location.")
            raise

        finally:
            cursor.close()
            connection.close()

        flash("Location added successfully.", "success")

        return redirect(url_for("locations.admin_location_list"))

    return render_template("locations/add.html")


# =================================================
# ADMIN: EDIT LOCATION
# =================================================

@locations_bp.route(
    "/admin/locations/edit/<int:location_id>",
    methods=["GET", "POST"]
)
@login_required
def edit_location(location_id):

    admin_required()

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        cursor.execute("""
            SELECT *
            FROM locations
            WHERE location_id = %s
        """, (location_id,))

        location = cursor.fetchone()

        if not location:
            abort(404)

        if request.method == "POST":

            name = request.form.get("location_name", "").strip()
            address = request.form.get("address", "").strip()
            district = request.form.get("district", "").strip()
            phone = request.form.get("phone", "").strip()

            latitude = request.form.get("latitude", "").strip()
            longitude = request.form.get("longitude", "").strip()

            if not name:
                flash("Location name is required.", "error")
                return redirect(
                    url_for(
                        "locations.edit_location",
                        location_id=location_id
                    )
                )

            try:
                lat = (
                    float(latitude)
                    if latitude
                    else (
                        float(location["latitude"])
                        if location["latitude"] is not None
                        else None
                    )
                )

                lng = (
                    float(longitude)
                    if longitude
                    else (
                        float(location["longitude"])
                        if location["longitude"] is not None
                        else None
                    )
                )

                if lat is not None and not -90 <= lat <= 90:
                    raise ValueError()

                if lng is not None and not -180 <= lng <= 180:
                    raise ValueError()

                if (lat is None) != (lng is None):
                    raise ValueError()

            except (ValueError, TypeError):
                flash(
                    "Please enter valid latitude and longitude.",
                    "error"
                )
                return redirect(
                    url_for(
                        "locations.edit_location",
                        location_id=location_id
                    )
                )

            cursor.execute("""
                UPDATE locations
                SET
                    location_name = %s,
                    address = %s,
                    district = %s,
                    phone = %s,
                    latitude = %s,
                    longitude = %s
                WHERE location_id = %s
            """, (
                name,
                address or None,
                district or None,
                phone or None,
                lat,
                lng,
                location_id
            ))

            connection.commit()

            flash("Location updated successfully.", "success")

            return redirect(url_for("locations.admin_location_list"))

    finally:
        cursor.close()
        connection.close()

    return render_template(
        "locations/edit.html",
        location=location
    )


# =================================================
# ADMIN: DEACTIVATE LOCATION
# =================================================

@locations_bp.route(
    "/admin/locations/delete/<int:location_id>",
    methods=["POST"]
)
@login_required
def delete_location(location_id):

    admin_required()

    connection = get_db_connection()
    cursor = connection.cursor()

    try:
        cursor.execute("""
            UPDATE locations
            SET is_active = 0
            WHERE location_id = %s
        """, (location_id,))

        connection.commit()
        deleted = cursor.rowcount > 0

    except Exception:
        connection.rollback()
        logger.exception("Unable to deactivate community location.")
        raise

    finally:
        cursor.close()
        connection.close()

    if deleted:
        flash("Location deactivated successfully.", "success")
    else:
        flash("Location not found.", "error")

    return redirect(url_for("locations.admin_location_list"))
