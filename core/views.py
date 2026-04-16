from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from .models import Course
from .serializer import CourseListSerializer, CourseDetailSerializer
import jwt
import datetime
from django.conf import settings


def generate_token(user):
    payload = {
        'user_id': user.id,
        'username': user.username,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=settings.JWT_EXP_HOURS)
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


# ── Auth ────────────────────────────────────────────

@api_view(['POST'])
def login(request):
    username = request.data.get('username', '').strip()
    password = request.data.get('password', '').strip()

    if not username or not password:
        return Response({"success": False, "message": "Thiếu username hoặc password"}, status=400)

    user = authenticate(username=username, password=password)
    if not user:
        return Response({"success": False, "message": "Sai username hoặc password"}, status=401)

    token = generate_token(user)
    return Response({
        "success": True,
        "token": token,
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
        }
    })


@api_view(['POST'])
def signup(request):
    username = request.data.get('username', '').strip()
    password = request.data.get('password', '').strip()
    email = request.data.get('email', '').strip()

    if not username or not password:
        return Response({"success": False, "message": "Thiếu username hoặc password"}, status=400)

    if User.objects.filter(username=username).exists():
        return Response({"success": False, "message": "Username đã tồn tại"}, status=400)

    user = User.objects.create_user(username=username, password=password, email=email)
    token = generate_token(user)
    return Response({
        "success": True,
        "message": "Đăng ký thành công",
        "token": token,
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
        }
    }, status=201)


# ── Course ───────────────────────────────────────────

@api_view(['GET'])
def get_all_courses(request):
    courses = Course.objects.filter(is_active=True).order_by('-created_at')
    serializer = CourseListSerializer(courses, many=True)
    return Response({
        "success": True,
        "count": courses.count(),
        "data": serializer.data
    })


@api_view(['GET'])
def get_course_detail(request, course_id):
    try:
        course = Course.objects.get(id=course_id, is_active=True)
    except Course.DoesNotExist:
        return Response({"success": False, "message": "Course không tồn tại"}, status=404)

    serializer = CourseDetailSerializer(course)
    return Response({"success": True, "data": serializer.data})