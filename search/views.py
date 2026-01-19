from rest_framework.views import APIView
from rest_framework.response import Response

from .config import SEARCH_CONFIG
from .utils import perform_search


class GlobalSearchAPIView(APIView):
    def get(self, request):
        q = request.GET.get("q", "").strip()

        if len(q) < 2:
            return Response({"error": "Query too short"}, status=400)

        results = {}

        for cfg in SEARCH_CONFIG:
            results[cfg["key"]] = perform_search(
                model=cfg["model"],
                fields=cfg["fields"],
                values=cfg["values"],
                query=q,
                request=request,   # ← ВАЖНО
            )

        return Response(results)
