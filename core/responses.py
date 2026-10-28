from rest_framework.response import Response


def ok(data=None, status=200):
    return Response({"ok": True, "data": data}, status=status)


def error(message, status=400):
    return Response({"ok": False, "error": message}, status=status)


def created(data=None):
    return ok(data, status=201)
