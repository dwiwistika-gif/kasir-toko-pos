"""
Module: database
================
Mengelola koneksi dan semua operasi CRUD ke database SQLite
untuk sistem kasir/POS.

External Library: sqlite3 (built-in Python standard library)

Author  : Asesi
Version : 1.0.0
"""

import sqlite3
import os
from datetime import datetime
from packages.models import Product, Transaction, TransactionItem


class DatabaseManager:
    """
    Kelas DatabaseManager: mengelola semua operasi database SQLite.

    Attributes:
        __db_path (str): Path ke file database (private).
    """

    def __init__(self, db_path: str):
        self.__db_path: str = db_path    # private
        self._connection = None           # protected

    # ─── Connection ──────────────────────────────────────────────

    def _connect(self) -> sqlite3.Connection:
        """Membuat dan mengembalikan koneksi ke database SQLite."""
        conn = sqlite3.connect(self.__db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    # ─── Initialization ──────────────────────────────────────────

    def initialize(self):
        """
        Membuat tabel-tabel jika belum ada dan mengisi data awal (seed).
        Dipanggil satu kali saat program pertama dijalankan.
        """
        with self._connect() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS products (
                    id          INTEGER PRIMARY KEY AUTOINCREMENT,
                    name        TEXT    NOT NULL,
                    category    TEXT    NOT NULL,
                    price       REAL    NOT NULL,
                    stock       INTEGER NOT NULL DEFAULT 0,
                    barcode     TEXT    DEFAULT '',
                    created_at  TEXT    NOT NULL
                );

                CREATE TABLE IF NOT EXISTS transactions (
                    id               INTEGER PRIMARY KEY AUTOINCREMENT,
                    cashier          TEXT    NOT NULL,
                    payment_method   TEXT    NOT NULL DEFAULT 'Tunai',
                    total            REAL    NOT NULL DEFAULT 0,
                    paid             REAL    NOT NULL DEFAULT 0,
                    transaction_date TEXT    NOT NULL,
                    created_at       TEXT    NOT NULL
                );

                CREATE TABLE IF NOT EXISTS transaction_items (
                    id             INTEGER PRIMARY KEY AUTOINCREMENT,
                    transaction_id INTEGER NOT NULL REFERENCES transactions(id),
                    product_id     INTEGER NOT NULL REFERENCES products(id),
                    quantity       INTEGER NOT NULL,
                    unit_price     REAL    NOT NULL,
                    created_at     TEXT    NOT NULL
                );
            """)
            count = conn.execute("SELECT COUNT(*) FROM products").fetchone()[0]
            if count == 0:
                self._seed_data(conn)

    def _seed_data(self, conn):
        """Mengisi data produk awal untuk demo."""
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        products = [
            ("Indomie Goreng",    "Makanan",   3500,   50, "8991001100012"),
            ("Aqua 600ml",        "Minuman",   4000,   100,"8999999121306"),
            ("Roti Tawar Sari",   "Makanan",   15000,  30, "8992388012345"),
            ("Teh Botol Sosro",   "Minuman",   6000,   60, "8992696100013"),
            ("Chitato BBQ",       "Snack",     11000,  40, "8991103100015"),
            ("Gula Pasir 1kg",    "Sembako",   14000,  25, "8996001234567"),
            ("Minyak Goreng 1L",  "Sembako",   18000,  20, "8998765432100"),
            ("Sabun Lifebuoy",    "Kebersihan",8500,   35, "8999001500016"),
            ("Pasta Gigi Pepsodent","Kebersihan",14000, 28, "8999007700017"),
            ("Paracetamol 500mg", "Kesehatan", 8000,   50, "8990001800018"),
        ]
        for p in products:
            conn.execute(
                "INSERT INTO products (name, category, price, stock, barcode, created_at) VALUES (?,?,?,?,?,?)",
                (*p, now)
            )

    # ─── PRODUCTS CRUD ────────────────────────────────────────────

    def get_all_products(self) -> list[Product]:
        """READ: Mengambil semua data produk dari database."""
        with self._connect() as conn:
            rows = conn.execute("SELECT * FROM products ORDER BY name").fetchall()
            products = []
            for row in rows:
                p = Product(row["name"], row["category"], row["price"],
                            row["stock"], row["barcode"], row["id"])
                p.created_at = row["created_at"]
                products.append(p)
            return products

    def get_product_by_id(self, product_id: int) -> Product | None:
        """READ: Mengambil produk berdasarkan ID."""
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM products WHERE id = ?", (product_id,)).fetchone()
            if row:
                p = Product(row["name"], row["category"], row["price"],
                            row["stock"], row["barcode"], row["id"])
                p.created_at = row["created_at"]
                return p
            return None

    def search_products(self, keyword: str) -> list[Product]:
        """READ: Mencari produk berdasarkan nama atau barcode."""
        with self._connect() as conn:
            like = f"%{keyword}%"
            rows = conn.execute(
                "SELECT * FROM products WHERE name LIKE ? OR barcode LIKE ? ORDER BY name",
                (like, like)
            ).fetchall()
            products = []
            for row in rows:
                p = Product(row["name"], row["category"], row["price"],
                            row["stock"], row["barcode"], row["id"])
                p.created_at = row["created_at"]
                products.append(p)
            return products

    def add_product(self, product: Product) -> bool:
        """CREATE: Menambahkan produk baru ke database."""
        try:
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            with self._connect() as conn:
                conn.execute(
                    "INSERT INTO products (name, category, price, stock, barcode, created_at) VALUES (?,?,?,?,?,?)",
                    (product.name, product.category, product.price,
                     product.stock, product.barcode, now)
                )
            return True
        except sqlite3.Error:
            return False

    def update_product(self, product: Product) -> bool:
        """UPDATE: Memperbarui data produk yang sudah ada."""
        try:
            with self._connect() as conn:
                conn.execute(
                    "UPDATE products SET name=?, category=?, price=?, stock=?, barcode=? WHERE id=?",
                    (product.name, product.category, product.price,
                     product.stock, product.barcode, product.id)
                )
            return True
        except sqlite3.Error:
            return False

    def delete_product(self, product_id: int) -> bool:
        """DELETE: Menghapus produk berdasarkan ID."""
        with self._connect() as conn:
            conn.execute("DELETE FROM products WHERE id = ?", (product_id,))
            return True

    def restock_product(self, product_id: int, qty: int) -> bool:
        """UPDATE: Menambah stok produk (restock)."""
        with self._connect() as conn:
            conn.execute(
                "UPDATE products SET stock = stock + ? WHERE id = ?",
                (qty, product_id)
            )
            return True

    # ─── TRANSACTION CRUD ─────────────────────────────────────────

    def get_all_transactions(self) -> list[Transaction]:
        """READ: Mengambil semua data transaksi dari database."""
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM transactions ORDER BY id DESC"
            ).fetchall()
            transactions = []
            for row in rows:
                t = Transaction(
                    row["cashier"], row["payment_method"],
                    row["total"], row["paid"], row["transaction_date"],
                    entity_id=row["id"]
                )
                t.created_at = row["created_at"]
                transactions.append(t)
            return transactions

    def get_transaction_items(self, transaction_id: int) -> list[TransactionItem]:
        """READ: Mengambil semua item dari satu transaksi."""
        with self._connect() as conn:
            rows = conn.execute("""
                SELECT ti.*, p.name as product_name
                FROM transaction_items ti
                JOIN products p ON ti.product_id = p.id
                WHERE ti.transaction_id = ?
            """, (transaction_id,)).fetchall()
            items = []
            for row in rows:
                item = TransactionItem(
                    row["transaction_id"], row["product_id"],
                    row["quantity"], row["unit_price"],
                    row["product_name"], row["id"]
                )
                items.append(item)
            return items

    def save_transaction(self, transaction: Transaction, items: list) -> tuple[bool, int]:
        """
        CREATE: Menyimpan satu transaksi beserta semua item-nya.

        Args:
            transaction (Transaction): Objek transaksi.
            items (list): List tuple (product_id, qty, unit_price).

        Returns:
            tuple[bool, int]: (sukses, id_transaksi_baru).
        """
        try:
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            with self._connect() as conn:
                # Simpan header transaksi
                cursor = conn.execute(
                    """INSERT INTO transactions
                       (cashier, payment_method, total, paid, transaction_date, created_at)
                       VALUES (?,?,?,?,?,?)""",
                    (transaction.cashier, transaction.payment_method,
                     transaction.total, transaction.paid,
                     transaction.transaction_date, now)
                )
                tx_id = cursor.lastrowid

                # Simpan setiap item transaksi
                for product_id, qty, unit_price in items:
                    conn.execute(
                        """INSERT INTO transaction_items
                           (transaction_id, product_id, quantity, unit_price, created_at)
                           VALUES (?,?,?,?,?)""",
                        (tx_id, product_id, qty, unit_price, now)
                    )
                    # Kurangi stok produk
                    conn.execute(
                        "UPDATE products SET stock = stock - ? WHERE id = ?",
                        (qty, product_id)
                    )
            return True, tx_id
        except sqlite3.Error as e:
            return False, -1

    # ─── REPORTS ──────────────────────────────────────────────────

    def get_sales_summary(self) -> dict:
        """
        READ: Mengambil ringkasan penjualan (laporan).

        Returns:
            dict: total_transaksi, total_pendapatan, rata_rata, hari_ini.
        """
        with self._connect() as conn:
            row = conn.execute("""
                SELECT
                    COUNT(*)            AS total_transaksi,
                    COALESCE(SUM(total), 0)  AS total_pendapatan,
                    COALESCE(AVG(total), 0)  AS rata_rata
                FROM transactions
            """).fetchone()

            today = datetime.now().strftime("%Y-%m-%d")
            hari_ini = conn.execute("""
                SELECT COALESCE(SUM(total), 0) AS hari_ini
                FROM transactions
                WHERE transaction_date LIKE ?
            """, (f"{today}%",)).fetchone()["hari_ini"]

            # Array produk terlaris (top 5)
            top_products = conn.execute("""
                SELECT p.name, SUM(ti.quantity) AS total_qty, SUM(ti.quantity * ti.unit_price) AS revenue
                FROM transaction_items ti
                JOIN products p ON ti.product_id = p.id
                GROUP BY p.id
                ORDER BY total_qty DESC
                LIMIT 5
            """).fetchall()

            return {
                "total_transaksi":  row["total_transaksi"],
                "total_pendapatan": row["total_pendapatan"],
                "rata_rata":        row["rata_rata"],
                "hari_ini":         hari_ini,
                "top_products":     [dict(r) for r in top_products],
            }

    def get_low_stock(self, threshold: int = 10) -> list[Product]:
        """READ: Mengambil produk dengan stok rendah."""
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM products WHERE stock <= ? ORDER BY stock ASC",
                (threshold,)
            ).fetchall()
            products = []
            for row in rows:
                p = Product(row["name"], row["category"], row["price"],
                            row["stock"], row["barcode"], row["id"])
                products.append(p)
            return products
