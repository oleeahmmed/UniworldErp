from django.urls import reverse
from .common_imports import *
from uniworlderp.models import PurchaseOrder, PurchaseOrderItem, Product, StockTransaction
from uniworlderp.forms import PurchaseOrderForm, PurchaseOrderItemFormSet
from company.models import Company, Branch, ContactPerson

class PurchaseOrderListView(ListView):
    model = PurchaseOrder
    template_name = 'purchase_order/list.html'
    context_object_name = 'purchase_orders'
    paginate_by = 10

    def get_queryset(self):
        search_query = self.request.GET.get('search', '')
        queryset = PurchaseOrder.objects.all().order_by('-order_date')

        if search_query:
            queryset = queryset.filter(
                Q(id__icontains=search_query) |
                Q(vendor__name__icontains=search_query) |
                Q(order_date__icontains=search_query)
            )

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_query'] = self.request.GET.get('search', '')
        return context

class PurchaseOrderItemDetailedListView(ListView):
    model = PurchaseOrderItem
    template_name = 'purchase_order/detailed_list.html'
    context_object_name = 'order_items'
    paginate_by = 20

    def get_queryset(self):
        queryset = PurchaseOrderItem.objects.select_related(
            'purchase_order__supplier',
            'product'
        ).annotate(
            total_amount=F('quantity') * F('unit_price')
        ).order_by('-purchase_order__order_date', 'purchase_order__id')

        search_query = self.request.GET.get('search', '')
        if search_query:
            queryset = queryset.filter(
                Q(purchase_order__id__icontains=search_query) |
                Q(purchase_order__vendor__name__icontains=search_query) |
                Q(product__name__icontains=search_query)
            ).distinct()

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_query'] = self.request.GET.get('search', '')
        return context

class PurchaseOrderCreateView(PermissionRequiredMixin, SuccessMessageMixin, CreateView):
    model = PurchaseOrder
    form_class = PurchaseOrderForm
    template_name = 'purchase_order/form.html'
    success_url = reverse_lazy('customer_vendor:purchase_order_list')
    permission_required = 'uniworlderp.add_purchaseorder'
    success_message = "Purchase Order added successfully!"

    def handle_no_permission(self):
        messages.error(self.request, "You do not have permission to add a purchase order.")
        return redirect('customer_vendor:purchase_order_list')

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        if self.request.POST:
            data['formset'] = PurchaseOrderItemFormSet(self.request.POST)
        else:
            data['formset'] = PurchaseOrderItemFormSet()
        data.update(self.get_common_context())
        data['action'] = 'Add'
        data['products'] = Product.objects.all()
        return data

    @transaction.atomic
    def form_valid(self, form):
        context = self.get_context_data()
        formset = context['formset']
        if form.is_valid() and formset.is_valid():
            self.object = form.save(commit=False)
            self.object.owner = self.request.user
            self.object.save()
            formset.instance = self.object
            formset.save()
            self.object.update_total_amount()
            return super().form_valid(form)
        else:
            return self.form_invalid(form)

    def form_invalid(self, form):
        context = self.get_context_data()
        formset = context['formset']
        if not form.is_valid():
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(self.request, f"{field}: {error}")
        if not formset.is_valid():
            for i, form_errors in enumerate(formset.errors):
                if form_errors:
                    for field, errors in form_errors.items():
                        for error in errors:
                            messages.error(self.request, f"Item {i+1} - {field}: {error}")
        return self.render_to_response(self.get_context_data(form=form))

    def get_common_context(self):
        purchase_orders = PurchaseOrder.objects.all().order_by('id')
        return {
            'model_name': self.model._meta.verbose_name.title(),
            'can_add': self.request.user.has_perm('uniworlderp.add_purchaseorder'),
            'can_edit': self.request.user.has_perm('uniworlderp.change_purchaseorder'),
            'can_view': self.request.user.has_perm('uniworlderp.view_purchaseorder'),
            'list_url': reverse_lazy('customer_vendor:purchase_order_list'),
            'create_url': reverse_lazy('customer_vendor:purchase_order_create'),
            'edit_url_name': 'customer_vendor:purchase_order_update',
            'view_url_name': 'customer_vendor:purchase_order_detail',
            'print_url_name': 'customer_vendor:purchase_order_print',
            'search_url': reverse_lazy('customer_vendor:purchase_order_search'),
            'first_id': purchase_orders.first().id if purchase_orders.exists() else None,
            'last_id': purchase_orders.last().id if purchase_orders.exists() else None,
            'prev_id': None,
            'next_id': None,
            'current_id': None,
        }

class PurchaseOrderUpdateView(PermissionRequiredMixin, SuccessMessageMixin, UpdateView):
    model = PurchaseOrder
    form_class = PurchaseOrderForm
    template_name = 'purchase_order/form.html'
    success_url = reverse_lazy('customer_vendor:purchase_order_list')
    permission_required = 'uniworlderp.change_purchaseorder'
    success_message = "Purchase Order updated successfully!"

    def handle_no_permission(self):
        messages.error(self.request, "You do not have permission to edit this purchase order.")
        return redirect('customer_vendor:purchase_order_list')

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        if self.request.POST:
            data['formset'] = PurchaseOrderItemFormSet(self.request.POST, instance=self.object)
        else:
            data['formset'] = PurchaseOrderItemFormSet(instance=self.object)
        data.update(self.get_common_context())
        data['action'] = 'Edit'
        data['products'] = Product.objects.all()
        return data

    @transaction.atomic
    def form_valid(self, form):
        context = self.get_context_data()
        formset = context['formset']
        if form.is_valid() and formset.is_valid():
            self.object = form.save()
            formset.instance = self.object
            formset.save()
            self.object.update_total_amount()
            return super().form_valid(form)
        else:
            return self.form_invalid(form)

    def form_invalid(self, form):
        context = self.get_context_data()
        formset = context['formset']
        if not form.is_valid():
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(self.request, f"{field}: {error}")
        if not formset.is_valid():
            for i, form_errors in enumerate(formset.errors):
                if form_errors:
                    for field, errors in form_errors.items():
                        for error in errors:
                            messages.error(self.request, f"Item {i+1} - {field}: {error}")
        return self.render_to_response(self.get_context_data(form=form))

    def get_common_context(self):
        purchase_orders = PurchaseOrder.objects.all().order_by('id')
        current_order = self.object
        return {
            'model_name': self.model._meta.verbose_name.title(),
            'can_add': self.request.user.has_perm('uniworlderp.add_purchaseorder'),
            'can_edit': self.request.user.has_perm('uniworlderp.change_purchaseorder'),
            'can_view': self.request.user.has_perm('uniworlderp.view_purchaseorder'),
            'list_url': reverse_lazy('customer_vendor:purchase_order_list'),
            'create_url': reverse_lazy('customer_vendor:purchase_order_create'),
            'edit_url_name': 'customer_vendor:purchase_order_update',
            'view_url_name': 'customer_vendor:purchase_order_detail',
            'print_url_name': 'customer_vendor:purchase_order_print',
            'search_url': reverse_lazy('customer_vendor:purchase_order_search'),
            'first_id': purchase_orders.first().id if purchase_orders.exists() else None,
            'last_id': purchase_orders.last().id if purchase_orders.exists() else None,
            'prev_id': purchase_orders.filter(id__lt=current_order.id).last().id if purchase_orders.filter(id__lt=current_order.id).exists() else None,
            'next_id': purchase_orders.filter(id__gt=current_order.id).first().id if purchase_orders.filter(id__gt=current_order.id).exists() else None,
            'current_id': current_order.id,
        }
class PurchaseOrderDetailView(PermissionRequiredMixin, DetailView):
    model = PurchaseOrder
    template_name = 'purchase_order/form.html'
    permission_required = 'uniworlderp.view_purchaseorder'

    def handle_no_permission(self):
        messages.error(self.request, "You do not have permission to view this purchase order.")
        return redirect('customer_vendor:purchase_order_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(self.get_common_context())
        context['action'] = 'View'
        context['form'] = PurchaseOrderForm(instance=self.object)
        context['formset'] = PurchaseOrderItemFormSet(instance=self.object)
        for form in context['formset']:
            for field in form.fields.values():
                field.widget.attrs['disabled'] = 'disabled'
        for field in context['form'].fields.values():
            field.widget.attrs['disabled'] = 'disabled'
        return context

    def get_common_context(self):
        purchase_orders = PurchaseOrder.objects.all().order_by('id')
        current_order = self.object
        return {
            'model_name': self.model._meta.verbose_name.title(),
            'can_add': self.request.user.has_perm('uniworlderp.add_purchaseorder'),
            'can_edit': self.request.user.has_perm('uniworlderp.change_purchaseorder'),
            'can_view': self.request.user.has_perm('uniworlderp.view_purchaseorder'),
            'list_url': reverse_lazy('customer_vendor:purchase_order_list'),
            'create_url': reverse_lazy('customer_vendor:purchase_order_create'),
            'edit_url_name': 'customer_vendor:purchase_order_update',
            'view_url_name': 'customer_vendor:purchase_order_detail',
            'print_url_name': 'customer_vendor:purchase_order_print',
            'first_id': purchase_orders.first().id if purchase_orders.exists() else None,
            'last_id': purchase_orders.last().id if purchase_orders.exists() else None,
            'prev_id': purchase_orders.filter(id__lt=current_order.id).last().id if purchase_orders.filter(id__lt=current_order.id).exists() else None,
            'next_id': purchase_orders.filter(id__gt=current_order.id).first().id if purchase_orders.filter(id__gt=current_order.id).exists() else None,
            'current_id': current_order.id,
        }

class PurchaseOrderDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = PurchaseOrder
    template_name = 'confirm_delete.html'
    success_url = reverse_lazy('customer_vendor:purchase_order_list')
    success_message = "Purchase order deleted successfully!"
    permission_required = 'uniworlderp.delete_purchaseorder'

    def handle_no_permission(self):
        messages.error(self.request, "You do not have permission to delete this purchase order.")
        return redirect('customer_vendor:purchase_order_list')

    @transaction.atomic
    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()

        # Revert stock quantities
        for item in self.object.order_items.all():
            StockTransaction.objects.create(
                product=item.product,
                transaction_type='OUT',
                quantity=item.quantity,
                reference=f"PO-{self.object.id}-Deleted",
                owner=self.request.user
            )
            item.product.stock_quantity -= item.quantity
            item.product.save()

        # messages.success(self.request, self.success_message)
        return super(PurchaseOrderDeleteView, self).delete(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['model_name'] = self.model._meta.verbose_name.title()
        context['cancel_url'] = reverse_lazy('customer_vendor:purchase_order_list')
        return context

class PurchaseOrderPrintView(LoginRequiredMixin, DetailView):
    model = PurchaseOrder
    template_name = 'purchase_order/print.html'
    context_object_name = 'purchase_order'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        company = Company.objects.first()  # Assuming you have only one company
        items = self.object.order_items.all()
        subtotal = sum(item.total for item in items)
        tax = subtotal * Decimal('0.0')  # 0% tax
        total = subtotal + tax

        context.update({
            'company': company,
            'items': items,
            'subtotal': subtotal,
            'tax': tax,
            'total': total,
        })
        return context

class PurchaseOrderReceiveView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = PurchaseOrder
    template_name = 'purchase_order/receive.html'
    fields = []
    permission_required = 'uniworlderp.change_purchaseorder'
    success_url = reverse_lazy('customer_vendor:purchase_order_list')

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        if self.object.delivery_status == 'P':
            for item in self.object.order_items.all():
                StockTransaction.objects.create(
                    product=item.product,
                    transaction_type='IN',
                    quantity=item.quantity,
                    reference=f"PO-{self.object.id}",
                    owner=self.request.user
                )
                # Update product stock quantity
                item.product.stock_quantity += item.quantity
                item.product.save()
            self.object.delivery_status = 'R'
            self.object.save()
            messages.success(request, "Purchase Order received successfully!")
        else:
            messages.error(request, "This Purchase Order has already been received.")
        return redirect(self.get_success_url())

