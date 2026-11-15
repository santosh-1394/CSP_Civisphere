
from flask_login import UserMixin
from extensions import get_db_connection


class User(UserMixin):

    def __init__(self, user_id, full_name, email, phone, password_hash, user_role):
        self.id = user_id
        self.full_name = full_name
        self.email = email
        self.phone = phone
        self.password_hash = password_hash
        self.user_role = user_role

    @property
    def role(self):
        return self.user_role

    @staticmethod
    def get_by_id(user_id):
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        try:
            cursor.execute(
                """
                SELECT user_id, full_name, email, phone,
                       password_hash, user_role
                FROM users
                WHERE user_id = %s AND is_active = TRUE
                """,
                (user_id,)
            )

            user_data = cursor.fetchone()

            if user_data:
                return User(
                    user_data["user_id"],
                    user_data["full_name"],
                    user_data["email"],
                    user_data["phone"],
                    user_data["password_hash"],
                    user_data["user_role"]
                )

            return None

        finally:
            cursor.close()
            connection.close()
