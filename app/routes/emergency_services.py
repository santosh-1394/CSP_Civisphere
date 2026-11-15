
from flask import (
    Blueprint,
    render_template,
    request,
    abort,
    redirect,
    url_for,
    flash
)

from flask_login import login_required, current_user
from extensions import get_db_connection


emergency_services_bp = Blueprint(
    "emergency_services",
    __name__,
    url_prefix="/emergency-services"
)


CATEGORIES = [
    "Hospitals",
    "Fire Stations",
    "Police Stations",
    "Ambulance Services",
    "Blood Banks",
    "Emergency Pharmacies",
    "Disaster Management and Rescue Centres",
    "Veterinary Emergency Services"
]


# ==========================================
# HELPER FUNCTIONS
# ==========================================

def emergency_admin_required():
    if not current_user.is_authenticated:
        abort(401)

    if (current_user.role or "").strip().lower() != "admin":
        abort(403)


def parse_coordinates(latitude, longitude):
    """Validate optional latitude and longitude values."""

    latitude = latitude.strip()
    longitude = longitude.strip()

    try:
        latitude = float(latitude) if latitude else None
        longitude = float(longitude) if longitude else None

        if latitude is not None and not -90 <= latitude <= 90:
            raise ValueError

        if longitude is not None and not -180 <= longitude <= 180:
            raise ValueError

        return latitude, longitude

    except (ValueError, TypeError):
        raise ValueError("Invalid map coordinates.")


# ==========================================
# PUBLIC: EMERGENCY SERVICES HOME
# ==========================================

@emergency_services_bp.route("/")
def emergency_services_home():

    return render_template(
        "emergency_services/index.html",
        categories=CATEGORIES
    )


# ==========================================
# PUBLIC: SEARCH BY LOCATION
# ==========================================

@emergency_services_bp.route("/search")
def search_services():

    location = request.args.get("location", "").strip()

    if not location:
        flash("Please enter a city, district or state.", "warning")
        return redirect(url_for("home"))

    search_term = f"%{location}%"

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        cursor.execute("""
            SELECT *
            FROM emergency_services
            WHERE is_active = 1
              AND (
                    state LIKE %s
                    OR district LIKE %s
                    OR city LIKE %s
                    OR address LIKE %s
                  )
            ORDER BY
                is_verified DESC,
                state ASC,
                district ASC,
                service_name ASC
        """, (
            search_term,
            search_term,
            search_term,
            search_term
        ))

        services = cursor.fetchall()

    finally:
        cursor.close()
        connection.close()

    return render_template(
        "emergency_services/search_results.html",
        services=services,
        location=location
    )


# ==========================================
# PUBLIC: CATEGORY LIST
# ==========================================

@emergency_services_bp.route("/category/<string:category>")
def category_list(category):

    if category not in CATEGORIES:
        abort(404)

    state = request.args.get("state", "").strip()
    district = request.args.get("district", "").strip()
    city = request.args.get("city", "").strip()
    search = request.args.get("search", "").strip()

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        query = """
            SELECT *
            FROM emergency_services
            WHERE category = %s
              AND is_active = 1
        """

        params = [category]

        if state:
            query += " AND state = %s"
            params.append(state)

        if district:
            query += " AND district = %s"
            params.append(district)

        if city:
            query += " AND city = %s"
            params.append(city)

        if search:
            query += """
                AND (
                    service_name LIKE %s
                    OR address LIKE %s
                    OR subcategory LIKE %s
                    OR district LIKE %s
                    OR city LIKE %s
                )
            """

            term = f"%{search}%"
            params.extend([term] * 5)

        query += """
            ORDER BY
                is_verified DESC,
                state ASC,
                district ASC,
                service_name ASC
        """

        cursor.execute(query, tuple(params))
        services = cursor.fetchall()

    finally:
        cursor.close()
        connection.close()

    return render_template(
        "emergency_services/list.html",
        category=category,
        services=services,
        selected_state=state,
        selected_district=district,
        selected_city=city,
        search=search
    )


# ==========================================
# PUBLIC: FACILITY DETAILS
# ==========================================

@emergency_services_bp.route("/details/<int:service_id>")
def service_details(service_id):

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        cursor.execute("""
            SELECT *
            FROM emergency_services
            WHERE service_id = %s
              AND is_active = 1
        """, (service_id,))

        service = cursor.fetchone()

    finally:
        cursor.close()
        connection.close()

    if not service:
        abort(404)

    return render_template(
        "emergency_services/details.html",
        service=service
    )


# ==========================================
# ADMIN: VIEW ALL FACILITIES
# ==========================================

@emergency_services_bp.route("/admin")
@login_required
def admin_list():

    emergency_admin_required()

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        cursor.execute("""
            SELECT *
            FROM emergency_services
            ORDER BY created_at DESC
        """)

        services = cursor.fetchall()

    finally:
        cursor.close()
        connection.close()

    return render_template(
        "emergency_services/admin_list.html",
        services=services
    )


# ==========================================
# ADMIN: ADD FACILITY
# ==========================================

@emergency_services_bp.route("/admin/add", methods=["GET", "POST"])
@login_required
def admin_add():

    emergency_admin_required()

    if request.method == "POST":

        category = request.form.get("category", "").strip()
        subcategory = request.form.get("subcategory", "").strip()
        service_name = request.form.get("service_name", "").strip()
        state = request.form.get("state", "").strip()
        district = request.form.get("district", "").strip()
        city = request.form.get("city", "").strip()
        address = request.form.get("address", "").strip()
        phone = request.form.get("phone", "").strip()
        alternate_phone = request.form.get("alternate_phone", "").strip()
        description = request.form.get("description", "").strip()
        operating_hours = request.form.get("operating_hours", "").strip()
        source = request.form.get("source", "").strip()

        if not all([category, service_name, state, address]):
            flash("Please fill in all required fields.", "danger")

            return render_template(
                "emergency_services/admin_add.html",
                categories=CATEGORIES
            )

        if category not in CATEGORIES:
            abort(400)

        # Coordinates are optional.
        # If the form does not contain coordinate fields,
        # the new facility will simply have NULL coordinates.
        try:
            latitude, longitude = parse_coordinates(
                request.form.get("latitude", ""),
                request.form.get("longitude", "")
            )

        except ValueError:
            flash("Please enter valid map coordinates.", "danger")

            return render_template(
                "emergency_services/admin_add.html",
                categories=CATEGORIES
            )

        connection = get_db_connection()
        cursor = connection.cursor()

        try:
            cursor.execute("""
                INSERT INTO emergency_services (
                    category,
                    subcategory,
                    service_name,
                    state,
                    district,
                    city,
                    address,
                    phone,
                    alternate_phone,
                    latitude,
                    longitude,
                    description,
                    operating_hours,
                    source,
                    is_verified,
                    is_active
                )
                VALUES (
                    %s, %s, %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s, %s, %s, 0, 1
                )
            """, (
                category,
                subcategory or None,
                service_name,
                state,
                district or None,
                city or None,
                address,
                phone or None,
                alternate_phone or None,
                latitude,
                longitude,
                description or None,
                operating_hours or None,
                source or None
            ))

            connection.commit()

            flash(
                "Emergency facility added successfully.",
                "success"
            )

        except Exception:
            connection.rollback()

            flash(
                "Unable to add the facility. Please check the information.",
                "danger"
            )

        finally:
            cursor.close()
            connection.close()

        return redirect(url_for("emergency_services.admin_list"))

    return render_template(
        "emergency_services/admin_add.html",
        categories=CATEGORIES
    )


# ==========================================
# ADMIN: EDIT FACILITY
# ==========================================

@emergency_services_bp.route(
    "/admin/edit/<int:service_id>",
    methods=["GET", "POST"]
)
@login_required
def admin_edit(service_id):

    emergency_admin_required()

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        cursor.execute("""
            SELECT *
            FROM emergency_services
            WHERE service_id = %s
        """, (service_id,))

        service = cursor.fetchone()

        if not service:
            abort(404)

        if request.method == "POST":

            category = request.form.get("category", "").strip()
            service_name = request.form.get("service_name", "").strip()
            state = request.form.get("state", "").strip()
            address = request.form.get("address", "").strip()

            if not all([category, service_name, state, address]):
                flash("Please fill in all required fields.", "danger")

                return render_template(
                    "emergency_services/admin_edit.html",
                    service=service,
                    categories=CATEGORIES
                )

            if category not in CATEGORIES:
                abort(400)

            # Preserve existing coordinates when the edit form
            # does not contain latitude/longitude fields.
            try:
                if (
                    "latitude" in request.form
                    or "longitude" in request.form
                ):
                    latitude, longitude = parse_coordinates(
                        request.form.get("latitude", ""),
                        request.form.get("longitude", "")
                    )
                else:
                    latitude = service["latitude"]
                    longitude = service["longitude"]

            except ValueError:
                flash("Please enter valid map coordinates.", "danger")

                return render_template(
                    "emergency_services/admin_edit.html",
                    service=service,
                    categories=CATEGORIES
                )

            cursor.execute("""
                UPDATE emergency_services
                SET
                    category = %s,
                    subcategory = %s,
                    service_name = %s,
                    state = %s,
                    district = %s,
                    city = %s,
                    address = %s,
                    phone = %s,
                    alternate_phone = %s,
                    latitude = %s,
                    longitude = %s,
                    description = %s,
                    operating_hours = %s,
                    source = %s
                WHERE service_id = %s
            """, (
                category,
                request.form.get("subcategory", "").strip() or None,
                service_name,
                state,
                request.form.get("district", "").strip() or None,
                request.form.get("city", "").strip() or None,
                address,
                request.form.get("phone", "").strip() or None,
                request.form.get("alternate_phone", "").strip() or None,
                latitude,
                longitude,
                request.form.get("description", "").strip() or None,
                request.form.get("operating_hours", "").strip() or None,
                request.form.get("source", "").strip() or None,
                service_id
            ))

            connection.commit()

            flash(
                "Facility information updated successfully.",
                "success"
            )

            return redirect(url_for("emergency_services.admin_list"))

    finally:
        cursor.close()
        connection.close()

    return render_template(
        "emergency_services/admin_edit.html",
        service=service,
        categories=CATEGORIES
    )


# ==========================================
# ADMIN: VERIFY / UNVERIFY FACILITY
# ==========================================

@emergency_services_bp.route(
    "/admin/verify/<int:service_id>",
    methods=["POST"]
)
@login_required
def admin_verify(service_id):

    emergency_admin_required()

    connection = get_db_connection()
    cursor = connection.cursor()

    try:
        cursor.execute("""
            UPDATE emergency_services
            SET is_verified = NOT is_verified
            WHERE service_id = %s
        """, (service_id,))

        if cursor.rowcount == 0:
            connection.rollback()
            abort(404)

        connection.commit()

        flash(
            "Facility verification status updated.",
            "success"
        )

    finally:
        cursor.close()
        connection.close()

    return redirect(url_for("emergency_services.admin_list"))


# ==========================================
# ADMIN: DEACTIVATE FACILITY
# ==========================================

@emergency_services_bp.route(
    "/admin/deactivate/<int:service_id>",
    methods=["POST"]
)
@login_required
def admin_deactivate(service_id):

    emergency_admin_required()

    connection = get_db_connection()
    cursor = connection.cursor()

    try:
        cursor.execute("""
            UPDATE emergency_services
            SET is_active = 0
            WHERE service_id = %s
        """, (service_id,))

        if cursor.rowcount == 0:
            # Check whether the facility actually exists.
            cursor.execute("""
                SELECT service_id
                FROM emergency_services
                WHERE service_id = %s
            """, (service_id,))

            if not cursor.fetchone():
                abort(404)

        connection.commit()

        flash(
            "Facility deactivated successfully.",
            "success"
        )

    finally:
        cursor.close()
        connection.close()

    return redirect(url_for("emergency_services.admin_list"))


# ==========================================
# ADMIN: REACTIVATE FACILITY
# ==========================================

@emergency_services_bp.route(
    "/admin/activate/<int:service_id>",
    methods=["POST"]
)
@login_required
def admin_activate(service_id):

    emergency_admin_required()

    connection = get_db_connection()
    cursor = connection.cursor()

    try:
        cursor.execute("""
            UPDATE emergency_services
            SET is_active = 1
            WHERE service_id = %s
        """, (service_id,))

        if cursor.rowcount == 0:
            cursor.execute("""
                SELECT service_id
                FROM emergency_services
                WHERE service_id = %s
            """, (service_id,))

            if not cursor.fetchone():
                abort(404)

        connection.commit()

        flash(
            "Facility reactivated successfully.",
            "success"
        )

    finally:
        cursor.close()
        connection.close()

    return redirect(url_for("emergency_services.admin_list"))
