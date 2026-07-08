"""Migration script to add jalali_time column to backups table."""

import sqlite3
import os

def migrate():
    """Add jalali_time column to backups table if it doesn't exist."""
    db_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'hesab.db')
    
    if not os.path.exists(db_path):
        print(f"Database not found at {db_path}")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check if column already exists
        cursor.execute("PRAGMA table_info(backups)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'jalali_time' not in columns:
            cursor.execute("ALTER TABLE backups ADD COLUMN jalali_time VARCHAR(20)")
            conn.commit()
            print("✅ Added jalali_time column to backups table")
        else:
            print("ℹ️ jalali_time column already exists")
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()
