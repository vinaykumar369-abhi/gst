import sys
import sqlite3
import re
import os
import csv
import shutil
import subprocess
from datetime import datetime, timedelta
from decimal import Decimal

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QTableWidget, QTableWidgetItem, QHeaderView, QLineEdit, 
    QPushButton, QLabel, QComboBox, QFormLayout, QTabWidget,
    QMessageBox, QFrame, QGridLayout, QDateEdit, QSpinBox, QDoubleSpinBox,
    QFileDialog
)
from PyQt6.QtCore import Qt, QDate, QRect, QPoint
from PyQt6.QtGui import QFont, QPainter, QColor, QPen, QBrush

# PDF Generation imports
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet

class SalesChart(QWidget):
    """A custom lightweight bar chart widget for displaying monthly sales trends."""
    def __init__(self, data):
        super().__init__()
        self.data = data # List of (MonthName, Value)
        self.setMinimumHeight(250)

    def paintEvent(self, event):
        if not self.data:
            return
            
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        width = self.width()
        height = self.height()
        padding = 40
        chart_width = width - (2 * padding)
        chart_height = height - (2 * padding)
        
        max_val = max([val for _, val in self.data]) if self.data else 0
        if max_val == 0: max_val = 1
        
        # Draw Axis
        painter.setPen(QPen(QColor("#333333"), 2))
        painter.drawLine(padding, height - padding, width - padding, height - padding) # X
        painter.drawLine(padding, padding, padding, height - padding) # Y
        
        bar_count = len(self.data)
        bar_spacing = chart_width / bar_count
        bar_width = bar_spacing * 0.6
        
        for i, (label, val) in enumerate(self.data):
            bar_h = (val / max_val) * chart_height
            x = padding + (i * bar_spacing) + (bar_spacing - bar_width) / 2
            y = height - padding - bar_h
            
            painter.setBrush(QBrush(QColor("#1976d2")))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRect(int(x), int(y), int(bar_width), int(bar_h))
            
            painter.setPen(QPen(QColor("#555555"), 1))
            painter.setFont(QFont("Arial", 8))
            painter.drawText(QRect(int(x - 5), height - padding + 5, int(bar_width + 10), 20), 
                             Qt.AlignmentFlag.AlignCenter, label)
            
            if val > 0:
                painter.drawText(QRect(int(x - 10), int(y - 20), int(bar_width + 20), 20), 
                                 Qt.AlignmentFlag.AlignCenter, f"₹{int(val)}")

class DatabaseManager:
    """Handles all offline SQLite operations including Stock, History, Reports, Backups, and Expenses."""
    def __init__(self, db_name="gst_billing.db"):
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
            gstin TEXT,
            date TEXT,
            total_taxable REAL,
            total_gst REAL,
            grand_total REAL,
            filename TEXT
        )''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT,
            category TEXT,
            description TEXT,
            amount REAL
        )''')
        self.conn.commit()

    def perform_backup(self):
        try:
            backup_dir = "backups"
            if not os.path.exists(backup_dir): os.makedirs(backup_dir)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = os.path.join(backup_dir, f"backup_gst_billing_{timestamp}.db")
            self.conn.close()
            shutil.copy2(self.db_name, backup_file)
            self.conn = sqlite3.connect(self.db_name)
            backups = sorted([os.path.join(backup_dir, f) for f in os.listdir(backup_dir)])
            if len(backups) > 10:
                for old_backup in backups[:-10]: os.remove(old_backup)
            return True, backup_file
        except Exception as e:
            return False, str(e)

    def get_stats(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT SUM(grand_total) FROM invoices")
        sales = cursor.fetchone()[0] or 0.0
        
        cursor.execute("SELECT SUM(total_gst) FROM invoices")
        gst = cursor.fetchone()[0] or 0.0
        
        cursor.execute("SELECT SUM(amount) FROM expenses")
        expenses = cursor.fetchone()[0] or 0.0
        
        profit = sales - gst - expenses
        return sales, gst, expenses, profit

    def get_low_stock_items(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT name, stock FROM products WHERE stock < 5")
        return cursor.fetchall()

    def get_monthly_trends(self):
        cursor = self.conn.cursor()
        trends = []
        for i in range(5, -1, -1):
            target_date = datetime.now() - timedelta(days=i*30)
            month_str = target_date.strftime("%Y-%m")
            month_name = target_date.strftime("%b")
            cursor.execute("SELECT SUM(grand_total) FROM invoices WHERE date LIKE ?", (f"{month_str}%",))
            val = cursor.fetchone()[0] or 0.0
            trends.append((month_name, val))
        return trends

    def get_invoices_by_date(self, start_date, end_date):
        cursor = self.conn.cursor()
        cursor.execute('''SELECT date, customer_name, gstin, total_taxable, total_gst, grand_total 
                          FROM invoices 
                          WHERE date BETWEEN ? AND ? 
                          ORDER BY date ASC''', (start_date, end_date))
        return cursor.fetchall()

class GSTEngine:
    @staticmethod
    def calculate(taxable_value, rate, is_interstate=False):
        taxable = Decimal(str(taxable_value))
        gst_rate = Decimal(str(rate))
        gst_amount = (taxable * gst_rate) / Decimal('100')
        total = taxable + gst_amount
        if is_interstate:
            return {"taxable": taxable, "igst": gst_amount, "cgst": Decimal('0'), "sgst": Decimal('0'), "total": total}
        else:
            split_gst = gst_amount / Decimal('2')
            return {"taxable": taxable, "igst": Decimal('0'), "cgst": split_gst, "sgst": split_gst, "total": total}

class InvoiceApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.db = DatabaseManager()
        self.setWindowTitle("GST Billing Pro - Premium Edition")
        self.setMinimumSize(1200, 850)
        self.init_ui()
        self.refresh_dashboard()

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        self.tabs = QTabWidget()
        self.tabs.addTab(self.create_dashboard_tab(), "Dashboard")
        self.tabs.addTab(self.create_invoice_tab(), "New Invoice")
        self.tabs.addTab(self.create_inventory_tab(), "Inventory")
        self.tabs.addTab(self.create_expense_tab(), "Expenses")
        self.tabs.addTab(self.create_history_tab(), "History")
        self.tabs.addTab(self.create_reports_tab(), "Reports")
        
        self.tabs.currentChanged.connect(self.on_tab_change)
        main_layout.addWidget(self.tabs)

    def closeEvent(self, event):
        self.db.perform_backup()
        event.accept()

    def on_tab_change(self, index):
        if index == 0: self.refresh_dashboard()
        elif index == 2: self.refresh_stock_table()
        elif index == 3: self.refresh_expense_table()
        elif index == 4: self.refresh_history_table()

    def create_dashboard_tab(self):
        widget = QWidget()
        self.dash_layout = QVBoxLayout(widget)
        
        header_layout = QHBoxLayout()
        header = QLabel("Business Performance")
        header.setFont(QFont("Arial", 22, QFont.Weight.Bold))
        header_layout.addWidget(header)
        header_layout.addStretch()
        
        self.alert_label = QLabel("")
        self.alert_label.setStyleSheet("color: #d32f2f; font-weight: bold; background: #ffebee; padding: 5px 15px; border-radius: 15px;")
        self.alert_label.setHidden(True)
        header_layout.addWidget(self.alert_label)
        
        self.dash_layout.addLayout(header_layout)
        
        self.grid = QGridLayout()
        self.dash_layout.addLayout(self.grid)
        
        self.chart_container = QFrame()
        self.chart_container.setStyleSheet("background-color: white; border: 1px solid #ddd; border-radius: 8px;")
        self.chart_vbox = QVBoxLayout(self.chart_container)
        self.dash_layout.addWidget(QLabel("<b>Monthly Sales Trend (Last 6 Months)</b>"))
        self.dash_layout.addWidget(self.chart_container)
        
        self.dash_layout.addStretch()
        return widget

    def refresh_dashboard(self):
        # Refresh Cards
        for i in reversed(range(self.grid.count())): 
            item = self.grid.itemAt(i)
            if item.widget(): item.widget().setParent(None)
            
        sales, gst, expenses, profit = self.db.get_stats()
        stats = [
            ("Gross Sales", f"₹ {sales:,.2f}", "#e3f2fd"),
            ("GST Payable", f"₹ {gst:,.2f}", "#f3e5f5"),
            ("Expenses", f"₹ {expenses:,.2f}", "#ffebee"),
            ("Net Profit", f"₹ {profit:,.2f}", "#f1f8e9")
        ]
        
        for i, (title, val, color) in enumerate(stats):
            frame = QFrame()
            frame.setStyleSheet(f"background-color: {color}; border-radius: 12px; border: 1px solid #cfd8dc;")
            f_layout = QVBoxLayout(frame)
            t_lbl = QLabel(title); t_lbl.setStyleSheet("color: #546e7a; font-size: 14px;")
            f_layout.addWidget(t_lbl)
            val_lbl = QLabel(val); val_lbl.setFont(QFont("Segoe UI", 22, QFont.Weight.Bold))
            f_layout.addWidget(val_lbl)
            self.grid.addWidget(frame, 0, i)
            
        # Refresh Chart
        for i in reversed(range(self.chart_vbox.count())):
            item = self.chart_vbox.itemAt(i)
            if item.widget(): item.widget().setParent(None)
        trends = self.db.get_monthly_trends()
        self.chart_vbox.addWidget(SalesChart(trends))
        
        # Check Stock Alerts
        low_stock = self.db.get_low_stock_items()
        if low_stock:
            self.alert_label.setText(f"⚠️ {len(low_stock)} Items Low in Stock!")
            self.alert_label.setHidden(False)
        else:
            self.alert_label.setHidden(True)

    def create_invoice_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        cust_group = QFrame()
        cust_group.setStyleSheet("background-color: #fafafa; border: 1px solid #ddd; border-radius: 5px;")
        cust_layout = QGridLayout(cust_group)
        self.cust_name = QLineEdit(); self.cust_gstin = QLineEdit()
        self.place_of_supply = QComboBox(); self.place_of_supply.addItems(["Intra-state (Local)", "Inter-state (Outside State)"])
        cust_layout.addWidget(QLabel("<b>Customer Name:</b>"), 0, 0)
        cust_layout.addWidget(self.cust_name, 0, 1)
        cust_layout.addWidget(QLabel("<b>GSTIN:</b>"), 0, 2)
        cust_layout.addWidget(self.cust_gstin, 0, 3)
        cust_layout.addWidget(QLabel("<b>Supply Type:</b>"), 0, 4)
        cust_layout.addWidget(self.place_of_supply, 0, 5)
        layout.addWidget(cust_group)
        self.item_table = QTableWidget(0, 7)
        self.item_table.setHorizontalHeaderLabels(["Item Name", "HSN/SAC", "Qty", "Price", "GST %", "Taxable Amt", "Total"])
        self.item_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.item_table)
        btn_layout = QHBoxLayout()
        add_row_btn = QPushButton("+ Add Row"); add_row_btn.clicked.connect(self.add_item_row)
        generate_btn = QPushButton("Generate Invoice & Update Stock")
        generate_btn.setStyleSheet("background-color: #2e7d32; color: white; font-weight: bold; padding: 12px;")
        generate_btn.clicked.connect(self.generate_invoice)
        btn_layout.addWidget(add_row_btn); btn_layout.addStretch(); btn_layout.addWidget(generate_btn)
        layout.addLayout(btn_layout)
        return widget

    def create_inventory_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        add_group = QFrame(); form = QFormLayout(add_group)
        self.prod_name = QLineEdit(); self.prod_hsn = QLineEdit()
        self.prod_price = QDoubleSpinBox(); self.prod_price.setRange(0, 1000000.0)
        self.prod_gst = QComboBox(); self.prod_gst.addItems(["0", "5", "12", "18", "28"])
        self.prod_stock = QSpinBox(); self.prod_stock.setRange(0, 10000)
        form.addRow("Product Name:", self.prod_name); form.addRow("HSN Code:", self.prod_hsn)
        form.addRow("Base Price (₹):", self.prod_price); form.addRow("GST Slab %:", self.prod_gst); form.addRow("Stock:", self.prod_stock)
        save_btn = QPushButton("Save Product"); save_btn.clicked.connect(self.save_product)
        form.addRow(save_btn)
        layout.addWidget(add_group)
        self.stock_table = QTableWidget(0, 5)
        self.stock_table.setHorizontalHeaderLabels(["ID", "Name", "HSN", "GST %", "Stock Level"])
        self.stock_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.stock_table)
        return widget

    def create_expense_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        exp_group = QFrame(); form = QFormLayout(exp_group)
        self.exp_desc = QLineEdit(); self.exp_amt = QDoubleSpinBox(); self.exp_amt.setRange(0, 1000000)
        self.exp_cat = QComboBox(); self.exp_cat.addItems(["Rent", "Utilities", "Salary", "Purchase", "Other"])
        form.addRow("Category:", self.exp_cat); form.addRow("Description:", self.exp_desc); form.addRow("Amount (₹):", self.exp_amt)
        add_btn = QPushButton("Add Expense"); add_btn.clicked.connect(self.save_expense)
        form.addRow(add_btn)
        layout.addWidget(exp_group)
        self.exp_table = QTableWidget(0, 4)
        self.exp_table.setHorizontalHeaderLabels(["Date", "Category", "Description", "Amount (₹)"])
        self.exp_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.exp_table)
        return widget

    def save_expense(self):
        cat, desc, amt = self.exp_cat.currentText(), self.exp_desc.text(), self.exp_amt.value()
        if amt <= 0: return
        cursor = self.db.conn.cursor()
        cursor.execute("INSERT INTO expenses (date, category, description, amount) VALUES (?, ?, ?, ?)",
                       (datetime.now().strftime('%Y-%m-%d'), cat, desc, amt))
        self.db.conn.commit()
        self.exp_desc.clear(); self.exp_amt.setValue(0); self.refresh_expense_table()

    def refresh_expense_table(self):
        cursor = self.db.conn.cursor()
        cursor.execute("SELECT date, category, description, amount FROM expenses ORDER BY id DESC")
        rows = cursor.fetchall(); self.exp_table.setRowCount(0)
        for row_data in rows:
            row_idx = self.exp_table.rowCount(); self.exp_table.insertRow(row_idx)
            for col, val in enumerate(row_data):
                self.exp_table.setItem(row_idx, col, QTableWidgetItem(str(val)))

    def create_history_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        self.history_table = QTableWidget(0, 6)
        self.history_table.setHorizontalHeaderLabels(["ID", "Date", "Customer", "GSTIN", "Total", "Action"])
        self.history_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.history_table)
        return widget

    def create_reports_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        csv_btn = QPushButton("Export Sales Report (CSV)"); csv_btn.clicked.connect(self.export_csv_report)
        backup_btn = QPushButton("Manual Backup"); backup_btn.clicked.connect(self.manual_backup)
        layout.addWidget(csv_btn); layout.addWidget(backup_btn); layout.addStretch()
        return widget

    def manual_backup(self):
        success, message = self.db.perform_backup()
        if success: QMessageBox.information(self, "Backup", "Success!")
        else: QMessageBox.critical(self, "Error", message)

    def export_csv_report(self):
        data = self.db.get_invoices_by_date("2000-01-01", "2100-01-01")
        f, _ = QFileDialog.getSaveFileName(self, "Save", "Sales_Report.csv", "CSV (*.csv)")
        if f:
            with open(f, 'w', newline='') as file:
                writer = csv.writer(file)
                writer.writerow(["Date", "Customer", "GSTIN", "Taxable", "GST", "Total"])
                writer.writerows(data)

    def refresh_stock_table(self):
        cursor = self.db.conn.cursor()
        cursor.execute("SELECT id, name, hsn, gst_rate, stock FROM products")
        rows = cursor.fetchall(); self.stock_table.setRowCount(0)
        for row in rows:
            idx = self.stock_table.rowCount(); self.stock_table.insertRow(idx)
            for col, val in enumerate(row):
                item = QTableWidgetItem(str(val))
                if col == 4 and val < 5: item.setForeground(QColor("red"))
                self.stock_table.setItem(idx, col, item)

    def refresh_history_table(self):
        cursor = self.db.conn.cursor()
        cursor.execute("SELECT id, date, customer_name, gstin, grand_total, filename FROM invoices ORDER BY id DESC")
        rows = cursor.fetchall(); self.history_table.setRowCount(0)
        for row in rows:
            idx = self.history_table.rowCount(); self.history_table.insertRow(idx)
            for col in range(5): self.history_table.setItem(idx, col, QTableWidgetItem(str(row[col])))
            btn = QPushButton("View PDF"); btn.clicked.connect(lambda ch, f=row[5]: self.open_invoice_pdf(f))
            self.history_table.setCellWidget(idx, 5, btn)

    def open_invoice_pdf(self, f):
        if os.path.exists(f): 
            if sys.platform == 'win32': os.startfile(f)
            else: subprocess.call(['open' if sys.platform == 'darwin' else 'xdg-open', f])

    def add_item_row(self):
        r = self.item_table.rowCount(); self.item_table.insertRow(r)
        for i in range(7): self.item_table.setItem(r, i, QTableWidgetItem(""))

    def save_product(self):
        n, h, p, g, s = self.prod_name.text(), self.prod_hsn.text(), self.prod_price.value(), float(self.prod_gst.currentText()), self.prod_stock.value()
        if not n: return
        cursor = self.db.conn.cursor()
        cursor.execute("INSERT INTO products (name, hsn, price, gst_rate, stock) VALUES (?, ?, ?, ?, ?) ON CONFLICT(name) DO UPDATE SET hsn=excluded.hsn, price=excluded.price, gst_rate=excluded.gst_rate, stock=excluded.stock", (n, h, p, g, s))
        self.db.conn.commit(); self.refresh_stock_table()

    def generate_invoice(self):
        is_inter = self.place_of_supply.currentIndex() == 1
        items, taxable_total, gst_total, grand_total = [], Decimal('0'), Decimal('0'), Decimal('0')
        cursor = self.db.conn.cursor()
        for row in range(self.item_table.rowCount()):
            name_item = self.item_table.item(row, 0)
            if not name_item or not name_item.text(): continue
            name, qty = name_item.text(), int(self.item_table.item(row, 2).text() or 0)
            price, rate = Decimal(self.item_table.item(row, 3).text() or '0'), Decimal(self.item_table.item(row, 4).text() or '0')
            cursor.execute("SELECT stock FROM products WHERE name = ?", (name,))
            r = cursor.fetchone()
            if not r or r[0] < qty: QMessageBox.warning(self, "Stock", f"Low stock: {name}"); return
            cursor.execute("UPDATE products SET stock = stock - ? WHERE name = ?", (qty, name))
            taxable = qty * price; res = GSTEngine.calculate(taxable, rate, is_inter)
            taxable_total += taxable; gst_total += (res['cgst'] + res['sgst'] + res['igst']); grand_total += res['total']
            items.append([name, self.item_table.item(row,1).text(), str(qty), f"{price:.2f}", f"{res['cgst']:.2f}", f"{res['sgst'] if not is_inter else res['igst']:.2f}", f"{res['total']:.2f}"])
        
        fname = f"Invoice_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        cursor.execute("INSERT INTO invoices (customer_name, gstin, date, total_taxable, total_gst, grand_total, filename) VALUES (?, ?, ?, ?, ?, ?, ?)",
                       (self.cust_name.text(), self.cust_gstin.text(), datetime.now().strftime('%Y-%m-%d'), float(taxable_total), float(gst_total), float(grand_total), fname))
        self.db.conn.commit(); self.create_pdf(items, grand_total, fname); self.refresh_dashboard()

    def create_pdf(self, data, total, filename):
        doc = SimpleDocTemplate(filename, pagesize=A4); styles = getSampleStyleSheet()
        elements = [Paragraph("TAX INVOICE", styles['Title']), Paragraph(f"Bill To: {self.cust_name.text() or 'Cash'}", styles['Normal']), Spacer(1, 20)]
        t = Table([["Item", "HSN", "Qty", "Rate", "CGST", "SGST/IGST", "Total"]] + data + [["", "", "", "", "", "TOTAL", f"{total:,.2f}"]])
        t.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,0), colors.grey), ('GRID', (0,0), (-1,-1), 0.5, colors.black)]))
        elements.append(t); doc.build(elements)

if __name__ == "__main__":
    app = QApplication(sys.argv); app.setStyle("Fusion")
    win = InvoiceApp(); win.show(); sys.exit(app.exec())
