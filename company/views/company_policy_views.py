
# Importing shared components from common_imports.py
from .common_imports import *

# Importing specific models and forms for CompanyPolicy
from company.models import CompanyPolicy
from company.forms import CompanyPolicyForm

# ListView for displaying all Company Policies

class CompanyPolicyListView(ListView):
    model = CompanyPolicy
    template_name = 'companypolicy/companypolicy_list.html'
    context_object_name = 'company_policies'
    paginate_by = 10

    def get_queryset(self):
        # Get the search query parameter from the GET request
        search_query = self.request.GET.get('search', '')

        # Filter the policies based on the search query (if present)
        if search_query:
            return CompanyPolicy.objects.filter(
                Q(title__icontains=search_query) | 
                Q(description__icontains=search_query) |
                Q(company__name__icontains=search_query)  
            )
        return CompanyPolicy.objects.all()


# CreateView for adding a new Company Policy
class CompanyPolicyCreateView(PermissionRequiredMixin, SuccessMessageMixin, CreateView):
    model = CompanyPolicy
    form_class = CompanyPolicyForm
    template_name = 'form.html'
    success_url = reverse_lazy('company:companypolicy_list')
    success_message = "Company Policy added successfully!"
    permission_required = 'company.add_companypolicy'
    
    def handle_no_permission(self):
        messages.error(self.request, "You do not have permission to add a company policy.")
        return redirect('company:companypolicy_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['model_name'] = self.model._meta.verbose_name.title() 
        context['can_edit'] = self.request.user.has_perm('company.add_companypolicy')
        return context

# UpdateView for editing an existing Company Policy
class CompanyPolicyUpdateView(PermissionRequiredMixin, SuccessMessageMixin, UpdateView):
    model = CompanyPolicy
    form_class = CompanyPolicyForm
    template_name = 'form.html'
    success_url = reverse_lazy('company:companypolicy_list')
    success_message = "Company Policy updated successfully!"
    permission_required = 'company.change_companypolicy'

    def handle_no_permission(self):
        messages.error(self.request, "You do not have permission to edit this company policy.")
        return redirect('company:companypolicy_list')
        
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['can_edit'] = self.request.user.has_perm('company.change_companypolicy')
        return context

# DeleteView for deleting a Company Policy
class CompanyPolicyDeleteView(PermissionRequiredMixin, SuccessMessageMixin, DeleteView):
    model = CompanyPolicy
    template_name = 'confirm_delete.html'  
    success_url = reverse_lazy('company:companypolicy_list')
    success_message = "Company Policy deleted successfully!"
    permission_required = 'company.delete_companypolicy'

    def handle_no_permission(self):
        """
        Redirect with an error message if the user lacks permission.
        """
        messages.error(self.request, "You do not have permission to delete this company policy.")
        return redirect(self.success_url)

    def get_context_data(self, **kwargs):
        """
        Provide dynamic context for the confirmation page.
        """
        context = super().get_context_data(**kwargs)
        context['model_name'] = self.model._meta.verbose_name.title()
        context['object_name'] = str(self.object)
        context['can_delete'] = self.request.user.has_perm(self.permission_required)
        context['cancel_url'] = self.get_cancel_url()
        return context

    def get_cancel_url(self):
        """
        Generate the cancel URL dynamically.
        """
        return reverse_lazy('company:companypolicy_list')
