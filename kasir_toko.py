"""
=============================================================
  SISTEM KASIR TOKO - Point of Sale (POS)
  POS System v1.0
=============================================================
Program  : Sistem Kasir / Point of Sale
Bahasa   : Python 3.x
Database : SQLite (file pos.db — otomatis dibuat)
Library  : sqlite3, abc, datetime, os
Author   : Asesi
Version  : 1.0.0
=============================================================

Cara menjalankan:
    python kasir_toko.py

Database akan dibuat otomatis di folder yang sama.
"""

import sqlite3
import os
from abc import ABC, abstractmethod
from datetime import datetime


# =============================================================
# PACKAGE 1: models — Kelas-kelas entitas domain
# =============================================================

class Printable(ABC):
    """
    Interface: Printable
    Abstract base class — setiap entitas yang bisa ditampilkan
    harus mengimplementasikan method display_info() dan to_dict().
    """

    @abstractmethod
    def display_info(self) -> str:
        """Mengembalikan informasi entitas dalam format string."""
        pass

    @abstractmethod
    def to_dict(self) -> dict:
        """Mengkonversi entitas ke dictionary."""
        pass


class BaseEntity(Printable):
    """
    Kelas dasar (parent) untuk semua entitas dalam sistem POS.

    Attributes:
        __id (int)         : ID unik entitas (private).
        _created_at (str)  : Timestamp pembuatan (protected).
    """

    def __init__(self, entity_id: int = None):
        self.__id: int = entity_id                                          # private
        self._created_at: str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")  # protected

    @property
    def id(self) -> int:
        """Property getter: mengembalikan id entitas."""
        return self.__id

    @id.setter
    def id(self, value: int):
        """Property setter: validasi id harus positif."""
        if value is not None and value <= 0:
            raise ValueError("ID harus bilangan positif.")
        self.__id = value

    @property
    def created_at(self) -> str:
        return self._created_at

    @created_at.setter
    def created_at(self, value: str):
        self._created_at = value


class Product(BaseEntity):
    """
    Kelas Product: merepresentasikan produk/barang di toko.
    Mewarisi BaseEntity, mengimplementasi interface Printable.

    Attributes:
        CATEGORIES (list): Array/list kategori produk yang tersedia.
    """

    # Array konstanta kategori produk
    CATEGORIES: list = [
        "Makanan", "Minuman", "Snack", "Sembako",
        "Kebersihan", "Kesehatan", "Elektronik", "Lainnya"
    ]

    def __init__(
        self,
        name: str,
        category: str,
        price: float,
        stock: int,
        barcode: str = "",
        entity_id: int = None
    ):
        super().__init__(entity_id)
        self.name: str       = name
        self.category: str   = category
        self.__price: float  = price    # private
        self.__stock: int    = stock    # private
        self.barcode: str    = barcode

    # ── Properties ────────────────────────────────────────────

    @property
    def price(self) -> float:
        """Property getter: harga produk."""
        return self.__price

    @price.setter
    def price(self, value: float):
        """Property setter: harga tidak boleh negatif."""
        if value < 0:
            raise ValueError("Harga tidak boleh negatif.")
        self.__price = value

    @property
    def stock(self) -> int:
        """Property getter: stok produk."""
        return self.__stock

    @stock.setter
    def stock(self, value: int):
        """Property setter: stok tidak boleh negatif."""
        if value < 0:
            raise ValueError("Stok tidak boleh negatif.")
        self.__stock = value

    # ── Methods ───────────────────────────────────────────────

    def is_available(self) -> bool:
        """Mengecek apakah stok produk masih tersedia."""
        return self.__stock > 0

    def formatted_price(self) -> str:
        """Mengembalikan harga dalam format Rupiah."""
        return f"Rp {self.__price:,.0f}"

    def display_info(self) -> str:
        """Polymorphism: implementasi dari interface Printable."""
        status = "Tersedia" if self.is_available() else "Habis"
        return (
            f"[{self.id}] {self.name}\n"
            f"    Kategori  : {self.category}\n"
            f"    Harga     : {self.formatted_price()}\n"
            f"    Stok      : {self.__stock} ({status})\n"
            f"    Barcode   : {self.barcode or '-'}"
        )

    def to_dict(self) -> dict:
        return {
            "id": self.id, "name": self.name, "category": self.category,
            "price": self.__price, "stock": self.__stock, "barcode": self.barcode,
        }

    def __str__(self) -> str:
        return f"Product({self.name!r}, {self.formatted_price()})"

    def __repr__(self) -> str:
        return f"Product(id={self.id}, name={self.name!r})"


class TransactionItem(BaseEntity):
    """
    Kelas TransactionItem: satu baris item dalam transaksi.
    Mewarisi BaseEntity, mengimplementasi interface Printable.

    Attributes:
        transaction_id (int): ID transaksi induk.
        product_id (int)    : ID produk yang dibeli.
        __quantity (int)    : Jumlah yang dibeli (private).
        __unit_price (float): Harga satuan saat transaksi (private).
    """

    def __init__(
        self,
        transaction_id: int,
        product_id: int,
        quantity: int,
        unit_price: float,
        product_name: str = "",
        entity_id: int = None
    ):
        super().__init__(entity_id)
        self.transaction_id: int  = transaction_id
        self.product_id: int      = product_id
        self.__quantity: int      = quantity       # private
        self.__unit_price: float  = unit_price     # private
        self.product_name: str    = product_name

    @property
    def quantity(self) -> int:
        return self.__quantity

    @quantity.setter
    def quantity(self, value: int):
        if value <= 0:
            raise ValueError("Jumlah harus lebih dari 0.")
        self.__quantity = value

    @property
    def unit_price(self) -> float:
        return self.__unit_price

    def subtotal(self) -> float:
        """Menghitung subtotal item (qty x harga satuan)."""
        return self.__quantity * self.__unit_price

    def display_info(self) -> str:
        """Polymorphism: implementasi dari interface Printable."""
        return (
            f"  {self.product_name:<25} "
            f"x{self.__quantity:<4} "
            f"@ Rp {self.__unit_price:>10,.0f}  "
            f"= Rp {self.subtotal():>12,.0f}"
        )

    def to_dict(self) -> dict:
        return {
            "id": self.id, "transaction_id": self.transaction_id,
            "product_id": self.product_id, "quantity": self.__quantity,
            "unit_price": self.__unit_price, "subtotal": self.subtotal(),
        }


class Transaction(BaseEntity):
    """
    Kelas Transaction: satu transaksi penjualan lengkap.
    Mewarisi BaseEntity, mengimplementasi interface Printable.

    Attributes:
        PAYMENT_METHODS (list): Array metode pembayaran yang tersedia.
        items (list)          : Array item-item dalam transaksi.
    """

    # Array metode pembayaran
    PAYMENT_METHODS: list = ["Tunai", "QRIS", "Transfer"]

    def __init__(
        self,
        cashier: str,
        payment_method: str = "Tunai",
        total: float = 0.0,
        paid: float = 0.0,
        transaction_date: str = "",
        items: list = None,
        entity_id: int = None
    ):
        super().__init__(entity_id)
        self.cashier: str            = cashier
        self.payment_method: str     = payment_method
        self.__total: float          = total          # private
        self.__paid: float           = paid           # private
        self.transaction_date: str   = transaction_date or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.items: list             = items or []    # array item transaksi

    @property
    def total(self) -> float:
        return self.__total

    @total.setter
    def total(self, value: float):
        if value < 0:
            raise ValueError("Total tidak boleh negatif.")
        self.__total = value

    @property
    def paid(self) -> float:
        return self.__paid

    @paid.setter
    def paid(self, value: float):
        self.__paid = value

    def change(self) -> float:
        """Menghitung kembalian pembayaran."""
        return self.__paid - self.__total

    def display_info(self) -> str:
        """Polymorphism: implementasi dari interface Printable."""
        return (
            f"[{self.id}] {self.transaction_date}\n"
            f"    Kasir      : {self.cashier}\n"
            f"    Pembayaran : {self.payment_method}\n"
            f"    Total      : Rp {self.__total:,.0f}\n"
            f"    Bayar      : Rp {self.__paid:,.0f}\n"
            f"    Kembalian  : Rp {self.change():,.0f}"
        )

    def to_dict(self) -> dict:
        return {
            "id": self.id, "cashier": self.cashier,
            "payment_method": self.payment_method,
            "total": self.__total, "paid": self.__paid,
            "transaction_date": self.transaction_date,
        }


# =============================================================
# PACKAGE 2: database — Koneksi & operasi CRUD ke SQLite
# =============================================================

class DatabaseManager:
    """
    Kelas DatabaseManager: mengelola semua operasi database SQLite.
    Menggunakan external library: sqlite3.

    Attributes:
        __db_path (str): Path ke file database SQLite (private).
    """

    def __init__(self, db_path: str):
        self.__db_path: str = db_path    # private
        self._connection   = None         # protected

    # ── Koneksi ───────────────────────────────────────────────

    def _connect(self) -> sqlite3.Connection:
        """Membuat dan mengembalikan koneksi ke database SQLite."""
        conn = sqlite3.connect(self.__db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    # ── Inisialisasi ──────────────────────────────────────────

    def initialize(self):
        """
        Membuat tabel-tabel jika belum ada dan mengisi data awal.
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
            # Isi data awal jika tabel produk masih kosong
            count = conn.execute("SELECT COUNT(*) FROM products").fetchone()[0]
            if count == 0:
                self._seed_data(conn)

    def _seed_data(self, conn):
        """Mengisi data produk awal untuk demo."""
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        products_data = [
            ("Indomie Goreng",      "Makanan",    3500,  50, "8991001100012"),
            ("Aqua 600ml",          "Minuman",    4000, 100, "8999999121306"),
            ("Roti Tawar Sari",     "Makanan",   15000,  30, "8992388012345"),
            ("Teh Botol Sosro",     "Minuman",    6000,  60, "8992696100013"),
            ("Chitato BBQ",         "Snack",     11000,  40, "8991103100015"),
            ("Gula Pasir 1kg",      "Sembako",   14000,  25, "8996001234567"),
            ("Minyak Goreng 1L",    "Sembako",   18000,  20, "8998765432100"),
            ("Sabun Lifebuoy",      "Kebersihan", 8500,  35, "8999001500016"),
            ("Pasta Gigi Pepsodent","Kebersihan",14000,  28, "8999007700017"),
            ("Paracetamol 500mg",   "Kesehatan",  8000,  50, "8990001800018"),
        ]
        for p in products_data:
            conn.execute(
                "INSERT INTO products (name, category, price, stock, barcode, created_at) VALUES (?,?,?,?,?,?)",
                (*p, now)
            )

    # ── CRUD Produk ───────────────────────────────────────────

    def get_all_products(self) -> list:
        """READ: Mengambil semua data produk dari database."""
        with self._connect() as conn:
            rows = conn.execute("SELECT * FROM products ORDER BY name").fetchall()
            result = []
            for row in rows:
                p = Product(row["name"], row["category"], row["price"],
                            row["stock"], row["barcode"], row["id"])
                p.created_at = row["created_at"]
                result.append(p)
            return result

    def get_product_by_id(self, product_id: int):
        """READ: Mengambil produk berdasarkan ID."""
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM products WHERE id = ?", (product_id,)).fetchone()
            if row:
                p = Product(row["name"], row["category"], row["price"],
                            row["stock"], row["barcode"], row["id"])
                p.created_at = row["created_at"]
                return p
            return None

    def search_products(self, keyword: str) -> list:
        """READ: Mencari produk berdasarkan nama atau barcode."""
        with self._connect() as conn:
            like = f"%{keyword}%"
            rows = conn.execute(
                "SELECT * FROM products WHERE name LIKE ? OR barcode LIKE ? ORDER BY name",
                (like, like)
            ).fetchall()
            result = []
            for row in rows:
                p = Product(row["name"], row["category"], row["price"],
                            row["stock"], row["barcode"], row["id"])
                p.created_at = row["created_at"]
                result.append(p)
            return result

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

    # ── CRUD Transaksi ────────────────────────────────────────

    def get_all_transactions(self) -> list:
        """READ: Mengambil semua data transaksi dari database."""
        with self._connect() as conn:
            rows = conn.execute("SELECT * FROM transactions ORDER BY id DESC").fetchall()
            result = []
            for row in rows:
                t = Transaction(
                    row["cashier"], row["payment_method"],
                    row["total"], row["paid"], row["transaction_date"],
                    entity_id=row["id"]
                )
                t.created_at = row["created_at"]
                result.append(t)
            return result

    def get_transaction_items(self, transaction_id: int) -> list:
        """READ: Mengambil semua item dari satu transaksi."""
        with self._connect() as conn:
            rows = conn.execute("""
                SELECT ti.*, p.name as product_name
                FROM transaction_items ti
                JOIN products p ON ti.product_id = p.id
                WHERE ti.transaction_id = ?
            """, (transaction_id,)).fetchall()
            result = []
            for row in rows:
                item = TransactionItem(
                    row["transaction_id"], row["product_id"],
                    row["quantity"], row["unit_price"],
                    row["product_name"], row["id"]
                )
                result.append(item)
            return result

    def save_transaction(self, transaction: Transaction, items: list) -> tuple:
        """
        CREATE: Menyimpan satu transaksi beserta semua item-nya ke database.

        Args:
            transaction (Transaction): Objek transaksi.
            items (list): List tuple (product_id, qty, unit_price).

        Returns:
            tuple: (sukses: bool, id_transaksi: int).
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

                # Simpan setiap item — pengulangan for
                for product_id, qty, unit_price in items:
                    conn.execute(
                        """INSERT INTO transaction_items
                           (transaction_id, product_id, quantity, unit_price, created_at)
                           VALUES (?,?,?,?,?)""",
                        (tx_id, product_id, qty, unit_price, now)
                    )
                    # Kurangi stok produk setelah terjual
                    conn.execute(
                        "UPDATE products SET stock = stock - ? WHERE id = ?",
                        (qty, product_id)
                    )
            return True, tx_id
        except sqlite3.Error:
            return False, -1

    # ── Laporan ───────────────────────────────────────────────

    def get_sales_summary(self) -> dict:
        """
        READ: Mengambil ringkasan penjualan untuk laporan.

        Returns:
            dict: total_transaksi, total_pendapatan, rata_rata,
                  hari_ini, top_products (array/list).
        """
        with self._connect() as conn:
            row = conn.execute("""
                SELECT COUNT(*) AS total_transaksi,
                       COALESCE(SUM(total), 0) AS total_pendapatan,
                       COALESCE(AVG(total), 0) AS rata_rata
                FROM transactions
            """).fetchone()

            today = datetime.now().strftime("%Y-%m-%d")
            hari_ini = conn.execute(
                "SELECT COALESCE(SUM(total),0) AS h FROM transactions WHERE transaction_date LIKE ?",
                (f"{today}%",)
            ).fetchone()["h"]

            # Array produk terlaris (top 5)
            top_rows = conn.execute("""
                SELECT p.name,
                       SUM(ti.quantity) AS total_qty,
                       SUM(ti.quantity * ti.unit_price) AS revenue
                FROM transaction_items ti
                JOIN products p ON ti.product_id = p.id
                GROUP BY p.id ORDER BY total_qty DESC LIMIT 5
            """).fetchall()

            return {
                "total_transaksi":  row["total_transaksi"],
                "total_pendapatan": row["total_pendapatan"],
                "rata_rata":        row["rata_rata"],
                "hari_ini":         hari_ini,
                "top_products":     [dict(r) for r in top_rows],
            }

    def get_low_stock(self, threshold: int = 10) -> list:
        """READ: Mengambil produk dengan stok rendah (di bawah threshold)."""
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM products WHERE stock <= ? ORDER BY stock ASC",
                (threshold,)
            ).fetchall()
            result = []
            for row in rows:
                p = Product(row["name"], row["category"], row["price"],
                            row["stock"], row["barcode"], row["id"])
                result.append(p)
            return result


# =============================================================
# PACKAGE 2: ui — Antarmuka pengguna (CLI)
# =============================================================

class UserInterface:
    """
    Kelas UserInterface: mengelola tampilan dan interaksi kasir via CLI.

    Attributes:
        __db (DatabaseManager): Instance database (private).
        __cart (list)          : Array keranjang belanja aktif (private).
        __cashier (str)        : Nama kasir yang bertugas (private).
    """

    # Array item-item menu
    MENU_MAIN = [
        "1. Transaksi Penjualan (Kasir)",
        "2. Manajemen Produk",
        "3. Laporan & Riwayat",
        "4. Produk Stok Menipis",
        "0. Keluar",
    ]
    MENU_PRODUCTS = [
        "1. Tampilkan Semua Produk",
        "2. Cari Produk",
        "3. Tambah Produk Baru",
        "4. Edit Produk",
        "5. Hapus Produk",
        "6. Restock (Tambah Stok)",
        "0. Kembali",
    ]
    MENU_REPORTS = [
        "1. Ringkasan Penjualan",
        "2. Riwayat Transaksi",
        "3. Detail Transaksi",
        "0. Kembali",
    ]

    def __init__(self, db: DatabaseManager):
        self.__db: DatabaseManager = db   # private
        self.__cart: list = []            # array keranjang belanja
        self.__cashier: str = ""          # private

    # ── Helper / Utilitas ─────────────────────────────────────

    @staticmethod
    def _sep(char="─", n=56):
        """Mencetak garis pemisah."""
        print("  " + char * n)

    @staticmethod
    def _title(text: str):
        """Mencetak judul section."""
        print(f"\n  {'─'*56}")
        print(f"  {text}")
        print(f"  {'─'*56}")

    def _input(self, prompt: str) -> str:
        """Membaca input teks dari pengguna."""
        return input(f"  {prompt}").strip()

    def _input_int(self, prompt: str, default: int = None):
        """Membaca input integer dengan validasi. Percabangan if-else."""
        while True:
            raw = input(f"  {prompt}").strip()
            if raw == "" and default is not None:
                return default
            try:
                return int(raw)
            except ValueError:
                print("  [!] Masukkan angka bulat yang valid.")

    def _input_float(self, prompt: str) -> float:
        """Membaca input float/desimal dengan validasi."""
        while True:
            raw = input(f"  {prompt}").strip()
            try:
                return float(raw.replace(",", "").replace(".", ""))
            except ValueError:
                print("  [!] Masukkan angka yang valid.")

    @staticmethod
    def _ok(msg: str):
        """Mencetak pesan sukses."""
        print(f"\n  [OK] {msg}")

    @staticmethod
    def _err(msg: str):
        """Mencetak pesan error."""
        print(f"\n  [!]  {msg}")

    def _print_menu(self, title: str, items: list):
        """Mencetak menu dengan judul dan pilihan."""
        self._title(title)
        for item in items:
            print(f"    {item}")
        self._sep()

    # ── Loop Utama ────────────────────────────────────────────

    def run(self):
        """Loop utama program menggunakan while True."""
        self.__cashier = self._input("Masukkan nama kasir : ")
        if not self.__cashier:
            self.__cashier = "Kasir"
        print(f"\n  Selamat datang, {self.__cashier}!")

        # Pengulangan while: program terus berjalan sampai pilih 0
        while True:
            self._print_menu("MENU UTAMA - SISTEM KASIR POS", self.MENU_MAIN)
            choice = self._input("Pilih menu : ")

            # Percabangan if-elif-else untuk navigasi menu
            if choice == "1":
                self._menu_transaction()
            elif choice == "2":
                self._menu_products()
            elif choice == "3":
                self._menu_reports()
            elif choice == "4":
                self._show_low_stock()
            elif choice == "0":
                print("\n  Terima kasih. Sampai jumpa!\n")
                break
            else:
                self._err("Pilihan tidak valid. Coba lagi.")

    # ── Transaksi / Kasir ─────────────────────────────────────

    def _menu_transaction(self):
        """Sub-menu transaksi penjualan (mode kasir)."""
        self.__cart = []   # reset keranjang untuk transaksi baru
        print(f"\n  == TRANSAKSI BARU == Kasir: {self.__cashier}")
        print("  Masukkan ID produk untuk ditambah ke keranjang.")
        print("  Ketik 's' untuk cari, 'selesai' untuk checkout, 'batal' untuk membatalkan.\n")

        # While loop: tambah produk sampai selesai/batal
        while True:
            self._show_cart()
            self._sep()
            print("    Perintah: [ID produk]  [s] Cari  [selesai] Checkout  [batal] Batalkan")
            self._sep()
            cmd = self._input("Perintah : ").lower()

            if cmd == "selesai":
                if not self.__cart:
                    self._err("Keranjang masih kosong.")
                else:
                    self._checkout()
                    break
            elif cmd == "batal":
                self._err("Transaksi dibatalkan.")
                break
            elif cmd == "s":
                keyword = self._input("Kata kunci produk : ")
                products = self.__db.search_products(keyword)
                if not products:
                    self._err("Produk tidak ditemukan.")
                else:
                    for p in products:
                        print(f"\n{p.display_info()}")
            else:
                try:
                    product_id = int(cmd)
                    self._add_to_cart(product_id)
                except ValueError:
                    self._err("Perintah tidak dikenal. Masukkan ID produk (angka) atau perintah yang valid.")

    def _show_cart(self):
        """Menampilkan isi keranjang belanja dalam format tabel."""
        self._title(f"KERANJANG BELANJA  [{datetime.now().strftime('%d/%m/%Y %H:%M')}]")
        if not self.__cart:
            print("  (Keranjang kosong — masukkan ID produk untuk menambah)")
        else:
            print(f"  {'No':<4} {'Produk':<27} {'Qty':>5} {'Harga/pcs':>12} {'Subtotal':>14}")
            self._sep("·")
            total = 0.0
            # For loop: tampilkan setiap item di keranjang
            for i, (prod, qty) in enumerate(self.__cart, 1):
                sub = prod.price * qty
                total += sub
                print(f"  {i:<4} {prod.name:<27} {qty:>5} {prod.price:>12,.0f} {sub:>14,.0f}")
            self._sep()
            print(f"  {'TOTAL':>51}  Rp {total:>12,.0f}")

    def _add_to_cart(self, product_id: int):
        """
        Menambahkan produk ke keranjang belanja.
        Menerapkan percabangan if-else untuk validasi stok.

        Args:
            product_id (int): ID produk yang akan ditambahkan.
        """
        product = self.__db.get_product_by_id(product_id)
        if not product:
            self._err(f"Produk dengan ID {product_id} tidak ditemukan.")
            return
        if not product.is_available():
            self._err(f"Stok '{product.name}' habis.")
            return

        qty = self._input_int(f"Jumlah '{product.name}' (stok tersedia: {product.stock}) : ", 1)
        if qty is None or qty <= 0:
            self._err("Jumlah harus lebih dari 0.")
            return
        if qty > product.stock:
            self._err(f"Stok tidak mencukupi. Stok tersedia: {product.stock}.")
            return

        # Cek apakah produk sudah ada di keranjang → update qty
        for i, (p, q) in enumerate(self.__cart):
            if p.id == product_id:
                new_qty = q + qty
                if new_qty > product.stock:
                    self._err("Total jumlah melebihi stok tersedia.")
                    return
                self.__cart[i] = (p, new_qty)
                self._ok(f"Jumlah '{product.name}' diperbarui menjadi {new_qty}.")
                return

        self.__cart.append((product, qty))
        self._ok(f"'{product.name}' x{qty} ditambahkan ke keranjang.")

    def _checkout(self):
        """Proses checkout: hitung total, terima pembayaran, simpan, cetak struk."""
        total = sum(p.price * qty for p, qty in self.__cart)

        self._title("CHECKOUT")
        print(f"  Total Belanja  : Rp {total:,.0f}")

        # Pilih metode pembayaran
        print(f"\n  Metode Pembayaran yang tersedia: {', '.join(Transaction.PAYMENT_METHODS)}")
        payment = self._input("Metode pembayaran (default: Tunai) : ") or "Tunai"
        if payment not in Transaction.PAYMENT_METHODS:
            payment = "Tunai"

        paid = self._input_float(f"Jumlah Bayar (Rp) : ")

        # Percabangan: validasi uang bayar cukup
        if paid < total:
            self._err(f"Uang kurang Rp {total - paid:,.0f}. Transaksi dibatalkan.")
            return

        change = paid - total
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        tx = Transaction(self.__cashier, payment, total, paid, now)
        items = [(p.id, qty, p.price) for p, qty in self.__cart]

        success, tx_id = self.__db.save_transaction(tx, items)
        if not success:
            self._err("Gagal menyimpan transaksi ke database.")
            return

        self._print_receipt(tx_id, total, paid, change, payment, now)
        self.__cart = []

    def _print_receipt(self, tx_id, total, paid, change, payment, date):
        """Mencetak struk pembelian ke layar terminal."""
        print("\n")
        print("  " + "=" * 44)
        print("          TOKO SERBA ADA SEJAHTERA")
        print("          Jl. Pahlawan No. 88, Kota")
        print("          Telp: 021-55667788")
        print("  " + "-" * 44)
        print(f"  No. Transaksi : TRX-{tx_id:05d}")
        print(f"  Tanggal       : {date}")
        print(f"  Kasir         : {self.__cashier}")
        print("  " + "-" * 44)
        print(f"  {'Produk':<26} {'Qty':>4} {'Subtotal':>12}")
        print("  " + "-" * 44)
        # For loop: cetak setiap item di struk
        items = self.__db.get_transaction_items(tx_id)
        for item in items:
            print(f"  {item.product_name:<26} {item.quantity:>4} {item.subtotal():>12,.0f}")
        print("  " + "-" * 44)
        print(f"  {'TOTAL':<26} {'':>4} {total:>12,.0f}")
        print(f"  {'BAYAR (' + payment + ')':<26} {'':>4} {paid:>12,.0f}")
        print(f"  {'KEMBALIAN':<26} {'':>4} {change:>12,.0f}")
        print("  " + "-" * 44)
        print("        Terima kasih telah berbelanja!")
        print("            Selamat datang kembali!")
        print("  " + "=" * 44 + "\n")

    # ── Manajemen Produk ──────────────────────────────────────

    def _menu_products(self):
        """Sub-menu manajemen produk (CRUD)."""
        while True:
            self._print_menu("MANAJEMEN PRODUK", self.MENU_PRODUCTS)
            choice = self._input("Pilih menu : ")

            if choice == "1":
                self._list_products()
            elif choice == "2":
                self._search_products()
            elif choice == "3":
                self._add_product()
            elif choice == "4":
                self._edit_product()
            elif choice == "5":
                self._delete_product()
            elif choice == "6":
                self._restock()
            elif choice == "0":
                break
            else:
                self._err("Pilihan tidak valid.")

    def _list_products(self):
        """Menampilkan semua produk dalam format tabel."""
        products = self.__db.get_all_products()
        self._title(f"DAFTAR PRODUK  ({len(products)} item)")
        if not products:
            print("  Belum ada produk.")
            return
        print(f"  {'ID':<5} {'Nama Produk':<28} {'Kategori':<12} {'Harga':>12} {'Stok':>6}")
        self._sep()
        for p in products:
            warn = " (!)" if p.stock <= 10 else ""
            print(f"  {p.id:<5} {p.name:<28} {p.category:<12} {p.price:>12,.0f} {p.stock:>5}{warn}")

    def _search_products(self):
        keyword = self._input("Kata kunci (nama/barcode) : ")
        products = self.__db.search_products(keyword)
        if not products:
            self._err(f"Produk '{keyword}' tidak ditemukan.")
        else:
            print(f"\n  Ditemukan {len(products)} produk:")
            for p in products:
                print(f"\n{p.display_info()}")

    def _add_product(self):
        """CREATE: Menambah produk baru."""
        self._title("TAMBAH PRODUK BARU")
        name     = self._input("Nama Produk    : ")
        print(f"  Pilihan kategori: {', '.join(Product.CATEGORIES)}")
        category = self._input("Kategori       : ")
        price    = self._input_float("Harga (Rp)     : ")
        stock    = self._input_int("Stok Awal      : ", 0)
        barcode  = self._input("Barcode        : ")

        p = Product(name, category, price, stock, barcode)
        if self.__db.add_product(p):
            self._ok(f"Produk '{name}' berhasil ditambahkan.")
        else:
            self._err("Gagal menambahkan produk.")

    def _edit_product(self):
        """UPDATE: Mengedit data produk."""
        self._list_products()
        pid = self._input_int("ID produk yang akan diedit : ")
        p = self.__db.get_product_by_id(pid)
        if not p:
            self._err("Produk tidak ditemukan.")
            return

        self._title(f"EDIT: {p.name}")
        print("  (Tekan Enter untuk mempertahankan nilai saat ini)\n")

        name     = self._input(f"Nama [{p.name}] : ")          or p.name
        category = self._input(f"Kategori [{p.category}] : ")   or p.category
        price_s  = self._input(f"Harga [{p.price:,.0f}] : ")
        price    = float(price_s) if price_s else p.price
        stock_s  = self._input(f"Stok [{p.stock}] : ")
        stock    = int(stock_s)   if stock_s else p.stock
        barcode  = self._input(f"Barcode [{p.barcode}] : ")     or p.barcode

        p.name = name; p.category = category
        p.price = price; p.stock = stock; p.barcode = barcode

        if self.__db.update_product(p):
            self._ok("Data produk berhasil diperbarui.")
        else:
            self._err("Gagal memperbarui produk.")

    def _delete_product(self):
        """DELETE: Menghapus produk."""
        self._list_products()
        pid = self._input_int("ID produk yang akan dihapus : ")
        p = self.__db.get_product_by_id(pid)
        if not p:
            self._err("Produk tidak ditemukan.")
            return
        confirm = self._input(f"Yakin hapus '{p.name}'? (y/n) : ")
        if confirm.lower() == "y":
            self.__db.delete_product(pid)
            self._ok(f"Produk '{p.name}' berhasil dihapus.")

    def _restock(self):
        """UPDATE: Menambah stok produk."""
        self._list_products()
        pid = self._input_int("ID produk yang akan di-restock : ")
        p = self.__db.get_product_by_id(pid)
        if not p:
            self._err("Produk tidak ditemukan.")
            return
        qty = self._input_int(f"Tambah berapa stok untuk '{p.name}' (stok sekarang: {p.stock}) : ")
        if qty and qty > 0:
            self.__db.restock_product(pid, qty)
            self._ok(f"Stok '{p.name}' ditambah {qty}. Stok baru: {p.stock + qty}.")

    # ── Laporan ───────────────────────────────────────────────

    def _menu_reports(self):
        """Sub-menu laporan & riwayat transaksi."""
        while True:
            self._print_menu("LAPORAN & RIWAYAT", self.MENU_REPORTS)
            choice = self._input("Pilih menu : ")
            if choice == "1":
                self._show_summary()
            elif choice == "2":
                self._show_transactions()
            elif choice == "3":
                self._show_transaction_detail()
            elif choice == "0":
                break
            else:
                self._err("Pilihan tidak valid.")

    def _show_summary(self):
        s = self.__db.get_sales_summary()
        self._title("RINGKASAN PENJUALAN")
        print(f"  Total Transaksi      : {s['total_transaksi']}")
        print(f"  Total Pendapatan     : Rp {s['total_pendapatan']:,.0f}")
        print(f"  Rata-rata/Transaksi  : Rp {s['rata_rata']:,.0f}")
        print(f"  Pendapatan Hari Ini  : Rp {s['hari_ini']:,.0f}")
        if s["top_products"]:
            print("\n  -- Produk Terlaris (Top 5) --")
            for i, prod in enumerate(s["top_products"], 1):
                print(f"  {i}. {prod['name']:<30} {prod['total_qty']:>5} unit   Rp {prod['revenue']:>12,.0f}")

    def _show_transactions(self):
        txs = self.__db.get_all_transactions()
        self._title(f"RIWAYAT TRANSAKSI  ({len(txs)} data)")
        if not txs:
            print("  Belum ada transaksi.")
            return
        print(f"  {'ID':<8} {'Tanggal':<22} {'Kasir':<14} {'Metode':<10} {'Total':>14}")
        self._sep()
        for tx in txs:
            print(f"  TRX-{tx.id:<4} {tx.transaction_date:<22} {tx.cashier:<14} {tx.payment_method:<10} Rp {tx.total:>10,.0f}")

    def _show_transaction_detail(self):
        self._show_transactions()
        tx_id = self._input_int("Masukkan ID transaksi yang ingin dilihat : ")
        items = self.__db.get_transaction_items(tx_id)
        if not items:
            self._err("Transaksi tidak ditemukan atau tidak ada item.")
            return
        self._title(f"DETAIL TRANSAKSI  TRX-{tx_id:05d}")
        total = 0.0
        for item in items:
            print(item.display_info())
            total += item.subtotal()
        self._sep()
        print(f"  {'TOTAL':>56}  Rp {total:>12,.0f}")

    def _show_low_stock(self):
        """Menampilkan produk dengan stok menipis."""
        products = self.__db.get_low_stock(10)
        self._title("PRODUK STOK MENIPIS  (stok <= 10)")
        if not products:
            print("  Semua produk stok aman.")
        else:
            print(f"  {'ID':<5} {'Nama Produk':<30} {'Stok':>6}  Keterangan")
            self._sep()
            for p in products:
                ket = "!! HABIS !!" if p.stock == 0 else "Segera restock"
                print(f"  {p.id:<5} {p.name:<30} {p.stock:>6}  {ket}")


# =============================================================
# ENTRY POINT — main()
# =============================================================

def main():
    """
    Fungsi utama: entry point program.
    Menginisialisasi database dan memulai antarmuka pengguna.
    """
    print("=" * 60)
    print("   SISTEM KASIR TOKO - Point of Sale (POS)")
    print("   POS System v1.0  |  Database: SQLite (pos.db)")
    print("=" * 60)

    # Inisialisasi database — file pos.db dibuat otomatis
    db = DatabaseManager("pos.db")
    db.initialize()

    # Jalankan antarmuka pengguna
    ui = UserInterface(db)
    ui.run()


if __name__ == "__main__":
    main()
