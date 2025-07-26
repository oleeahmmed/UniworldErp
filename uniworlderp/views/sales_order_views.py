
# customer_views.py


from django import forms
from django.urls import reverse

from uniworlderp import models
from .common_imports import *
from uniworlderp.models import ReturnSales, ReturnSalesItem, SalesOrder, SalesOrderItem, Product,StockTransaction,SalesEmployee
from uniworlderp.forms import ReturnSalesForm, ReturnSalesItemFormSet, SalesOrderForm, SalesOrderItemFormSet, get_return_sales_item_formset
from company.models import Company, Branch, ContactPerson

class SalesOrderListView(ListView):
    model = SalesOrder
    template_name = 'sales_order/list.html'
    context_object_name = 'sales_orders'
    paginate_by = 20

    def get_queryset(self):
        # Get the search query from the request
        search_query = self.request.GET.get('search', '')

        # Fetch all records and order them by the latest order_date
        queryset = SalesOrder.objects.all().order_by('-id')

        # Apply search filters if a search query is present
        if search_query:
            queryset = queryset.filter(
                Q(id__icontains=search_query) |
                Q(customer__name__icontains=search_query) |
                Q(sales_employee__user__username__icontains=search_query) |
                Q(order_date__icontains=search_query)
            )

        return queryset

    def get_context_data(self, **kwargs):
        # Add the search query to the context for use in the template
        context = super().get_context_data(**kwargs)
        context['search_query'] = self.request.GET.get('search', '')
        return context

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_query'] = self.request.GET.get('search', '')
        return context
class SalesOrderItemDetailedListView(ListView):
    model = SalesOrderItem
    template_name = 'sales_order/detailed_list.html'
    context_object_name = 'order_items'

    def get_queryset(self):
        queryset = SalesOrderItem.objects.select_related(
            'sales_order__customer',
            'sales_order__sales_employee',
            'sales_order__invoice',
            'product'
        ).annotate(
            total_amount=F('quantity') * F('unit_price')
        ).order_by('-sales_order__order_date', 'sales_order__id')

        search_query = self.request.GET.get('search', '')
        if search_query:
            queryset = queryset.filter(
                Q(sales_order__id__icontains=search_query) |
                Q(sales_order__customer__name__icontains=search_query) |
                Q(sales_order__sales_employee__full_name__icontains=search_query) |
                Q(product__name__icontains=search_query)
            ).distinct()

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_query'] = self.request.GET.get('search', '')
        return context
    
class SalesOrderCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = SalesOrder
    form_class = SalesOrderForm
    template_name = 'sales_order/form.html'
    success_url = reverse_lazy('customer_vendor:sales_order_list')
    permission_required = 'uniworlderp.add_salesorder'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['formset'] = SalesOrderItemFormSet(self.request.POST)
        else:
            context['formset'] = SalesOrderItemFormSet()
        context.update(self.get_common_context())
        context['action'] = 'Add'
        context['products'] = Product.objects.all().order_by('name')
        return context

    @transaction.atomic
    def form_valid(self, form):
        context = self.get_context_data()
        formset = context['formset']
        if form.is_valid() and formset.is_valid():
            try:
                with transaction.atomic():
                    self.object = form.save(commit=False)
                    self.object.owner = self.request.user  # Set the owner to the current user
                    self.object.save()
                    formset.instance = self.object
                    formset.save()
                messages.success(self.request, 'Sales Order created successfully.')
                return super().form_valid(form)
            except Exception as e:
                messages.error(self.request, f'Error creating Sales Order: {str(e)}')
                return self.form_invalid(form)
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
        return super().form_invalid(form)

    def get_common_context(self):
        sales_orders = SalesOrder.objects.all().order_by('id')
        return {
            'model_name': self.model._meta.verbose_name.title(),
            'can_add': self.request.user.has_perm('uniworlderp.add_salesorder'),
            'can_edit': self.request.user.has_perm('uniworlderp.change_salesorder'),
            'can_view': self.request.user.has_perm('uniworlderp.view_salesorder'),
            'list_url': reverse_lazy('customer_vendor:sales_order_list'),
            'create_url': reverse_lazy('customer_vendor:sales_order_create'),
            'edit_url_name': 'customer_vendor:sales_order_update',
            'view_url_name': 'customer_vendor:sales_order_view',
            'print_url_name': 'customer_vendor:sales_order_print',
            'search_url': reverse_lazy('customer_vendor:sales_order_search'),
            'first_id': sales_orders.first().id if sales_orders.exists() else None,
            'last_id': sales_orders.last().id if sales_orders.exists() else None,
            'prev_id': None,
            'next_id': None,
            'current_id': None,
        }

class SalesOrderUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = SalesOrder
    form_class = SalesOrderForm
    template_name = 'sales_order/form.html'
    success_url = reverse_lazy('customer_vendor:sales_order_list')
    permission_required = 'uniworlderp.change_salesorder'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['formset'] = SalesOrderItemFormSet(self.request.POST, instance=self.object)
        else:
            context['formset'] = SalesOrderItemFormSet(instance=self.object)
        context.update(self.get_common_context())
        context['action'] = 'Edit'
        context['products'] = Product.objects.all().order_by('name')         
        context['can_create_invoice'] = self.request.user.has_perm('uniworlderp.add_arinvoice')
        context['create_invoice_url'] = reverse('customer_vendor:invoice_create_from_sales_order', kwargs={'sales_order_id': self.object.id})
        return context

    @transaction.atomic
    def form_valid(self, form):
        context = self.get_context_data()
        formset = context['formset']
        if formset.is_valid():
            self.object = form.save()
            formset.instance = self.object
            formset.save()
            return super().form_valid(form)
        else:
            return self.form_invalid(form)

    def get_common_context(self):
        sales_orders = SalesOrder.objects.all().order_by('id')
        current_order = self.object
        return {
            'model_name': self.model._meta.verbose_name.title(),
            'can_add': self.request.user.has_perm('uniworlderp.add_salesorder'),
            'can_edit': self.request.user.has_perm('uniworlderp.change_salesorder'),
            'can_view': self.request.user.has_perm('uniworlderp.view_salesorder'),
            'list_url': reverse_lazy('customer_vendor:sales_order_list'),
            'create_url': reverse_lazy('customer_vendor:sales_order_create'),
            'edit_url_name': 'customer_vendor:sales_order_update',
            'view_url_name': 'customer_vendor:sales_order_view',
            'print_url_name': 'customer_vendor:sales_order_print',
            'search_url': reverse_lazy('customer_vendor:sales_order_search'),
            'first_id': sales_orders.first().id if sales_orders.exists() else None,
            'last_id': sales_orders.last().id if sales_orders.exists() else None,
            'prev_id': sales_orders.filter(id__lt=current_order.id).last().id if sales_orders.filter(id__lt=current_order.id).exists() else None,
            'next_id': sales_orders.filter(id__gt=current_order.id).first().id if sales_orders.filter(id__gt=current_order.id).exists() else None,
            'current_id': current_order.id,
        }
class SalesOrderDetailView(PermissionRequiredMixin, DetailView):
    model = SalesOrder
    template_name = 'sales_order/form.html'
    permission_required = 'uniworlderp.view_salesorder'

    def handle_no_permission(self):
        messages.error(self.request, "You do not have permission to view this sales order.")
        return redirect('customer_vendor:sales_order_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(self.get_common_context())
        context['action'] = 'View'
        context['form'] = SalesOrderForm(instance=self.object)
        context['formset'] = SalesOrderItemFormSet(instance=self.object)
        for form in context['formset']:
            for field in form.fields.values():
                field.widget.attrs['disabled'] = 'disabled'
        for field in context['form'].fields.values():
            field.widget.attrs['disabled'] = 'disabled'
        # Add context for the invoice creation button
        context['can_create_invoice'] = self.request.user.has_perm('uniworlderp.add_arinvoice')
        context['create_invoice_url'] = reverse('customer_vendor:invoice_create_from_sales_order', kwargs={'sales_order_id': self.object.id})
                    
        return context

    def get_common_context(self):
        sales_orders = SalesOrder.objects.all().order_by('id')
        current_order = self.object
        return {
            'model_name': self.model._meta.verbose_name.title(),
            'can_add': self.request.user.has_perm('uniworlderp.add_salesorder'),
            'can_edit': self.request.user.has_perm('uniworlderp.change_salesorder'),
            'can_view': self.request.user.has_perm('uniworlderp.view_salesorder'),
            'list_url': reverse_lazy('customer_vendor:sales_order_list'),
            'create_url': reverse_lazy('customer_vendor:sales_order_create'),
            'edit_url_name': 'customer_vendor:sales_order_update',
            'view_url_name': 'customer_vendor:sales_order_view',
            'print_url_name': 'customer_vendor:sales_order_print',
            'first_id': sales_orders.first().id if sales_orders.exists() else None,
            'last_id': sales_orders.last().id if sales_orders.exists() else None,
            'prev_id': sales_orders.filter(id__lt=current_order.id).last().id if sales_orders.filter(id__lt=current_order.id).exists() else None,
            'next_id': sales_orders.filter(id__gt=current_order.id).first().id if sales_orders.filter(id__gt=current_order.id).exists() else None,
            'current_id': current_order.id,
        }

class SalesOrderDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = SalesOrder
    template_name = 'confirm_delete.html'
    success_url = reverse_lazy('customer_vendor:sales_order_list')
    success_message = "Sales order deleted successfully!"
    permission_required = 'uniworlderp.delete_salesorder'

    def handle_no_permission(self):
        messages.error(self.request, "You do not have permission to delete this sales order.")
        return redirect('customer_vendor:sales_order_list')

    @transaction.atomic
    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        
        # Revert stock quantities
        for item in self.object.order_items.all():
            StockTransaction.objects.create(
                product=item.product,
                transaction_type='IN',
                quantity=item.quantity,
                reference=f"SO-{self.object.id}-Deleted",
                owner=self.request.user
            )
            # Directly update the product's stock quantity
            Product.objects.filter(id=item.product.id).update(stock_quantity=F('stock_quantity') + item.quantity)

        # messages.success(self.request, self.success_message)
        return super(SalesOrderDeleteView, self).delete(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['model_name'] = self.model._meta.verbose_name.title()
        context['cancel_url'] = reverse_lazy('customer_vendor:sales_order_list')
        return context

class SalesOrderPrintView(LoginRequiredMixin, DetailView):
    model = SalesOrder
    template_name = 'sales_order/print.html'
    context_object_name = 'sales_order'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        company = Company.objects.first()  # Assuming you have only one company
        items = self.object.order_items.all()
        subtotal = sum(item.total for item in items)
        discount = self.object.discount
        shipping = self.object.shipping
        tax = subtotal * Decimal('0.0')  # 12% tax
        total = subtotal - discount + shipping + tax

        context.update({
            'company': company,
            'items': items,
            'subtotal': subtotal,
            'discount': discount,
            'shipping': shipping,
            'tax': tax,
            'total': total,
        })
        return context


# views for return sales
class ReturnSalesCreateView(LoginRequiredMixin,PermissionRequiredMixin, CreateView):
    model = ReturnSales
    form_class = ReturnSalesForm
    template_name = 'sales_order/return.html'
    permission_required = 'uniworlderp.add_salesorder'
    
    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.sales_order_id = kwargs.get('sales_order_id')
        self.sales_order = get_object_or_404(SalesOrder, id=self.sales_order_id)
    
    def get_success_url(self):
        return reverse_lazy('customer_vendor:stock_transfer_detailed_list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['formset'] = ReturnSalesItemFormSet(self.request.POST, instance=self.object)
        else:
            # Initialize formset with sales order items
            initial_data = []
            for item in self.sales_order.order_items.all():
                # Calculate max returnable quantity
                previously_returned = ReturnSalesItem.objects.filter(
                    sales_order_item=item
                ).aggregate(total=Sum('quantity'))['total'] or 0
            
                max_returnable = item.quantity - previously_returned
            
                # Add all items to initial data, even if max_returnable is 0
                initial_data.append({
                    'sales_order_item': item.id,
                    'unit_price': item.unit_price,
                    'quantity': 0,  # Default to 0 
                    'sales_quantity': item.quantity,
                    'max_returnable': max_returnable,
                    'product_name': item.product.name,
                })
        
            # Use the factory function instead of the static formset
            context['formset'] = get_return_sales_item_formset(
                sales_order=self.sales_order,
                queryset=ReturnSalesItem.objects.none(),
                initial=initial_data
            )

            for form in context['formset'].forms:
                form.fields['sales_order_item'].queryset = SalesOrderItem.objects.filter(sales_order=self.sales_order)

        context['sales_order'] = self.sales_order
        context['action'] = 'Create'
        context['title'] = f'Create Return for Sales Order #{self.sales_order.id}'
        return context
        
    @transaction.atomic
    def form_valid(self, form):
        context = self.get_context_data()
        formset = context['formset']
        
        if form.is_valid() and formset.is_valid():
            try:
                with transaction.atomic():
                    self.object = form.save(commit=False)
                    self.object.sales_order = self.sales_order
                    self.object.owner = self.request.user
                    self.object.save()  
                    
                    # Now save the formset items
                    formset.instance = self.object  
                    formset_items = formset.save(commit=False)
                    
                    has_items = False
                    # Process each form/item manually
                    for item in formset_items:
                        # Only save items with quantity > 0
                        if item.quantity > 0:
                            has_items = True
                            # Ensure total is calculated
                            item.total = Decimal(item.quantity) * item.unit_price  
                            item.return_sales = self.object  
                            item.save()  
                    
                    # Handle deleted forms if any
                    for form in formset.deleted_forms:
                        if form.instance.pk:
                            form.instance.delete()
                    
                    # Check if at least one item was returned
                    if not has_items:
                        raise ValidationError("You must return at least one item.")
                    
                    # Update total amount
                    self.object.update_total_amount()
                    
                    messages.success(self.request, 'Sales return created successfully.')
                    return HttpResponseRedirect(self.get_success_url())
            except ValidationError as e:
                messages.error(self.request, str(e))
                return self.form_invalid(form)
            except Exception as e:
                messages.error(self.request, f'Error creating sales return: {str(e)}')
                return self.form_invalid(form)
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
        return super().form_invalid(form)


class ReturnSalesDetailView(LoginRequiredMixin, DetailView):
    model = ReturnSales
    template_name = 'sales_order/return_view.html'
    context_object_name = 'return_sales'
    permission_required = 'uniworlderp.view_returnsales'
    
    def get_object(self, queryset=None):
        sales_order_id = self.kwargs.get('sales_order_id')
        a = get_object_or_404(ReturnSales, sales_order=sales_order_id)
        print(a)
        print(a.return_employee)
        return a
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return_sales = self.object
        context['sales_order'] = return_sales.sales_order
        context['return_items'] = ReturnSalesItem.objects.filter(return_sales=return_sales)
        
        return context

