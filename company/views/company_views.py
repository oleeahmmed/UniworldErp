
# company_views.py

# Importing shared components from common_imports.py
from .common_imports import *

# Importing specific models and forms for Company
from company.models import Company
from company.forms import CompanyForm

class CompanyListView(ListView):
    model = Company
    template_name = 'company/company_list.html'
    context_object_name = 'companies'
    paginate_by = 3  # Show 10 companies per page

    def get_queryset(self):
        # Get the search query parameter from the GET request
        search_query = self.request.GET.get('search', '')

        # Filter the companies based on the search query (if present)
        if search_query:
            return Company.objects.filter(
                Q(name__icontains=search_query) |
                Q(address__icontains=search_query) |
                Q(phone__icontains=search_query)
            )
        return Company.objects.all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_query'] = self.request.GET.get('search', '')
        return context


class CompanyCreateView(PermissionRequiredMixin, SuccessMessageMixin, CreateView):
    model = Company
    form_class = CompanyForm
    template_name = 'common/form.html'
    success_url = reverse_lazy('company:company_list')
    success_message = "Company added successfully!"
    permission_required = 'company.add_company'

    def handle_no_permission(self):
        messages.error(self.request, "You do not have permission to add a company.")
        return redirect('company:company_list')

    def form_valid(self, form):
        # form.instance.owner = self.request.user
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(self.get_common_context())
        context['can_add'] = self.request.user.has_perm('company.add_company')
        context['can_edit'] = False
        context['can_view'] = False
        context['action'] = 'Add'
        return context

    def get_common_context(self):
        companies = Company.objects.all().order_by('id')
        return {
            'model_name': self.model._meta.verbose_name.title(),
            'list_url': reverse_lazy('company:company_list'),
            'create_url': reverse_lazy('company:company_create'),
            'edit_url_name': 'company:company_edit',
            'view_url_name': 'company:company_detail',
            'delete_url_name': 'company:company_delete',
            'first_id': companies.first().id if companies.exists() else None,
            'last_id': companies.last().id if companies.exists() else None,
            'prev_id': None,
            'next_id': None,
            'current_id': None,
        }

class CompanyUpdateView(PermissionRequiredMixin, SuccessMessageMixin, UpdateView):
    model = Company
    form_class = CompanyForm
    template_name = 'common/form.html'
    success_url = reverse_lazy('company:company_list')
    success_message = "Company updated successfully!"
    permission_required = 'company.change_company'

    def handle_no_permission(self):
        messages.error(self.request, "You do not have permission to edit this company.")
        return redirect('company:company_list')

    def form_valid(self, form):
        # if not form.instance.owner:
        #     form.instance.owner = self.request.user
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(self.get_common_context())
        context['can_add'] = False
        context['can_edit'] = self.request.user.has_perm('company.change_company')
        context['can_view'] = True
        context['action'] = 'Edit'
        return context

    def get_common_context(self):
        companies = Company.objects.all().order_by('id')
        current_company = self.object
        return {
            'model_name': self.model._meta.verbose_name.title(),
            'list_url': reverse_lazy('company:company_list'),
            'create_url': reverse_lazy('company:company_create'),
            'edit_url_name': 'company:company_edit',
            'view_url_name': 'company:company_detail',
            'delete_url_name': 'company:company_delete',
            'first_id': companies.first().id if companies.exists() else None,
            'last_id': companies.last().id if companies.exists() else None,
            'prev_id': companies.filter(id__lt=current_company.id).last().id if companies.filter(id__lt=current_company.id).exists() else None,
            'next_id': companies.filter(id__gt=current_company.id).first().id if companies.filter(id__gt=current_company.id).exists() else None,
            'current_id': current_company.id,
        }
class CompanyDeleteView(PermissionRequiredMixin, SuccessMessageMixin, DeleteView):
    model = Company
    template_name = 'confirm_delete.html'
    success_url = reverse_lazy('company:company_list')
    success_message = "Company deleted successfully!"
    permission_required = 'company.delete_company'

    def handle_no_permission(self):
        """
        Redirect with an error message if the user lacks permission.
        """
        messages.error(self.request, "You do not have permission to delete this company.")
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
        return reverse_lazy('company:company_list')
class CompanyDetailView(DetailView):
    model = Company
    template_name = 'company/company_detail.html' 
    context_object_name = 'company'  