from django.shortcuts import render
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from uniworlderp.models import SalesOrder, CustomerVendor, Product, SalesEmployee, SalesOrderItem, StockTransaction
from django.db.models import Sum, F, ExpressionWrapper, DecimalField, Q, Value, IntegerField
from django.db.models.functions import Coalesce
from datetime import datetime, timedelta, time
from django.utils import timezone
import pytz
from uniworlderp.forms import StockReportForm
from django.db import transaction

# Minimum allowed date for any stock report queries
MIN_STOCK_DATE = timezone.make_aware(datetime(2025, 7, 27))

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

class StockReportView(LoginRequiredMixin, PermissionRequiredMixin, View):
    """View for generating and displaying stock reports."""
    template_name = 'reports/stock_report.html'
    permission_required = 'uniworlderp.view_product'

    def get(self, request, *args, **kwargs):
        form = StockReportForm()
        return render(request, self.template_name, {'form': form})

    def post(self, request, *args, **kwargs):
        form = StockReportForm(request.POST)
        if form.is_valid():
            report_data, context = self.generate_report_data(form)
            
            # --- Start Debug Logging ---
            import logging
            logger = logging.getLogger(__name__)
            logger.setLevel(logging.DEBUG)
            
            # Create a handler that writes to stderr
            handler = logging.StreamHandler()
            handler.setLevel(logging.DEBUG)
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            
            # Add the handler to the logger
            if not logger.handlers:
                logger.addHandler(handler)
            
            logger.debug("--- Stock Report Data ---")
            for item in report_data:
                logger.debug(item)
            logger.debug("-------------------------")
            # --- End Debug Logging ---
            
            context['form'] = form
            context['report_data'] = report_data
            return render(request, self.template_name, context)
        return render(request, self.template_name, {'form': form})

    @staticmethod
    def generate_report_data(form):
        product_id = form.cleaned_data.get('product_id')
        date_range = form.cleaned_data.get('date_range')
        start_date = form.cleaned_data.get('start_date')
        end_date = form.cleaned_data.get('end_date')

        now = timezone.now()
        bdt = pytz.timezone('Asia/Dhaka')
        now_bdt = now.astimezone(bdt)
        
        # --- Date Handling ---
        if date_range == 'today':
            start_dt = bdt.localize(datetime.combine(now_bdt.date(), time.min))
            end_dt = now_bdt
            report_date_display = f"{now_bdt.date().strftime('%d/%m/%Y')}"
        else: # custom range
            start_dt = bdt.localize(datetime.combine(start_date, time.min))
            if end_date == now_bdt.date():
                end_dt = now_bdt
            else:
                end_dt = bdt.localize(datetime.combine(end_date, time.max))
            
            if start_date == end_date:
                report_date_display = f"{start_date.strftime('%d/%m/%Y')}"
            else:
                report_date_display = f"{start_date.strftime('%d/%m/%Y')} to {end_date.strftime('%d/%m/%Y')}"

        products = Product.objects.filter(is_active=True)
        if product_id:
            products = products.filter(pk=product_id.pk)

        report_results = []
        with transaction.atomic():
            for i, product in enumerate(products, 1):
                # --- Stock Calculation Logic ---
                
                # 1. Get movements within the date range
                transactions_in_range = StockTransaction.objects.filter(
                    product=product,
                    transaction_date__gte=start_dt,
                    transaction_date__lte=end_dt
                ).aggregate(
                    received=Coalesce(Sum('quantity', filter=Q(transaction_type__in=['IN', 'RET'])), 0, output_field=IntegerField()),
                    issued=Coalesce(Sum('quantity', filter=Q(transaction_type='OUT')), 0, output_field=IntegerField()),
                )
                received_qty = transactions_in_range['received']
                issued_qty = transactions_in_range['issued']
                
                # 2. Determine Closing Stock
                # Start with the product's current stock as the most reliable value
                closing_stock = product.stock_quantity or 0

                # 3. Determine Opening Stock
                # Opening Stock = Closing Stock - Received Qty + Issued Qty
                opening_stock = closing_stock - received_qty + issued_qty

                remarks = "Order Required" if closing_stock <= product.reorder_level else ""

                report_results.append({
                    'sl': i,
                    'product_name': product.name,
                    'product_code': product.sku,
                    'unit': 'pcs',
                    'opening_stock': opening_stock,
                    'received_qty': received_qty,
                    'issued_qty': issued_qty,
                    'closing_stock': closing_stock,
                    'remarks': remarks,
                })

        # --- Context for Template ---
        report_start_time = start_dt.strftime('%d/%m/%Y %I:%M %p')
        report_end_time = end_dt.strftime('%d/%m/%Y %I:%M %p')

        context = {
            'report_generated_at_formatted': now_bdt.strftime('%d/%m/%Y %I:%M %p'),
            'report_date_display': report_date_display,
            'report_start_time': report_start_time,
            'report_end_time': report_end_time,
            'get_params': form.data.urlencode() if hasattr(form.data, 'urlencode') else ''
        }
        return report_results, context


class StockReportPrintView(LoginRequiredMixin, PermissionRequiredMixin, View):
    """View for printing stock reports."""
    template_name = 'reports/stock_report_print.html'
    permission_required = 'uniworlderp.view_product'

    def get(self, request, *args, **kwargs):
        form = StockReportForm(request.GET)
        if form.is_valid():
            report_data, context = StockReportView.generate_report_data(form)
            context['report_data'] = report_data
            return render(request, self.template_name, context)
        
        return render(request, 'reports/stock_report_print.html', {'error': 'Invalid parameters for print view.'})
