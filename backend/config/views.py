from django.db import Error, connection
from django.http import JsonResponse


def bad_request(request, exception):
    return JsonResponse({"detail": "Bad request.", "code": "bad_request"}, status=400)


def not_found(request, exception):
    return JsonResponse({"detail": "Not found.", "code": "not_found"}, status=404)


def server_error(request):
    body = {"detail": "Server error.", "code": "server_error", "request_id": request.request_id}
    return JsonResponse(body, status=500)


def healthz(request):
    """Liveness only. Stays off the database, so frequent probes don't keep Neon awake."""
    return JsonResponse({"status": "ok"})


def readyz(request):
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
    except Error:
        return JsonResponse({"status": "unavailable"}, status=503)
    return JsonResponse({"status": "ok"})
