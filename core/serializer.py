from rest_framework import serializers
from django.contrib.auth.models import User
from django.db import transaction
from .models import Course, CourseExercise, Exercise, Equipment, Profile, WorkoutSession


class EquipmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Equipment
        fields = ['id', 'name', 'description']


class ExerciseSerializer(serializers.ModelSerializer):
    equipment = EquipmentSerializer(read_only=True)

    class Meta:
        model = Exercise
        fields = ['id', 'name', 'description', 'muscle_group', 'guidelines', 'equipment', 'calories_per_minute']


class CourseExerciseSerializer(serializers.ModelSerializer):
    exercise = ExerciseSerializer(read_only=True)

    class Meta:
        model = CourseExercise
        fields = ['id', 'exercise', 'sets', 'reps', 'order', 'rest_seconds']


class CourseExerciseAdminSerializer(serializers.ModelSerializer):
    exercise = ExerciseSerializer(read_only=True)
    exercise_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = CourseExercise
        fields = ['id', 'exercise', 'exercise_id', 'sets', 'reps', 'order', 'rest_seconds']

    def validate_exercise_id(self, value):
        if not Exercise.objects.filter(id=value).exists():
            raise serializers.ValidationError('Exercise không tồn tại')
        return value


class CourseListSerializer(serializers.ModelSerializer):
    exercise_count = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Course
        fields = ['id', 'name', 'description', 'is_active', 'created_at', 'exercise_count']
        read_only_fields = ['created_at', 'exercise_count']

    def get_exercise_count(self, obj):
        return obj.courseexercise_set.count()


class CourseAdminSerializer(serializers.ModelSerializer):
    exercise_count = serializers.SerializerMethodField(read_only=True)
    exercises = CourseExerciseAdminSerializer(source='courseexercise_set', many=True, required=False)

    class Meta:
        model = Course
        fields = ['id', 'name', 'description', 'is_active', 'created_at', 'exercise_count', 'exercises']
        read_only_fields = ['created_at', 'exercise_count']

    def get_exercise_count(self, obj):
        return obj.courseexercise_set.count()

    def validate(self, attrs):
        rows = attrs.get('courseexercise_set', None)
        if rows is None:
            return attrs

        exercise_ids = [row.get('exercise_id') for row in rows]
        if len(exercise_ids) != len(set(exercise_ids)):
            raise serializers.ValidationError({'exercises': 'Không được trùng exercise trong cùng một course'})

        for row in rows:
            if row.get('sets', 0) <= 0 or row.get('reps', 0) <= 0:
                raise serializers.ValidationError({'exercises': 'Sets và reps phải lớn hơn 0'})
            rest_seconds = row.get('rest_seconds', None)
            if rest_seconds is not None and rest_seconds < 0:
                raise serializers.ValidationError({'exercises': 'Rest seconds không được âm'})

        return attrs

    @transaction.atomic
    def _replace_course_exercises(self, course, course_exercises_data):
        course.courseexercise_set.all().delete()

        rows = []
        for index, item in enumerate(course_exercises_data):
            rows.append(
                CourseExercise(
                    course=course,
                    exercise_id=item['exercise_id'],
                    sets=item['sets'],
                    reps=item['reps'],
                    order=index + 1,
                    rest_seconds=item.get('rest_seconds'),
                )
            )

        if rows:
            CourseExercise.objects.bulk_create(rows)

    @transaction.atomic
    def create(self, validated_data):
        course_exercises_data = validated_data.pop('courseexercise_set', [])
        user = self.context.get('user')
        if user and not validated_data.get('created_by'):
            validated_data['created_by'] = user
        course = Course.objects.create(**validated_data)
        self._replace_course_exercises(course, course_exercises_data)
        return course

    @transaction.atomic
    def update(self, instance, validated_data):
        course_exercises_data = validated_data.pop('courseexercise_set', None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if course_exercises_data is not None:
            self._replace_course_exercises(instance, course_exercises_data)

        return instance


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
        fields = ['id', 'name', 'description', 'muscle_group', 'guidelines', 'equipment', 'calories_per_minute']


class ExerciseDetailSerializer(serializers.ModelSerializer):
    equipment = EquipmentSerializer(read_only=True)
    equipment_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)

    class Meta:
        model = Exercise
        fields = ['id', 'name', 'description', 'muscle_group', 'guidelines', 'equipment', 'equipment_id', 'calories_per_minute']

    def create(self, validated_data):
        equipment_id = validated_data.pop('equipment_id', None)
        exercise = Exercise.objects.create(**validated_data, equipment_id=equipment_id)
        return exercise


class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ['gender', 'blood_type', 'medical_conditions', 'height_cm', 'weight_kg', 'age', 'avatar']


class WorkoutSessionSerializer(serializers.ModelSerializer):
    course_name = serializers.CharField(source='course.name', read_only=True)

    class Meta:
        model = WorkoutSession
        fields = ['id', 'course_name', 'session_date', 'start_time', 'end_time', 'total_duration_minutes', 'total_calories', 'notes']