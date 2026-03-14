import sys
import sqlite3
import os
import subprocess
from datetime import datetime
from decimal import Decimal

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QTableWidget, QTableWidgetItem, QHeaderView, QLineEdit, 
    QPushButton, QLabel, QComboBox, QFormLayout, QTabWidget,
    QMessageBox, QFrame, QSpinBox, QDoubleSpinBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QColor

# PDF Generation imports
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet

class DatabaseManager:
    """Simplified Database for Stock and Invoices."""
    def __init__(self, db_name="gst_billing_simple.db"):
        self.db_name = db_name
        self.conn = sqlite3.connect(db_name)
        self.create_tables()

    def create_tables(self):
        cursor = self.conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            hsn TEXT,
            price REAL,
            gst_rate REAL,
            stock INTEGER DEFAULT 0
        )''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS invoices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_name TEXT,
            date TEXT,
            grand_total REAL,
            filename TEXT
        )''')
        self.conn.commit()

class InvoiceApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.db = DatabaseManager()
        self.setWindowTitle("GST Billing Simple - Small Business Edition")
        self.setMinimumSize(900, 700)
        self.init_ui()

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        self.tabs = QTabWidget()
        self.tabs.addTab(self.create_invoice_tab(), "Create Bill")
        self.tabs.addTab(self.create_inventory_tab(), "Stock Manager")
        self.tabs.addTab(self.create_history_tab(), "Past Bills")
        
        layout.addWidget(self.tabs)

    def create_invoice_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        cust_group = QFrame()
        cust_layout = QFormLayout(cust_group)
        self.cust_name = QLineEdit()
        self.supply_type = QComboBox()
        self.supply_type.addItems(["Local (CGST/SGST)", "Inter-state (IGST)"])
        cust_layout.addRow("Customer Name:", self.cust_name)
        cust_layout.addRow("Tax Type:", self.supply_type)
        layout.addWidget(cust_group)

        self.item_table = QTableWidget(5, 5)
        self.item_table.setHorizontalHeaderLabels(["Item Name", "Qty", "Rate", "GST %", "Total"])
        self.item_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.item_table)

        gen_btn = QPushButton("Generate & Save Invoice")
        gen_btn.setStyleSheet("background-color: #1976d2; color: white; height: 40px; font-weight: bold;")
        gen_btn.clicked.connect(self.generate_invoice)
        layout.addWidget(gen_btn)
        return widget

    def create_inventory_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        form = QFormLayout()
        self.p_name = QLineEdit(); self.p_price = QDoubleSpinBox(); self.p_price.setRange(0, 999999)
        self.p_gst = QComboBox(); self.p_gst.addItems(["5", "12", "18", "28"])
        self.p_stock = QSpinBox(); self.p_stock.setRange(0, 9999); self.p_hsn = QLineEdit()
        
        form.addRow("Product Name:", self.p_name)
        form.addRow("HSN Code:", self.p_hsn)
        form.addRow("Price (Excl. GST):", self.p_price)
        form.addRow("GST %:", self.p_gst)
        form.addRow("Initial Stock:", self.p_stock)
        
        add_btn = QPushButton("Add/Update Product")
        add_btn.clicked.connect(self.save_product)
        form.addRow(add_btn)
        
        layout.addLayout(form)
        self.stock_table = QTableWidget(0, 4)
        self.stock_table.setHorizontalHeaderLabels(["Name", "Price", "GST", "Stock"])
        self.stock_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.stock_table)
        self.refresh_stock()
        return widget

    def create_history_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        self.hist_table = QTableWidget(0, 4)
        self.hist_table.setHorizontalHeaderLabels(["ID", "Date", "Customer", "Total"])
        layout.addWidget(self.hist_table)
        refresh_btn = QPushButton("Refresh History")
        refresh_btn.clicked.connect(self.refresh_history)
        layout.addWidget(refresh_btn)
        return widget

    def save_product(self):
        name = self.p_name.text()
        if not name: return
        cursor = self.db.conn.cursor()
        cursor.execute("INSERT INTO products (name, hsn, price, gst_rate, stock) VALUES (?, ?, ?, ?, ?) ON CONFLICT(name) DO UPDATE SET price=excluded.price, stock=excluded.stock", 
                       (name, self.p_hsn.text(), self.p_price.value(), float(self.p_gst.currentText()), self.p_stock.value()))
        self.db.conn.commit()
        self.refresh_stock()
        QMessageBox.information(self, "Success", "Product Saved")

    def refresh_stock(self):
        cursor = self.db.conn.cursor()
        cursor.execute("SELECT name, price, gst_rate, stock FROM products")
        rows = cursor.fetchall()
        self.stock_table.setRowCount(0)
        for row_data in rows:
            row_idx = self.stock_table.rowCount(); self.stock_table.insertRow(row_idx)
            for col, val in enumerate(row_data):
                self.stock_table.setItem(row_idx, col, QTableWidgetItem(str(val)))

    def refresh_history(self):
        cursor = self.db.conn.cursor()
        cursor.execute("SELECT id, date, customer_name, grand_total FROM invoices ORDER BY id DESC")
        rows = cursor.fetchall()
        self.hist_table.setRowCount(0)
        for row_data in rows:
            row_idx = self.hist_table.rowCount(); self.hist_table.insertRow(row_idx)
            for col, val in enumerate(row_data):
                self.hist_table.setItem(row_idx, col, QTableWidgetItem(str(val)))

    def generate_invoice(self):
        cust = self.cust_name.text() or "Cash Customer"
        is_igst = self.supply_type.currentIndex() == 1
        invoice_items = []
        grand_total = Decimal('0')

        cursor = self.db.conn.cursor()
        for r in range(self.item_table.rowCount()):
            name_item = self.item_table.item(r, 0)
            if not name_item or not name_item.text(): continue
            
            name = name_item.text()
            qty = int(self.item_table.item(r, 1).text() or 0)
            price = Decimal(self.item_table.item(r, 2).text() or '0')
            gst_p = Decimal(self.item_table.item(r, 3).text() or '0')
            
            taxable = qty * price
            gst_amt = (taxable * gst_p) / Decimal('100')
            total = taxable + gst_amt
            grand_total += total
            
            invoice_items.append([name, str(qty), f"{price:.2f}", f"{gst_p}%", f"{total:.2f}"])
            cursor.execute("UPDATE products SET stock = stock - ? WHERE name = ?", (qty, name))

        fname = f"Bill_{datetime.now().strftime('%H%M%S')}.pdf"
        cursor.execute("INSERT INTO invoices (customer_name, date, grand_total, filename) VALUES (?, ?, ?, ?)",
                       (cust, datetime.now().strftime('%Y-%m-%d'), float(grand_total), fname))
        self.db.conn.commit()
        
        self.create_pdf(cust, invoice_items, grand_total, fname)
        QMessageBox.information(self, "Success", f"Invoice Generated: {fname}")

    def create_pdf(self, cust, items, total, fname):
        doc = SimpleDocTemplate(fname, pagesize=A4)
        styles = getSampleStyleSheet()
        elements = [
            Paragraph("RETAIL INVOICE", styles['Title']),
            Paragraph(f"Customer: {cust}", styles['Normal']),
            Paragraph(f"Date: {datetime.now().strftime('%d-%m-%Y')}", styles['Normal']),
            Spacer(1, 15)
        ]
        table_data = [["Item", "Qty", "Rate", "GST", "Total"]] + items + [["", "", "", "TOTAL", f"Rs. {total:,.2f}"]]
        t = Table(table_data)
        t.setStyle(TableStyle([('GRID', (0,0), (-1,-1), 1, colors.black), ('BACKGROUND', (0,0), (-1,0), colors.lightgrey)]))
        elements.append(t)
        doc.build(elements)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = InvoiceApp()
    window.show()
    sys.exit(app.exec())
