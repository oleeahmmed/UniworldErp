from rest_framework.response import Response
from rest_framework import status

def success_response(message, data=None, status_code=status.HTTP_200_OK):
    """
    Return a consistent success response structure.
    """
    return Response({
        "status": "success",
        "message": message,
        "data": data if data is not None else []
    }, status=status_code)

def error_response(message, details=None, error_type="Error", status_code=status.HTTP_400_BAD_REQUEST):
    """
    Return a consistent error response structure with error type.
    """
    return Response({
        "status": "error",
        "error_type": error_type,  # Specify the type of error (e.g., ValidationError, ServerError, etc.)
        "message": message,
        "details": details if details is not None else []
    }, status=status_code)

# Advanced utility to handle validation errors in detail
def validation_error_response(serializer_errors):
    """
    Return a detailed validation error response.
    """
    errors = []
    for field, messages in serializer_errors.items():
        for message in messages:
            errors.append({"field": field, "error": message})
    
    return error_response("Validation failed", details=errors, error_type="ValidationError", status_code=status.HTTP_400_BAD_REQUEST)