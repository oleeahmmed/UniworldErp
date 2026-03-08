"""
fix_stock_history.py
====================
Fixes StockTransaction records from March 7, 2026 onwards where
previous_stock and current_stock are incorrectly showing 0.

Run from the project root:
    python fix_stock_history.py

Set DRY_RUN = True to preview changes without touching the database.
"""

import os
import sys
import django
from datetime import datetime

# ── Django setup ──────────────────────────────────────────────────────────────
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')
django.setup()

from django.db import transaction as db_transaction
from django.utils import timezone
from uniworlderp.models import StockTransaction, Product

# ── Config ────────────────────────────────────────────────────────────────────
# Records from this date onwards will be fixed
FIX_FROM_DATE = datetime(2026, 3, 7, 0, 0, 0)
FIX_FROM_DATE = timezone.make_aware(FIX_FROM_DATE)

# Set to True to just print what would change, without saving anything
DRY_RUN = False
# ─────────────────────────────────────────────────────────────────────────────


def recalculate_stock():
    # Find all products that have transactions from March 7 onwards
    affected_product_ids = (
        StockTransaction.objects
        .filter(transaction_date__gte=FIX_FROM_DATE)
        .values_list('product_id', flat=True)
        .distinct()
    )

    if not affected_product_ids:
        print("No transactions found from March 7 onwards. Nothing to fix.")
        return

    print(f"Found {len(affected_product_ids)} affected product(s).\n")
    print("=" * 70)

    total_fixed = 0

    with db_transaction.atomic():
        for product_id in affected_product_ids:
            product = Product.objects.get(pk=product_id)

            # ── Step 1: Find the baseline stock ──────────────────────────────
            # The last known-good transaction BEFORE March 7
            last_good = (
                StockTransaction.objects
                .filter(product_id=product_id, transaction_date__lt=FIX_FROM_DATE)
                .order_by('-transaction_date')
                .first()
            )

            if last_good:
                baseline_stock = last_good.current_stock
                print(f"Product: {product.name}")
                print(f"  Baseline from last good transaction "
                      f"({last_good.transaction_date.strftime('%Y-%m-%d %H:%M')}): "
                      f"stock = {baseline_stock}")
            else:
                baseline_stock = 0
                print(f"Product: {product.name}")
                print(f"  No prior transaction found, starting from 0.")

            # ── Step 2: Get all broken transactions in chronological order ───
            broken_txns = (
                StockTransaction.objects
                .filter(product_id=product_id, transaction_date__gte=FIX_FROM_DATE)
                .order_by('transaction_date')
            )

            running_stock = baseline_stock

            for txn in broken_txns:
                prev = running_stock

                if txn.transaction_type == 'IN':
                    curr = running_stock + txn.quantity
                elif txn.transaction_type == 'OUT':
                    curr = running_stock - txn.quantity
                elif txn.transaction_type == 'ADJ':
                    curr = txn.quantity
                elif txn.transaction_type == 'RET':
                    curr = running_stock + txn.quantity
                else:
                    curr = running_stock  # unknown type, don't change

                print(f"  [{txn.transaction_date.strftime('%m-%d %H:%M')}] "
                      f"{txn.get_transaction_type_display():10s} "
                      f"qty={txn.quantity:5d}  "
                      f"prev: {txn.previous_stock} → {prev}  "
                      f"curr: {txn.current_stock} → {curr}  "
                      f"ref={txn.reference or '-'}")

                if not DRY_RUN:
                    # Use update() so it bypasses StockTransaction.save()
                    # (we don't want to trigger stock updates again)
                    StockTransaction.objects.filter(pk=txn.pk).update(
                        previous_stock=prev,
                        current_stock=curr,
                    )

                running_stock = curr
                total_fixed += 1

            # ── Step 3: Update product's stock_quantity to the final value ───
            print(f"  Product stock_quantity: {product.stock_quantity} → {running_stock}")
            if not DRY_RUN:
                Product.objects.filter(pk=product_id).update(stock_quantity=running_stock)

            print()

        if DRY_RUN:
            db_transaction.set_rollback(True)  # rollback everything in dry run
            print("=" * 70)
            print("DRY RUN — no changes were saved. Set DRY_RUN=False to apply.")
        else:
            print("=" * 70)
            print(f"✅  Done! Fixed {total_fixed} transaction record(s).")


if __name__ == '__main__':
    if '--dry-run' in sys.argv:
        DRY_RUN = True
        print("Running in DRY RUN mode (no changes will be saved)...\n")
    else:
        print("Running in LIVE mode (changes WILL be saved to the database)...\n")

    recalculate_stock()
