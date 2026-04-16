from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Course, CourseExercise, Exercise, Equipment
from .models import Course, CourseExercise, Exercise, Equipment, Profile, WorkoutSession

class EquipmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Equipment
        fields = ['id', 'name', 'description']


class ExerciseSerializer(serializers.ModelSerializer):
    equipment = EquipmentSerializer(read_only=True)

    class Meta:
        model = Exercise
        fields = ['id', 'name', 'description', 'muscle_group', 'equipment', 'calories_per_minute']


class CourseExerciseSerializer(serializers.ModelSerializer):
    exercise = ExerciseSerializer(read_only=True)

    class Meta:
        model = CourseExercise
        fields = ['id', 'exercise', 'sets', 'reps', 'order', 'rest_seconds']


class CourseListSerializer(serializers.ModelSerializer):
    exercise_count = serializers.SerializerMethodField()

    class Meta:
        model = Course
        fields = ['id', 'name', 'description', 'is_active', 'created_at', 'exercise_count']

    def get_exercise_count(self, obj):
        return obj.courseexercise_set.count()


class CourseDetailSerializer(serializers.ModelSerializer):
    exercises = serializers.SerializerMethodField()

    class Meta:
        model = Course
        fields = ['id', 'name', 'description', 'is_active', 'created_at', 'exercises']

    def get_exercises(self, obj):
        ce_qs = obj.courseexercise_set.select_related('exercise__equipment').order_by('order')
        return CourseExerciseSerializer(ce_qs, many=True).data


class ExerciseListSerializer(serializers.ModelSerializer):
    equipment = EquipmentSerializer(read_only=True)

    class Meta:
        model = Exercise
        fields = ['id', 'name', 'muscle_group', 'equipment', 'calories_per_minute']


class ExerciseDetailSerializer(serializers.ModelSerializer):
    equipment = EquipmentSerializer(read_only=True)

    class Meta:
        model = Exercise
        fields = ['id', 'name', 'description', 'muscle_group', 'equipment', 'calories_per_minute']


class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ['gender', 'height_cm', 'weight_kg', 'age']


class WorkoutSessionSerializer(serializers.ModelSerializer):
    course_name = serializers.CharField(source='course.name', read_only=True)

    class Meta:
        model = WorkoutSession
        fields = ['id', 'course_name', 'session_date', 'start_time', 'end_time', 'total_duration_minutes', 'total_calories', 'notes']