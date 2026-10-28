from rest_framework.views import exception_handler as drf_exception_handler


def custom_exception_handler(exc, context):
    response = drf_exception_handler(exc, context)
    if response is not None:
        detail = response.data.get("detail", str(response.data))
        response.data = {"ok": False, "error": str(detail)}
    return response
