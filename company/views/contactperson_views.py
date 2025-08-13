# Importing shared components from common_imports.py
from .common_imports import *

# Importing specific models and forms for ContactPerson
from company.models import ContactPerson
from company.forms import ContactPersonForm

class ContactPersonListView(ListView):
    model = ContactPerson
    template_name = 'contactperson/contactperson_list.html'
    context_object_name = 'contactpersons'
    paginate_by = 10  

class ContactPersonCreateView(PermissionRequiredMixin, SuccessMessageMixin, CreateView):
    model = ContactPerson
    form_class = ContactPersonForm
    template_name = 'form.html'
    success_url = reverse_lazy('company:contactperson_list')
    success_message = "Contact Person added successfully!"
    permission_required = 'company.add_contactperson'
    
    def handle_no_permission(self):
        messages.error(self.request, "You do not have permission to add a contact person.")
        return redirect('company:contactperson_list')

    def get_context_data(self, **kwargs):
        # Add the model name dynamically to the context
        context = super().get_context_data(**kwargs)
        context['model_name'] = self.model._meta.verbose_name.title() 
        context['can_edit'] = self.request.user.has_perm('company.add_contactperson')
        return context        

class ContactPersonUpdateView(PermissionRequiredMixin, SuccessMessageMixin, UpdateView):
    model = ContactPerson
    form_class = ContactPersonForm
    template_name = 'form.html'
    success_url = reverse_lazy('company:contactperson_list')
    success_message = "Contact Person updated successfully!"
    permission_required = 'company.change_contactperson'

    def handle_no_permission(self):
        messages.error(self.request, "You do not have permission to edit this contact person.")
        return redirect('company:contactperson_list')
        
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Check if the user has the permission to change the contact person
        context['can_edit'] = self.request.user.has_perm('company.change_contactperson')
        return context

class ContactPersonDeleteView(PermissionRequiredMixin, SuccessMessageMixin, DeleteView):
    model = ContactPerson
    template_name = 'confirm_delete.html'  
    success_url = reverse_lazy('company:contactperson_list')
    success_message = "Contact Person deleted successfully!"
    permission_required = 'company.delete_contactperson'

    def handle_no_permission(self):
        """
        Redirect with an error message if the user lacks permission.
        """
        messages.error(self.request, "You do not have permission to delete this contact person.")
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
        return reverse_lazy('company:contactperson_list')
