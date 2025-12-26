from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from user.serializers.me import UserSerializer

from rest_framework import generics, viewsets, parsers

import logging
logger = logging.getLogger(__name__)


class GetUser(generics.RetrieveAPIView):
    # permission_classes = [IsAuthenticated]
    serializer_class = UserSerializer

    def get_object(self):
        print(self.request.user)
        return self.request.user


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

