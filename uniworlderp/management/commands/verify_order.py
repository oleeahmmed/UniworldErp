from django.core.management.base import BaseCommand
from uniworlderp.models import SalesOrder, SalesOrderItem, ReturnSalesItem
from decimal import Decimal


class Command(BaseCommand):
    help = 'Verify calculation for a specific sales order'

    def add_arguments(self, parser):
        parser.add_argument('order_id', type=int, help='Sales Order ID to verify')

    def handle(self, *args, **options):
        order_id = options['order_id']
        
        try:
            sales_order = SalesOrder.objects.get(id=order_id)
            self.stdout.write("=" * 80)
            self.stdout.write(f"SALES ORDER #{sales_order.id}")
            self.stdout.write("=" * 80)
            self.stdout.write(f"Customer: {sales_order.customer.name}")
            self.stdout.write(f"Order Date: {sales_order.order_date}")
            self.stdout.write(f"Sales Employee: {sales_order.sales_employee.full_name if sales_order.sales_employee else 'N/A'}")
            self.stdout.write(f"Order-Level Discount: {sales_order.discount}")
            self.stdout.write(f"Shipping: {sales_order.shipping}")
            self.stdout.write(f"Total Amount: {sales_order.total_amount}")
            self.stdout.write("")
            
            # Get all items in this order
            items = SalesOrderItem.objects.filter(sales_order=sales_order)
            
            self.stdout.write("=" * 80)
            self.stdout.write("SALES ORDER ITEMS")
            self.stdout.write("=" * 80)
            
            order_subtotal = Decimal('0.00')
            
            for item in items:
                self.stdout.write(f"\nProduct: {item.product.name}")
                self.stdout.write(f"  SKU: {item.product.sku}")
                self.stdout.write(f"  Unit Price (at sale): {item.unit_price}")
                self.stdout.write(f"  Quantity: {item.quantity}")
                self.stdout.write(f"  Unit Discount: {item.Unit_discount}")
                self.stdout.write(f"  Total Discount: {item.total_discount}")
                self.stdout.write(f"  Item Total (after item discount): {item.total}")
                
                order_subtotal += item.total
            
            self.stdout.write(f"\nOrder Subtotal (sum of all item.total): {order_subtotal}")
            self.stdout.write(f"Order-Level Discount: {sales_order.discount}")
            
            # Process each item
            for item in items:
                self.stdout.write("\n" + "=" * 80)
                self.stdout.write(f"DETAILED CALCULATION FOR: {item.product.name}")
                self.stdout.write("=" * 80)
                
                # Step 1: Gross Amount
                gross_amount = item.quantity * item.unit_price
                self.stdout.write(f"\n1. Gross Amount = quantity × unit_price")
                self.stdout.write(f"   = {item.quantity} × {item.unit_price}")
                self.stdout.write(f"   = {gross_amount}")
                
                # Step 2: Item-level discount
                self.stdout.write(f"\n2. Item-Level Discount = {item.total_discount}")
                self.stdout.write(f"   Amount after item discount = {item.total}")
                
                # Step 3: Proportional order-level discount
                if order_subtotal > 0 and sales_order.discount > 0:
                    item_discount_share = (item.total / order_subtotal) * sales_order.discount
                    self.stdout.write(f"\n3. Proportional Order-Level Discount:")
                    self.stdout.write(f"   = (item.total / order_subtotal) × order_discount")
                    self.stdout.write(f"   = ({item.total} / {order_subtotal}) × {sales_order.discount}")
                    self.stdout.write(f"   = {item_discount_share}")
                    
                    discounted_total = item.total - item_discount_share
                    self.stdout.write(f"\n4. Discounted Total (after both discounts):")
                    self.stdout.write(f"   = item.total - proportional_discount")
                    self.stdout.write(f"   = {item.total} - {item_discount_share}")
                    self.stdout.write(f"   = {discounted_total}")
                else:
                    discounted_total = item.total
                    item_discount_share = Decimal('0.00')
                    self.stdout.write(f"\n3. No order-level discount to distribute")
                    self.stdout.write(f"4. Discounted Total = {discounted_total}")
                
                # Step 4: Returns
                returns = ReturnSalesItem.objects.filter(sales_order_item=item)
                
                if returns.exists():
                    self.stdout.write("\n" + "-" * 40)
                    self.stdout.write("RETURNS FOR THIS ITEM")
                    self.stdout.write("-" * 40)
                    
                    total_returned_qty = 0
                    total_returned_amount = Decimal('0.00')
                    
                    for ret in returns:
                        self.stdout.write(f"\nReturn #{ret.return_sales.id}")
                        self.stdout.write(f"  Return Date: {ret.return_sales.return_date}")
                        self.stdout.write(f"  Quantity Returned: {ret.quantity}")
                        self.stdout.write(f"  Unit Price: {ret.unit_price}")
                        self.stdout.write(f"  Return Amount: {ret.total}")
                        
                        total_returned_qty += ret.quantity
                        total_returned_amount += ret.total
                    
                    self.stdout.write(f"\nTotal Returned Qty: {total_returned_qty}")
                    self.stdout.write(f"Total Returned Amount: {total_returned_amount}")
                    
                    # Step 5: Net calculations
                    net_qty = item.quantity - total_returned_qty
                    net_amount = discounted_total - total_returned_amount
                    
                    self.stdout.write("\n" + "-" * 40)
                    self.stdout.write("FINAL CALCULATIONS")
                    self.stdout.write("-" * 40)
                    self.stdout.write(f"\nGross Sold: {item.quantity}")
                    self.stdout.write(f"Qty Returned: {total_returned_qty}")
                    self.stdout.write(f"Net Qty: {net_qty}")
                    self.stdout.write(f"\nGross Amount: {gross_amount}")
                    self.stdout.write(f"Item Discount: {item.total_discount}")
                    self.stdout.write(f"Proportional Order Discount: {item_discount_share}")
                    self.stdout.write(f"Return Amount: {total_returned_amount}")
                    self.stdout.write(f"Net Amount: {net_amount}")
                    
                    # Show the breakdown
                    self.stdout.write("\n" + "-" * 40)
                    self.stdout.write("AMOUNT FLOW BREAKDOWN")
                    self.stdout.write("-" * 40)
                    self.stdout.write(f"Gross Amount:                    {gross_amount:>10.2f}")
                    self.stdout.write(f"  - Item Discount:               {item.total_discount:>10.2f}")
                    self.stdout.write(f"  = After Item Discount:         {item.total:>10.2f}")
                    self.stdout.write(f"  - Proportional Order Discount: {item_discount_share:>10.2f}")
                    self.stdout.write(f"  = Discounted Total:            {discounted_total:>10.2f}")
                    self.stdout.write(f"  - Return Amount:               {total_returned_amount:>10.2f}")
                    self.stdout.write(f"  = Net Amount:                  {net_amount:>10.2f}")
                    
                else:
                    self.stdout.write("\nNo returns found for this item")
                    self.stdout.write(f"Net Amount = Discounted Total = {discounted_total}")

        except SalesOrder.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"Sales Order #{order_id} not found in database"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error: {e}"))
            import traceback
            traceback.print_exc()
