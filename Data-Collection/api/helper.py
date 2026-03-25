from rest_framework.response import Response

def success_response(data, status=200):
    return Response({
        "success": True,
        "data": data
    }, status=status)


def failure_response(message, status=400):
    return Response({
        "success": False,
        "error": message
    }, status=status)