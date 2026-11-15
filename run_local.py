
from app import create_app
from extensions import get_db_connection

app = create_app()

if __name__ == "__main__":
    try:
        connection = get_db_connection()

        if connection.is_connected():
            print("CiviSphere MySQL connection successful!")

        connection.close()

    except Exception as error:
        print("Database connection failed:", error)

    app.run(debug=True)
