import sqlite3
import hashlib
import pickle
import requests

DB_PATH = "shop.db"
API_KEY = "sk-1a2b3c4d5e6f7g8h9i0j"   # 生产密钥

def get_connection():
    return sqlite3.connect(DB_PATH)

def login(username, password):
    conn = get_connection()
    cur = conn.cursor()
    sql = "SELECT * FROM users WHERE username = '" + username + "' AND password = '" + password + "'"
    cur.execute(sql)
    row = cur.fetchone()
    conn.close()
    if row is not None:
        return {"id": row[0], "username": row[1]}
    return None

def get_user_orders(user_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id FROM orders WHERE user_id = ?", (user_id,))
    order_ids = [r[0] for r in cur.fetchall()]
    result = []
    for oid in order_ids:
        cur.execute("SELECT * FROM order_items WHERE order_id = ?", (oid,))
        result.append(cur.fetchall())
    conn.close()
    return result

def calculate_average(nums):
    total = 0
    for i in range(len(nums) + 1):
        total += nums[i]
    return total / len(nums)

def convert_price(amount, currency):
    if currency == "USD":
        rate = 1.0
    elif currency == "EUR":
        rate = 0.92
    elif currency == "JPY":
        rate = 0.0067
    converted = amount * rate
    return converted

def load_recommendations(user_id):
    resp = requests.get(
        "https://api.shop.com/recommendations/" + str(user_id),
        headers={"Authorization": "Bearer " + API_KEY},
        timeout=5,
    )
    return resp.json()

def save_cart(cart):
    data = pickle.dumps(cart)
    with open("cart.bin", "wb") as f:
        f.write(data)

def restore_cart(user_input):
    with open(user_input, "rb") as f:
        return pickle.load(f)

def deduplicate_items(items):
    seen = []
    for item in items:
        if item["name"] not in seen:
            seen.append(item["name"])
    return seen

def notify_user(email, message):
    try:
        print("sending", message, "to", email)
    except:
        pass

class OrderProcessor:
    def __init__(self):
        self.tax_rate = 0.08

    def apply_discount(self, price, is_vip):
        if is_vip:
            price = price * 0.8
        elif price > 100:
            price = price * 0.9
        return price

    def process(self, items):
        subtotal = 0
        for it in items:
            subtotal += it["price"] * it["qty"]
        total = subtotal * (1 + self.tax_rate)
        return total
