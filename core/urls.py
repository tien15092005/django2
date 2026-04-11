from django.urls import path
from . import views

urlpatterns = [
    # ── Auth ────────────────────────────────────────────
    path('login/',          views.login,                name='login'),
    path('signup/',         views.signup,               name='signup'),

    # ── Users ───────────────────────────────────────────
    path('users/',          views.get_all_users,        name='get_all_users'),
    path('getuserdetail/',  views.get_user_by_username, name='get_user_by_username'),
    path('updateuser/',     views.update_user,          name='update_user'),
    path('deleteuser/',     views.delete_user,          name='delete_user'),
    path('adduser/',        views.add_user,             name='add_user'),

    # ── Questions ───────────────────────────────────────
    path('questions/',      views.get_questions,        name='get_questions'),

    # ── Exams ───────────────────────────────────────────
    path('exams/',          views.get_all_exams,        name='get_all_exams'),
    path('examdetail/',     views.get_exam_detail,      name='get_exam_detail'),
    path('createexam/',     views.create_exam,          name='create_exam'),
    path('updateexam/',     views.update_exam,          name='update_exam'),
    path('deleteexam/',     views.delete_exam,          name='delete_exam'),

    # ── Attempts ────────────────────────────────────────
    path('submitexam/<int:id>/', views.submit_exam,     name='submit_exam'),
    path('attempts/',       views.get_all_attempts,     name='get_all_attempts'),

    # ── Search & Stats ──────────────────────────────────
    path('search/',         views.search_by_msv,        name='search_by_msv'),
    path('dashboard/',      views.dashboard,            name='dashboard'),

    # ── Misc ────────────────────────────────────────────
    path('resetpassword/',  views.reset_password,       name='reset_password'),
]