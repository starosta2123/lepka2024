import sqlite3

def init_db():
    conn = sqlite3.connect('orders.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            order_number INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            phone TEXT,
            comment TEXT,
            chat_id INTEGER,
            notified INTEGER DEFAULT 0,
            status TEXT DEFAULT 'new'
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS order_photos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_number INTEGER,
            photo_id TEXT,
            FOREIGN KEY(order_number) REFERENCES orders(order_number)
        )
    ''')
    conn.commit()
    conn.close()

def add_order(name, phone, comment, chat_id):
    conn = sqlite3.connect('orders.db')
    c = conn.cursor()
    c.execute('''
        INSERT INTO orders (name, phone, comment, chat_id) VALUES (?, ?, ?, ?)
    ''', (name, phone, comment, chat_id))
    order_id = c.lastrowid
    conn.commit()
    conn.close()
    return order_id

def get_last_orders(limit=15):
    conn = sqlite3.connect('orders.db')
    c = conn.cursor()
    c.execute('''
        SELECT * FROM orders ORDER BY order_number DESC LIMIT ?
    ''', (limit,))
    orders = c.fetchall()
    conn.close()
    return orders

def mark_as_notified(chat_id):
    conn = sqlite3.connect('orders.db')
    c = conn.cursor()
    c.execute('''
        UPDATE orders SET notified = 1 WHERE chat_id = ?
    ''', (chat_id,))
    conn.commit()
    conn.close()

def get_user_by_chat_id(chat_id):
    conn = sqlite3.connect('orders.db')
    c = conn.cursor()
    c.execute('SELECT * FROM orders WHERE chat_id = ?', (chat_id,))
    user = c.fetchone()
    conn.close()
    return user

def get_new_orders():
    conn = sqlite3.connect('orders.db')
    c = conn.cursor()
    c.execute('SELECT * FROM orders WHERE notified = 0 AND status = "new" ORDER BY order_number DESC')
    orders = c.fetchall()
    conn.close()
    return orders

def update_order_status(order_number, status):
    conn = sqlite3.connect('orders.db')
    c = conn.cursor()
    c.execute('''
        UPDATE orders SET status = ? WHERE order_number = ?
    ''', (status, order_number))
    conn.commit()
    conn.close()

def get_photos_for_order(order_number):
    conn = sqlite3.connect('orders.db')
    c = conn.cursor()
    c.execute('SELECT photo_id FROM order_photos WHERE order_number = ?', (order_number,))
    photos = c.fetchall()
    conn.close()
    return [photo[0] for photo in photos]
