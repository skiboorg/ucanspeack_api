from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import date
from user.models import School
User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    is_pupil = serializers.SerializerMethodField()
    is_subscription_expired = serializers.SerializerMethodField()
    password = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = User
        fields = [
            'id',
            'is_school',
            'max_logins',
            'avatar',
            'email',
            'full_name',
            'phone',
            'subscription_expire',
            'is_superuser',
            'last_lesson_url',
            'is_pupil',
            'is_subscription_expired',
            'password'
        ]
        read_only_fields = ['id']

        extra_kwargs = {
            'password': {'required': False},
            'is_superuser': {'read_only': False},
        }

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user

    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if password:
            instance.set_password(password)
        instance.save()
        return instance

    def get_is_pupil(self, obj):
        return School.objects.filter(pupils=obj).exists()

    def get_is_subscription_expired(self, obj):
        if obj.subscription_expire is None:
            return True  # Если дата не установлена, считаем подписку истекшей
        return obj.subscription_expire < date.today()