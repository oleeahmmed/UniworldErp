
# customer_views.py


from .common_imports import *

from django.db.models import Sum, F, Value, DecimalField

from company.models import Company
from django.db.models.functions import Coalesce

from uniworlderp.models import CustomerVendor, SalesOrder, ARInvoice,PurchaseOrder
from uniworlderp.forms import CustomerVendorForm
class CustomerVendorListView(ListView):
    model = CustomerVendor
    template_name = 'customer_vendor/list.html'
    context_object_name = 'customers'
    paginate_by = 10

    def get_queryset(self):
        search_query = self.request.GET.get('search', '')
        entity_type = self.request.GET.get('entity_type', '')
        business_type = self.request.GET.get('business_type', '')
        queryset = CustomerVendor.objects.all()

        # Search filtering
        if search_query:
            queryset = queryset.filter(
                Q(name__icontains=search_query) |
                Q(email__icontains=search_query) |
                Q(phone_number__icontains=search_query) |
                Q(address__icontains=search_query)
            )

        # Entity type filtering
        if entity_type:
            queryset = queryset.filter(entity_type=entity_type)
            
        # Business type filtering
        if business_type:
            queryset = queryset.filter(business_type=business_type)

        # Annotate with total sales and total invoices
        queryset = queryset.annotate(
            total_sales=Coalesce(Sum('sales_orders__total_amount', output_field=DecimalField(max_digits=10, decimal_places=2)), Value(0, output_field=DecimalField(max_digits=10, decimal_places=2))),
            total_invoices=Coalesce(Sum('ar_invoices__total_amount', output_field=DecimalField(max_digits=10, decimal_places=2)), Value(0, output_field=DecimalField(max_digits=10, decimal_places=2)))
        )

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_query'] = self.request.GET.get('search', '')
        context['entity_type'] = self.request.GET.get('entity_type', '')
        context['business_type'] = self.request.GET.get('business_type', '')
        context['business_type_choices'] = CustomerVendor.BUSINESS_TYPE_CHOICES
        return context
class CustomerVendorCreateView(PermissionRequiredMixin, SuccessMessageMixin, CreateView):
    model = CustomerVendor
    form_class = CustomerVendorForm
    template_name = 'common/form.html'
    success_url = reverse_lazy('customer_vendor:customer_list')
    success_message = "%(entity_type)s added successfully!"
    permission_required = 'uniworlderp.add_customervendor'

    def handle_no_permission(self):
        messages.error(self.request, "You do not have permission to add a customer/vendor.")
        return redirect('customer_vendor:customer_list')

    def form_valid(self, form):
        form.instance.owner = self.request.user
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(self.get_common_context())
        context['can_add'] = self.request.user.has_perm('uniworlderp.add_customervendor')
        context['can_edit'] = False
        context['can_view'] = False
        return context

    def get_common_context(self):
        customer_vendors = CustomerVendor.objects.all().order_by('id')
        return {
            'model_name': self.model._meta.verbose_name.title(),
            'list_url': reverse_lazy('customer_vendor:customer_list'),
            'create_url': reverse_lazy('customer_vendor:customer_create'),
            'edit_url_name': 'customer_vendor:customer_edit',
            'view_url_name': 'customer_vendor:customer_view',
            'print_url_name': 'customer_vendor:customer_print',
            'first_id': customer_vendors.first().id if customer_vendors.exists() else None,
            'last_id': customer_vendors.last().id if customer_vendors.exists() else None,
            'prev_id': None,
            'next_id': None,
            'current_id': None,
        }

class CustomerVendorUpdateView(PermissionRequiredMixin, SuccessMessageMixin, UpdateView):
    model = CustomerVendor
    form_class = CustomerVendorForm
    template_name = 'common/form.html'
    success_url = reverse_lazy('customer_vendor:customer_list')
    success_message = "%(entity_type)s updated successfully!"
    permission_required = 'uniworlderp.change_customervendor'

    def handle_no_permission(self):
        messages.error(self.request, "You do not have permission to edit this customer/vendor.")
        return redirect('customer_vendor:customer_list')

    def form_valid(self, form):
        if not form.instance.owner:
            form.instance.owner = self.request.user
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(self.get_common_context())
        context['can_add'] = False
        context['can_edit'] = self.request.user.has_perm('uniworlderp.change_customervendor')
        context['can_view'] = False
        return context

    def get_common_context(self):
        customer_vendors = CustomerVendor.objects.all().order_by('id')
        current_vendor = self.object
        return {
            'model_name': self.model._meta.verbose_name.title(),
            'list_url': reverse_lazy('customer_vendor:customer_list'),
            'create_url': reverse_lazy('customer_vendor:customer_create'),
            'edit_url_name': 'customer_vendor:customer_edit',
            'view_url_name': 'customer_vendor:customer_view',
            'print_url_name': 'customer_vendor:customer_print',
            'first_id': customer_vendors.first().id if customer_vendors.exists() else None,
            'last_id': customer_vendors.last().id if customer_vendors.exists() else None,
            'prev_id': customer_vendors.filter(id__lt=current_vendor.id).last().id if customer_vendors.filter(id__lt=current_vendor.id).exists() else None,
            'next_id': customer_vendors.filter(id__gt=current_vendor.id).first().id if customer_vendors.filter(id__gt=current_vendor.id).exists() else None,
            'current_id': current_vendor.id,
        }

class CustomerVendorDetailView(PermissionRequiredMixin, DetailView):
    model = CustomerVendor
    template_name = 'common/form.html'
    permission_required = 'uniworlderp.view_customervendor'

    def handle_no_permission(self):
        messages.error(self.request, "You do not have permission to view this customer/vendor.")
        return redirect('customer_vendor:customer_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(self.get_common_context())
        context['can_add'] = False
        context['can_edit'] = False
        context['can_view'] = self.request.user.has_perm('uniworlderp.view_customervendor')
        context['form'] = CustomerVendorForm(instance=self.object)
        for field in context['form'].fields.values():
            field.widget.attrs['disabled'] = 'disabled'
        return context

    def get_common_context(self):
        customer_vendors = CustomerVendor.objects.all().order_by('id')
        current_vendor = self.object
        return {
            'model_name': self.model._meta.verbose_name.title(),
            'list_url': 'customer_vendor:customer_list',
            'create_url': reverse_lazy('customer_vendor:customer_create'),
            'edit_url_name': 'customer_vendor:customer_edit',
            'view_url_name': 'customer_vendor:customer_view',
            'print_url_name': 'customer_vendor:customer_print',
            'first_id': customer_vendors.first().id if customer_vendors.exists() else None,
            'last_id': customer_vendors.last().id if customer_vendors.exists() else None,
            'prev_id': customer_vendors.filter(id__lt=current_vendor.id).last().id if customer_vendors.filter(id__lt=current_vendor.id).exists() else None,
            'next_id': customer_vendors.filter(id__gt=current_vendor.id).first().id if customer_vendors.filter(id__gt=current_vendor.id).exists() else None,
            'current_id': current_vendor.id,
        }

class CustomerVendorDeleteView(PermissionRequiredMixin, SuccessMessageMixin, DeleteView):
    model = CustomerVendor
    template_name = 'customer_vendor/confirm_delete.html'
    success_url = reverse_lazy('customer_vendor:customer_list')
    success_message = "%(entity_type)s deleted successfully!"
    permission_required = 'uniworlderp.delete_customervendor'

    def handle_no_permission(self):
        messages.error(self.request, "You do not have permission to delete this customer/vendor.")
        return redirect(self.success_url)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['model_name'] = self.model._meta.verbose_name.title()
        context['object_name'] = str(self.object)
        context['can_delete'] = self.request.user.has_perm(self.permission_required)
        context['cancel_url'] = self.get_cancel_url()
        return context

    def get_cancel_url(self):
        return reverse_lazy('customer_vendor:customer_list')

    def get_success_message(self, cleaned_data):
        return self.success_message % {
            'entity_type': self.model._meta.verbose_name.title()
        }

class CustomerVendorPrintView(LoginRequiredMixin, DetailView):
    model = CustomerVendor
    template_name = 'customer_vendor/print.html'
    context_object_name = 'customer_vendor'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        company = Company.objects.first()  # Assuming you have only one company
        context.update({
            'company': company,
        })
        return context


class SalesOrderListView(ListView):
    model = SalesOrder
    template_name = 'customer_vendor/sales_order_list.html'
    context_object_name = 'sales_orders'
    paginate_by = 10

    def get_queryset(self):
        customer = get_object_or_404(CustomerVendor, pk=self.kwargs['pk'])
        return SalesOrder.objects.filter(customer=customer)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['customer'] = get_object_or_404(CustomerVendor, pk=self.kwargs['pk'])
        return context

class PurchaseOrderListView(ListView):
    model = PurchaseOrder
    template_name = 'customer_vendor/purchase_order_list.html'
    context_object_name = 'purchase_orders'
    paginate_by = 10

    def get_queryset(self):
        vendor = get_object_or_404(CustomerVendor, pk=self.kwargs['pk'])
        return PurchaseOrder.objects.filter(supplier=vendor)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['vendor'] = get_object_or_404(CustomerVendor, pk=self.kwargs['pk'])
        return context

class InvoiceListView(ListView):
    model = ARInvoice
    template_name = 'customer_vendor/invoice_list.html'
    context_object_name = 'invoices'
    paginate_by = 10

    def get_queryset(self):
        customer = get_object_or_404(CustomerVendor, pk=self.kwargs['pk'])
        return ARInvoice.objects.filter(customer=customer)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['customer'] = get_object_or_404(CustomerVendor, pk=self.kwargs['pk'])
        return context

