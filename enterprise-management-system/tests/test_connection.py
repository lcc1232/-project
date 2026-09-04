# test_connection.py
import psycopg2

try:
    conn = psycopg2.connect(
        host="localhost",
        port=5433,
        database="enterprise_management",
        user="postgres",
        password="123456"  # 改成你的实际密码
    )
    print("✓ 数据库连接成功！")
    conn.close()
except Exception as e:
    print(f"✗ 数据库连接失败：{e}")