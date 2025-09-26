# db_connection.py
import mysql.connector
import os
from flask import Flask
from flask_cors import CORS


app = Flask(__name__)
CORS(app)

def get_connection():
    DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
    DB_PORT = int(os.getenv("DB_PORT", 3306))
    DB_USER = os.getenv("DB_USER", "Muskan_Sheikh")
    DB_PASS = os.getenv("DB_PASS", "Sheikh@123")
    DB_NAME = os.getenv("DB_NAME", "synthetic_data_db")

    conn = mysql.connector.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASS,
        database=DB_NAME,
        autocommit=False
    )
    return conn

def init_db():
    """Create DB tables if needed (simple)."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS uploads (
      id INT AUTO_INCREMENT PRIMARY KEY,
      filename VARCHAR(255) NOT NULL,
      uploaded_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )""")
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS synthetic_dataset (
      id INT AUTO_INCREMENT PRIMARY KEY,
      pregnancies FLOAT,
      glucose FLOAT,
      blood_pressure FLOAT,
      skin_thickness FLOAT,
      insulin FLOAT,
      bmi FLOAT,
      diabetes_pedigree_function FLOAT,
      age FLOAT,
      outcome VARCHAR(32)
    )""")
    conn.commit()
    cursor.close()
    conn.close()
