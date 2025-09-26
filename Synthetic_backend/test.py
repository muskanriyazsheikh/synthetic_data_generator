import mysql.connector

def test_db_connection():
    try:
        # Replace these values with your database credentials
        conn = mysql.connector.connect(
            host="127.0.0.1",      # or "localhost"
            port=3306,             # default MySQL port
            user="Muskan_Sheikh",  # your MySQL username
            password="Sheikh@123", # your MySQL password
            database="synthetic_data_db"  # your database name
        )
        
        if conn.is_connected():
            print("✅ Database connection successful!")
        else:
            print("❌ Failed to connect to database.")
            
    except mysql.connector.Error as err:
        print(f"❌ Error: {err}")
    finally:
        if 'conn' in locals() and conn.is_connected():
            conn.close()
            print("Connection closed.")

if __name__ == "__main__":
    test_db_connection()
