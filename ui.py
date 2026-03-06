"""
Module: ui
==========
Modul antarmuka pengguna (CLI) untuk sistem kasir POS.
Mengelola semua input dari kasir dan output ke layar.

Author  : Asesi
Version : 1.0.0
"""

from datetime import datetime
from packages.models import Product, Transaction, TransactionItem
from packages.database import DatabaseManager


class UserInterface:
    """
    Kelas UserInterface: mengelola tampilan dan interaksi kasir.

    Attributes:
        __db (DatabaseManager): Instance database (private).
        __cart (list): Keranjang belanja sesi aktif (private).
        __cashier (str): Nama kasir yang sedang bertugas (private).
    """

    MENU_MAIN = [
        "1. Transaksi Penjualan (Kasir)",
        "2. Manajemen Produk",
        "3. Laporan & Riwayat",
        "4. Stok Menipis",
        "0. Keluar",
    ]
    MENU_PRODUCTS = [
        "1. Tampilkan Semua Produk",
        "2. Cari Produk",
        "3. Tambah Produk",
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
        self.__db: DatabaseManager = db
        self.__cart: list = []        # array keranjang belanja
        self.__cashier: str = ""

    # ─── Helpers ─────────────────────────────────────────────────

    @staticmethod
    def _sep(char="─", n=56):
        print("  " + char * n)

    @staticmethod
    def _title(text: str):
        print(f"\n  {'─'*56}")
        print(f"  {'  ' + text}")
        print(f"  {'─'*56}")

    def _input(self, prompt: str) -> str:
        return input(f"  {prompt}").strip()

    def _input_int(self, prompt: str, default: int = None) -> int | None:
        while True:
            raw = input(f"  {prompt}").strip()
            if raw == "" and default is not None:
                return default
            try:
                return int(raw)
            except ValueError:
                print("  [!] Masukkan angka yang valid.")

    def _input_float(self, prompt: str) -> float:
        while True:
            raw = input(f"  {prompt}").strip()
            try:
                return float(raw)
            except ValueError:
                print("  [!] Masukkan angka yang valid.")

    @staticmethod
    def _ok(msg: str):
        print(f"\n  [✓] {msg}")

    @staticmethod
    def _err(msg: str):
        print(f"\n  [✗] {msg}")

    def _print_menu(self, title: str, items: list):
        self._title(title)
        for item in items:
            print(f"    {item}")
        self._sep()

    # ─── Main Loop ───────────────────────────────────────────────

    def run(self):
        """Loop utama program. Meminta nama kasir lalu menampilkan menu."""
        self.__cashier = self._input("Masukkan nama kasir : ")
        if not self.__cashier:
            self.__cashier = "Kasir"
        print(f"\n  Selamat datang, {self.__cashier}!")

        while True:
            self._print_menu("MENU UTAMA - SISTEM KASIR POS", self.MENU_MAIN)
            choice = self._input("Pilih menu : ")

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
                self._err("Pilihan tidak valid.")

    # ─── Transaction (Kasir) ─────────────────────────────────────

    def _menu_transaction(self):
        """Sub-menu transaksi penjualan (kasir mode)."""
        self.__cart = []   # reset keranjang baru

        print(f"\n  ══ TRANSAKSI BARU ══  Kasir: {self.__cashier}")
        print("  Tambahkan produk ke keranjang. Ketik 'selesai' untuk checkout.\n")

        while True:
            self._show_cart()
            self._sep()
            print("    [s] Cari produk  [id] Masukkan ID langsung  [selesai] Checkout  [batal] Batalkan")
            self._sep()
            cmd = self._input("Perintah : ").lower()

            if cmd == "selesai":
                if not self.__cart:
                    self._err("Keranjang kosong. Tambahkan produk terlebih dahulu.")
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
                        print(f"    {p.display_info()}")
                        print()
            else:
                try:
                    product_id = int(cmd)
                    self._add_to_cart(product_id)
                except ValueError:
                    self._err("Perintah tidak dikenal.")

    def _show_cart(self):
        """Menampilkan isi keranjang belanja saat ini."""
        self._title(f"KERANJANG BELANJA — {datetime.now().strftime('%d/%m/%Y %H:%M')}")
        if not self.__cart:
            print("  (Keranjang kosong)")
        else:
            print(f"  {'No':<4} {'Produk':<26} {'Qty':>5} {'Harga':>12} {'Subtotal':>14}")
            self._sep("·")
            total = 0.0
            for i, (prod, qty) in enumerate(self.__cart, 1):
                sub = prod.price * qty
                total += sub
                print(f"  {i:<4} {prod.name:<26} {qty:>5} {prod.price:>12,.0f} {sub:>14,.0f}")
            self._sep("─")
            print(f"  {'TOTAL':>49} Rp {total:>12,.0f}")

    def _add_to_cart(self, product_id: int):
        """Menambahkan produk ke keranjang belanja."""
        product = self.__db.get_product_by_id(product_id)
        if not product:
            self._err(f"Produk ID {product_id} tidak ditemukan.")
            return
        if not product.is_available():
            self._err(f"Stok '{product.name}' habis.")
            return

        qty = self._input_int(f"Jumlah '{product.name}' (stok: {product.stock}) : ", 1)
        if qty <= 0:
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
                    self._err("Total jumlah melebihi stok.")
                    return
                self.__cart[i] = (p, new_qty)
                self._ok(f"Jumlah '{product.name}' diperbarui menjadi {new_qty}.")
                return

        self.__cart.append((product, qty))
        self._ok(f"'{product.name}' x{qty} ditambahkan ke keranjang.")

    def _checkout(self):
        """Proses checkout: hitung total, terima pembayaran, cetak struk."""
        # Hitung total
        total = sum(p.price * qty for p, qty in self.__cart)

        self._title("CHECKOUT")
        print(f"  Total Belanja : Rp {total:,.0f}")

        # Pilih metode pembayaran
        print(f"\n  Metode Pembayaran: {', '.join(Transaction.PAYMENT_METHODS)}")
        payment = self._input("Metode (default: Tunai) : ") or "Tunai"
        if payment not in Transaction.PAYMENT_METHODS:
            payment = "Tunai"

        paid = self._input_float(f"Jumlah Bayar (Rp) : ")
        if paid < total:
            self._err(f"Uang kurang. Kekurangan: Rp {total - paid:,.0f}")
            return

        change = paid - total
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Buat objek transaksi
        tx = Transaction(self.__cashier, payment, total, paid, now)

        # Siapkan item list
        items = [(p.id, qty, p.price) for p, qty in self.__cart]

        success, tx_id = self.__db.save_transaction(tx, items)
        if not success:
            self._err("Gagal menyimpan transaksi.")
            return

        # Cetak struk
        self._print_receipt(tx_id, total, paid, change, payment, now)
        self.__cart = []

    def _print_receipt(self, tx_id, total, paid, change, payment, date):
        """Mencetak struk pembelian ke layar."""
        print("\n")
        print("  " + "═" * 40)
        print("          TOKO SERBA ADA SEJAHTERA")
        print("          Jl. Pahlawan No. 88, Kota")
        print("          Telp: 021-55667788")
        print("  " + "─" * 40)
        print(f"  No. Transaksi : TRX-{tx_id:05d}")
        print(f"  Tanggal       : {date}")
        print(f"  Kasir         : {self.__cashier}")
        print("  " + "─" * 40)
        print(f"  {'Produk':<24} {'Qty':>4} {'Subtotal':>12}")
        print("  " + "─" * 40)
        for p, qty in self.__cart if self.__cart else []:
            sub = p.price * qty
            print(f"  {p.name:<24} {qty:>4} {sub:>12,.0f}")

        items = self.__db.get_transaction_items(tx_id)
        if items:
            for item in items:
                print(f"  {item.product_name:<24} {item.quantity:>4} {item.subtotal():>12,.0f}")
        print("  " + "─" * 40)
        print(f"  {'TOTAL':<24} {'':>4} {total:>12,.0f}")
        print(f"  {'BAYAR (' + payment + ')':<24} {'':>4} {paid:>12,.0f}")
        print(f"  {'KEMBALIAN':<24} {'':>4} {change:>12,.0f}")
        print("  " + "─" * 40)
        print("       Terima kasih telah berbelanja!")
        print("           Selamat datang kembali")
        print("  " + "═" * 40)

    # ─── Products Menu ───────────────────────────────────────────

    def _menu_products(self):
        """Sub-menu manajemen produk."""
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
        products = self.__db.get_all_products()
        self._title(f"DAFTAR PRODUK ({len(products)} item)")
        if not products:
            print("  Belum ada produk.")
            return
        print(f"  {'ID':<5} {'Nama':<28} {'Kategori':<12} {'Harga':>12} {'Stok':>6}")
        self._sep("─")
        for p in products:
            stok_warn = " ⚠" if p.stock <= 10 else ""
            print(f"  {p.id:<5} {p.name:<28} {p.category:<12} {p.price:>12,.0f} {p.stock:>5}{stok_warn}")

    def _search_products(self):
        keyword = self._input("Kata kunci : ")
        products = self.__db.search_products(keyword)
        if not products:
            self._err("Produk tidak ditemukan.")
        else:
            for p in products:
                print(f"\n{p.display_info()}")

    def _add_product(self):
        self._title("TAMBAH PRODUK BARU")
        name = self._input("Nama Produk    : ")
        print(f"  Kategori: {', '.join(Product.CATEGORIES)}")
        category = self._input("Kategori       : ")
        price = self._input_float("Harga (Rp)     : ")
        stock = self._input_int("Stok Awal      : ", 0)
        barcode = self._input("Barcode        : ")

        product = Product(name, category, price, stock, barcode)
        if self.__db.add_product(product):
            self._ok(f"Produk '{name}' berhasil ditambahkan.")
        else:
            self._err("Gagal menambahkan produk.")

    def _edit_product(self):
        self._list_products()
        pid = self._input_int("ID produk yang akan diedit : ")
        p = self.__db.get_product_by_id(pid)
        if not p:
            self._err("Produk tidak ditemukan.")
            return

        self._title(f"EDIT PRODUK: {p.name}")
        print("  (Tekan Enter untuk mempertahankan nilai saat ini)\n")

        name     = self._input(f"Nama [{p.name}] : ") or p.name
        category = self._input(f"Kategori [{p.category}] : ") or p.category
        price_s  = self._input(f"Harga [{p.price:,.0f}] : ")
        price    = float(price_s) if price_s else p.price
        stock_s  = self._input(f"Stok [{p.stock}] : ")
        stock    = int(stock_s) if stock_s else p.stock
        barcode  = self._input(f"Barcode [{p.barcode}] : ") or p.barcode

        p.name     = name
        p.category = category
        p.price    = price
        p.stock    = stock
        p.barcode  = barcode

        if self.__db.update_product(p):
            self._ok("Produk berhasil diperbarui.")
        else:
            self._err("Gagal memperbarui produk.")

    def _delete_product(self):
        self._list_products()
        pid = self._input_int("ID produk yang akan dihapus : ")
        p = self.__db.get_product_by_id(pid)
        if not p:
            self._err("Produk tidak ditemukan.")
            return
        confirm = self._input(f"Hapus '{p.name}'? (y/n) : ")
        if confirm.lower() == "y":
            self.__db.delete_product(pid)
            self._ok("Produk berhasil dihapus.")

    def _restock(self):
        self._list_products()
        pid = self._input_int("ID produk yang akan di-restock : ")
        p = self.__db.get_product_by_id(pid)
        if not p:
            self._err("Produk tidak ditemukan.")
            return
        qty = self._input_int(f"Tambah stok untuk '{p.name}' (stok sekarang: {p.stock}) : ")
        if qty and qty > 0:
            self.__db.restock_product(pid, qty)
            self._ok(f"Stok '{p.name}' berhasil ditambah {qty}. Stok baru: {p.stock + qty}.")

    # ─── Reports ─────────────────────────────────────────────────

    def _menu_reports(self):
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
        print(f"  Total Transaksi   : {s['total_transaksi']}")
        print(f"  Total Pendapatan  : Rp {s['total_pendapatan']:,.0f}")
        print(f"  Rata-rata/Transaksi: Rp {s['rata_rata']:,.0f}")
        print(f"  Pendapatan Hari Ini: Rp {s['hari_ini']:,.0f}")
        if s["top_products"]:
            print("\n  ── Produk Terlaris ──")
            for i, prod in enumerate(s["top_products"], 1):
                print(f"  {i}. {prod['name']:<28} {prod['total_qty']:>5} unit  Rp {prod['revenue']:>12,.0f}")

    def _show_transactions(self):
        txs = self.__db.get_all_transactions()
        self._title(f"RIWAYAT TRANSAKSI ({len(txs)} transaksi)")
        if not txs:
            print("  Belum ada transaksi.")
            return
        print(f"  {'ID':<8} {'Tanggal':<20} {'Kasir':<12} {'Metode':<10} {'Total':>14}")
        self._sep("─")
        for tx in txs:
            print(f"  TRX-{tx.id:<4} {tx.transaction_date:<20} {tx.cashier:<12} {tx.payment_method:<10} Rp {tx.total:>10,.0f}")

    def _show_transaction_detail(self):
        self._show_transactions()
        tx_id = self._input_int("Masukkan ID transaksi : ")
        items = self.__db.get_transaction_items(tx_id)
        if not items:
            self._err("Transaksi tidak ditemukan atau tidak memiliki item.")
            return
        self._title(f"DETAIL TRANSAKSI TRX-{tx_id:05d}")
        total = 0.0
        for item in items:
            print(item.display_info())
            total += item.subtotal()
        self._sep("─")
        print(f"  {'TOTAL':>55} Rp {total:>12,.0f}")

    def _show_low_stock(self):
        products = self.__db.get_low_stock(10)
        self._title("PRODUK STOK MENIPIS (≤ 10)")
        if not products:
            print("  Semua produk stok aman.")
        else:
            print(f"  {'ID':<5} {'Nama':<30} {'Stok':>6}")
            self._sep("─")
            for p in products:
                warn = "⚠ HABIS" if p.stock == 0 else ""
                print(f"  {p.id:<5} {p.name:<30} {p.stock:>5} {warn}")
