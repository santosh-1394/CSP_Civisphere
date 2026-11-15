
from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from extensions import get_db_connection

chatbot_bp = Blueprint("chatbot", __name__)


def find_answer(question):
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    cursor.execute("""
        SELECT question, answer, keywords
        FROM chatbot_faq
        WHERE is_active = TRUE
    """)

    faqs = cursor.fetchall()

    cursor.close()
    connection.close()

    question_lower = question.lower()
    question_words = set(question_lower.split())

    best_answer = None
    best_score = 0

    for faq in faqs:
        score = 0

        faq_question = faq["question"].lower()
        keywords = faq["keywords"] or ""

        if faq_question in question_lower:
            score += 5

        for keyword in keywords.split(","):
            keyword = keyword.strip().lower()

            if keyword and keyword in question_lower:
                score += 3

        for word in faq_question.split():
            if len(word) > 2 and word in question_words:
                score += 1

        if score > best_score:
            best_score = score
            best_answer = faq["answer"]

    if best_answer and best_score > 0:
        return best_answer

    return (
        "Sorry, I couldn't understand your question. "
        "Please try asking about services, complaints, "
        "blood donors, contacts, locations or feedback."
    )


@chatbot_bp.route("/chatbot", methods=["GET"])
@login_required
def chatbot_page():
    return render_template("chatbot/index.html")


@chatbot_bp.route("/chatbot/ask", methods=["POST"])
@login_required
def chatbot_ask():
    data = request.get_json(silent=True) or {}
    question = data.get("question", "").strip()

    if not question:
        return jsonify({
            "answer": "Please enter a question."
        }), 400

    if len(question) > 1000:
        return jsonify({
            "answer": "Please keep your question under 1000 characters."
        }), 400

    answer = find_answer(question)

    try:
        connection = get_db_connection()
        cursor = connection.cursor()

        cursor.execute("""
            INSERT INTO chatbot_logs (user_id, question, answer)
            VALUES (%s, %s, %s)
        """, (current_user.id, question, answer))

        connection.commit()
        cursor.close()
        connection.close()

    except Exception:
        pass

    return jsonify({"answer": answer})
