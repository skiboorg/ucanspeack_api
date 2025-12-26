from rest_framework import  serializers
from django.contrib.auth import get_user_model

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = [
            'is_school',
            'avatar',
            'email',
            'full_name',
            'phone',
            'subscription_expire',
            'is_superuser',
            'last_lesson_url',
        ]

        extra_kwargs = {
            'password': {'required': False},
            'is_superuser' : {'read_only': False},
        }
