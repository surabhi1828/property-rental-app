import mysql.connector
from mysql.connector import Error
import os

class Database:
    def __init__(self):
        self.host = os.getenv('DB_HOST', 'localhost')
        self.user = os.getenv('DB_USER', 'root')
        self.password = os.getenv('DB_PASSWORD', 'password') 
        self.database = os.getenv('DB_NAME', 'rental_db')
        self.connection = None
    
    
    def connect(self):
        try:
            self.connection = mysql.connector.connect(
                host=self.host,
                user=self.user,
                password=self.password,
                database=self.database
            )
            if self.connection.is_connected():
                return True
        except Error as e:
            print(f"Error connecting to MySQL: {e}")
            return False
    
    def disconnect(self):
        if self.connection and self.connection.is_connected():
            self.connection.close()
    
    def execute_query(self, query, params=None, fetch=True):
        """Execute a query and optionally fetch results"""
        cursor = None
        try:
            cursor = self.connection.cursor(dictionary=True)
            cursor.execute(query, params or ())
            
            if fetch:
                result = cursor.fetchall()
                return {'success': True, 'data': result, 'messages': []}
            else:
                self.connection.commit()
                # Get any messages from triggers/procedures
                messages = []
                try:
                    cursor.execute("SHOW WARNINGS")
                    warnings = cursor.fetchall()
                    for warning in warnings:
                        messages.append(warning.get('Message', ''))
                except:
                    pass
                
                return {
                    'success': True, 
                    'affected_rows': cursor.rowcount,
                    'last_id': cursor.lastrowid,
                    'messages': messages
                }
        except Error as e:
            return {'success': False, 'error': str(e), 'messages': []}
        finally:
            if cursor:
                cursor.close()
    
    def call_procedure(self, proc_name, params=None):
        """Call a stored procedure"""
        cursor = None
        try:
            cursor = self.connection.cursor(dictionary=True)
            cursor.callproc(proc_name, params or ())
            
            # Fetch results if any
            results = []
            for result in cursor.stored_results():
                results.extend(result.fetchall())
            
            self.connection.commit()
            return {'success': True, 'data': results, 'messages': []}
        except Error as e:
            return {'success': False, 'error': str(e), 'messages': []}
        finally:
            if cursor:
                cursor.close()
