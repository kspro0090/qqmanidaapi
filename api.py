from flask import Blueprint, request, jsonify
import sqlite3
from datetime import datetime

api = Blueprint('api', __name__)

def _get_key_from_header():
    auth = request.headers.get('Authorization', '')
    if auth.startswith('Bearer '):
        return auth.split(' ', 1)[1].strip()
    return auth.strip()


def _is_key_valid(key: str) -> bool:
    if not key:
        return False
    conn = sqlite3.connect('system.db')
    c = conn.cursor()
    c.execute("SELECT id FROM api_keys WHERE key = ?", (key,))
    result = c.fetchone()
    conn.close()
    return result is not None


@api.route('/api/departments', methods=['GET'])
def api_departments():
    api_key = _get_key_from_header()
    if not _is_key_valid(api_key):
        return jsonify({'error': 'Unauthorized'}), 401

    conn = sqlite3.connect('system.db')
    c = conn.cursor()
    c.execute("SELECT id, name FROM departments")
    departments = [{'id': row[0], 'name': row[1]} for row in c.fetchall()]
    conn.close()
    return jsonify(departments)


@api.route('/api/questions', methods=['POST'])
def api_questions():
    api_key = _get_key_from_header()
    if not _is_key_valid(api_key):
        return jsonify({'error': 'Unauthorized'}), 401

    data = request.get_json(force=True, silent=True) or {}
    required = ['full_name', 'phone_number', 'question_text', 'department_id']
    if not all(field in data for field in required):
        return jsonify({'error': 'Missing fields'}), 400

    full_name = data['full_name']
    phone_number = data['phone_number']
    question_text = data['question_text']
    department_id = data['department_id']

    conn = sqlite3.connect('system.db')
    c = conn.cursor()

    # Validate department
    c.execute("SELECT id FROM departments WHERE id = ?", (department_id,))
    if not c.fetchone():
        conn.close()
        return jsonify({'error': 'Invalid department_id'}), 400

    # Get or create user
    c.execute("SELECT id FROM users WHERE phone = ?", (phone_number,))
    user = c.fetchone()
    if user:
        user_id = user[0]
    else:
        c.execute("INSERT INTO users (name, phone) VALUES (?, ?)", (full_name, phone_number))
        user_id = c.lastrowid

    # Get base reward and timer
    c.execute("SELECT base_reward_amount, base_timer_hours FROM admin_settings WHERE id = 1")
    settings = c.fetchone()
    base_reward = settings[0] if settings else 200000
    base_hours = settings[1] if settings else 24

    now = datetime.now()
    c.execute(
        """INSERT INTO questions
            (user_id, department_id, question_text, status, created_at, reward_amount, timer_hours, fixed_reward, waiting_count, penalty_multiplier)
            VALUES (?, ?, ?, 'pending', ?, 0, ?, ?, 0, 3)
        """,
        (user_id, department_id, question_text, now, base_hours, base_reward)
    )
    question_id = c.lastrowid
    conn.commit()
    conn.close()
    return jsonify({'question_id': question_id})
