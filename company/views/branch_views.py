# branch_views.py

# Importing shared components from common_imports.py
from .common_imports import *

# Importing specific models and forms for Branch
from company.models import Branch
from company.forms import BranchForm

# Branch Views

class BranchListView(ListView):
    model = Branch
    template_name = 'branch/branch_list.html'  
    context_object_name = 'branches'
    paginate_by = 10


class BranchCreateView(PermissionRequiredMixin, SuccessMessageMixin, CreateView):
    model = Branch
    form_class = BranchForm
    template_name = 'form.html'
    success_url = reverse_lazy('company:branch_list')
    success_message = "Branch added successfully!"
    permission_required = 'company.add_branch'  

    def handle_no_permission(self):
        messages.error(self.request, "You do not have permission to perform this action.")
        return redirect(self.success_url)

    def get_context_data(self, **kwargs):
        # Add the model name dynamically to the context
        context = super().get_context_data(**kwargs)
        context['model_name'] = self.model._meta.verbose_name.title() 
        context['can_edit'] = self.request.user.has_perm('company.change_branch')

        return context

class BranchUpdateView(PermissionRequiredMixin, SuccessMessageMixin, UpdateView):
    model = Branch
    form_class = BranchForm
    template_name = 'form.html'
    success_url = reverse_lazy('company:branch_list')
    success_message = "Branch updated successfully!"
    permission_required = 'company.change_branch'  # Adjust this based on your permission logic

    def handle_no_permission(self):
        messages.error(self.request, "You do not have permission to perform this action.")
        return redirect(self.success_url)

class BranchDeleteView(DeleteView):
    model = Branch
    template_name = 'confirm_delete.html'
    success_url = reverse_lazy('company:branch_list')
    success_message = "Branch deleted successfully!"

    def get_context_data(self, **kwargs):
        """
        Provide dynamic context for the confirmation page.
        """
        context = super().get_context_data(**kwargs)
        context['model_name'] = self.model._meta.verbose_name.title()
        context['object_name'] = str(self.object)
        context['cancel_url'] = self.get_cancel_url()
        return context

    def get_cancel_url(self):
        """
        Generate the cancel URL dynamically.
        """
        return reverse_lazy('company:branch_list')
        

class BranchDetailView(DetailView):
    model = Branch
    template_name = 'branch/branch_detail.html'
    context_object_name = 'branch'
