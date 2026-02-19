from django.db.models import Sum
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.db import models

from user.models import User
from user.models.school import School

from user.serializers.me import UserSerializer


def create_school(admin_user:User):
    School.objects.create(
        name=f'{admin_user.email} school',
        admin=admin_user,
    )


class SchoolPupilViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    def get_school(self, request):
        return get_object_or_404(School, admin=request.user)

    def check_max_logins_limit(self, school, new_max_logins, exclude_pupil_id=None):
        pupils_qs = school.pupils.all()
        if exclude_pupil_id:
            pupils_qs = pupils_qs.exclude(id=exclude_pupil_id)

        current_sum = pupils_qs.aggregate(total=Sum('max_logins'))['total'] or 0
        admin_limit = school.admin.max_logins

        return (current_sum + new_max_logins) <= admin_limit

    # GET /school-pupils/
    def list(self, request):
        school = self.get_school(request)
        pupils = school.pupils.all()
        serializer = UserSerializer(pupils, many=True)
        print(serializer.data[0] if serializer.data else 'empty')
        return Response(serializer.data)

    # POST /school-pupils/
    def create(self, request):
        school = self.get_school(request)
        serializer = UserSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        new_max_logins = serializer.validated_data.get('max_logins', 0)

        if not self.check_max_logins_limit(school, new_max_logins):
            return Response(
                {
                    'detail': f'Превышен лимит подключений. Доступно: {school.admin.max_logins - school.pupils.aggregate(total=models.Sum("max_logins"))["total"] or 0}'},
                status=status.HTTP_400_BAD_REQUEST
            )

        pupil = serializer.save()

        pupil.subscription_expire = school.admin.subscription_expire
        pupil.save()

        school.pupils.add(pupil)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    # GET /school-pupils/{id}/
    def retrieve(self, request, pk=None):
        school = self.get_school(request)
        pupil = get_object_or_404(school.pupils, id=pk)
        serializer = UserSerializer(pupil)
        return Response(serializer.data)

    # PUT/PATCH /school-pupils/{id}/
    def partial_update(self, request, pk=None):
        school = self.get_school(request)
        pupil = get_object_or_404(school.pupils, id=pk)
        serializer = UserSerializer(pupil, data=request.data, partial=True)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        new_max_logins = serializer.validated_data.get('max_logins', pupil.max_logins)

        if not self.check_max_logins_limit(school, new_max_logins, exclude_pupil_id=pk):
            used = school.pupils.exclude(id=pk).aggregate(total=Sum('max_logins'))['total'] or 0
            available = school.admin.max_logins - used
            return Response(
                {'detail': f'Превышен лимит подключений. Доступно: {available}'},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer.save()
        return Response(serializer.data)

    # DELETE /school-pupils/{id}/
    def destroy(self, request, pk=None):
        school = self.get_school(request)
        pupil = get_object_or_404(school.pupils, id=pk)
        school.pupils.remove(pupil)  # убираем из школы, не удаляем юзера
        # pupil.delete()  # раскомментировать если нужно удалять юзера полностью
        return Response(status=status.HTTP_204_NO_CONTENT)