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


from .serializer import ExerciseListSerializer, ExerciseDetailSerializer, ProfileSerializer, WorkoutSessionSerializer
from .models import Exercise, Profile, WorkoutSession


# ── Exercise ─────────────────────────────────────────

@api_view(['GET'])
def get_all_exercises(request):
    exercises = Exercise.objects.select_related('equipment').all()
    serializer = ExerciseListSerializer(exercises, many=True)
    return Response({
        "success": True,
        "count": exercises.count(),
        "data": serializer.data
    })


@api_view(['GET'])
def get_exercise_detail(request, exercise_id):
    try:
        exercise = Exercise.objects.get(id=exercise_id)
    except Exercise.DoesNotExist:
        return Response({"success": False, "message": "Bài tập không tồn tại"}, status=404)

    serializer = ExerciseDetailSerializer(exercise)
    return Response({"success": True, "data": serializer.data})


@api_view(['GET'])
def search_exercises(request):
    name = request.query_params.get('name', '').strip()
    if not name:
        return Response({"success": False, "message": "Thiếu tham số name"}, status=400)

    exercises = Exercise.objects.filter(name__icontains=name)
    serializer = ExerciseListSerializer(exercises, many=True)
    return Response({
        "success": True,
        "count": exercises.count(),
        "data": serializer.data
    })


# ── User Settings & History ───────────────────────────

@api_view(['GET', 'POST'])
def user_settings(request, user_id):
    try:
        profile = Profile.objects.get(user_id=user_id)
    except Profile.DoesNotExist:
        return Response({"success": False, "message": "User không tồn tại"}, status=404)

    if request.method == 'GET':
        serializer = ProfileSerializer(profile)
        return Response({"success": True, "data": serializer.data})

    elif request.method == 'POST':
        serializer = ProfileSerializer(profile, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({"success": True, "message": "Cập nhật thành công", "data": serializer.data})
        return Response({"success": False, "errors": serializer.errors}, status=400)


@api_view(['GET'])
def user_history(request, user_id):
    sessions = WorkoutSession.objects.filter(user_id=user_id).order_by('-session_date')
    serializer = WorkoutSessionSerializer(sessions, many=True)
    return Response({
        "success": True,
        "count": sessions.count(),
        "data": serializer.data
    })