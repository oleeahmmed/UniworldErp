from django.shortcuts import render
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from uniworlderp.models import SalesOrder, CustomerVendor, Product, SalesEmployee, SalesOrderItem
from django.db.models import Sum, F, ExpressionWrapper, DecimalField
from datetime import datetime, timedelta
from django.utils import timezone

class ReportView(LoginRequiredMixin, View):
    template_name = 'reports/report.html'

    def get(self, request):
        # Fetch data for filters
        customers = CustomerVendor.objects.filter(entity_type='customer')
        products = Product.objects.all()
        sales_employees = SalesEmployee.objects.all()

        # Render the template with context
        return render(request, self.template_name, {
            'customers': customers,
            'products': products,
            'sales_employees': sales_employees,
        })

    def post(self, request):
        # Handle form submission and filter data
        customer_id = request.POST.get('customer')
        product_id = request.POST.get('product')
        sales_employee_id = request.POST.get('sales_employee')
        
        # Set default start and end dates
        today = timezone.now().date()
        first_day_of_month = today.replace(day=1)
        
        start_date = request.POST.get('start_date', first_day_of_month)
        end_date = request.POST.get('end_date', today)

        # Filter sales orders based on the selected criteria
        sales_orders = SalesOrder.objects.all()
        if customer_id:
            sales_orders = sales_orders.filter(customer_id=customer_id)
        if product_id:
            sales_orders = sales_orders.filter(order_items__product_id=product_id)
        if sales_employee_id:
            sales_orders = sales_orders.filter(sales_employee_id=sales_employee_id)
        if start_date and end_date:
            sales_orders = sales_orders.filter(order_date__range=[start_date, end_date])

        # Calculate summary amounts
        customer_summary = sales_orders.values('customer__name').annotate(total_amount=Sum('total_amount'))
        
        # Calculate product summary within the date range
        product_summary = SalesOrderItem.objects.filter(
            sales_order__in=sales_orders
        ).values(
            product_name=F('product__name')
        ).annotate(
            total_amount=Sum('total')
        ).order_by('product_name')
        sales_employee_summary = sales_orders.values('sales_employee__full_name').annotate(total_amount=Sum('total_amount'))

        # Calculate date-wise summary
        date_summary = sales_orders.values('order_date').annotate(total_amount=Sum('total_amount')).order_by('order_date')

        # Render the template with filtered data and summaries
        return render(request, self.template_name, {
            'sales_orders': sales_orders,
            'customers': CustomerVendor.objects.filter(entity_type='customer'),
            'products': Product.objects.all(),
            'sales_employees': SalesEmployee.objects.all(),
            'customer_summary': customer_summary,
            'product_summary': product_summary,
            'sales_employee_summary': sales_employee_summary,
            'date_summary': date_summary,
        })