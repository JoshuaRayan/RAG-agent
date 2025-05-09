import pymysql
import cryptography
conn = pymysql.connect(
    host='localhost',
    user='root',
    password='YourNewPassword123',
    database='federal_registry'
)
print("Connected successfully")
