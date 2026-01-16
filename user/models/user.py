import uuid

from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db.models.signals import post_save

from user.models.school import School

import logging
logger = logging.getLogger(__name__)

class UserManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self._create_user(email, password, **extra_fields)



class User(AbstractUser):
    username = None
    firstname = None
    lastname = None
    school = models.ForeignKey(School, on_delete=models.SET_NULL, null=True, blank=True)
    is_school = models.BooleanField('Это школа', default=False, null=False)

    uuid = models.UUIDField(default=uuid.uuid4, editable=False)
    avatar = models.FileField(upload_to='avatars', null=True, blank=True)
    email = models.CharField('Почта', max_length=255, blank=True, null=True, unique=True)
    login = models.CharField('Логин', max_length=255, blank=True, null=True, unique=True)
    full_name = models.CharField('ФИО', max_length=255, blank=True, null=True)
    phone = models.CharField('Телефон', max_length=255, blank=True, null=True)
    comment = models.TextField('Коментарий', blank=True, null=True)

    last_lesson_url = models.CharField(max_length=255, blank=True, null=True)

    subscription_expire = models.DateField('Подписка до', blank=True, null=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []
    objects = UserManager()

    def __str__(self):
        return f'{self.full_name or self.email}'

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = '1. Пользователи'


def user_post_save(sender, instance, created, **kwargs):
    #import monthdelta
    #datetime.date.today() + monthdelta.monthdelta(months=1)
    from user.services.school import create_school
    if created:
        print('created')
        if instance.is_school:
            create_school(admin_user=instance)


post_save.connect(user_post_save, sender=User)

