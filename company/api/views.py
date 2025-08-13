from .imports import *

# Company ViewSet
from ..models import Company
from .serializers import CompanySerializer
class CompanyViewSet(viewsets.ModelViewSet):
    queryset = Company.objects.all()
    serializer_class = CompanySerializer
    authentication_classes = [JWTAuthentication]  
    permission_classes = [AllowAny]  

    # Swagger documentation for listing companies
    @swagger_auto_schema(
        operation_summary="Retrieve a list of all companies",
        operation_description="This endpoint returns a list of all companies present in the system.",
        tags=['Company Information'],
        responses={200: CompanySerializer(many=True)}
    )
    def list(self, request, *args, **kwargs):
        """
        Retrieve all companies.
        """
        return super().list(request, *args, **kwargs)

    # Swagger documentation for creating a new company
    @swagger_auto_schema(
        operation_summary="Create a new company",
        operation_description="This endpoint allows you to create a new company by providing details such as name, address, etc.",
        tags=['Company Information'],
        request_body=CompanySerializer,
        responses={201: CompanySerializer}
    )
    def create(self, request, *args, **kwargs):
        """
        Create a new company in the system.
        """
        return super().create(request, *args, **kwargs)

    # Swagger documentation for updating an existing company
    @swagger_auto_schema(
        operation_summary="Update an existing company",
        operation_description="This endpoint allows you to update an existing company's details, such as name or address.",
        tags=['Company Information'],
        request_body=CompanySerializer,
        responses={200: CompanySerializer}
    )
    def update(self, request, *args, **kwargs):
        """
        Update an existing company.
        """
        return super().update(request, *args, **kwargs)

    # Swagger documentation for partially updating an existing company
    @swagger_auto_schema(
        operation_summary="Partially update an existing company",
        operation_description="This endpoint allows you to update only specific fields of an existing company's information, such as modifying just the address or contact number.",
        tags=['Company Information'],
        request_body=CompanySerializer,
        responses={200: CompanySerializer}
    )
    def partial_update(self, request, *args, **kwargs):
        """
        Partially update an existing company's information.
        """
        return super().partial_update(request, *args, **kwargs)

    # Swagger documentation for deleting a company
    @swagger_auto_schema(
        operation_summary="Delete a company",
        operation_description="This endpoint allows you to delete a company from the system by providing its ID.",
        tags=['Company Information'],
        responses={204: 'No Content'}
    )
    def destroy(self, request, *args, **kwargs):
        """
        Delete a company.
        """
        return super().destroy(request, *args, **kwargs)

# Branch ViewSet
from ..models import  Branch
from .serializers import BranchSerializer
class BranchViewSet(viewsets.ModelViewSet):
    queryset = Branch.objects.all()
    serializer_class = BranchSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [AllowAny]

    # Swagger documentation for listing branches
    @swagger_auto_schema(
        operation_summary="Retrieve a list of all branches",
        operation_description="This endpoint returns a list of all branches for the given company.",
        tags=['Company Branch Management'],
        responses={200: BranchSerializer(many=True)}
    )
    def list(self, request, *args, **kwargs):
        """
        Retrieve all branches.
        """
        return super().list(request, *args, **kwargs)

    # Swagger documentation for creating a new branch
    @swagger_auto_schema(
        operation_summary="Create a new branch",
        operation_description="This endpoint allows you to create a new branch by providing the necessary details such as branch name, address, etc.",
        tags=['Company Branch Management'],
        request_body=BranchSerializer,
        responses={201: BranchSerializer}
    )
    def create(self, request, *args, **kwargs):
        """
        Create a new branch in the system.
        """
        return super().create(request, *args, **kwargs)

    # Swagger documentation for updating an existing branch
    @swagger_auto_schema(
        operation_summary="Update an existing branch",
        operation_description="This endpoint allows you to update an existing branch's details such as name, location, etc.",
        tags=['Company Branch Management'],
        request_body=BranchSerializer,
        responses={200: BranchSerializer}
    )
    def update(self, request, *args, **kwargs):
        """
        Update an existing branch.
        """
        return super().update(request, *args, **kwargs)

    # Swagger documentation for partially updating an existing branch
    @swagger_auto_schema(
        operation_summary="Partially update an existing branch",
        operation_description="This endpoint allows you to update specific fields of an existing branch, such as address or contact number.",
        tags=['Company Branch Management'],
        request_body=BranchSerializer,
        responses={200: BranchSerializer}
    )
    def partial_update(self, request, *args, **kwargs):
        """
        Partially update an existing branch's details.
        """
        return super().partial_update(request, *args, **kwargs)

    # Swagger documentation for deleting a branch
    @swagger_auto_schema(
        operation_summary="Delete a branch",
        operation_description="This endpoint allows you to delete a branch from the system by providing its ID.",
        tags=['Company Branch Management'],
        responses={204: 'No Content'}
    )
    def destroy(self, request, *args, **kwargs):
        """
        Delete a branch.
        """
        return super().destroy(request, *args, **kwargs)


# ContactPerson ViewSet
from ..models import   ContactPerson
from .serializers import ContactPersonSerializer
class ContactPersonViewSet(viewsets.ModelViewSet):
    queryset = ContactPerson.objects.all()
    serializer_class = ContactPersonSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [AllowAny]


# CompanyPolicy ViewSet
from ..models import   CompanyPolicy
from .serializers import CompanyPolicySerializer
class CompanyPolicyViewSet(viewsets.ModelViewSet):
    queryset = CompanyPolicy.objects.all()
    serializer_class = CompanyPolicySerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [AllowAny]


from django.contrib.auth.models import User
from .serializers import UserProfileSerializer

class UserProfileView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Get the profile of the authenticated user",
        responses={200: UserProfileSerializer},
        tags=["User Profile Management"]  # Add tag here
    )
    def get(self, request, *args, **kwargs):
        # Get the profile of the currently authenticated user
        user = request.user
        serializer = UserProfileSerializer(user)
        return Response(serializer.data)

    @swagger_auto_schema(
        operation_description="Update the profile of the authenticated user",
        request_body=UserProfileSerializer,
        responses={200: UserProfileSerializer, 400: 'Bad Request'},
        tags=["User Profile Management"]  # Add tag here
    )
    def put(self, request, *args, **kwargs):
        # Update the profile of the currently authenticated user
        user = request.user
        serializer = UserProfileSerializer(user, data=request.data, partial=True)
        
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)