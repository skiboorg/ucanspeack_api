from djoser.serializers import TokenCreateSerializer
from django.contrib.auth import get_user_model
from rest_framework import serializers
from user.models import UserToken

User = get_user_model()

MAX_SESSIONS = 1

class CustomTokenCreateSerializer(TokenCreateSerializer):
    login = serializers.CharField(required=True)
    password = serializers.CharField(required=True, write_only=True)

    def validate(self, attrs):
        login = attrs.get("login")
        password = attrs.get("password")

        try:
            user = User.objects.get(email=login)
        except User.DoesNotExist:
            raise serializers.ValidationError("User not found")

        if not user.check_password(password):
            raise serializers.ValidationError("Invalid password")

        # проверяем количество активных сессий
        count = UserToken.objects.filter(user=user).count()
        if count >= MAX_SESSIONS:
            raise serializers.ValidationError("Maximum sessions limit reached")

        token = UserToken.objects.create(user=user)

        return {
            "auth_token": token.key
        }
