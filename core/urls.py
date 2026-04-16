from django.urls import path
from . import views

urlpatterns = [
    # ── Auth ────────────────────────────────────────────
    path('login/',                      views.login,                name='login'),
    path('signup/',                     views.signup,               name='signup'),

    # ── Course ──────────────────────────────────────────
    path('courses/',                    views.get_all_courses,      name='get_all_courses'),
    path('courses/<int:course_id>/',    views.get_course_detail,    name='get_course_detail'),

# ── Exercise ─────────────────────────────────────────
    path('exercises/',                      views.get_all_exercises,    name='get_all_exercises'),
    path('exercises/<int:exercise_id>/',    views.get_exercise_detail,  name='get_exercise_detail'),
    path('exercises/search/',               views.search_exercises,     name='search_exercises'),

    # ── User ─────────────────────────────────────────────
    path('users/<int:user_id>/settings/',   views.user_settings,        name='user_settings'),
    path('users/<int:user_id>/history/',    views.user_history,         name='user_history'),
]

