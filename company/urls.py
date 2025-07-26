from django.urls import path
from company.views.company_views import (
    CompanyListView, 
    CompanyCreateView, 
    CompanyUpdateView, 
    CompanyDeleteView, 
    CompanyDetailView
)

from company.views.branch_views import (
    BranchListView, 
    BranchCreateView, 
    BranchUpdateView, 
    BranchDeleteView, 
    BranchDetailView

)

from company.views.contactperson_views import (
    ContactPersonListView, 
    ContactPersonCreateView, 
    ContactPersonUpdateView, 
    ContactPersonDeleteView
)



from company.views.company_policy_views  import CompanyPolicyListView, CompanyPolicyCreateView, CompanyPolicyUpdateView, CompanyPolicyDeleteView

app_name = 'company'

urlpatterns = [
    path('', CompanyListView.as_view(), name='company_list'),
    path('add/', CompanyCreateView.as_view(), name='company_create'),
    path('<int:pk>/edit/', CompanyUpdateView.as_view(), name='company_edit'),
    path('<int:pk>/delete/', CompanyDeleteView.as_view(), name='company_delete'),
    path('<int:pk>/', CompanyDetailView.as_view(), name='company_detail'), 

    # Branch URLs
    path('branches/', BranchListView.as_view(), name='branch_list'),  # List all branches
    path('branches/add/', BranchCreateView.as_view(), name='branch_create'),  # Add a new branch
    path('branches/<int:pk>/edit/', BranchUpdateView.as_view(), name='branch_edit'),  # Edit a branch
    path('branches/<int:pk>/delete/', BranchDeleteView.as_view(), name='branch_delete'),  # Delete a branch
    path('branches/<int:pk>/', BranchDetailView.as_view(), name='branch_detail'),  # View details of a branch

    path('contactpersons/', ContactPersonListView.as_view(), name='contactperson_list'),
    path('contactpersons/add/', ContactPersonCreateView.as_view(), name='contact_create'),
    path('contactpersons/<int:pk>/edit/', ContactPersonUpdateView.as_view(), name='contact_edit'),
    path('contactpersons/<int:pk>/delete/', ContactPersonDeleteView.as_view(), name='contact_delete'),    

    path('company-policies/', CompanyPolicyListView.as_view(), name='companypolicy_list'),
    path('company-policy/create/', CompanyPolicyCreateView.as_view(), name='companypolicy_create'),
    path('company-policy/<int:pk>/update/', CompanyPolicyUpdateView.as_view(), name='companypolicy_edit'),
    path('company-policy/<int:pk>/delete/', CompanyPolicyDeleteView.as_view(), name='companypolicy_delete'),
]
