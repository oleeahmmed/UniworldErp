"""
Django management command to fix StockTransaction records from March 7, 2026
where previous_stock and current_stock are incorrectly showing 0.

Usage:
    # Preview changes (safe, nothing is saved):
    python manage.py fix_stock_history --dry-run

    # Apply the fix for real:
    python manage.py fix_stock_history
"""

from django.core.management.base import BaseCommand
from django.db import transaction as db_transaction
from django.utils import timezone
from datetime import datetime

from uniworlderp.models import StockTransaction, Product


FIX_FROM_DATE = timezone.make_aware(datetime(2026, 3, 7, 0, 0, 0))


class Command(BaseCommand):
    help = 'Fixes previous_stock and current_stock for transactions from March 7, 2026 onwards'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Preview what would change without saving anything',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']

        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN — no changes will be saved.\n'))
        else:
            self.stdout.write(self.style.WARNING('LIVE MODE — changes WILL be saved to the database.\n'))

        # Find all products that have broken transactions from March 7 onwards
        affected_product_ids = (
            StockTransaction.objects
            .filter(transaction_date__gte=FIX_FROM_DATE)
            .values_list('product_id', flat=True)
            .distinct()
        )

        if not affected_product_ids:
            self.stdout.write(self.style.SUCCESS('No transactions found from March 7 onwards. Nothing to fix.'))
            return

        self.stdout.write(f'Found {len(affected_product_ids)} affected product(s).\n')
        self.stdout.write('=' * 70)

        total_fixed = 0

        try:
            with db_transaction.atomic():
                for product_id in affected_product_ids:
                    product = Product.objects.get(pk=product_id)
                    self.stdout.write(f'\nProduct: {self.style.SUCCESS(product.name)}')

                    # Step 1: Get the baseline stock from the last GOOD transaction
                    # (the last transaction recorded BEFORE March 7 which had correct values)
                    last_good = (
                        StockTransaction.objects
                        .filter(product_id=product_id, transaction_date__lt=FIX_FROM_DATE)
                        .order_by('-transaction_date')
                        .first()
                    )

                    if last_good:
                        baseline_stock = last_good.current_stock
                        self.stdout.write(
                            f'  Baseline from last good transaction '
                            f'({last_good.transaction_date.strftime("%Y-%m-%d %H:%M")}): '
                            f'stock = {baseline_stock}'
                        )
                    else:
                        # No prior StockTransaction exists for this product.
                        # Because the bug prevented stock updates, product.stock_quantity
                        # still holds the correct pre-March-7 value — use that as baseline.
                        baseline_stock = product.stock_quantity
                        self.stdout.write(
                            f'  No prior transaction found — using current '
                            f'product.stock_quantity ({baseline_stock}) as baseline.'
                        )

                    # Step 2: Get all broken transactions in chronological order
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
                            curr = max(0, running_stock - txn.quantity)
                        elif txn.transaction_type == 'ADJ':
                            curr = txn.quantity
                        elif txn.transaction_type == 'RET':
                            curr = running_stock + txn.quantity
                        else:
                            curr = running_stock

                        self.stdout.write(
                            f'  [{txn.transaction_date.strftime("%m-%d %H:%M")}] '
                            f'{txn.get_transaction_type_display():10s} '
                            f'qty={txn.quantity:<5d} '
                            f'prev_stock: {txn.previous_stock} -> {prev}  |  '
                            f'curr_stock: {txn.current_stock} -> {curr}  '
                            f'ref={txn.reference or "-"}'
                        )

                        if not dry_run:
                            # Use .update() to bypass StockTransaction.save()
                            # so we don't trigger stock changes again
                            StockTransaction.objects.filter(pk=txn.pk).update(
                                previous_stock=prev,
                                current_stock=curr,
                            )

                        running_stock = curr
                        total_fixed += 1

                    # Step 3: Fix product.stock_quantity to the correct final value
                    self.stdout.write(
                        f'  Product stock_quantity: '
                        f'{product.stock_quantity} -> {self.style.SUCCESS(str(running_stock))}'
                    )
                    if not dry_run:
                        Product.objects.filter(pk=product_id).update(stock_quantity=running_stock)

                if dry_run:
                    # Roll back everything — we don't want to save in dry run
                    db_transaction.set_rollback(True)

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'\nError: {e}'))
            raise

        self.stdout.write('\n' + '=' * 70)
        if dry_run:
            self.stdout.write(self.style.WARNING(
                f'DRY RUN complete. {total_fixed} transaction(s) would be fixed. '
                f'Run without --dry-run to apply.'
            ))
        else:
            self.stdout.write(self.style.SUCCESS(
                f'Done! Fixed {total_fixed} transaction record(s).'
            ))
