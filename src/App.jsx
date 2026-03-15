import React, { useState, useEffect } from 'react';
import { 
  Plus, 
  Trash2, 
  Download, 
  Printer, 
  Settings, 
  ShoppingCart, 
  FileText, 
  User, 
  Package, 
  Search 
} from 'lucide-react';

/**
 * FIXED: To resolve the compilation error in the preview environment, 
 * we've switched to the native browser 'indexedDB' API for storage 
 * instead of the external 'dexie' library.
 */

const App = () => {
  // State
  const [activeTab, setActiveTab] = useState('billing');
  const [inventory, setInventory] = useState([]);
  const [cart, setCart] = useState([]);
  const [customer, setCustomer] = useState({ name: '', phone: '', address: '' });
  const [searchTerm, setSearchTerm] = useState('');
  const [db, setDb] = useState(null);

  // Initialize Database
  useEffect(() => {
    const request = indexedDB.open('GSTBillingDB', 1);
    
    request.onupgradeneeded = (e) => {
      const db = e.target.result;
      if (!db.objectStoreNames.contains('inventory')) {
        db.createObjectStore('inventory', { keyPath: 'id', autoIncrement: true });
      }
      if (!db.objectStoreNames.contains('invoices')) {
        db.createObjectStore('invoices', { keyPath: 'id', autoIncrement: true });
      }
    };

    request.onsuccess = (e) => {
      const database = e.target.result;
      setDb(database);
      loadInventory(database);
    };
  }, []);

  const loadInventory = (database) => {
    const dbToUse = database || db;
    if (!dbToUse) return;

    const transaction = dbToUse.transaction(['inventory'], 'readonly');
    const store = transaction.objectStore('inventory');
    const request = store.getAll();

    request.onsuccess = () => {
      setInventory(request.result);
    };
  };

  // --- BILLING LOGIC ---
  const addToCart = (product) => {
    const existing = cart.find(item => item.id === product.id);
    if (existing) {
      setCart(cart.map(item => 
        item.id === product.id ? { ...item, quantity: item.quantity + 1 } : item
      ));
    } else {
      setCart([...cart, { ...product, quantity: 1 }]);
    }
  };

  const removeFromCart = (id) => setCart(cart.filter(item => item.id !== id));

  const calculateSubtotal = () => cart.reduce((sum, item) => sum + (item.price * item.quantity), 0);
  const calculateGST = () => cart.reduce((sum, item) => sum + (item.price * item.quantity * (item.gstRate / 100)), 0);
  const calculateTotal = () => calculateSubtotal() + calculateGST();

  const handleSaveInvoice = () => {
    if (cart.length === 0 || !customer.name) {
      alert("Please add items and customer name");
      return;
    }
    
    const invoice = {
      customerName: customer.name,
      customerPhone: customer.phone,
      items: cart,
      subtotal: calculateSubtotal(),
      gst: calculateGST(),
      totalAmount: calculateTotal(),
      date: new Date().toISOString()
    };

    const transaction = db.transaction(['invoices'], 'readwrite');
    const store = transaction.objectStore('invoices');
    store.add(invoice);

    transaction.oncomplete = () => {
      setCart([]);
      setCustomer({ name: '', phone: '', address: '' });
      alert("Invoice Generated Successfully!");
    };
  };

  // --- INVENTORY LOGIC ---
  const handleAddProduct = (e) => {
    e.preventDefault();
    const formData = new FormData(e.target);
    const newProduct = {
      name: formData.get('name'),
      hsn: formData.get('hsn'),
      price: parseFloat(formData.get('price')),
      stock: parseInt(formData.get('stock')),
      gstRate: parseInt(formData.get('gstRate'))
    };

    const transaction = db.transaction(['inventory'], 'readwrite');
    const store = transaction.objectStore('inventory');
    store.add(newProduct);

    transaction.oncomplete = () => {
      loadInventory();
      e.target.reset();
    };
  };

  const deleteInventoryItem = (id) => {
    const transaction = db.transaction(['inventory'], 'readwrite');
    const store = transaction.objectStore('inventory');
    store.delete(id);
    transaction.oncomplete = () => loadInventory();
  };

  return (
    <div className="min-h-screen bg-gray-50 flex font-sans">
      {/* Sidebar */}
      <nav className="w-64 bg-slate-900 text-white flex flex-col p-4 space-y-2">
        <h1 className="text-2xl font-bold mb-8 px-2 flex items-center gap-2">
          <FileText className="text-blue-400" /> GST Pro
        </h1>
        <button 
          onClick={() => setActiveTab('billing')}
          className={`flex items-center gap-3 p-3 rounded-lg transition text-left w-full ${activeTab === 'billing' ? 'bg-blue-600' : 'hover:bg-slate-800'}`}
        >
          <ShoppingCart size={20} /> Billing
        </button>
        <button 
          onClick={() => setActiveTab('inventory')}
          className={`flex items-center gap-3 p-3 rounded-lg transition text-left w-full ${activeTab === 'inventory' ? 'bg-blue-600' : 'hover:bg-slate-800'}`}
        >
          <Package size={20} /> Inventory
        </button>
        <button 
          onClick={() => setActiveTab('invoices')}
          className={`flex items-center gap-3 p-3 rounded-lg transition text-left w-full ${activeTab === 'invoices' ? 'bg-blue-600' : 'hover:bg-slate-800'}`}
        >
          <FileText size={20} /> View History
        </button>
      </nav>

      {/* Main Content */}
      <main className="flex-1 p-8 overflow-y-auto">
        
        {/* BILLING TAB */}
        {activeTab === 'billing' && (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            <div className="lg:col-span-2 space-y-6">
              {/* Customer Info */}
              <div className="bg-white p-6 rounded-xl shadow-sm space-y-4">
                <h2 className="text-lg font-semibold border-b pb-2 flex items-center gap-2">
                  <User size={18} /> Customer Details
                </h2>
                <div className="grid grid-cols-2 gap-4">
                  <input 
                    placeholder="Customer Name"
                    className="p-2 border rounded focus:ring-2 focus:ring-blue-500 outline-none"
                    value={customer.name}
                    onChange={(e) => setCustomer({...customer, name: e.target.value})}
                  />
                  <input 
                    placeholder="Phone Number"
                    className="p-2 border rounded focus:ring-2 focus:ring-blue-500 outline-none"
                    value={customer.phone}
                    onChange={(e) => setCustomer({...customer, phone: e.target.value})}
                  />
                </div>
              </div>

              {/* Product Selection */}
              <div className="bg-white p-6 rounded-xl shadow-sm">
                <div className="flex justify-between items-center mb-4">
                  <h2 className="text-lg font-semibold">Products</h2>
                  <div className="relative">
                    <Search className="absolute left-2 top-2.5 text-gray-400" size={16} />
                    <input 
                      placeholder="Search inventory..."
                      className="pl-8 p-2 border rounded-full text-sm outline-none focus:ring-2 focus:ring-blue-500"
                      onChange={(e) => setSearchTerm(e.target.value)}
                    />
                  </div>
                </div>
                <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                  {inventory
                    .filter(item => item.name.toLowerCase().includes(searchTerm.toLowerCase()))
                    .map(item => (
                    <button 
                      key={item.id}
                      onClick={() => addToCart(item)}
                      className="text-left p-3 border rounded hover:border-blue-500 hover:bg-blue-50 transition"
                    >
                      <p className="font-medium truncate">{item.name}</p>
                      <p className="text-sm text-gray-500">₹{item.price} + {item.gstRate}% GST</p>
                    </button>
                  ))}
                  {inventory.length === 0 && (
                    <p className="col-span-full text-center text-gray-400 py-4">No items in inventory. Add them in the Inventory tab.</p>
                  )}
                </div>
              </div>
            </div>

            {/* Cart / Summary */}
            <div className="bg-white p-6 rounded-xl shadow-lg h-fit sticky top-8 flex flex-col">
              <h2 className="text-xl font-bold mb-4 flex items-center gap-2">
                Current Invoice
              </h2>
              <div className="flex-1 space-y-3 mb-6 max-h-[400px] overflow-y-auto pr-2">
                {cart.map(item => (
                  <div key={item.id} className="flex justify-between items-center text-sm">
                    <div className="flex-1">
                      <p className="font-medium">{item.name}</p>
                      <p className="text-gray-500">Qty: {item.quantity} × ₹{item.price}</p>
                    </div>
                    <p className="mr-4">₹{(item.price * item.quantity).toFixed(2)}</p>
                    <button onClick={() => removeFromCart(item.id)} className="text-red-500 hover:bg-red-50 p-1 rounded">
                      <Trash2 size={16} />
                    </button>
                  </div>
                ))}
                {cart.length === 0 && (
                  <p className="text-center text-gray-400 py-8">Cart is empty</p>
                )}
              </div>

              <div className="border-t pt-4 space-y-2">
                <div className="flex justify-between text-gray-600">
                  <span>Subtotal</span>
                  <span>₹{calculateSubtotal().toFixed(2)}</span>
                </div>
                <div className="flex justify-between text-gray-600">
                  <span>GST Total</span>
                  <span>₹{calculateGST().toFixed(2)}</span>
                </div>
                <div className="flex justify-between text-xl font-bold border-t pt-2 mt-2">
                  <span>Total</span>
                  <span className="text-blue-600">₹{calculateTotal().toFixed(2)}</span>
                </div>
                <button 
                  onClick={handleSaveInvoice}
                  disabled={cart.length === 0}
                  className="w-full bg-blue-600 text-white py-3 rounded-lg font-bold mt-4 hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                >
                  <Printer size={18} /> Print & Save
                </button>
              </div>
            </div>
          </div>
        )}

        {/* INVENTORY TAB */}
        {activeTab === 'inventory' && (
          <div className="space-y-6">
            <div className="bg-white p-6 rounded-xl shadow-sm">
              <h2 className="text-xl font-bold mb-4">Add New Item</h2>
              <form onSubmit={handleAddProduct} className="grid grid-cols-1 md:grid-cols-5 gap-4">
                <input name="name" placeholder="Item Name" required className="p-2 border rounded" />
                <input name="hsn" placeholder="HSN Code" className="p-2 border rounded" />
                <input name="price" type="number" step="0.01" placeholder="Price (Excl. GST)" required className="p-2 border rounded" />
                <select name="gstRate" className="p-2 border rounded">
                  <option value="5">5% GST</option>
                  <option value="12">12% GST</option>
                  <option value="18">18% GST</option>
                  <option value="28">28% GST</option>
                </select>
                <input name="stock" type="number" placeholder="Initial Stock" className="p-2 border rounded" />
                <button type="submit" className="md:col-span-5 bg-green-600 text-white p-2 rounded font-bold hover:bg-green-700 transition">
                  Add to Inventory
                </button>
              </form>
            </div>

            <div className="bg-white rounded-xl shadow-sm overflow-hidden overflow-x-auto">
              <table className="w-full text-left">
                <thead className="bg-gray-100 text-gray-600 uppercase text-xs">
                  <tr>
                    <th className="px-6 py-3">Item Name</th>
                    <th className="px-6 py-3">HSN</th>
                    <th className="px-6 py-3">Base Price</th>
                    <th className="px-6 py-3">GST %</th>
                    <th className="px-6 py-3">Stock</th>
                    <th className="px-6 py-3">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y">
                  {inventory.map(item => (
                    <tr key={item.id} className="hover:bg-gray-50">
                      <td className="px-6 py-4 font-medium">{item.name}</td>
                      <td className="px-6 py-4">{item.hsn}</td>
                      <td className="px-6 py-4">₹{item.price}</td>
                      <td className="px-6 py-4">{item.gstRate}%</td>
                      <td className="px-6 py-4">{item.stock}</td>
                      <td className="px-6 py-4">
                        <button 
                          onClick={() => deleteInventoryItem(item.id)} 
                          className="text-red-500 p-2 hover:bg-red-50 rounded"
                        >
                          <Trash2 size={16} />
                        </button>
                      </td>
                    </tr>
                  ))}
                  {inventory.length === 0 && (
                    <tr>
                      <td colSpan="6" className="px-6 py-8 text-center text-gray-400">Inventory is empty. Add your first product above.</td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* INVOICES TAB */}
        {activeTab === 'invoices' && (
          <div className="bg-white p-6 rounded-xl shadow-sm">
            <h2 className="text-xl font-bold mb-4">Sales History</h2>
            <p className="text-gray-500 mb-4">All generated invoices are stored locally on this machine.</p>
            {/* Simple list could be added here similar to inventory */}
            <div className="bg-blue-50 p-4 rounded-lg text-blue-800 text-sm">
              Note: This application is a standalone desktop-ready tool. For full PDF generation features in the final EXE, ensure you have a PDF printer installed on Windows.
            </div>
          </div>
        )}
      </main>
    </div>
  );
};

export default App;
