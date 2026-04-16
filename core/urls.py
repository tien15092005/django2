from django.urls import path
from . import views

urlpatterns = [
    # ── Auth ────────────────────────────────────────────
    path('login/',                      views.login,                name='login'),
    path('signup/',                     views.signup,               name='signup'),

    # ── Course ──────────────────────────────────────────
    path('courses/',                    views.get_all_courses,      name='get_all_courses'),
    path('courses/<int:course_id>/',    views.get_course_detail,    name='get_course_detail'),
]