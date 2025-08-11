import sqlite3
import os

def check_database_tables(db_path, db_name):
    if os.path.exists(db_path):
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        
        print(f"\n=== {db_name} ===")
        print(f"Database: {db_path}")
        print(f"Tables found: {len(tables)}")
        
        for table in tables:
            table_name = table[0]
            print(f"- {table_name}")
            
            # Check if it's a license-related table
            if 'license' in table_name.lower() or 'subscription' in table_name.lower() or 'trial' in table_name.lower():
                print(f"  ✅ LICENSE TABLE FOUND!")
                # Get row count
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                count = cursor.fetchone()[0]
                print(f"  Rows: {count}")
        
        conn.close()
        return len(tables)
    else:
        print(f"\n❌ {db_name}: NOT FOUND at {db_path}")
        return 0

# Check main workspace database
main_db = r"c:\Users\PRASHANT\Desktop\Classroom\timetable.db"
check_database_tables(main_db, "Main Workspace Database")

# Check clientdeploy database  
client_db = r"c:\Users\PRASHANT\Desktop\Classroom\clientdeploy\timetable.db"
check_database_tables(client_db, "ClientDeploy Database")

# Check if we need to copy the updated database
print("\n" + "="*50)
print("DATABASE UPDATE ANALYSIS")
print("="*50)

if os.path.exists(main_db) and os.path.exists(client_db):
    main_size = os.path.getsize(main_db)
    client_size = os.path.getsize(client_db)
    
    print(f"Main workspace DB size: {main_size:,} bytes")
    print(f"ClientDeploy DB size: {client_size:,} bytes")
    
    if main_size != client_size:
        print("⚠️  DATABASE SIZES DIFFERENT - UPDATE NEEDED!")
    else:
        print("✅ Database sizes match")
    
    # Check modification times
    main_mtime = os.path.getmtime(main_db)
    client_mtime = os.path.getmtime(client_db)
    
    if main_mtime > client_mtime:
        print("⚠️  Main database is newer - UPDATE NEEDED!")
    else:
        print("✅ ClientDeploy database is up to date")
