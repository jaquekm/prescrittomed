from django.db import connections
from django.http import JsonResponse


def health(request):
    return JsonResponse({"status": "ok"})


def ready(request):
    try:
        with connections["default"].cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
        return JsonResponse({"status": "ready"})
    except Exception:
        return JsonResponse({"status": "unready"}, status=503)
