from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated

from user.models import School
from user.serializers.me import UserSerializer
from djoser.views import TokenCreateView
from rest_framework import generics, viewsets, parsers

import logging

from user.serializers.school import SchoolSerializer

logger = logging.getLogger(__name__)




class CustomTokenCreateView(TokenCreateView):
    def _action(self, serializer):
        serializer.is_valid(raise_exception=True)
        return Response(serializer.validated_data, status=200)

class GetUser(generics.RetrieveAPIView):
    # permission_classes = [IsAuthenticated]
    serializer_class = UserSerializer

    def get_object(self):
        print(self.request.user)
        return self.request.user


class SchoolData(APIView):
    def get(self, request):
        slug = request.GET.get('slug', None)
        result = {'image':None}
        if slug:
            qs = School.objects.filter(slug=slug)
            if qs.exists():
                school = qs.first()
                serializer = SchoolSerializer(school)
                result = serializer.data
        return Response(result, status=200)

class UpdateUser(APIView):
    def patch(self, request):
        print(request.data)
        serializer = UserSerializer(instance=request.user, data=request.data)
        password = request.data.get('password', None)
        if serializer.is_valid():
            user = serializer.save()
            if password:
                user.set_password(password)
                user.save()
            return Response(status=200)
        else:
            print(serializer.errors)
            return Response(serializer.errors,status=400)

