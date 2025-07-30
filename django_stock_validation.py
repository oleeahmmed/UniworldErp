#!/usr/bin/env python
import os
import sys
import django
from datetime import datetime, time, date
import pytz

# Add the project directory to the Python path
sys.path.append('/home/rabbie/dev/uniworld 25 07 2025')

# Configure Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')
django.setup()

from uniworlderp.models import Product, StockTransaction
from django.db.models import Sum, Q
from django.db.models.functions import Coalesce
from django.db.models import IntegerField
from django.utils import timezone

def validate_stock_calculation():
    """
    This function mimics the exact calculation logic from the Django view
    to validate the stock calculation algorithm.
    """
    
    # Minimum allowed date for any stock report queries (from Django view)
    MIN_STOCK_DATE = timezone.make_aware(datetime(2025, 7, 27))
    
    bdt = pytz.timezone('Asia/Dhaka')
    now_bdt = datetime.now(bdt)
    
    # --- Test Case 1: Today's Report ---
    today_start = timezone.make_aware(datetime.combine(now_bdt.date(), time.min))
    today_end = now_bdt
    today_effective_start = max(today_start, MIN_STOCK_DATE)
    
    # --- Test Case 2: Specific Day (28/07/2025) ---
    specific_day = date(2025, 7, 28)
    specific_day_start = timezone.make_aware(datetime.combine(specific_day, time.min))
    specific_day_end = timezone.make_aware(datetime.combine(specific_day, time.max))
    specific_day_effective_start = max(specific_day_start, MIN_STOCK_DATE)
    
    # --- Test Case 3: Date Range (28/07/2025 to Today) ---
    range_start = timezone.make_aware(datetime.combine(specific_day, time.min))
    range_end = now_bdt
    range_effective_start = max(range_start, MIN_STOCK_DATE)
    
    # Test products
    product_ids = [
        "24375821-1510-49b2-8cf5-81a140f9c107",  # SBS Sprayable Adhesive -SB601
        "d46d0abc-daeb-4418-818a-ab37277dc344",  # Aerosol Spray Paint
        "2017459a-ea3d-49f4-bd43-311c7baf859d",  # Neoprene SR Adhesive 15 Liter
    ]
    
    print("=== DJANGO STOCK VALIDATION ===")
    print(f"MIN_STOCK_DATE: {MIN_STOCK_DATE}")
    print(f"Now (BD Time): {now_bdt}")
    
    for product_id in product_ids:
        try:
            product = Product.objects.get(pk=product_id)
            print(f"\n--- Product: {product.name} ({product.sku}) ---")
            
            # Test scenarios
            scenarios = [
                ("Today", today_effective_start, today_end),
                ("28/07/2025", specific_day_effective_start, specific_day_end),
                ("28/07/2025 to Today", range_effective_start, range_end)
            ]
            
            for scenario_name, effective_start_dt, end_dt in scenarios:
                print(f"\n* {scenario_name} Report:")
                print(f"  Effective Start: {effective_start_dt}")
                print(f"  End: {end_dt}")
                
                # Opening Stock Calculation (matching Django view logic)
                last_transaction_before_start = StockTransaction.objects.filter(
                    product=product,
                    transaction_date__lt=effective_start_dt,
                    transaction_date__gte=MIN_STOCK_DATE
                ).order_by('-transaction_date').first()

                if last_transaction_before_start:
                    opening_stock = last_transaction_before_start.current_stock
                else:
                    # Check the first transaction in range for previous_stock
                    first_transaction_in_range = StockTransaction.objects.filter(
                        product=product,
                        transaction_date__gte=effective_start_dt
                    ).order_by('transaction_date').first()
                    
                    if first_transaction_in_range:
                        opening_stock = first_transaction_in_range.previous_stock
                    else:
                        # Final fallback: use product's current stock_quantity from database
                        opening_stock = product.stock_quantity or 0
                
                # Received and Issued Quantities
                transactions_in_range = StockTransaction.objects.filter(
                    product=product,
                    transaction_date__gte=effective_start_dt,
                    transaction_date__lte=end_dt
                ).aggregate(
                    received=Coalesce(Sum('quantity', filter=Q(transaction_type__in=['IN', 'RET'])), 0, output_field=IntegerField()),
                    issued=Coalesce(Sum('quantity', filter=Q(transaction_type='OUT')), 0, output_field=IntegerField()),
                )
                
                received_qty = transactions_in_range['received']
                issued_qty = transactions_in_range['issued']
                
                # Closing Stock Calculation
                last_transaction = StockTransaction.objects.filter(
                    product=product,
                    transaction_date__lte=end_dt,
                    transaction_date__gte=MIN_STOCK_DATE,
                ).order_by('-transaction_date').first()

                if last_transaction:
                    closing_stock = last_transaction.current_stock
                else:
                    # Look for any transaction before MIN_STOCK_DATE
                    last_transaction_before_min = StockTransaction.objects.filter(
                        product=product,
                        transaction_date__lt=MIN_STOCK_DATE
                    ).order_by('-transaction_date').first()
                    
                    if last_transaction_before_min:
                        closing_stock = last_transaction_before_min.current_stock
                    else:
                        # Final fallback: use product's current stock_quantity from database
                        closing_stock = product.stock_quantity or 0
                
                # Additional validation: Manual calculation
                manual_closing = opening_stock + received_qty - issued_qty
                
                print(f"  Opening: {opening_stock}")
                print(f"  Received: {received_qty}")
                print(f"  Issued: {issued_qty}")
                print(f"  Closing (from DB): {closing_stock}")
                print(f"  Closing (calculated): {manual_closing}")
                print(f"  Match: {'✓' if closing_stock == manual_closing else '✗'}")
                
                # Show recent transactions for debugging
                recent_transactions = StockTransaction.objects.filter(
                    product=product,
                    transaction_date__gte=effective_start_dt,
                    transaction_date__lte=end_dt
                ).order_by('-transaction_date')[:5]
                
                if recent_transactions.exists():
                    print(f"  Recent transactions in range:")
                    for t in recent_transactions:
                        print(f"    {t.transaction_date}: {t.transaction_type} {t.quantity} (Stock: {t.current_stock})")
                        
        except Product.DoesNotExist:
            print(f"Product {product_id} not found")

if __name__ == "__main__":
    validate_stock_calculation()
