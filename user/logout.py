# views.py
from rest_framework import status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from .models import UserToken


class CustomLogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        """
        Кастомный logout с условным удалением токенов

        Параметры:
        - all_devices: bool (optional) - если True, удаляет все токены пользователя,
                                         если False или не указан - только текущий токен
        """
        user = request.user

        # Получаем параметр из тела запроса или query params
        all_devices = request.data.get('all_devices', False)
        if not all_devices:
            all_devices = request.query_params.get('all_devices', 'false').lower() == 'true'

        if all_devices:
            # Удаляем все токены пользователя
            deleted_count, _ = UserToken.objects.filter(user=user).delete()
            return Response(
                {
                    "detail": f"Successfully logged out from all devices. {deleted_count} token(s) deleted."
                },
                status=status.HTTP_204_NO_CONTENT
            )
        else:
            # Удаляем только текущий токен
            if hasattr(request, 'auth') and request.auth:
                request.auth.delete()
                return Response(
                    {"detail": "Successfully logged out from this device."},
                    status=status.HTTP_204_NO_CONTENT
                )
            else:
                return Response(
                    {"detail": "No active token found."},
                    status=status.HTTP_400_BAD_REQUEST
                )