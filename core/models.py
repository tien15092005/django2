from django.db import models
from django.contrib.auth.models import User


# 👤 Profile (extend user)
class Profile(models.Model):
    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, unique=True)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    height_cm = models.FloatField(null=True, blank=True)
    weight_kg = models.FloatField(null=True, blank=True)
    age = models.IntegerField(null=True, blank=True)

    class Meta:
        db_table = "profile"

    def __str__(self):
        return self.user.username


# 🏋️ Equipment
class Equipment(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)

    class Meta:
        db_table = "equipment"

    def __str__(self):
        return self.name


# 💪 Exercise
class Exercise(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(null=True, blank=True)
    muscle_group = models.CharField(max_length=100, null=True, blank=True)

    equipment = models.ForeignKey(
        Equipment,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    calories_per_minute = models.FloatField(default=5)

    class Meta:
        db_table = "exercise"

    def __str__(self):
        return self.name


# 📚 Course (admin tạo)
class Course(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(null=True, blank=True)

    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        db_column='created_by'
    )

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "course"

    def __str__(self):
        return self.name


# 🔗 Course - Exercise
class CourseExercise(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    exercise = models.ForeignKey(Exercise, on_delete=models.CASCADE)

    sets = models.IntegerField()
    reps = models.IntegerField()
    order = models.IntegerField()
    rest_seconds = models.IntegerField(null=True, blank=True)

    class Meta:
        db_table = "course_exercise"


# 🎯 Goal
class Goal(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    target_weight = models.FloatField(null=True, blank=True)
    target_fat_percent = models.FloatField(null=True, blank=True)

    start_date = models.DateField()
    end_date = models.DateField()

    class Meta:
        db_table = "goal"


# 📊 Progress
class Progress(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    date = models.DateField()
    weight = models.FloatField(null=True, blank=True)
    fat_percent = models.FloatField(null=True, blank=True)

    workout_minutes = models.IntegerField(default=0)
    calories_burned = models.FloatField(default=0)

    class Meta:
        db_table = "progress"


# 🏃 Workout Session
class WorkoutSession(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    course = models.ForeignKey(
        Course,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    session_date = models.DateField()
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()

    total_duration_minutes = models.FloatField(null=True, blank=True)
    total_calories = models.FloatField(default=0)

    notes = models.TextField(null=True, blank=True)

    class Meta:
        db_table = "workout_session"


# 🔥 Exercise trong session
class WorkoutExercise(models.Model):
    session = models.ForeignKey(WorkoutSession, on_delete=models.CASCADE)
    exercise = models.ForeignKey(Exercise, on_delete=models.CASCADE)

    sets = models.IntegerField()
    reps = models.IntegerField()
    weight_kg = models.FloatField(null=True, blank=True)

    duration_minutes = models.FloatField(null=True, blank=True)
    calories_burned = models.FloatField(default=0)

    class Meta:
        db_table = "workout_exercise"