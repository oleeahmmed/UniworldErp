
import sqlite3
from datetime import datetime, time, date
import pytz

def get_stock_data(product_id, start_dt, end_dt):
    try:
        conn = sqlite3.connect('db.sqlite3')
        cursor = conn.cursor()
        
        # MIN_STOCK_DATE constraint from Django view (convert to UTC for database)
        min_stock_date = datetime(2025, 7, 27, tzinfo=pytz.UTC)
        
        print(f"  DEBUG: Checking product {product_id}")
        print(f"  DEBUG: start_dt_utc: {start_dt.astimezone(pytz.UTC)}")
        print(f"  DEBUG: end_dt_utc: {end_dt.astimezone(pytz.UTC)}")
        print(f"  DEBUG: min_stock_date: {min_stock_date}")
        
        # Convert all dates to UTC and format as strings (without timezone info) for SQLite
        start_dt_utc = start_dt.astimezone(pytz.UTC)
        end_dt_utc = end_dt.astimezone(pytz.UTC)
        effective_start_dt = max(start_dt_utc, min_stock_date)
        
        # Format dates as strings for SQLite (Django stores them as datetime strings)
        effective_start_str = effective_start_dt.strftime('%Y-%m-%d %H:%M:%S.%f')
        end_dt_str = end_dt_utc.strftime('%Y-%m-%d %H:%M:%S.%f')
        min_stock_str = min_stock_date.strftime('%Y-%m-%d %H:%M:%S.%f')

        # Opening Stock Calculation (uses start_dt)
        cursor.execute('''
            SELECT current_stock
            FROM uniworlderp_stocktransaction
            WHERE product_id = ? AND transaction_date < ? AND transaction_date >= ?
            ORDER BY transaction_date DESC
            LIMIT 1
        ''', (product_id, start_dt_utc.strftime('%Y-%m-%d %H:%M:%S.%f'), min_stock_str))
        opening_stock_row = cursor.fetchone()
        opening_stock = opening_stock_row[0] if opening_stock_row else 0

        # Received and Issued Quantities (uses effective_start_dt)
        cursor.execute('''
            SELECT 
                SUM(CASE WHEN transaction_type IN ('IN', 'RET') THEN quantity ELSE 0 END) as received,
                SUM(CASE WHEN transaction_type = 'OUT' THEN quantity ELSE 0 END) as issued
            FROM uniworlderp_stocktransaction
            WHERE product_id = ? AND transaction_date >= ? AND transaction_date <= ?
        ''', (product_id, effective_start_str, end_dt_str))
        transactions_row = cursor.fetchone()
        received_qty = transactions_row[0] or 0
        issued_qty = transactions_row[1] or 0

        # Closing Stock Calculation (uses min_stock_date constraint)
        cursor.execute('''
            SELECT current_stock
            FROM uniworlderp_stocktransaction
            WHERE product_id = ? AND transaction_date <= ? AND transaction_date >= ?
            ORDER BY transaction_date DESC
            LIMIT 1
        ''', (product_id, end_dt_str, min_stock_str))
        closing_stock_row = cursor.fetchone()
        closing_stock = closing_stock_row[0] if closing_stock_row else 0
        
        # Debug information
        cursor.execute('''
            SELECT COUNT(*) 
            FROM uniworlderp_stocktransaction
            WHERE product_id = ? AND transaction_date >= ? AND transaction_date <= ?
        ''', (product_id, effective_start_str, end_dt_str))
        transaction_count = cursor.fetchone()[0]
        
        return {
            "opening_stock": opening_stock,
            "received_qty": received_qty,
            "issued_qty": issued_qty,
            "closing_stock": closing_stock,
            "effective_start_dt": effective_start_str,
            "end_dt": end_dt_str,
            "transaction_count": transaction_count
        }
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return None
    finally:
        if conn:
            conn.close()

def main():
    bdt = pytz.timezone('Asia/Dhaka')
    now_bdt = datetime.now(bdt)
    
    # --- Test Case 1: Today's Report ---
    today_start = bdt.localize(datetime.combine(now_bdt.date(), time.min))
    today_end = now_bdt
    
    # --- Test Case 2: Specific Day (28/07/2025) ---
    specific_day = date(2025, 7, 28)
    specific_day_start = bdt.localize(datetime.combine(specific_day, time.min))
    specific_day_end = bdt.localize(datetime.combine(specific_day, time.max))
    
    # --- Test Case 3: Date Range (28/07/2025 to Today) ---
    range_start = bdt.localize(datetime.combine(specific_day, time.min))
    range_end = now_bdt

    # Actual product IDs from database
    product_ids = [
        "24375821-1510-49b2-8cf5-81a140f9c107",  # SBS Sprayable Adhesive -SB601
        "d46d0abc-daeb-4418-818a-ab37277dc344",  # Aerosol Spray Paint
        "2017459a-ea3d-49f4-bd43-311c7baf859d",  # Neoprene SR Adhesive 15 Liter
    ]

    print("--- Stock Validation Script ---")
    for product_id in product_ids:
        print(f"\n--- Product ID: {product_id} ---")
        
        # Today's validation
        print("\n- Today's Report:")
        today_data = get_stock_data(product_id, today_start, today_end)
        if today_data:
            print(f"  Opening: {today_data['opening_stock']}, Received: {today_data['received_qty']}, Issued: {today_data['issued_qty']}, Closing: {today_data['closing_stock']}")

        # Specific day validation
        print("\n- Specific Day (28/07/2025) Report:")
        specific_day_data = get_stock_data(product_id, specific_day_start, specific_day_end)
        if specific_day_data:
            print(f"  Opening: {specific_day_data['opening_stock']}, Received: {specific_day_data['received_qty']}, Issued: {specific_day_data['issued_qty']}, Closing: {specific_day_data['closing_stock']}")

        # Date range validation
        print("\n- Date Range (28/07/2025 to Today) Report:")
        range_data = get_stock_data(product_id, range_start, range_end)
        if range_data:
            print(f"  Opening: {range_data['opening_stock']}, Received: {range_data['received_qty']}, Issued: {range_data['issued_qty']}, Closing: {range_data['closing_stock']}")

if __name__ == "__main__":
    main()

