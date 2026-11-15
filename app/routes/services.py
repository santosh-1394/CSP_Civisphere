
from flask import Blueprint, render_template, request
from flask_login import login_required
from extensions import get_db_connection

services_bp = Blueprint("services", __name__)



@services_bp.route("/services")
@login_required
def list_services():

    search = request.args.get("q", "").strip()
    category = request.args.get("category", "").strip()

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    query = """
        SELECT service_id, service_name, description, category
        FROM services
        WHERE is_active = TRUE
    """

    params = []

    if search:
        query += """
            AND (
                service_name LIKE %s
                OR description LIKE %s
                OR category LIKE %s
            )
        """
        params.extend([
            f"%{search}%",
            f"%{search}%",
            f"%{search}%"
        ])

    if category:
        query += " AND category = %s"
        params.append(category)

    query += " ORDER BY category, service_name"

    cursor.execute(query, tuple(params))
    services = cursor.fetchall()

    cursor.execute("""
        SELECT DISTINCT category
        FROM services
        WHERE is_active = TRUE
        ORDER BY category
    """)

    categories = [row["category"] for row in cursor.fetchall()]

    cursor.close()
    connection.close()

    return render_template(
        "services/list.html",
        services=services,
        search=search,
        categories=categories,
        selected_category=category
    )

    
@services_bp.route("/services/<int:service_id>")
@login_required
def service_details(service_id):

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    cursor.execute(
        """
        SELECT service_id, service_name, description, category
        FROM services
        WHERE service_id = %s AND is_active = TRUE
        """,
        (service_id,)
    )

    service = cursor.fetchone()

    cursor.close()
    connection.close()

    if service is None:
        from flask import abort
        abort(404)

    return render_template(
        "services/details.html",
        service=service
    )
