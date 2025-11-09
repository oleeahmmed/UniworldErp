from django.shortcuts import render
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from uniworlderp.models import SalesOrder, CustomerVendor, Product, SalesEmployee, SalesOrderItem, StockTransaction
from django.db.models import Sum, F, ExpressionWrapper, DecimalField, Q, Value, IntegerField
from django.db.models.functions import Coalesce
from datetime import datetime, timedelta, time
from django.utils import timezone
from django.utils.dateparse import parse_date
import pytz
from uniworlderp.forms import StockReportForm
from django.db import transaction
from django.http import HttpResponse
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment
import io


# Minimum allowed date for any stock report queries
MIN_STOCK_DATE = timezone.make_aware(datetime(2025, 7, 27))

class ReportView(LoginRequiredMixin, View):
    template_name = 'reports/report.html'

    def get(self, request):
        # Fetch data for filters
        customers = CustomerVendor.objects.filter(entity_type='customer')
        products = Product.objects.all()
        sales_employees = SalesEmployee.objects.all()

        # Initialize empty summaries for tabs
        customer_summary = []
        product_summary = []
        sales_employee_summary = []
        date_summary = []

        # Render the template with context
        return render(request, self.template_name, {
            'customers': customers,
            'products': products,
            'sales_employees': sales_employees,
            'customer_summary': customer_summary,
            'product_summary': product_summary,
            'sales_employee_summary': sales_employee_summary,
            'date_summary': date_summary,
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

        # Check if this is a single product transaction report request
        if product_id and not customer_id and not sales_employee_id:
            return self.handle_single_product_report(request, product_id, start_date, end_date)

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

    def handle_single_product_report(self, request, product_id, start_date, end_date):
        """Handle single product transaction report."""
        try:
            product = Product.objects.get(id=product_id, is_active=True)
            transactions = self.get_product_transactions(product, start_date, end_date)
            summary = self.calculate_summary(transactions)
            
            context = {
                'single_product_report': True,
                'product': product,
                'transactions': transactions,
                'summary': summary,
                'customers': CustomerVendor.objects.filter(entity_type='customer'),
                'products': Product.objects.all(),
                'sales_employees': SalesEmployee.objects.all(),
                'selected_product_id': product_id,
                'start_date': start_date,
                'end_date': end_date,
            }
            return render(request, self.template_name, context)
        except Product.DoesNotExist:
            # If product not found, return to regular report with error
            context = {
                'error': 'Product not found or inactive.',
                'customers': CustomerVendor.objects.filter(entity_type='customer'),
                'products': Product.objects.all(),
                'sales_employees': SalesEmployee.objects.all(),
            }
            return render(request, self.template_name, context)

    def get_product_transactions(self, product, start_date=None, end_date=None):
        """Get stock transactions (IN/OUT/RET/ADJ) for a product within an optional date range."""
        qs = StockTransaction.objects.filter(product=product)

        # Support dates as strings (YYYY-MM-DD) or date objects
        if start_date and end_date:
            qs = qs.filter(transaction_date__date__range=[start_date, end_date])

        qs = qs.order_by('transaction_date', 'id')

        txns = []
        for t in qs:
            ttype = t.transaction_type
            # Signed quantity for display/running math (+ for IN/RET, - for OUT). ADJ sets absolute stock
            if ttype in ('IN', 'RET'):
                signed_qty = t.quantity
            elif ttype == 'OUT':
                signed_qty = -t.quantity
            else:  # 'ADJ'
                signed_qty = 0

            txns.append({
                'datetime': getattr(t, 'transaction_date', None),
                'type': ttype,
                'type_label': t.get_transaction_type_display() if hasattr(t, 'get_transaction_type_display') else ttype,
                'quantity': t.quantity if ttype in ('IN', 'RET') else t.quantity,  # Raw quantity for display
                'signed_qty': signed_qty,  # Signed quantity for calculations
                'in_qty': signed_qty if signed_qty > 0 else 0,
                'out_qty': abs(signed_qty) if signed_qty < 0 else 0,
                'reference': getattr(t, 'reference', ''),
                'previous_stock': getattr(t, 'previous_stock', None),
                'current_stock': getattr(t, 'current_stock', None),
            })

        return txns

    def calculate_summary(self, transactions):
        """Calculate opening, total received, total issued, returns, and closing stock from transaction rows."""
        if not transactions:
            return {
                'opening_stock': 0,
                'total_in': 0,
                'total_issued': 0,
                'total_returned': 0,
                'total_received': 0,
                'closing_stock': 0,
            }

        opening_stock = transactions[0].get('previous_stock') or 0
        closing_stock = transactions[-1].get('current_stock') or opening_stock

        # Separate calculations for each transaction type
        total_in = sum(t['quantity'] for t in transactions if t.get('type') == 'IN')
        total_out = sum(abs(t['quantity']) for t in transactions if t.get('type') == 'OUT')
        total_returned = sum(t['quantity'] for t in transactions if t.get('type') == 'RET')
        
        # Legacy calculation for backward compatibility
        total_received = sum(t['quantity'] for t in transactions if t['quantity'] > 0)
        total_issued = sum(abs(t['quantity']) for t in transactions if t['quantity'] < 0)

        return {
            'opening_stock': opening_stock,
            'total_in': total_in,
            'total_issued': total_out,
            'total_returned': total_returned,
            'total_received': total_received,
            'closing_stock': closing_stock,
        }


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

            # If a single product is selected, include detailed transactions in the same page
            product_obj = form.cleaned_data.get('product_id')
            if product_obj:
                # Determine date range as dates for filtering
                date_range = form.cleaned_data.get('date_range')
                start_date = form.cleaned_data.get('start_date')
                end_date = form.cleaned_data.get('end_date')
                if date_range == 'today':
                    # Use today's date for both bounds
                    today_bd = timezone.localtime().date()
                    start_date = today_bd
                    end_date = today_bd

                report_view = ReportView()
                transactions = report_view.get_product_transactions(product_obj, start_date, end_date)
                summary = report_view.calculate_summary(transactions)

                context.update({
                    'single_product': product_obj,
                    'single_product_transactions': transactions,
                    'single_product_summary': summary,
                    'single_product_start_date': start_date,
                    'single_product_end_date': end_date,
                })
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
                    'unit': product.get_unit_display(),
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


class SingleProductReportPrintView(LoginRequiredMixin, View):
    """View for printing single product transaction reports."""
    template_name = 'reports/single_product_transaction_report.html'

    def get(self, request, *args, **kwargs):
        product_id = request.GET.get('product_id')
        start_date_raw = request.GET.get('start_date')
        end_date_raw = request.GET.get('end_date')
        # Normalize dates: accept YYYY-MM-DD or other human strings
        start_date = parse_date(start_date_raw) if start_date_raw else None
        end_date = parse_date(end_date_raw) if end_date_raw else None
        if start_date is None and start_date_raw:
            # fallback: try common format like 'Aug. 11, 2025' without the dot
            try:
                from datetime import datetime
                start_date = datetime.strptime(start_date_raw.replace('.', ''), '%b %d, %Y').date()
            except Exception:
                start_date = None
        if end_date is None and end_date_raw:
            try:
                from datetime import datetime
                end_date = datetime.strptime(end_date_raw.replace('.', ''), '%b %d, %Y').date()
            except Exception:
                end_date = None
        
        if not product_id:
            return render(request, self.template_name, {'error': 'Product ID is required.'})
        
        try:
            product = Product.objects.get(id=product_id, is_active=True)
            report_view = ReportView()
            transactions = report_view.get_product_transactions(product, start_date, end_date)
            summary = report_view.calculate_summary(transactions)
            
            context = {
                'product': product,
                'transactions': transactions,
                'summary': summary,
                'start_date': start_date,
                'end_date': end_date,
                'print_view': True,
            }
            return render(request, self.template_name, context)
        except Product.DoesNotExist:
            return render(request, self.template_name, {'error': 'Product not found or inactive.'})


class SingleProductStockReportPrintView(LoginRequiredMixin, View):
    """View for printing single product stock reports with proper format."""
    template_name = 'reports/single_product_stock_report_print.html'

    def get(self, request, *args, **kwargs):
        product_id = request.GET.get('product_id')
        start_date_raw = request.GET.get('start_date')
        end_date_raw = request.GET.get('end_date')
        
        # Parse dates
        start_date = parse_date(start_date_raw) if start_date_raw else None
        end_date = parse_date(end_date_raw) if end_date_raw else None
        
        if not product_id:
            return render(request, self.template_name, {'error': 'Product ID is required.'})
        
        try:
            product = Product.objects.get(id=product_id, is_active=True)
            report_view = ReportView()
            transactions = report_view.get_product_transactions(product, start_date, end_date)
            summary = report_view.calculate_summary(transactions)
            
            # Format dates for display
            now = timezone.now()
            bdt = pytz.timezone('Asia/Dhaka')
            now_bdt = now.astimezone(bdt)
            
            if start_date and end_date:
                if start_date == end_date:
                    report_date_display = f"{start_date.strftime('%d/%m/%Y')}"
                else:
                    report_date_display = f"{start_date.strftime('%d/%m/%Y')} to {end_date.strftime('%d/%m/%Y')}"
                report_start_time = start_date.strftime('%d/%m/%Y %I:%M %p')
                report_end_time = end_date.strftime('%d/%m/%Y %I:%M %p')
            else:
                report_date_display = "All Transactions"
                report_start_time = "All Time"
                report_end_time = "All Time"
            
            context = {
                'product': product,
                'transactions': transactions,
                'summary': summary,
                'start_date': start_date,
                'end_date': end_date,
                'print_view': True,
                'user': request.user,
                'report_date_display': report_date_display,
                'report_start_time': report_start_time,
                'report_end_time': report_end_time,
                'report_generated_at_formatted': now_bdt.strftime('%d/%m/%Y %I:%M %p'),
            }
            return render(request, self.template_name, context)
        except Product.DoesNotExist:
            return render(request, self.template_name, {'error': 'Product not found or inactive.'})


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


class CustomerReportView(LoginRequiredMixin, PermissionRequiredMixin, View):
    """View for generating and displaying customer reports."""
    template_name = 'reports/customer_report.html'
    permission_required = 'uniworlderp.view_customervendor'

    def get(self, request, *args, **kwargs):
        """Display full customer report (all customers, no filters)."""
        # Fetch all customers for this owner
        customers = (
            CustomerVendor.objects
            .filter(entity_type='customer')
            .order_by('name')
        )

        # Prepare report metadata similar to stock report
        now_bd = timezone.localtime()
        context = {
            'customers': customers,
            'total_customers': customers.count(),
            'user': request.user,
            'report_date_display': now_bd.strftime('%Y-%m-%d'),
            'report_generated_at_formatted': now_bd.strftime('%Y-%m-%d %H:%M:%S'),
        }

        return render(request, self.template_name, context)


class CustomerReportPrintView(LoginRequiredMixin, PermissionRequiredMixin, View):
    """View for printing customer reports."""
    template_name = 'reports/customer_report_print.html'
    permission_required = 'uniworlderp.view_customervendor'

    def get(self, request, *args, **kwargs):
        """Display printable full customer report."""
        customers = (
            CustomerVendor.objects
            .filter(entity_type='customer')
            .order_by('name')
        )

        now_bd = timezone.localtime()
        context = {
            'customers': customers,
            'total_customers': customers.count(),
            'user': request.user,
            'report_date_display': now_bd.strftime('%Y-%m-%d'),
            'report_generated_at_formatted': now_bd.strftime('%Y-%m-%d %H:%M:%S'),
        }

        return render(request, self.template_name, context)


class CustomerReportExcelView(LoginRequiredMixin, PermissionRequiredMixin, View):
    """View for exporting customer reports to Excel."""
    permission_required = 'uniworlderp.view_customervendor'

    def get(self, request, *args, **kwargs):
        """Export full customer report to Excel (all customers)."""
        customers = (
            CustomerVendor.objects
            .filter(entity_type='customer')
            .order_by('name')
        )

        # Create Excel workbook
        wb = Workbook()
        ws = wb.active
        ws.title = "Customer Report"
        
        # Add headers
        headers = [
            'SL', 'Company Name', 'Phone', 'Email', 'WhatsApp',
            'Business Type', 'Address', 'Created At', 'Updated At'
        ]
        
        # Style headers
        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=1, column=col, value=header)
            cell.font = Font(bold=True)
            cell.alignment = Alignment(horizontal="center")
        
        # Add data
        for i, customer in enumerate(customers, 1):
            row = [
                i,
                customer.name,
                customer.phone_number,
                customer.email or '',
                customer.whatsapp_number or '',
                customer.get_business_type_display(),
                customer.address or '',
                customer.created_at.strftime('%Y-%m-%d %H:%M:%S') if customer.created_at else '',
                customer.updated_at.strftime('%Y-%m-%d %H:%M:%S') if customer.updated_at else '',
            ]
            for col, value in enumerate(row, 1):
                ws.cell(row=i+1, column=col, value=value)
        
        # Auto-adjust column widths
        for column in ws.columns:
            max_length = 0
            column_letter = column[0].column_letter
            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            adjusted_width = (max_length + 2)
            ws.column_dimensions[column_letter].width = min(adjusted_width, 50)
        
        # Save to buffer
        buffer = io.BytesIO()
        wb.save(buffer)
        buffer.seek(0)
        
        # Create response
        response = HttpResponse(
            buffer.getvalue(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = 'attachment; filename=customer_report.xlsx'
        
        return response


class ProductWiseReportView(LoginRequiredMixin, PermissionRequiredMixin, View):
    """View for generating product-wise sales reports."""
    template_name = 'reports/product_wise_report.html'
    permission_required = 'uniworlderp.view_product'

    def get(self, request, *args, **kwargs):
        # Fetch data for filters
        products = Product.objects.all()
        
        # Render the template with context
        return render(request, self.template_name, {
            'products': products,
        })

    def post(self, request, *args, **kwargs):
        # Get form data
        product_id = request.POST.get('product')
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        
        # Check if this is an AJAX request
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.content_type == 'application/x-www-form-urlencoded'
        
        # Validation
        if not product_id:
            error_message = "Please select a product for the report."
            context = {
                'products': Product.objects.all(),
                'error': error_message
            }
            if is_ajax:
                return render(request, 'reports/product_wise_report_partial.html', context)
            return render(request, self.template_name, context)
        
        if not start_date or not end_date:
            error_message = "Please select both start and end dates."
            context = {
                'products': Product.objects.all(),
                'error': error_message
            }
            if is_ajax:
                return render(request, 'reports/product_wise_report_partial.html', context)
            return render(request, self.template_name, context)
        
        try:
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            error_message = "Product not found."
            context = {
                'products': Product.objects.all(),
                'error': error_message
            }
            if is_ajax:
                return render(request, 'reports/product_wise_report_partial.html', context)
            return render(request, self.template_name, context)
        
        # Get sales data for the product within date range
        sales_data = SalesOrderItem.objects.filter(
            product=product,
            sales_order__order_date__range=[start_date, end_date]
        ).select_related(
            'sales_order__customer',
            'sales_order__sales_employee'
        ).order_by('-sales_order__order_date')
        
        # Check if no data found
        if not sales_data.exists():
            error_message = f"No sales data found for '{product.name}' between {start_date} and {end_date}."
            context = {
                'products': Product.objects.all(),
                'error': error_message,
                'selected_product': product,
                'start_date': start_date,
                'end_date': end_date
            }
            if is_ajax:
                return render(request, 'reports/product_wise_report_partial.html', context)
            return render(request, self.template_name, context)
        
        # Calculate totals
        total_qty = sum(item.quantity for item in sales_data)
        total_amount = sum(item.total for item in sales_data)
        
        # Format dates for display
        now = timezone.now()
        bdt = pytz.timezone('Asia/Dhaka')
        now_bdt = now.astimezone(bdt)
        
        context = {
            'products': Product.objects.all(),
            'selected_product': product,
            'start_date': start_date,
            'end_date': end_date,
            'sales_data': sales_data,
            'total_qty': total_qty,
            'total_amount': total_amount,
            'user': request.user,
            'report_generated_at': now_bdt.strftime('%d/%m/%Y %I:%M %p'),
            'report_data': sales_data  # For potential future use
        }
        
        # Return partial template for AJAX requests
        if is_ajax:
            return render(request, 'reports/product_wise_report_partial.html', context)
        
        return render(request, self.template_name, context)


class ProductWiseReportPrintView(LoginRequiredMixin, PermissionRequiredMixin, View):
    """View for printing product-wise sales reports."""
    template_name = 'reports/product_wise_report_print.html'
    permission_required = 'uniworlderp.view_product'

    def get(self, request, *args, **kwargs):
        product_id = request.GET.get('product')
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')
        
        # Validation
        if not product_id or not start_date or not end_date:
            return render(request, self.template_name, {'error': 'Missing required parameters.'})
        
        try:
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            return render(request, self.template_name, {'error': 'Product not found.'})
        
        # Get sales data
        sales_data = SalesOrderItem.objects.filter(
            product=product,
            sales_order__order_date__range=[start_date, end_date]
        ).select_related(
            'sales_order__customer',
            'sales_order__sales_employee'
        ).order_by('-sales_order__order_date')
        
        # Calculate totals
        total_qty = sum(item.quantity for item in sales_data)
        total_amount = sum(item.total for item in sales_data)
        
        # Format dates
        now = timezone.now()
        bdt = pytz.timezone('Asia/Dhaka')
        now_bdt = now.astimezone(bdt)
        
        context = {
            'product': product,
            'start_date': start_date,
            'end_date': end_date,
            'sales_data': sales_data,
            'total_qty': total_qty,
            'total_amount': total_amount,
            'user': request.user,
            'report_generated_at': now_bdt.strftime('%d/%m/%Y %I:%M %p'),
            'print_view': True
        }
        
        return render(request, self.template_name, context)


class ProductWiseReportExcelView(LoginRequiredMixin, PermissionRequiredMixin, View):
    """View for exporting product-wise sales reports to Excel."""
    permission_required = 'uniworlderp.view_product'

    def get(self, request, *args, **kwargs):
        product_id = request.GET.get('product')
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')
        
        if not product_id or not start_date or not end_date:
            return HttpResponse('Missing required parameters', status=400)
        
        try:
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            return HttpResponse('Product not found', status=404)
        
        # Get sales data
        sales_data = SalesOrderItem.objects.filter(
            product=product,
            sales_order__order_date__range=[start_date, end_date]
        ).select_related(
            'sales_order__customer',
            'sales_order__sales_employee'
        ).order_by('-sales_order__order_date')
        
        # Create Excel workbook
        wb = Workbook()
        ws = wb.active
        ws.title = "Product Wise Report"
        
        # Add title and product info
        ws.merge_cells('A1:H1')
        title_cell = ws.cell(row=1, column=1, value=f"Product-wise Sales Report")
        title_cell.font = Font(bold=True, size=14)
        title_cell.alignment = Alignment(horizontal="center")
        
        ws.merge_cells('A2:H2')
        product_cell = ws.cell(row=2, column=1, value=f"Product: {product.name} | Code: {product.sku} | Unit: {product.get_unit_display()} | Price: ৳{product.price}")
        product_cell.font = Font(bold=True)
        product_cell.alignment = Alignment(horizontal="center")
        
        ws.merge_cells('A3:H3')
        date_cell = ws.cell(row=3, column=1, value=f"Date Range: {start_date} to {end_date}")
        date_cell.alignment = Alignment(horizontal="center")
        
        # Add headers
        headers = ['Customer Name', 'Invoice No', 'Sales Order No', 'Date', 'Qty', 'Unit', 'Price', 'Total']
        
        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=5, column=col, value=header)
            cell.font = Font(bold=True)
            cell.alignment = Alignment(horizontal="center")
        
        # Add data
        row_num = 6
        total_qty = 0
        total_amount = 0
        
        for item in sales_data:
            invoice_no = item.sales_order.invoice.id if hasattr(item.sales_order, 'invoice') and item.sales_order.invoice else 'N/A'
            
            row = [
                item.sales_order.customer.name,
                invoice_no,
                item.sales_order.id,
                item.sales_order.order_date.strftime('%d/%m/%Y'),
                item.quantity,
                product.get_unit_display(),
                float(item.unit_price),
                float(item.total)
            ]
            
            for col, value in enumerate(row, 1):
                ws.cell(row=row_num, column=col, value=value)
            
            total_qty += item.quantity
            total_amount += float(item.total)
            row_num += 1
        
        # Add totals
        total_row = row_num + 1
        ws.merge_cells(f'A{total_row}:D{total_row}')
        ws.cell(row=total_row, column=1, value='TOTALS:').font = Font(bold=True)
        ws.cell(row=total_row, column=5, value=total_qty).font = Font(bold=True)
        ws.cell(row=total_row, column=8, value=total_amount).font = Font(bold=True)
        
        # Auto-adjust column widths
        for column in ws.columns:
            max_length = 0
            column_letter = column[0].column_letter if hasattr(column[0], 'column_letter') else None
            if column_letter:
                for cell in column:
                    try:
                        if hasattr(cell, 'value') and len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                adjusted_width = min(max_length + 2, 50)
                ws.column_dimensions[column_letter].width = adjusted_width
        
        # Save to buffer
        buffer = io.BytesIO()
        wb.save(buffer)
        buffer.seek(0)
        
        # Create response
        response = HttpResponse(
            buffer.getvalue(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = f'attachment; filename=product_wise_report_{product.name}_{start_date}_to_{end_date}.xlsx'
        
        return response


class CustomerWiseReportView(LoginRequiredMixin, PermissionRequiredMixin, View):
    """View for generating customer-wise sales reports."""
    template_name = 'reports/customer_wise_report.html'
    permission_required = 'uniworlderp.view_customervendor'

    def get(self, request, *args, **kwargs):
        # Fetch data for filters
        customers = CustomerVendor.objects.filter(entity_type='customer')
        
        # Render the template with context
        return render(request, self.template_name, {
            'customers': customers,
        })

    def post(self, request, *args, **kwargs):
        # Get form data
        customer_id = request.POST.get('customer')
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        
        # Check if this is an AJAX request
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.content_type == 'application/x-www-form-urlencoded'
        
        # Validation
        if not customer_id:
            error_message = "Please select a customer for the report."
            context = {
                'customers': CustomerVendor.objects.filter(entity_type='customer'),
                'error': error_message
            }
            if is_ajax:
                return render(request, 'reports/customer_wise_report_partial.html', context)
            return render(request, self.template_name, context)
        
        if not start_date or not end_date:
            error_message = "Please select both start and end dates."
            context = {
                'customers': CustomerVendor.objects.filter(entity_type='customer'),
                'error': error_message
            }
            if is_ajax:
                return render(request, 'reports/customer_wise_report_partial.html', context)
            return render(request, self.template_name, context)
        
        try:
            customer = CustomerVendor.objects.get(id=customer_id, entity_type='customer')
        except CustomerVendor.DoesNotExist:
            error_message = "Customer not found."
            context = {
                'customers': CustomerVendor.objects.filter(entity_type='customer'),
                'error': error_message
            }
            if is_ajax:
                return render(request, 'reports/customer_wise_report_partial.html', context)
            return render(request, self.template_name, context)
        
        # Get sales orders for the customer within date range
        sales_orders = SalesOrder.objects.filter(
            customer=customer,
            order_date__range=[start_date, end_date]
        ).select_related('sales_employee').prefetch_related(
            'order_items__product'
        ).order_by('-order_date')
        
        # Check if no data found
        if not sales_orders.exists():
            error_message = f"No sales data found for '{customer.name}' between {start_date} and {end_date}."
            context = {
                'customers': CustomerVendor.objects.filter(entity_type='customer'),
                'error': error_message,
                'selected_customer': customer,
                'start_date': start_date,
                'end_date': end_date
            }
            if is_ajax:
                return render(request, 'reports/customer_wise_report_partial.html', context)
            return render(request, self.template_name, context)
        
        # Calculate totals
        total_purchase = sum(order.total_amount - order.discount for order in sales_orders)
        total_discount = sum(order.discount for order in sales_orders)
        net_amount = sum(order.total_amount for order in sales_orders)
        
        # Format dates for display
        now = timezone.now()
        bdt = pytz.timezone('Asia/Dhaka')
        now_bdt = now.astimezone(bdt)
        
        context = {
            'customers': CustomerVendor.objects.filter(entity_type='customer'),
            'selected_customer': customer,
            'start_date': start_date,
            'end_date': end_date,
            'sales_orders': sales_orders,
            'total_purchase': total_purchase,
            'total_discount': total_discount,
            'net_amount': net_amount,
            'user': request.user,
            'report_generated_at': now_bdt.strftime('%d/%m/%Y %I:%M %p'),
        }
        
        # Return partial template for AJAX requests
        if is_ajax:
            return render(request, 'reports/customer_wise_report_partial.html', context)
        
        return render(request, self.template_name, context)


class CustomerWiseReportPrintView(LoginRequiredMixin, PermissionRequiredMixin, View):
    """View for printing customer-wise sales reports."""
    template_name = 'reports/customer_wise_report_print.html'
    permission_required = 'uniworlderp.view_customervendor'

    def get(self, request, *args, **kwargs):
        customer_id = request.GET.get('customer')
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')
        
        # Validation
        if not customer_id or not start_date or not end_date:
            return render(request, self.template_name, {'error': 'Missing required parameters.'})
        
        try:
            customer = CustomerVendor.objects.get(id=customer_id, entity_type='customer')
        except CustomerVendor.DoesNotExist:
            return render(request, self.template_name, {'error': 'Customer not found.'})
        
        # Get sales orders
        sales_orders = SalesOrder.objects.filter(
            customer=customer,
            order_date__range=[start_date, end_date]
        ).select_related('sales_employee').prefetch_related(
            'order_items__product'
        ).order_by('-order_date')
        
        # Calculate totals
        total_purchase = sum(order.total_amount - order.discount for order in sales_orders)
        total_discount = sum(order.discount for order in sales_orders)
        net_amount = sum(order.total_amount for order in sales_orders)
        
        # Format dates
        now = timezone.now()
        bdt = pytz.timezone('Asia/Dhaka')
        now_bdt = now.astimezone(bdt)
        
        context = {
            'customer': customer,
            'start_date': start_date,
            'end_date': end_date,
            'sales_orders': sales_orders,
            'total_purchase': total_purchase,
            'total_discount': total_discount,
            'net_amount': net_amount,
            'user': request.user,
            'report_generated_at': now_bdt.strftime('%d/%m/%Y %I:%M %p'),
            'print_view': True
        }
        
        return render(request, self.template_name, context)


class CustomerWiseReportExcelView(LoginRequiredMixin, PermissionRequiredMixin, View):
    """View for exporting customer-wise sales reports to Excel."""
    permission_required = 'uniworlderp.view_customervendor'

    def get(self, request, *args, **kwargs):
        customer_id = request.GET.get('customer')
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')
        
        if not customer_id or not start_date or not end_date:
            return HttpResponse('Missing required parameters', status=400)
        
        try:
            customer = CustomerVendor.objects.get(id=customer_id, entity_type='customer')
        except CustomerVendor.DoesNotExist:
            return HttpResponse('Customer not found', status=404)
        
        # Get sales orders
        sales_orders = SalesOrder.objects.filter(
            customer=customer,
            order_date__range=[start_date, end_date]
        ).select_related('sales_employee').prefetch_related(
            'order_items__product'
        ).order_by('-order_date')
        
        # Create Excel workbook
        wb = Workbook()
        ws = wb.active
        ws.title = "Customer Wise Report"
        
        # Add title and customer info
        ws.merge_cells('A1:J1')
        title_cell = ws.cell(row=1, column=1, value=f"Customer-wise Sales Report")
        title_cell.font = Font(bold=True, size=14)
        title_cell.alignment = Alignment(horizontal="center")
        
        ws.merge_cells('A2:J2')
        customer_cell = ws.cell(row=2, column=1, value=f"Customer Name: {customer.name}")
        customer_cell.font = Font(bold=True)
        customer_cell.alignment = Alignment(horizontal="center")
        
        ws.merge_cells('A3:J3')
        address_cell = ws.cell(row=3, column=1, value=f"Address: {customer.address or 'N/A'}")
        address_cell.alignment = Alignment(horizontal="center")
        
        ws.merge_cells('A4:J4')
        mobile_cell = ws.cell(row=4, column=1, value=f"Mobile: {customer.phone_number}")
        mobile_cell.alignment = Alignment(horizontal="center")
        
        ws.merge_cells('A5:J5')
        date_cell = ws.cell(row=5, column=1, value=f"Start Date: {start_date} & End Date: {end_date}")
        date_cell.alignment = Alignment(horizontal="center")
        
        # Add headers
        headers = ['Order Date', 'Order ID', 'Customer', 'Product Details', 'Qty', 'Unit', 'Price', 'Sub Total', 'Discount', 'Net Amount', 'Sales Employee']
        
        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=7, column=col, value=header)
            cell.font = Font(bold=True)
            cell.alignment = Alignment(horizontal="center")
        
        # Add data
        row_num = 8
        total_purchase = 0
        total_discount = 0
        net_amount = 0
        
        for order in sales_orders:
            # Create product details string
            product_details = ', '.join([f"{item.product.name} ({item.quantity})" for item in order.order_items.all()])
            sub_total = order.total_amount - order.discount
            
            row = [
                order.order_date.strftime('%d/%m/%Y'),
                order.id,
                customer.name,
                product_details,
                sum(item.quantity for item in order.order_items.all()),
                'Mixed' if order.order_items.count() > 1 else (order.order_items.first().product.get_unit_display() if order.order_items.exists() else 'N/A'),
                float(sum(item.unit_price for item in order.order_items.all())),
                float(sub_total),
                float(order.discount),
                float(order.total_amount),
                order.sales_employee.full_name if order.sales_employee else 'N/A'
            ]
            
            for col, value in enumerate(row, 1):
                ws.cell(row=row_num, column=col, value=value)
            
            total_purchase += float(sub_total)
            total_discount += float(order.discount)
            net_amount += float(order.total_amount)
            row_num += 1
        
        # Add totals
        total_row = row_num + 1
        ws.merge_cells(f'A{total_row}:G{total_row}')
        ws.cell(row=total_row, column=1, value='TOTALS:').font = Font(bold=True)
        ws.cell(row=total_row, column=8, value=f'৳{total_purchase:,.2f}').font = Font(bold=True)
        ws.cell(row=total_row, column=9, value=f'৳{total_discount:,.2f}').font = Font(bold=True)
        ws.cell(row=total_row, column=10, value=f'৳{net_amount:,.2f}').font = Font(bold=True)
        
        # Auto-adjust column widths
        for column in ws.columns:
            max_length = 0
            column_letter = column[0].column_letter if hasattr(column[0], 'column_letter') else None
            if column_letter:
                for cell in column:
                    try:
                        if hasattr(cell, 'value') and len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                adjusted_width = min(max_length + 2, 50)
                ws.column_dimensions[column_letter].width = adjusted_width
        
        # Save to buffer
        buffer = io.BytesIO()
        wb.save(buffer)
        buffer.seek(0)
        
        # Create response
        response = HttpResponse(
            buffer.getvalue(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = f'attachment; filename=customer_wise_report_{customer.name}_{start_date}_to_{end_date}.xlsx'
        
        return response

