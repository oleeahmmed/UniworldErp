from .common_imports import *
from company.models import Company
from uniworlderp.models import SalesEmployee
from uniworlderp.forms import SalesEmployeeForm

class SalesEmployeeListView(ListView):
    model = SalesEmployee
    template_name = 'sales_employee/list.html'
    context_object_name = 'sales_employees'
    paginate_by = 10

    def get_queryset(self):
        search_query = self.request.GET.get('search', '')
        queryset = SalesEmployee.objects.all()

        if search_query:
            queryset = queryset.filter(
                Q(user__username__icontains=search_query) |
                Q(user__email__icontains=search_query) |
                Q(phone_number__icontains=search_query)
            )

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_query'] = self.request.GET.get('search', '')
        return context

class SalesEmployeeCreateView(PermissionRequiredMixin, SuccessMessageMixin, CreateView):
    model = SalesEmployee
    form_class = SalesEmployeeForm
    template_name = 'common/form.html'
    success_url = reverse_lazy('customer_vendor:sales_employee_list')
    success_message = "Sales Employee added successfully!"
    permission_required = 'uniworlderp.add_salesemployee'

    def handle_no_permission(self):
        messages.error(self.request, "You do not have permission to add a sales employee.")
        return redirect('customer_vendor:sales_employee_list')

    def form_valid(self, form):
        form.instance.owner = self.request.user
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(self.get_common_context())
        context['can_add'] = self.request.user.has_perm('uniworlderp.add_salesemployee')
        context['can_edit'] = False
        context['can_view'] = False
        return context

    def get_common_context(self):
        sales_employees = SalesEmployee.objects.all().order_by('id')
        return {
            'model_name': self.model._meta.verbose_name.title(),
            'list_url': reverse_lazy('customer_vendor:sales_employee_list'),
            'create_url': reverse_lazy('customer_vendor:sales_employee_create'),
            'edit_url_name': 'customer_vendor:sales_employee_edit',
            'view_url_name': 'customer_vendor:sales_employee_view',
            'print_url_name': 'customer_vendor:sales_employee_print',
            'first_id': sales_employees.first().id if sales_employees.exists() else None,
            'last_id': sales_employees.last().id if sales_employees.exists() else None,
            'prev_id': None,
            'next_id': None,
            'current_id': None,
        }

class SalesEmployeeUpdateView(PermissionRequiredMixin, SuccessMessageMixin, UpdateView):
    model = SalesEmployee
    form_class = SalesEmployeeForm
    template_name = 'common/form.html'
    success_url = reverse_lazy('customer_vendor:sales_employee_list')
    success_message = "Sales Employee updated successfully!"
    permission_required = 'uniworlderp.change_salesemployee'

    def handle_no_permission(self):
        messages.error(self.request, "You do not have permission to edit this sales employee.")
        return redirect('customer_vendor:sales_employee_list')

    def form_valid(self, form):
        if not form.instance.owner:
            form.instance.owner = self.request.user
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(self.get_common_context())
        context['can_add'] = False
        context['can_edit'] = self.request.user.has_perm('uniworlderp.change_salesemployee')
        context['can_view'] = False
        return context

    def get_common_context(self):
        sales_employees = SalesEmployee.objects.all().order_by('id')
        current_employee = self.object
        return {
            'model_name': self.model._meta.verbose_name.title(),
            'list_url': reverse_lazy('customer_vendor:sales_employee_list'),
            'create_url': reverse_lazy('customer_vendor:sales_employee_create'),
            'edit_url_name': 'customer_vendor:sales_employee_edit',
            'view_url_name': 'customer_vendor:sales_employee_view',
            'print_url_name': 'customer_vendor:sales_employee_print',
            'first_id': sales_employees.first().id if sales_employees.exists() else None,
            'last_id': sales_employees.last().id if sales_employees.exists() else None,
            'prev_id': sales_employees.filter(id__lt=current_employee.id).last().id if sales_employees.filter(id__lt=current_employee.id).exists() else None,
            'next_id': sales_employees.filter(id__gt=current_employee.id).first().id if sales_employees.filter(id__gt=current_employee.id).exists() else None,
            'current_id': current_employee.id,
        }

class SalesEmployeeDetailView(PermissionRequiredMixin, DetailView):
    model = SalesEmployee
    template_name = 'common/form.html'
    permission_required = 'uniworlderp.view_salesemployee'

    def handle_no_permission(self):
        messages.error(self.request, "You do not have permission to view this sales employee.")
        return redirect('customer_vendor:sales_employee_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(self.get_common_context())
        context['can_add'] = False
        context['can_edit'] = False
        context['can_view'] = self.request.user.has_perm('uniworlderp.view_salesemployee')
        context['form'] = SalesEmployeeForm(instance=self.object)
        for field in context['form'].fields.values():
            field.widget.attrs['disabled'] = 'disabled'
        return context

    def get_common_context(self):
        sales_employees = SalesEmployee.objects.all().order_by('id')
        current_employee = self.object
        return {
            'model_name': self.model._meta.verbose_name.title(),
            'list_url': 'customer_vendor:sales_employee_list',
            'create_url': reverse_lazy('customer_vendor:sales_employee_create'),
            'edit_url_name': 'customer_vendor:sales_employee_edit',
            'view_url_name': 'customer_vendor:sales_employee_view',
            'print_url_name': 'customer_vendor:sales_employee_print',
            'first_id': sales_employees.first().id if sales_employees.exists() else None,
            'last_id': sales_employees.last().id if sales_employees.exists() else None,
            'prev_id': sales_employees.filter(id__lt=current_employee.id).last().id if sales_employees.filter(id__lt=current_employee.id).exists() else None,
            'next_id': sales_employees.filter(id__gt=current_employee.id).first().id if sales_employees.filter(id__gt=current_employee.id).exists() else None,
            'current_id': current_employee.id,
        }

class SalesEmployeeDeleteView(PermissionRequiredMixin, SuccessMessageMixin, DeleteView):
    model = SalesEmployee
    template_name = 'sales_employee/confirm_delete.html'
    success_url = reverse_lazy('customer_vendor:sales_employee_list')
    success_message = "Sales Employee deleted successfully!"
    permission_required = 'uniworlderp.delete_salesemployee'

    def handle_no_permission(self):
        messages.error(self.request, "You do not have permission to delete this sales employee.")
        return redirect(self.success_url)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['model_name'] = self.model._meta.verbose_name.title()
        context['object_name'] = str(self.object)
        context['can_delete'] = self.request.user.has_perm(self.permission_required)
        context['cancel_url'] = self.get_cancel_url()
        return context

    def get_cancel_url(self):
        return reverse_lazy('customer_vendor:sales_employee_list')

    def get_success_message(self, cleaned_data):
        return self.success_message

class SalesEmployeePrintView(LoginRequiredMixin, DetailView):
    model = SalesEmployee
    template_name = 'sales_employee/print.html'
    context_object_name = 'sales_employee'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        company = Company.objects.first()  # Assuming you have only one company
        context.update({
            'company': company,
            'model_name': self.model._meta.verbose_name.title(),
        })
        return context

