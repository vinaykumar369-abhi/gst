import React, { useState, useEffect, useMemo } from 'react';

// --- EXTERNAL LIBRARIES (CDN) ---
// We inject these scripts to ensure the offline-first database works in this environment
const loadScript = (src) => {
  return new Promise((resolve) => {
    const script = document.createElement('script');
    script.src = src;
    script.onload = () => resolve(window.Dexie || window.lucide);
    document.head.appendChild(script);
  });
};

// --- CONSTANTS ---
const GST_SLABS = [0, 5, 12, 18, 28];
const STATES = [
  "01-Jammu & Kashmir", "02-Himachal Pradesh", "03-Punjab", "04-Chandigarh", "05-Uttarakhand",
  "06-Haryana", "07-Delhi", "08-Rajasthan", "09-Uttar Pradesh", "10-Bihar", "19-West Bengal",
  "24-Gujarat", "27-Maharashtra", "29-Karnataka", "32-Kerala", "33-Tamil Nadu", "36-Telangana"
];

// --- MAIN APPLICATION COMPONENT ---
export default function App() {
  const [db, setDb] = useState(null);
  const [activeTab, setActiveTab] = useState('dashboard');
  const [myBusiness, setMyBusiness] = useState({
    name: 'My Business Name',
    gstin: '',
    state: '27-Maharashtra',
    address: '123 Business Street'
  });

  // Initialize Database and Dependencies
  useEffect(() => {
    const init = async () => {
      const DexieClass = await loadScript('https://unpkg.com/dexie@latest/dist/dexie.js');
      const newDb = new DexieClass('GSTBillingDB');
      newDb.version(1).stores({
        products: '++id, name, hsn, price, gstRate',
        invoices: '++id, invoiceNo, date, customerName, totalAmount',
        settings: 'id, businessName, gstin, state'
      });
      
      const saved = await newDb.settings.get(1);
      if (saved) setMyBusiness(saved);
      setDb(newDb);
    };
    init();
  }, []);

  const saveSettings = async (newData) => {
    setMyBusiness(newData);
    if (db) await db.settings.put({ id: 1, ...newData });
  };

  if (!db) return <div className="flex items-center justify-center h-screen bg-slate-900 text-white font-bold">Initializing Offline Database...</div>;

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col md:flex-row font-sans text-slate-900">
      {/* Sidebar */}
      <nav className="w-full md:w-64 bg-slate-900 text-white p-6 space-y-8 print:hidden">
        <div className="flex items-center gap-3">
          <div className="bg-blue-600 p-2 rounded-lg">
            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/><polyline points="10 9 9 9 8 9"/></svg>
          </div>
          <h1 className="text-xl font-bold tracking-tight">GST Billing <span className="text-blue-400">Pro</span></h1>
        </div>

        <div className="space-y-2">
          <SidebarLink icon="layout-dashboard" label="Dashboard" active={activeTab === 'dashboard'} onClick={() => setActiveTab('dashboard')} />
          <SidebarLink icon="plus-circle" label="New Invoice" active={activeTab === 'billing'} onClick={() => setActiveTab('billing')} />
          <SidebarLink icon="package" label="Products" active={activeTab === 'products'} onClick={() => setActiveTab('products')} />
          <SidebarLink icon="history" label="History" active={activeTab === 'history'} onClick={() => setActiveTab('history')} />
        </div>

        <div className="pt-10 border-t border-slate-800">
          <p className="text-xs text-slate-500 uppercase font-bold mb-4">Business Profile</p>
          <input 
            className="w-full bg-slate-800 border-none rounded p-2 text-sm mb-2 focus:ring-1 focus:ring-blue-500 outline-none"
            value={myBusiness.name}
            onChange={(e) => saveSettings({...myBusiness, name: e.target.value})}
            placeholder="Business Name"
          />
          <select 
            className="w-full bg-slate-800 border-none rounded p-2 text-sm focus:ring-1 focus:ring-blue-500 outline-none"
            value={myBusiness.state}
            onChange={(e) => saveSettings({...myBusiness, state: e.target.value})}
          >
            {STATES.map(s => <option key={s} value={s}>{s}</option>)}
          </select>
        </div>
      </nav>

      {/* Main Content Area */}
      <main className="flex-1 p-4 md:p-8 overflow-y-auto">
        {activeTab === 'dashboard' && <Dashboard db={db} />}
        {activeTab === 'billing' && <BillingSection db={db} myBusiness={myBusiness} />}
        {activeTab === 'products' && <ProductManager db={db} />}
        {activeTab === 'history' && <InvoiceHistory db={db} />}
      </main>
    </div>
  );
}

// --- SUB-COMPONENTS ---

function SidebarLink({ icon, label, active, onClick }) {
  return (
    <button 
      onClick={onClick}
      className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl transition-all ${
        active ? 'bg-blue-600 text-white shadow-lg shadow-blue-900/20' : 'text-slate-400 hover:bg-slate-800 hover:text-white'
      }`}
    >
      <span className="w-5 h-5 opacity-80 uppercase text-[10px] font-bold flex items-center justify-center border border-current rounded">
        {label[0]}
      </span>
      <span className="font-medium text-sm">{label}</span>
    </button>
  );
}

function Dashboard({ db }) {
  const [stats, setStats] = useState({ totalSales: 0, taxCollected: 0, count: 0 });

  useEffect(() => {
    db.invoices.toArray().then(items => {
      const totals = items.reduce((acc, curr) => ({
        totalSales: acc.totalSales + curr.totalAmount,
        taxCollected: acc.taxCollected + curr.totalTax,
        count: acc.count + 1
      }), { totalSales: 0, taxCollected: 0, count: 0 });
      setStats(totals);
    });
  }, [db]);

  return (
    <div className="space-y-6">
      <header>
        <h2 className="text-2xl font-bold">Performance Overview</h2>
        <p className="text-slate-500 text-sm">Real-time local data statistics</p>
      </header>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <StatCard title="Total Revenue" value={`₹${stats.totalSales.toFixed(2)}`} color="bg-blue-500" />
        <StatCard title="GST Collected" value={`₹${stats.taxCollected.toFixed(2)}`} color="bg-emerald-500" />
        <StatCard title="Invoices Issued" value={stats.count} color="bg-purple-500" />
      </div>
    </div>
  );
}

function StatCard({ title, value, color }) {
  return (
    <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-100 flex items-center gap-5">
      <div className={`${color} w-3 h-12 rounded-full`}></div>
      <div>
        <p className="text-slate-500 text-xs font-bold uppercase tracking-wider">{title}</p>
        <p className="text-2xl font-black">{value}</p>
      </div>
    </div>
  );
}

function BillingSection({ db, myBusiness }) {
  const [customer, setCustomer] = useState({ name: '', gstin: '', state: '27-Maharashtra', address: '' });
  const [items, setItems] = useState([{ id: Date.now(), name: '', hsn: '', qty: 1, rate: 0, gst: 18 }]);
  const [availableProducts, setAvailableProducts] = useState([]);

  useEffect(() => {
    db.products.toArray().then(setAvailableProducts);
  }, [db]);

  const addItem = () => setItems([...items, { id: Date.now(), name: '', hsn: '', qty: 1, rate: 0, gst: 18 }]);
  const removeItem = (id) => setItems(items.length > 1 ? items.filter(i => i.id !== id) : items);

  const updateItem = (id, field, value) => {
    setItems(items.map(item => {
      if (item.id === id) {
        if (field === 'name') {
          const prod = availableProducts.find(p => p.name === value);
          if (prod) return { ...item, name: value, hsn: prod.hsn, rate: prod.price, gst: prod.gstRate };
        }
        return { ...item, [field]: value };
      }
      return item;
    }));
  };

  const totals = useMemo(() => {
    return items.reduce((acc, item) => {
      const taxable = (item.qty || 0) * (item.rate || 0);
      const taxAmount = (taxable * (item.gst || 0)) / 100;
      return {
        taxable: acc.taxable + taxable,
        tax: acc.tax + taxAmount,
        total: acc.total + taxable + taxAmount
      };
    }, { taxable: 0, tax: 0, total: 0 });
  }, [items]);

  const isIntraState = myBusiness.state.split('-')[0] === customer.state.split('-')[0];

  const handleSaveInvoice = async () => {
    if (!customer.name) return alert('Customer name is required');
    const inv = {
      invoiceNo: `INV-${Date.now()}`,
      date: new Date().toLocaleDateString(),
      customerName: customer.name,
      customerGSTIN: customer.gstin,
      items,
      taxableValue: totals.taxable,
      totalTax: totals.tax,
      totalAmount: totals.total,
      isIntraState
    };
    await db.invoices.add(inv);
    window.print();
  };

  return (
    <div className="space-y-6">
      <div className="bg-white p-8 rounded-2xl shadow-xl border border-slate-100 max-w-5xl mx-auto print:shadow-none print:border-none print:p-0">
        
        <div className="flex justify-between border-b pb-8 mb-8">
          <div>
            <h1 className="text-3xl font-black text-blue-600 mb-1 uppercase tracking-tighter">Tax Invoice</h1>
            <p className="text-slate-500 font-medium">#{Date.now().toString().slice(-6)}</p>
          </div>
          <div className="text-right">
            <h3 className="font-bold text-lg">{myBusiness.name}</h3>
            <p className="text-sm text-slate-500">{myBusiness.address}</p>
            <p className="text-sm font-bold text-slate-700">GSTIN: {myBusiness.gstin || 'NOT PROVIDED'}</p>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-8 mb-8 print:grid-cols-2">
          <div className="space-y-3">
            <label className="text-xs font-bold text-slate-400 uppercase print:hidden">Bill To:</label>
            <input 
              placeholder="Customer Name" 
              className="w-full text-xl font-bold border-b border-dashed border-slate-200 focus:border-blue-500 outline-none pb-1 bg-transparent"
              value={customer.name}
              onChange={e => setCustomer({...customer, name: e.target.value})}
            />
            <input 
              placeholder="Customer GSTIN (Optional)" 
              className="w-full text-sm border-b border-dashed border-slate-200 outline-none pb-1 bg-transparent"
              value={customer.gstin}
              onChange={e => setCustomer({...customer, gstin: e.target.value})}
            />
            <select 
              className="w-full text-sm border-b border-dashed border-slate-200 outline-none pb-1 bg-transparent"
              value={customer.state}
              onChange={e => setCustomer({...customer, state: e.target.value})}
            >
              {STATES.map(s => <option key={s} value={s}>{s}</option>)}
            </select>
          </div>
          <div className="flex flex-col justify-end text-right">
            <p className="text-sm text-slate-500">Date: <span className="text-slate-900 font-bold">{new Date().toLocaleDateString()}</span></p>
            <p className="text-sm text-slate-500">Place of Supply: <span className="text-slate-900 font-bold">{customer.state}</span></p>
          </div>
        </div>

        <div className="overflow-x-auto mb-8">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-slate-50 text-slate-500 text-xs uppercase tracking-wider font-bold">
                <th className="p-3 rounded-l-lg">Item Description</th>
                <th className="p-3 text-center">HSN</th>
                <th className="p-3 text-center">Qty</th>
                <th className="p-3 text-right">Rate</th>
                <th className="p-3 text-center">GST %</th>
                <th className="p-3 text-right">Taxable</th>
                <th className="p-3 text-right rounded-r-lg print:hidden"></th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {items.map((item) => (
                <tr key={item.id} className="group">
                  <td className="py-4 px-3">
                    <input 
                      list="product-list"
                      className="w-full font-medium outline-none focus:text-blue-600 bg-transparent"
                      value={item.name}
                      onChange={e => updateItem(item.id, 'name', e.target.value)}
                      placeholder="Enter Item Name"
                    />
                    <datalist id="product-list">
                      {availableProducts.map(p => <option key={p.id} value={p.name} />)}
                    </datalist>
                  </td>
                  <td className="p-3">
                    <input className="w-16 text-center text-sm outline-none bg-transparent" value={item.hsn} onChange={e => updateItem(item.id, 'hsn', e.target.value)} />
                  </td>
                  <td className="p-3">
                    <input type="number" className="w-12 text-center font-bold outline-none bg-transparent" value={item.qty} onChange={e => updateItem(item.id, 'qty', parseFloat(e.target.value))} />
                  </td>
                  <td className="p-3">
                    <input type="number" className="w-20 text-right outline-none bg-transparent" value={item.rate} onChange={e => updateItem(item.id, 'rate', parseFloat(e.target.value))} />
                  </td>
                  <td className="p-3">
                    <select className="w-14 text-center bg-transparent outline-none" value={item.gst} onChange={e => updateItem(item.id, 'gst', parseInt(e.target.value))}>
                      {GST_SLABS.map(s => <option key={s} value={s}>{s}%</option>)}
                    </select>
                  </td>
                  <td className="p-3 text-right font-bold text-slate-700">
                    ₹{((item.qty || 0) * (item.rate || 0)).toFixed(2)}
                  </td>
                  <td className="p-3 text-right print:hidden">
                    <button onClick={() => removeItem(item.id)} className="text-slate-300 hover:text-red-500">×</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          <button 
            onClick={addItem}
            className="mt-4 flex items-center gap-2 text-blue-600 text-sm font-bold hover:bg-blue-50 px-3 py-2 rounded-lg transition-all print:hidden"
          >
            + Add Another Item
          </button>
        </div>

        <div className="flex flex-col items-end space-y-2 border-t pt-8">
          <div className="w-full max-w-xs space-y-2">
            <div className="flex justify-between text-sm text-slate-500">
              <span>Taxable Value:</span>
              <span className="font-bold">₹{totals.taxable.toFixed(2)}</span>
            </div>
            {isIntraState ? (
              <>
                <div className="flex justify-between text-sm text-slate-500">
                  <span>CGST:</span>
                  <span className="font-bold">₹{(totals.tax / 2).toFixed(2)}</span>
                </div>
                <div className="flex justify-between text-sm text-slate-500">
                  <span>SGST:</span>
                  <span className="font-bold">₹{(totals.tax / 2).toFixed(2)}</span>
                </div>
              </>
            ) : (
              <div className="flex justify-between text-sm text-slate-500">
                <span>IGST:</span>
                <span className="font-bold">₹{totals.tax.toFixed(2)}</span>
              </div>
            )}
            <div className="flex justify-between text-xl font-black text-slate-900 pt-4 border-t-2 border-double border-slate-200">
              <span>Total Amount:</span>
              <span>₹{totals.total.toFixed(2)}</span>
            </div>
          </div>
        </div>

        <div className="mt-12 text-center text-[10px] text-slate-400 uppercase tracking-widest hidden print:block">
          This is a computer generated invoice and does not require a physical signature.
        </div>
      </div>

      <div className="flex justify-center gap-4 print:hidden pb-10">
        <button 
          onClick={handleSaveInvoice}
          className="flex items-center gap-2 bg-blue-600 text-white px-8 py-4 rounded-2xl font-black shadow-xl shadow-blue-200 hover:scale-105 transition-transform"
        >
          Print & Save Invoice
        </button>
      </div>
    </div>
  );
}

function ProductManager({ db }) {
  const [prods, setProds] = useState([]);
  const [newProd, setNewProd] = useState({ name: '', hsn: '', price: 0, gstRate: 18 });

  const load = () => db.products.toArray().then(setProds);
  useEffect(() => { load(); }, [db]);

  const add = async () => {
    if (!newProd.name) return;
    await db.products.add(newProd);
    setNewProd({ name: '', hsn: '', price: 0, gstRate: 18 });
    load();
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <h2 className="text-2xl font-bold">Product Inventory</h2>
      
      <div className="bg-white p-6 rounded-2xl border border-slate-200 grid grid-cols-1 md:grid-cols-5 gap-4 items-end">
        <div className="col-span-1 md:col-span-2 space-y-1">
          <label className="text-xs font-bold text-slate-500">Product Name</label>
          <input className="w-full bg-slate-50 p-2 rounded-lg border-none" value={newProd.name} onChange={e => setNewProd({...newProd, name: e.target.value})} />
        </div>
        <div className="space-y-1">
          <label className="text-xs font-bold text-slate-500">HSN Code</label>
          <input className="w-full bg-slate-50 p-2 rounded-lg border-none" value={newProd.hsn} onChange={e => setNewProd({...newProd, hsn: e.target.value})} />
        </div>
        <div className="space-y-1">
          <label className="text-xs font-bold text-slate-500">Price</label>
          <input type="number" className="w-full bg-slate-50 p-2 rounded-lg border-none font-bold text-blue-600" value={newProd.price} onChange={e => setNewProd({...newProd, price: parseFloat(e.target.value) || 0})} />
        </div>
        <button onClick={add} className="bg-blue-600 text-white p-2 rounded-lg font-bold hover:bg-blue-700">Add Item</button>
      </div>

      <div className="bg-white rounded-2xl border border-slate-200 overflow-hidden">
        <table className="w-full text-left">
          <thead className="bg-slate-50 text-slate-400 text-xs uppercase font-bold">
            <tr>
              <th className="p-4">Name</th>
              <th className="p-4">HSN</th>
              <th className="p-4 text-right">Unit Price</th>
              <th className="p-4 text-center">GST %</th>
              <th className="p-4 text-center">Action</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {prods.map(p => (
              <tr key={p.id}>
                <td className="p-4 font-bold">{p.name}</td>
                <td className="p-4 text-slate-500">{p.hsn}</td>
                <td className="p-4 text-right font-black text-blue-600">₹{p.price.toFixed(2)}</td>
                <td className="p-4 text-center">{p.gstRate}%</td>
                <td className="p-4 text-center">
                  <button onClick={async () => { await db.products.delete(p.id); load(); }} className="text-red-400 hover:text-red-600 font-bold">Delete</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function InvoiceHistory({ db }) {
  const [invoices, setInvoices] = useState([]);

  useEffect(() => {
    db.invoices.toArray().then(items => setInvoices(items.reverse()));
  }, [db]);

  return (
    <div className="max-w-4xl mx-auto">
      <h2 className="text-2xl font-bold mb-6">Invoice History</h2>
      <div className="grid gap-4">
        {invoices.map(inv => (
          <div key={inv.id} className="bg-white p-6 rounded-2xl border border-slate-100 flex items-center justify-between shadow-sm hover:shadow-md transition-shadow">
            <div className="flex items-center gap-4">
              <div className="bg-slate-100 p-3 rounded-xl text-slate-500">
                📄
              </div>
              <div>
                <p className="font-black text-slate-900">{inv.invoiceNo}</p>
                <p className="text-sm text-slate-500">{inv.customerName} • {inv.date}</p>
              </div>
            </div>
            <div className="text-right">
              <p className="text-xl font-black text-emerald-600">₹{inv.totalAmount.toFixed(2)}</p>
              <span className="text-[10px] font-bold uppercase text-slate-400 tracking-tighter bg-slate-50 px-2 py-1 rounded border">Success</span>
            </div>
          </div>
        ))}
        {invoices.length === 0 && (
          <div className="text-center py-20 bg-white rounded-3xl border-2 border-dashed border-slate-200">
            <p className="text-slate-400 font-medium">No invoices found in local storage.</p>
          </div>
        )}
      </div>
    </div>
  );
}
