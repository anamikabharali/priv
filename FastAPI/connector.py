import mysql.connector
 
# Set up your database connection details
config = {
    'user': 'bigdata',
    'password': '#8r5BB9LBp&Nk-dN',
    'host': 'causal-prism-404015:us-east1:bigdata',  # Use the Cloud SQL instance connection name    'database': 'bigdata',
    'unix_socket': '/cloudsql/causal-prism-404015:us-east1:bigdata',
}
 
# Connect to the database
connection = mysql.connector.connect(**config)
 
try:
    # Create a cursor
    cursor = connection.cursor()
 
    # Execute SQL queries
    cursor.execute("SELECT * FROM your_table_name")
 
    # Fetch and print results
    results = cursor.fetchall()
    for row in results:
        print(row)
 
finally:
    # Close the cursor and connection
    cursor.close()
    connection.close()