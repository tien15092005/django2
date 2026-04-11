from django.db import connection, transaction
from rest_framework.response import Response
from rest_framework.decorators import api_view

from .serializer import QuestionSerializer, UserSerializer
from .auth_utils import (
    hash_password, check_password,
    generate_token, require_auth, require_admin,
)


# ═══════════════════════════════════════════════════════════════════════════════
# AUTH
# ═══════════════════════════════════════════════════════════════════════════════

@api_view(['POST'])
def login(request):
    """
    POST /api/login/
    Body: { "username": "...", "pwd": "..." }
    Trả về JWT token + thông tin user (kể cả role).
    """
    username = request.data.get('username', '').strip()
    pwd = request.data.get('pwd', '').strip()
    if not username or not pwd:
        return Response({'error': 'Thiếu username hoặc pwd'}, status=400)

    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT id, name, username, pwd, role FROM users WHERE username = %s",
            [username]
        )
        row = cursor.fetchone()

    if not row:
        return Response({'error': 'Sai username hoặc mật khẩu'}, status=401)

    user_id, name, uname, hashed_pwd, role = row

    if not check_password(pwd, hashed_pwd):
        return Response({'error': 'Sai username hoặc mật khẩu'}, status=401)

    token = generate_token(user_id, role)
    return Response({
        'access_token': token,
        'token_type': 'Bearer',
        'user': {
            'id': user_id,
            'name': name,
            'username': uname,
            'role': role,
        }
    }, status=200)


@api_view(['POST'])
def signup(request):
    """
    POST /api/signup/
    Body: { "id": "...", "name": "...", "username": "...", "pwd": "..." }
    Role mặc định = 'student'.
    """
    user_id  = request.data.get('id', '').strip()
    name     = request.data.get('name', '').strip()
    username = request.data.get('username', '').strip()
    pwd      = request.data.get('pwd', '').strip()

    if not all([user_id, name, username, pwd]):
        return Response({'error': 'Thiếu trường bắt buộc'}, status=400)

    hashed = hash_password(pwd)
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                "INSERT INTO users (id, name, username, pwd, role) VALUES (%s, %s, %s, %s, 'student')",
                [user_id, name, username, hashed]
            )
        return Response({'message': 'Đăng ký thành công'}, status=201)
    except Exception as e:
        if 'unique' in str(e).lower():
            return Response({'error': 'Username đã tồn tại'}, status=409)
        return Response({'error': str(e)}, status=500)


# ═══════════════════════════════════════════════════════════════════════════════
# USERS  (yêu cầu admin)
# ═══════════════════════════════════════════════════════════════════════════════

@api_view(['GET'])
def get_all_users(request):
    """
    GET /api/users/?page=1&limit=20&search=<tên hoặc msv>
    Yêu cầu admin token.
    """
    payload, err = require_admin(request)
    if err:
        return err

    page    = max(int(request.GET.get('page',  1)),  1)
    limit   = max(int(request.GET.get('limit', 20)), 1)
    search  = request.GET.get('search', '').strip()
    offset  = (page - 1) * limit

    with connection.cursor() as cursor:
        if search:
            cursor.execute(
                """
                SELECT id, name, username, role
                FROM users
                WHERE name ILIKE %s OR id ILIKE %s
                ORDER BY id
                LIMIT %s OFFSET %s
                """,
                [f'%{search}%', f'%{search}%', limit, offset]
            )
        else:
            cursor.execute(
                "SELECT id, name, username, role FROM users ORDER BY id LIMIT %s OFFSET %s",
                [limit, offset]
            )
        rows = cursor.fetchall()

        # Tổng để FE phân trang
        if search:
            cursor.execute(
                "SELECT COUNT(*) FROM users WHERE name ILIKE %s OR id ILIKE %s",
                [f'%{search}%', f'%{search}%']
            )
        else:
            cursor.execute("SELECT COUNT(*) FROM users")
        total = cursor.fetchone()[0]

    users = [{'id': r[0], 'name': r[1], 'username': r[2], 'role': r[3]} for r in rows]
    return Response({'total': total, 'page': page, 'limit': limit, 'data': users}, status=200)


@api_view(['GET'])
def get_user_by_username(request):
    """GET /api/getuserdetail/?username=<username>"""
    payload, err = require_admin(request)
    if err:
        return err

    username = request.GET.get('username', '').strip()
    if not username:
        return Response({'error': 'Thiếu username'}, status=400)

    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT id, name, username, role FROM users WHERE username = %s", [username]
        )
        row = cursor.fetchone()

    if not row:
        return Response({'error': 'Không tìm thấy user'}, status=404)

    return Response({'id': row[0], 'name': row[1], 'username': row[2], 'role': row[3]}, status=200)


@api_view(['POST'])
def add_user(request):
    """
    POST /api/adduser/
    Body: { "id", "name", "username", "pwd", "role" }
    Yêu cầu admin.
    """
    payload, err = require_admin(request)
    if err:
        return err

    user_id  = request.data.get('id', '').strip()
    name     = request.data.get('name', '').strip()
    username = request.data.get('username', '').strip()
    pwd      = request.data.get('pwd', '').strip()
    role     = request.data.get('role', 'student').strip()

    if not all([user_id, name, username, pwd]):
        return Response({'error': 'Thiếu trường bắt buộc'}, status=400)
    if role not in ('admin', 'student'):
        return Response({'error': 'role phải là admin hoặc student'}, status=400)

    hashed = hash_password(pwd)
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                "INSERT INTO users (id, name, username, pwd, role) VALUES (%s, %s, %s, %s, %s)",
                [user_id, name, username, hashed, role]
            )
        return Response({'message': 'Thêm user thành công'}, status=201)
    except Exception as e:
        if 'unique' in str(e).lower():
            return Response({'error': 'Username hoặc ID đã tồn tại'}, status=409)
        return Response({'error': str(e)}, status=500)


@api_view(['PUT'])
def update_user(request):
    """
    PUT /api/updateuser/
    Body: { "id", "name", "username", "pwd" (optional), "role" (optional) }
    Yêu cầu admin.
    """
    payload, err = require_admin(request)
    if err:
        return err

    user_id  = request.data.get('id', '').strip()
    name     = request.data.get('name', '').strip()
    username = request.data.get('username', '').strip()
    pwd      = request.data.get('pwd', '').strip()
    role     = request.data.get('role', '').strip()

    if not all([user_id, name, username]):
        return Response({'error': 'Thiếu id, name hoặc username'}, status=400)

    try:
        with connection.cursor() as cursor:
            if pwd:
                hashed = hash_password(pwd)
                cursor.execute(
                    "UPDATE users SET name=%s, username=%s, pwd=%s, role=COALESCE(NULLIF(%s,''), role) WHERE id=%s",
                    [name, username, hashed, role, user_id]
                )
            else:
                cursor.execute(
                    "UPDATE users SET name=%s, username=%s, role=COALESCE(NULLIF(%s,''), role) WHERE id=%s",
                    [name, username, role, user_id]
                )
        return Response({'message': 'Cập nhật user thành công'}, status=200)
    except Exception as e:
        return Response({'error': str(e)}, status=500)


@api_view(['DELETE'])
def delete_user(request):
    """DELETE /api/deleteuser/?username=<username> — yêu cầu admin."""
    payload, err = require_admin(request)
    if err:
        return err

    username = request.GET.get('username', '').strip()
    if not username:
        return Response({'error': 'Thiếu username'}, status=400)

    with connection.cursor() as cursor:
        cursor.execute("DELETE FROM users WHERE username = %s", [username])
    return Response({'message': 'Xóa user thành công'}, status=200)


@api_view(['POST'])
def reset_password(request):
    """
    POST /api/resetpassword/
    Body: { "username": "...", "new_pwd": "..." }
    Yêu cầu admin.
    """
    payload, err = require_admin(request)
    if err:
        return err

    username = request.data.get('username', '').strip()
    new_pwd  = request.data.get('new_pwd', '').strip()
    if not username or not new_pwd:
        return Response({'error': 'Thiếu username hoặc new_pwd'}, status=400)

    hashed = hash_password(new_pwd)
    with connection.cursor() as cursor:
        cursor.execute(
            "UPDATE users SET pwd = %s WHERE username = %s", [hashed, username]
        )
    return Response({'message': 'Đặt lại mật khẩu thành công'}, status=200)


# ═══════════════════════════════════════════════════════════════════════════════
# QUESTIONS
# ═══════════════════════════════════════════════════════════════════════════════

@api_view(['GET'])
def get_questions(request):
    """GET /api/questions/ — yêu cầu đăng nhập."""
    _, err = require_auth(request)
    if err:
        return err

    with connection.cursor() as cursor:
        cursor.execute("SELECT id, content FROM questions")
        rows = cursor.fetchall()

    questions = [{'id': r[0], 'content': r[1]} for r in rows]
    serializer = QuestionSerializer(questions, many=True)
    return Response(serializer.data)


# ═══════════════════════════════════════════════════════════════════════════════
# EXAMS
# ═══════════════════════════════════════════════════════════════════════════════

@api_view(['GET'])
def get_all_exams(request):
    """
    GET /api/exams/?page=1&limit=20&type=<type>&status=<status>&search=<title>
    Trả về danh sách bài thi có phân trang + lọc.
    """
    _, err = require_auth(request)
    if err:
        return err

    page    = max(int(request.GET.get('page',  1)),  1)
    limit   = max(int(request.GET.get('limit', 20)), 1)
    offset  = (page - 1) * limit
    q_type  = request.GET.get('type',   '').strip()
    status  = request.GET.get('status', '').strip()
    search  = request.GET.get('search', '').strip()

    filters = []
    params  = []
    if q_type:
        filters.append("q.type = %s");    params.append(q_type)
    if status:
        filters.append("q.status = %s");  params.append(status)
    if search:
        filters.append("q.title ILIKE %s"); params.append(f'%{search}%')

    where = ('WHERE ' + ' AND '.join(filters)) if filters else ''

    with connection.cursor() as cursor:
        cursor.execute(f"""
            SELECT q.id, q.title, q.type, q.status, q.time_limit,
                   q.created_at, COUNT(qq.question_id) AS q_count
            FROM quizzes q
            LEFT JOIN quiz_questions qq ON q.id = qq.quiz_id
            {where}
            GROUP BY q.id, q.title, q.type, q.status, q.time_limit, q.created_at
            ORDER BY q.created_at DESC
            LIMIT %s OFFSET %s
        """, params + [limit, offset])
        rows = cursor.fetchall()

        cursor.execute(f"SELECT COUNT(*) FROM quizzes q {where}", params)
        total = cursor.fetchone()[0]

    exams = [
        {
            'id': r[0], 'title': r[1], 'type': r[2],
            'status': r[3], 'time_limit': r[4],
            'created_at': str(r[5]), 'question_count': r[6],
        }
        for r in rows
    ]
    return Response({'total': total, 'page': page, 'limit': limit, 'data': exams}, status=200)


@api_view(['GET'])
def get_exam_detail(request):
    """GET /api/examdetail/?id=<id>"""
    _, err = require_auth(request)
    if err:
        return err

    exam_id = request.GET.get('id', '').strip()
    if not exam_id:
        return Response({'error': 'Thiếu id'}, status=400)

    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT id, title, created_at, type, status, time_limit FROM quizzes WHERE id = %s",
            [exam_id]
        )
        quiz = cursor.fetchone()
        if not quiz:
            return Response({'error': 'Không tìm thấy bài thi'}, status=404)

        quiz_data = {
            'id': quiz[0], 'title': quiz[1], 'created_at': str(quiz[2]),
            'type': quiz[3], 'status': quiz[4], 'time_limit': quiz[5],
            'questions': [],
        }

        cursor.execute("""
            SELECT q.id, q.content, c.id, c.content, c.is_correct
            FROM quiz_questions qq
            JOIN questions q ON qq.question_id = q.id
            JOIN choices    c ON c.question_id  = q.id
            WHERE qq.quiz_id = %s
            ORDER BY q.id
        """, [exam_id])
        rows = cursor.fetchall()

    question_map = {}
    for row in rows:
        q_id = row[0]
        if q_id not in question_map:
            question_map[q_id] = {'id': q_id, 'content': row[1], 'choices': []}
        question_map[q_id]['choices'].append({
            'id': row[2], 'content': row[3], 'is_correct': row[4]
        })

    quiz_data['questions'] = list(question_map.values())
    return Response(quiz_data, status=200)


@api_view(['POST'])
def create_exam(request):
    """
    POST /api/createexam/
    Body: { "title", "type", "status", "time_limit" (phút, 0=không giới hạn), "questions": [...] }
    Yêu cầu admin.
    """
    payload, err = require_admin(request)
    if err:
        return err

    title      = request.data.get('title', '').strip()
    quiz_type  = request.data.get('type', '').strip()
    status     = request.data.get('status', 'free').strip()
    time_limit = request.data.get('time_limit', 0)
    questions  = request.data.get('questions', [])

    if not title or not questions:
        return Response({'error': 'Thiếu title hoặc questions'}, status=400)
    if status not in ('free', 'limited'):
        return Response({'error': 'status phải là free hoặc limited'}, status=400)

    try:
        with transaction.atomic():
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO quizzes (title, created_at, type, status, time_limit)
                    VALUES (%s, NOW(), %s, %s, %s) RETURNING id
                    """,
                    [title, quiz_type, status, time_limit]
                )
                quiz_id = cursor.fetchone()[0]

                for q in questions:
                    content = q.get('content', '').strip()
                    choices = q.get('choices', [])
                    if not content or not choices:
                        raise ValueError('Câu hỏi thiếu content hoặc choices')

                    cursor.execute(
                        "INSERT INTO questions (content) VALUES (%s) RETURNING id", [content]
                    )
                    question_id = cursor.fetchone()[0]
                    cursor.execute(
                        "INSERT INTO quiz_questions (quiz_id, question_id) VALUES (%s, %s)",
                        [quiz_id, question_id]
                    )
                    for c in choices:
                        cursor.execute(
                            "INSERT INTO choices (question_id, content, is_correct) VALUES (%s, %s, %s)",
                            [question_id, c.get('content', ''), c.get('is_correct', False)]
                        )

        return Response({'message': 'Tạo bài thi thành công', 'quiz_id': quiz_id}, status=201)
    except ValueError as e:
        return Response({'error': str(e)}, status=400)
    except Exception as e:
        return Response({'error': str(e)}, status=500)


@api_view(['PUT'])
def update_exam(request):
    """
    PUT /api/updateexam/?id=<id>
    Body: { "title", "type", "status", "time_limit", "questions": [...] }
    Yêu cầu admin.
    """
    payload, err = require_admin(request)
    if err:
        return err

    exam_id    = request.GET.get('id', '').strip()
    title      = request.data.get('title', '').strip()
    quiz_type  = request.data.get('type', '').strip()
    status     = request.data.get('status', '').strip()
    time_limit = request.data.get('time_limit', None)
    questions  = request.data.get('questions', [])

    if not exam_id or not title or not questions:
        return Response({'error': 'Thiếu id, title hoặc questions'}, status=400)

    try:
        with transaction.atomic():
            with connection.cursor() as cursor:
                cursor.execute("SELECT id FROM quizzes WHERE id = %s", [exam_id])
                if not cursor.fetchone():
                    return Response({'error': 'Không tìm thấy bài thi'}, status=404)

                cursor.execute(
                    """
                    UPDATE quizzes
                    SET title      = %s,
                        type       = COALESCE(NULLIF(%s,''), type),
                        status     = COALESCE(NULLIF(%s,''), status),
                        time_limit = COALESCE(%s, time_limit)
                    WHERE id = %s
                    """,
                    [title, quiz_type, status, time_limit, exam_id]
                )

                cursor.execute(
                    "SELECT question_id FROM quiz_questions WHERE quiz_id = %s", [exam_id]
                )
                old_ids = [r[0] for r in cursor.fetchall()]
                if old_ids:
                    cursor.execute("DELETE FROM choices   WHERE question_id = ANY(%s)", [old_ids])
                    cursor.execute("DELETE FROM questions WHERE id          = ANY(%s)", [old_ids])
                cursor.execute("DELETE FROM quiz_questions WHERE quiz_id = %s", [exam_id])

                for q in questions:
                    content = q.get('content', '').strip()
                    choices = q.get('choices', [])
                    if not content or not choices:
                        raise ValueError('Câu hỏi thiếu content hoặc choices')
                    cursor.execute(
                        "INSERT INTO questions (content) VALUES (%s) RETURNING id", [content]
                    )
                    question_id = cursor.fetchone()[0]
                    cursor.execute(
                        "INSERT INTO quiz_questions (quiz_id, question_id) VALUES (%s, %s)",
                        [exam_id, question_id]
                    )
                    for c in choices:
                        cursor.execute(
                            "INSERT INTO choices (question_id, content, is_correct) VALUES (%s, %s, %s)",
                            [question_id, c.get('content', ''), c.get('is_correct', False)]
                        )

        return Response({'message': 'Cập nhật bài thi thành công'}, status=200)
    except ValueError as e:
        return Response({'error': str(e)}, status=400)
    except Exception as e:
        return Response({'error': str(e)}, status=500)


@api_view(['DELETE'])
def delete_exam(request):
    """DELETE /api/deleteexam/?id=<id> — yêu cầu admin."""
    payload, err = require_admin(request)
    if err:
        return err

    exam_id = request.GET.get('id', '').strip()
    if not exam_id:
        return Response({'error': 'Thiếu id'}, status=400)

    try:
        with transaction.atomic():
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT question_id FROM quiz_questions WHERE quiz_id = %s", [exam_id]
                )
                q_ids = [r[0] for r in cursor.fetchall()]
                if q_ids:
                    cursor.execute("DELETE FROM choices   WHERE question_id = ANY(%s)", [q_ids])
                    cursor.execute("DELETE FROM questions WHERE id          = ANY(%s)", [q_ids])
                cursor.execute("DELETE FROM quiz_questions WHERE quiz_id = %s", [exam_id])
                cursor.execute("DELETE FROM quizzes WHERE id = %s", [exam_id])
        return Response({'message': 'Xóa bài thi thành công'}, status=200)
    except Exception as e:
        return Response({'error': str(e)}, status=500)


# ═══════════════════════════════════════════════════════════════════════════════
# SUBMIT & ATTEMPTS
# ═══════════════════════════════════════════════════════════════════════════════

@api_view(['POST'])
def submit_exam(request, id):
    """
    POST /api/submitexam/<id>/
    Body: { "user_id": "...", "answers": [{"question_id": ..., "choice_id": ...}] }
    Tự động chấm, lưu kết quả.
    """
    payload, err = require_auth(request)
    if err:
        return err

    user_id = request.data.get('user_id', '').strip()
    answers = request.data.get('answers', [])
    if not user_id or not answers:
        return Response({'error': 'Thiếu user_id hoặc answers'}, status=400)

    try:
        with transaction.atomic():
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT id, status, time_limit FROM quizzes WHERE id = %s", [id]
                )
                quiz = cursor.fetchone()
                if not quiz:
                    return Response({'error': 'Không tìm thấy bài thi'}, status=404)

                quiz_status = quiz[1]
                if quiz_status == 'limited':
                    # Kiểm tra user đã nộp bài này chưa
                    cursor.execute(
                        "SELECT id FROM attempts WHERE user_id = %s AND quiz_id = %s",
                        [user_id, id]
                    )
                    if cursor.fetchone():
                        return Response(
                            {'error': 'Bài thi có giới hạn – bạn đã nộp bài này rồi'},
                            status=403
                        )

                # Lấy đáp án đúng
                cursor.execute("""
                    SELECT q.id, c.id
                    FROM quiz_questions qq
                    JOIN questions q ON qq.question_id = q.id
                    JOIN choices   c ON c.question_id  = q.id
                    WHERE qq.quiz_id = %s AND c.is_correct = TRUE
                """, [id])
                correct_map = {row[0]: row[1] for row in cursor.fetchall()}

                total = len(correct_map)
                score = sum(
                    1 for ans in answers
                    if correct_map.get(ans.get('question_id')) == ans.get('choice_id')
                )

                cursor.execute(
                    "INSERT INTO attempts (user_id, quiz_id, score, created_at) VALUES (%s, %s, %s, NOW()) RETURNING id",
                    [user_id, id, score]
                )
                attempt_id = cursor.fetchone()[0]

                for ans in answers:
                    cursor.execute(
                        "INSERT INTO answers (attempt_id, question_id, choice_id) VALUES (%s, %s, %s)",
                        [attempt_id, ans.get('question_id'), ans.get('choice_id')]
                    )

        return Response({
            'message': 'Nộp bài thành công',
            'attempt_id': attempt_id,
            'score': score,
            'total': total,
        }, status=200)
    except Exception as e:
        return Response({'error': str(e)}, status=500)


@api_view(['GET'])
def get_all_attempts(request):
    """
    GET /api/attempts/?page=1&limit=20
    Yêu cầu admin.
    """
    payload, err = require_admin(request)
    if err:
        return err

    page   = max(int(request.GET.get('page',  1)),  1)
    limit  = max(int(request.GET.get('limit', 20)), 1)
    offset = (page - 1) * limit

    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT
                u.id                        AS msv,
                u.name                      AS ho_ten,
                qz.title                    AS ten_de,
                a.score,
                COUNT(qq.question_id)       AS total,
                a.created_at,
                a.id                        AS attempt_id
            FROM attempts a
            JOIN users          u  ON a.user_id = u.id
            JOIN quizzes        qz ON a.quiz_id  = qz.id
            LEFT JOIN quiz_questions qq ON qq.quiz_id = qz.id
            GROUP BY u.id, u.name, qz.title, a.score, a.created_at, a.id
            ORDER BY a.created_at DESC
            LIMIT %s OFFSET %s
        """, [limit, offset])
        rows = cursor.fetchall()

        cursor.execute("SELECT COUNT(*) FROM attempts")
        total_count = cursor.fetchone()[0]

    data = [
        {
            'attempt_id': r[6],
            'msv':        r[0],
            'ho_ten':     r[1],
            'ten_de':     r[2],
            'score':      r[3],
            'total':      r[4],
            'created_at': str(r[5]),
        }
        for r in rows
    ]
    return Response({'total': total_count, 'page': page, 'limit': limit, 'data': data}, status=200)


# ═══════════════════════════════════════════════════════════════════════════════
# SEARCH & DASHBOARD
# ═══════════════════════════════════════════════════════════════════════════════

@api_view(['GET'])
def search_by_msv(request):
    """GET /api/search/?msv=<msv> — tra cứu sinh viên + lịch sử làm bài."""
    _, err = require_auth(request)
    if err:
        return err

    msv = request.GET.get('msv', '').strip()
    if not msv:
        return Response({'error': 'Thiếu msv'}, status=400)

    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT id, name, username, role FROM users WHERE id = %s", [msv]
        )
        user_row = cursor.fetchone()
        if not user_row:
            return Response({'error': 'Không tìm thấy sinh viên'}, status=404)

        cursor.execute("""
            SELECT
                qz.title,
                a.score,
                COUNT(qq.question_id) AS total,
                a.created_at
            FROM attempts a
            JOIN quizzes qz ON a.quiz_id = qz.id
            LEFT JOIN quiz_questions qq ON qq.quiz_id = qz.id
            WHERE a.user_id = %s
            GROUP BY qz.title, a.score, a.created_at
            ORDER BY a.created_at DESC
        """, [msv])
        attempt_rows = cursor.fetchall()

    return Response({
        'msv':      user_row[0],
        'ho_ten':   user_row[1],
        'username': user_row[2],
        'role':     user_row[3],
        'attempts': [
            {
                'ten_de':     r[0],
                'score':      r[1],
                'total':      r[2],
                'created_at': str(r[3]),
            }
            for r in attempt_rows
        ],
    }, status=200)


@api_view(['GET'])
def dashboard(request):
    """
    GET /api/dashboard/
    Trả về số liệu tổng quan cho trang admin.
    Yêu cầu admin.
    """
    payload, err = require_admin(request)
    if err:
        return err

    with connection.cursor() as cursor:
        cursor.execute("SELECT COUNT(*) FROM users")
        total_users = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM quizzes")
        total_exams = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM attempts")
        total_attempts = cursor.fetchone()[0]

        # Phân phối điểm (histogram, 10 bucket)
        cursor.execute("""
            SELECT
                FLOOR(score / 10) * 10  AS bucket,
                COUNT(*)                AS count
            FROM attempts
            GROUP BY bucket
            ORDER BY bucket
        """)
        score_distribution = [
            {'range': f"{r[0]}-{r[0]+9}", 'count': r[1]}
            for r in cursor.fetchall()
        ]

        # Top 5 bài thi được làm nhiều nhất
        cursor.execute("""
            SELECT qz.title, COUNT(a.id) AS attempt_count
            FROM attempts a
            JOIN quizzes qz ON a.quiz_id = qz.id
            GROUP BY qz.title
            ORDER BY attempt_count DESC
            LIMIT 5
        """)
        top_exams = [{'title': r[0], 'attempt_count': r[1]} for r in cursor.fetchall()]

    return Response({
        'total_users':        total_users,
        'total_exams':        total_exams,
        'total_attempts':     total_attempts,
        'score_distribution': score_distribution,
        'top_exams':          top_exams,
    }, status=200)