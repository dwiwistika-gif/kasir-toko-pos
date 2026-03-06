"""
Module: models
==============
Berisi kelas-kelas model data untuk sistem kasir.
Menerapkan OOP: inheritance, polymorphism, overloading, interface (ABC),
hak akses (private/protected), dan properties.

Author  : Asesi
Version : 1.0.0
"""

from abc import ABC, abstractmethod
from datetime import datetime


# ─── Interface (Abstract Base Class) ─────────────────────────────────────────

class Printable(ABC):
    """
    Interface: Printable
    Setiap entitas yang dapat ditampilkan/dicetak harus
    mengimplementasikan method ini.
    """

    @abstractmethod
    def display_info(self) -> str:
        """Mengembalikan informasi entitas dalam format string."""
        pass

    @abstractmethod
    def to_dict(self) -> dict:
        """Mengkonversi entitas ke dictionary."""
        pass


# ─── Base Class ───────────────────────────────────────────────────────────────

class BaseEntity(Printable):
    """
    Kelas dasar untuk semua entitas dalam sistem POS.

    Attributes:
        __id (int): ID unik entitas (private).
        _created_at (str): Timestamp pembuatan (protected).
    """

    def __init__(self, entity_id: int = None):
        self.__id: int = entity_id
        self._created_at: str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    @property
    def id(self) -> int:
        """Property getter: id entitas."""
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


# ─── Product Class ────────────────────────────────────────────────────────────

class Product(BaseEntity):
    """
    Kelas Product: merepresentasikan produk/barang di toko.
    Mewarisi BaseEntity, mengimplementasi interface Printable.

    Attributes:
        CATEGORIES (list): Array kategori produk yang tersedia.
    """

    # Array/list konstanta kategori produk
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
        self.name: str = name
        self.category: str = category
        self.__price: float = price     # private
        self.__stock: int = stock       # private
        self.barcode: str = barcode

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

    def is_available(self) -> bool:
        """Mengecek ketersediaan stok produk."""
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
            "id": self.id,
            "name": self.name,
            "category": self.category,
            "price": self.__price,
            "stock": self.__stock,
            "barcode": self.barcode,
        }

    def __str__(self) -> str:
        return f"Product({self.name!r}, {self.formatted_price()})"

    def __repr__(self) -> str:
        return f"Product(id={self.id}, name={self.name!r})"


# ─── TransactionItem Class ────────────────────────────────────────────────────

class TransactionItem(BaseEntity):
    """
    Kelas TransactionItem: merepresentasikan satu baris item dalam transaksi.
    Mewarisi BaseEntity, mengimplementasi interface Printable.

    Attributes:
        transaction_id (int): ID transaksi induk.
        product_id (int): ID produk yang dibeli.
        quantity (int): Jumlah yang dibeli.
        unit_price (float): Harga satuan saat transaksi.
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
        self.transaction_id: int = transaction_id
        self.product_id: int = product_id
        self.__quantity: int = quantity      # private
        self.__unit_price: float = unit_price  # private
        self.product_name: str = product_name

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
        """Menghitung subtotal item (qty x harga)."""
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
            "id": self.id,
            "transaction_id": self.transaction_id,
            "product_id": self.product_id,
            "quantity": self.__quantity,
            "unit_price": self.__unit_price,
            "subtotal": self.subtotal(),
        }


# ─── Transaction Class ────────────────────────────────────────────────────────

class Transaction(BaseEntity):
    """
    Kelas Transaction: merepresentasikan satu transaksi penjualan.
    Mewarisi BaseEntity, mengimplementasi interface Printable.

    Attributes:
        items (list[TransactionItem]): Daftar item dalam transaksi.
    """

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
        self.cashier: str = cashier
        self.payment_method: str = payment_method
        self.__total: float = total         # private
        self.__paid: float = paid           # private
        self.transaction_date: str = transaction_date or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.items: list = items or []      # array item transaksi

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
        """Menghitung kembalian."""
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
            "id": self.id,
            "cashier": self.cashier,
            "payment_method": self.payment_method,
            "total": self.__total,
            "paid": self.__paid,
            "transaction_date": self.transaction_date,
        }
