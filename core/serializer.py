from rest_framework import serializers


class QuestionSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    content = serializers.CharField()


class UserSerializer(serializers.Serializer):
    id = serializers.CharField()
    name = serializers.CharField()
    username = serializers.CharField()
    role = serializers.CharField()
    # pwd KHÔNG trả về ngoài API