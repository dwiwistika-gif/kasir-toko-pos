"""
Point of Sale (POS) System - Sistem Kasir Toko
===============================================
Aplikasi kasir sederhana berbasis terminal untuk mengelola
produk, transaksi penjualan, dan laporan pendapatan.

Author  : Asesi
Version : 1.0.0
Date    : 2025
"""

import sys
from packages.database import DatabaseManager
from packages.ui import UserInterface


def main():
    """
    Entry point utama program.
    Menginisialisasi database dan memulai antarmuka pengguna.
    """
    print("=" * 60)
    print("   SISTEM KASIR TOKO - Point of Sale (POS)")
    print("   POS System v1.0")
    print("=" * 60)

    db = DatabaseManager("pos.db")
    db.initialize()

    ui = UserInterface(db)
    ui.run()


if __name__ == "__main__":
    main()
