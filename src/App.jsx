import React, { useState, useEffect, useMemo } from 'react';
import { 
  LayoutDashboard, 
  Wallet, 
  TrendingUp, 
  Target, 
  PieChart, 
  Settings, 
  Plus, 
  Trash2, 
  Edit3, 
  ChevronRight, 
  Bell, 
  ShieldCheck, 
  ArrowUpCircle, 
  ArrowDownCircle, 
  Calendar,
  Download,
  AlertTriangle,
  Lightbulb,
  LogOut
} from 'lucide-react';
import { 
  BarChart, 
  Bar, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer, 
  Cell,
  PieChart as RePieChart,
  Pie,
  LineChart,
  Line,
  AreaChart,
  Area
} from 'recharts';

// --- CONSTANTS & DEFAULTS ---
const CATEGORIES = ["Food", "Rent", "Travel", "Bills", "Shopping", "Others"];
const INVESTMENT_TYPES = [
  { name: 'Fixed Deposits', rate: 0.06, color: '#3b82f6' },
  { name: 'Mutual Funds', rate: 0.12, color: '#8b5cf6' },
  { name: 'Stocks', rate: 0.15, color: '#10b981' },
  { name: 'Gold', rate: 0.08, color: '#f59e0b' }
];

const COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#6366f1'];

// --- APP COMPONENT ---
export default function App() {
  // --- STATE ---
  const [activeTab, setActiveTab] = useState('dashboard');
  const [expenses, setExpenses] = useState([]);
  const [income, setIncome] = useState([]);
  const [budgets, setBudgets] = useState({});
  const [goals, setGoals] = useState([]);
  const [investments, setInvestments] = useState([]);
  const [isLocked, setIsLocked] = useState(true);
  const [pin, setPin] = useState("");
  const [userPin, setUserPin] = useState("1234"); // Default PIN
  const [notifications, setNotifications] = useState([]);
  const [showAddModal, setShowAddModal] = useState(false);

  // --- INITIALIZATION & PERSISTENCE ---
  useEffect(() => {
    const savedData = localStorage.getItem('smart_finance_data');
    if (savedData) {
      const parsed = JSON.parse(savedData);
      setExpenses(parsed.expenses || []);
      setIncome(parsed.income || []);
      setBudgets(parsed.budgets || {});
      setGoals(parsed.goals || []);
      setInvestments(parsed.investments || []);
      setUserPin(parsed.userPin || "1234");
    }
  }, []);

  useEffect(() => {
    const data = { expenses, income, budgets, goals, investments, userPin };
    localStorage.setItem('smart_finance_data', JSON.stringify(data));
    checkBudgets();
  }, [expenses, income, budgets, goals, investments, userPin]);

  // --- CALCULATED VALUES ---
  const totalIncome = useMemo(() => income.reduce((acc, curr) => acc + Number(curr.amount), 0), [income]);
  const totalExpenses = useMemo(() => expenses.reduce((acc, curr) => acc + Number(curr.amount), 0), [expenses]);
  const balance = totalIncome - totalExpenses;
  
  const categorySpending = useMemo(() => {
    const map = {};
    expenses.forEach(ex => {
      map[ex.category] = (map[ex.category] || 0) + Number(ex.amount);
    });
    return Object.keys(map).map(cat => ({ name: cat, value: map[cat] }));
  }, [expenses]);

  // --- ACTIONS ---
  const handleAddExpense = (e) => {
    e.preventDefault();
    const formData = new FormData(e.target);
    const newEx = {
      id: Date.now(),
      amount: formData.get('amount'),
      category: formData.get('category'),
      date: formData.get('date'),
      paymentMode: formData.get('mode'),
      notes: formData.get('notes')
    };
    setExpenses([...expenses, newEx]);
    e.target.reset();
    setShowAddModal(false);
  };

  const checkBudgets = () => {
    const newNotes = [];
    Object.keys(budgets).forEach(cat => {
      const spent = categorySpending.find(c => c.name === cat)?.value || 0;
      if (spent > budgets[cat] * 0.9) {
        newNotes.push({
          id: Date.now() + Math.random(),
          title: `Budget Alert: ${cat}`,
          message: spent > budgets[cat] ? `You exceeded your ${cat} budget!` : `Nearing budget limit for ${cat}`,
          type: spent > budgets[cat] ? 'danger' : 'warning'
        });
      }
    });
    if (newNotes.length > 0) setNotifications(newNotes);
  };

  const exportData = () => {
    const data = JSON.stringify({ expenses, income, budgets, goals });
    const blob = new Blob([data], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'smart_finance_backup.json';
    a.click();
  };

  // --- SUB-COMPONENTS (VIEWS) ---
  
  const Sidebar = () => (
    <div className="w-64 bg-slate-900 text-white flex flex-col h-screen sticky top-0">
      <div className="p-6 flex items-center gap-3">
        <div className="bg-blue-600 p-2 rounded-lg">
          <Wallet className="w-6 h-6" />
        </div>
        <h1 className="text-xl font-bold tracking-tight">SmartFinance</h1>
      </div>
      
      <nav className="flex-1 px-4 space-y-2 mt-4">
        {[
          { id: 'dashboard', icon: LayoutDashboard, label: 'Dashboard' },
          { id: 'expenses', icon: ArrowDownCircle, label: 'Expenses' },
          { id: 'income', icon: ArrowUpCircle, label: 'Income' },
          { id: 'budgets', icon: PieChart, label: 'Budgets' },
          { id: 'goals', icon: Target, label: 'Goals' },
          { id: 'investments', icon: TrendingUp, label: 'Investments' },
          { id: 'reports', icon: Calendar, label: 'Reports' },
        ].map(item => (
          <button
            key={item.id}
            onClick={() => setActiveTab(item.id)}
            className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl transition-all ${
              activeTab === item.id ? 'bg-blue-600 shadow-lg' : 'hover:bg-slate-800 text-slate-400'
            }`}
          >
            <item.icon className="w-5 h-5" />
            <span className="font-medium">{item.label}</span>
          </button>
        ))}
      </nav>

      <div className="p-4 border-t border-slate-800 space-y-2">
        <button onClick={exportData} className="w-full flex items-center gap-3 px-4 py-2 text-slate-400 hover:text-white transition-colors">
          <Download className="w-4 h-4" />
          <span className="text-sm">Export Backup</span>
        </button>
        <button onClick={() => setIsLocked(true)} className="w-full flex items-center gap-3 px-4 py-2 text-red-400 hover:text-red-300 transition-colors">
          <LogOut className="w-4 h-4" />
          <span className="text-sm">Lock App</span>
        </button>
      </div>
    </div>
  );

  const DashboardView = () => (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <StatCard title="Total Balance" value={balance} color="blue" />
        <StatCard title="Income" value={totalIncome} color="green" />
        <StatCard title="Expenses" value={totalExpenses} color="red" />
        <StatCard title="Savings Rate" value={totalIncome ? Math.round((balance/totalIncome)*100) : 0} suffix="%" color="purple" />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white p-6 rounded-2xl border shadow-sm">
          <h3 className="text-lg font-semibold mb-6">Spending Overview</h3>
          <div className="h-[300px]">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={categorySpending}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} />
                <XAxis dataKey="name" />
                <YAxis />
                <Tooltip cursor={{fill: '#f8fafc'}} />
                <Bar dataKey="value" radius={[4, 4, 0, 0]}>
                  {categorySpending.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="bg-white p-6 rounded-2xl border shadow-sm">
          <h3 className="text-lg font-semibold mb-4">Insights & Tips</h3>
          <div className="space-y-4">
            {totalExpenses > totalIncome * 0.7 && (
              <div className="flex gap-4 p-4 bg-orange-50 border border-orange-100 rounded-xl">
                <AlertTriangle className="w-6 h-6 text-orange-600 shrink-0" />
                <div>
                  <p className="font-semibold text-orange-900 text-sm">High Spending Alert</p>
                  <p className="text-orange-700 text-xs">You've spent over 70% of your income this month. Consider cutting back on 'Others'.</p>
                </div>
              </div>
            )}
            <div className="flex gap-4 p-4 bg-blue-50 border border-blue-100 rounded-xl">
              <Lightbulb className="w-6 h-6 text-blue-600 shrink-0" />
              <div>
                <p className="font-semibold text-blue-900 text-sm">Smart Saving Tip</p>
                <p className="text-blue-700 text-xs">Based on your surplus, you could invest ₹{Math.round(balance * 0.3)} in Mutual Funds for 12% returns.</p>
              </div>
            </div>
            {goals.length > 0 && (
                <div className="p-4 bg-slate-50 rounded-xl border">
                   <p className="text-sm font-medium mb-2">Savings Goals Progress</p>
                   {goals.slice(0, 2).map(goal => (
                     <div key={goal.id} className="mb-2">
                        <div className="flex justify-between text-xs mb-1">
                            <span>{goal.name}</span>
                            <span>{Math.round((goal.current/goal.target)*100)}%</span>
                        </div>
                        <div className="h-1.5 w-full bg-slate-200 rounded-full overflow-hidden">
                            <div className="h-full bg-blue-600" style={{width: `${(goal.current/goal.target)*100}%`}}></div>
                        </div>
                     </div>
                   ))}
                </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );

  const ExpensesView = () => (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold">Expense History</h2>
        <button 
          onClick={() => setShowAddModal(true)}
          className="bg-blue-600 text-white px-4 py-2 rounded-xl flex items-center gap-2 hover:bg-blue-700 shadow-md"
        >
          <Plus className="w-4 h-4" /> Add Expense
        </button>
      </div>

      <div className="bg-white rounded-2xl border shadow-sm overflow-hidden">
        <table className="w-full text-left">
          <thead className="bg-slate-50 border-b">
            <tr>
              <th className="px-6 py-4 font-semibold text-slate-600">Date</th>
              <th className="px-6 py-4 font-semibold text-slate-600">Category</th>
              <th className="px-6 py-4 font-semibold text-slate-600">Mode</th>
              <th className="px-6 py-4 font-semibold text-slate-600 text-right">Amount</th>
              <th className="px-6 py-4 font-semibold text-slate-600 text-center">Action</th>
            </tr>
          </thead>
          <tbody className="divide-y">
            {expenses.length === 0 ? (
              <tr><td colSpan="5" className="px-6 py-10 text-center text-slate-400">No expenses recorded yet.</td></tr>
            ) : (
              expenses.slice().reverse().map(ex => (
                <tr key={ex.id} className="hover:bg-slate-50 transition-colors">
                  <td className="px-6 py-4 text-slate-600">{ex.date}</td>
                  <td className="px-6 py-4">
                    <span className="bg-slate-100 px-2 py-1 rounded text-xs font-medium text-slate-600">{ex.category}</span>
                  </td>
                  <td className="px-6 py-4 text-slate-500 text-sm">{ex.paymentMode}</td>
                  <td className="px-6 py-4 font-bold text-slate-900 text-right">₹{Number(ex.amount).toLocaleString()}</td>
                  <td className="px-6 py-4 text-center">
                    <button onClick={() => setExpenses(expenses.filter(e => e.id !== ex.id))} className="text-red-500 hover:text-red-700 p-1">
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );

  const InvestmentView = () => {
    const [principal, setPrincipal] = useState(10000);
    const [years, setYears] = useState(5);

    return (
      <div className="space-y-6">
        <div className="bg-gradient-to-br from-indigo-600 to-blue-700 p-8 rounded-3xl text-white shadow-xl">
          <h2 className="text-2xl font-bold mb-2">Smart Investment Planner</h2>
          <p className="opacity-80">Project your future wealth based on asset allocation.</p>
          
          <div className="mt-8 grid grid-cols-1 md:grid-cols-2 gap-8">
            <div className="space-y-4">
              <label className="block text-sm font-medium opacity-90">Investment Amount (₹)</label>
              <input 
                type="number" 
                value={principal} 
                onChange={(e) => setPrincipal(e.target.value)}
                className="w-full bg-white/10 border border-white/20 rounded-xl px-4 py-3 outline-none focus:bg-white/20 transition-all text-xl font-bold"
              />
              <label className="block text-sm font-medium opacity-90">Time Horizon (Years)</label>
              <input 
                type="range" min="1" max="30" 
                value={years} 
                onChange={(e) => setYears(e.target.value)}
                className="w-full accent-white"
              />
              <div className="flex justify-between text-xs font-mono">
                <span>1 Year</span>
                <span className="text-lg font-bold">{years} Years</span>
                <span>30 Years</span>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              {INVESTMENT_TYPES.map(inv => {
                const fv = principal * Math.pow((1 + inv.rate), years);
                return (
                  <div key={inv.name} className="bg-white/10 p-4 rounded-2xl border border-white/10">
                    <p className="text-xs opacity-70 mb-1">{inv.name}</p>
                    <p className="text-lg font-bold">₹{Math.round(fv).toLocaleString()}</p>
                    <p className="text-[10px] text-green-300">+{Math.round(inv.rate * 100)}% Expected PA</p>
                  </div>
                );
              })}
            </div>
          </div>
        </div>

        <div className="bg-white p-6 rounded-2xl border shadow-sm">
          <h3 className="text-lg font-semibold mb-6">Comparison of Growth (Logarithmic Projection)</h3>
          <div className="h-[350px]">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={Array.from({length: Number(years) + 1}, (_, i) => ({
                year: i,
                FD: Math.round(principal * Math.pow(1.06, i)),
                Stocks: Math.round(principal * Math.pow(1.15, i)),
                Gold: Math.round(principal * Math.pow(1.08, i))
              }))}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} />
                <XAxis dataKey="year" label={{ value: 'Years', position: 'bottom' }} />
                <YAxis />
                <Tooltip />
                <Line type="monotone" dataKey="FD" stroke="#3b82f6" strokeWidth={2} />
                <Line type="monotone" dataKey="Stocks" stroke="#10b981" strokeWidth={2} />
                <Line type="monotone" dataKey="Gold" stroke="#f59e0b" strokeWidth={2} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
    );
  };

  const GoalsView = () => {
    const [newGoal, setNewGoal] = useState({ name: '', target: '', deadline: '' });
    
    const handleAddGoal = () => {
        if (!newGoal.name || !newGoal.target) return;
        setGoals([...goals, { ...newGoal, id: Date.now(), current: 0 }]);
        setNewGoal({ name: '', target: '', deadline: '' });
    };

    return (
        <div className="space-y-6">
            <div className="flex justify-between items-center">
                <h2 className="text-2xl font-bold">Savings Goals</h2>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className="bg-white p-6 rounded-2xl border border-dashed border-slate-300 flex flex-col justify-center items-center text-center">
                    <div className="bg-blue-100 p-4 rounded-full mb-4">
                        <Target className="w-8 h-8 text-blue-600" />
                    </div>
                    <h3 className="font-bold mb-4">New Goal</h3>
                    <div className="space-y-3 w-full">
                        <input 
                            placeholder="Goal Name (e.g. Car)" 
                            className="w-full border rounded-lg px-3 py-2 text-sm"
                            value={newGoal.name}
                            onChange={e => setNewGoal({...newGoal, name: e.target.value})}
                        />
                        <input 
                            type="number" 
                            placeholder="Target Amount" 
                            className="w-full border rounded-lg px-3 py-2 text-sm"
                            value={newGoal.target}
                            onChange={e => setNewGoal({...newGoal, target: e.target.value})}
                        />
                        <button onClick={handleAddGoal} className="w-full bg-blue-600 text-white rounded-lg py-2 text-sm font-bold">Add Goal</button>
                    </div>
                </div>

                {goals.map(goal => (
                    <div key={goal.id} className="bg-white p-6 rounded-2xl border shadow-sm flex flex-col justify-between">
                        <div>
                            <div className="flex justify-between items-start mb-4">
                                <h4 className="font-bold text-lg text-slate-800">{goal.name}</h4>
                                <button onClick={() => setGoals(goals.filter(g => g.id !== goal.id))} className="text-slate-300 hover:text-red-500"><Trash2 className="w-4 h-4"/></button>
                            </div>
                            <div className="flex justify-between items-end mb-2">
                                <p className="text-2xl font-black text-blue-600">₹{Number(goal.current).toLocaleString()}</p>
                                <p className="text-xs text-slate-400">Target: ₹{Number(goal.target).toLocaleString()}</p>
                            </div>
                            <div className="h-2 w-full bg-slate-100 rounded-full overflow-hidden mb-4">
                                <div className="h-full bg-blue-500 rounded-full" style={{width: `${Math.min((goal.current/goal.target)*100, 100)}%`}}></div>
                            </div>
                        </div>
                        <div className="flex gap-2">
                            <input 
                                type="number" 
                                placeholder="Add ₹" 
                                className="flex-1 border rounded-lg px-2 py-1 text-xs"
                                onKeyDown={(e) => {
                                    if (e.key === 'Enter') {
                                        const amt = Number(e.target.value);
                                        setGoals(goals.map(g => g.id === goal.id ? {...g, current: Number(g.current) + amt} : g));
                                        e.target.value = '';
                                    }
                                }}
                            />
                            <p className="text-[10px] text-slate-400 italic">Press Enter to contribute</p>
                        </div>
                    </div>
                ))}
            </div>
        </div>
    )
  }

  // --- LOGIN / LOCK SCREEN ---
  if (isLocked) {
    return (
      <div className="min-h-screen bg-slate-950 flex items-center justify-center p-4">
        <div className="max-w-md w-full bg-slate-900 rounded-3xl p-8 border border-slate-800 shadow-2xl text-center">
          <div className="bg-blue-600 w-16 h-16 rounded-2xl flex items-center justify-center mx-auto mb-6 shadow-lg shadow-blue-500/20">
            <ShieldCheck className="text-white w-8 h-8" />
          </div>
          <h2 className="text-2xl font-bold text-white mb-2">SmartFinance Planner</h2>
          <p className="text-slate-400 text-sm mb-8">Enter your security PIN to continue</p>
          
          <div className="flex justify-center gap-3 mb-8">
            {[1, 2, 3, 4].map(i => (
              <div key={i} className={`w-3 h-3 rounded-full ${pin.length >= i ? 'bg-blue-500' : 'bg-slate-700'}`} />
            ))}
          </div>

          <div className="grid grid-cols-3 gap-4">
            {[1, 2, 3, 4, 5, 6, 7, 8, 9, 'C', 0, 'OK'].map(key => (
              <button
                key={key}
                onClick={() => {
                  if (key === 'C') setPin("");
                  else if (key === 'OK') {
                    if (pin === userPin) setIsLocked(false);
                    else { alert("Incorrect PIN (Hint: 1234)"); setPin(""); }
                  }
                  else if (pin.length < 4) setPin(pin + key);
                }}
                className="h-16 rounded-xl bg-slate-800 text-white font-bold text-xl hover:bg-slate-700 active:scale-95 transition-all"
              >
                {key}
              </button>
            ))}
          </div>
        </div>
      </div>
    );
  }

  // --- MAIN UI ---
  return (
    <div className="min-h-screen bg-slate-50 flex font-sans text-slate-900">
      <Sidebar />

      <main className="flex-1 p-8 overflow-y-auto h-screen">
        <header className="flex justify-between items-center mb-8">
          <div>
            <p className="text-slate-500 text-sm font-medium uppercase tracking-wider">Welcome Back</p>
            <h1 className="text-3xl font-black text-slate-900">Financial Snapshot</h1>
          </div>
          
          <div className="flex items-center gap-4">
            <div className="relative">
              <Bell className="w-6 h-6 text-slate-400 cursor-pointer" />
              {notifications.length > 0 && (
                <span className="absolute -top-1 -right-1 bg-red-500 w-2 h-2 rounded-full border-2 border-white"></span>
              )}
            </div>
            <div className="w-10 h-10 rounded-full bg-slate-200 border border-slate-300 flex items-center justify-center font-bold text-slate-600">JD</div>
          </div>
        </header>

        {activeTab === 'dashboard' && <DashboardView />}
        {activeTab === 'expenses' && <ExpensesView />}
        {activeTab === 'investments' && <InvestmentView />}
        {activeTab === 'goals' && <GoalsView />}
        {activeTab === 'income' && <IncomeTrackingView income={income} setIncome={setIncome} totalIncome={totalIncome} />}
        {activeTab === 'budgets' && <BudgetView budgets={budgets} setBudgets={setBudgets} categorySpending={categorySpending} />}
        {activeTab === 'reports' && <ReportsView expenses={expenses} categorySpending={categorySpending} />}

        {/* MODAL: ADD EXPENSE */}
        {showAddModal && (
          <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
            <div className="bg-white rounded-3xl p-8 w-full max-w-md shadow-2xl">
              <div className="flex justify-between items-center mb-6">
                <h3 className="text-xl font-bold">Quick Add Expense</h3>
                <button onClick={() => setShowAddModal(false)} className="text-slate-400 hover:text-slate-600">×</button>
              </div>
              <form onSubmit={handleAddExpense} className="space-y-4">
                <div>
                  <label className="block text-xs font-semibold uppercase text-slate-400 mb-1">Amount (₹)</label>
                  <input name="amount" required type="number" className="w-full border rounded-xl p-3 focus:ring-2 ring-blue-500 outline-none" placeholder="0.00" />
                </div>
                <div>
                  <label className="block text-xs font-semibold uppercase text-slate-400 mb-1">Category</label>
                  <select name="category" className="w-full border rounded-xl p-3 outline-none">
                    {CATEGORIES.map(c => <option key={c} value={c}>{c}</option>)}
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-semibold uppercase text-slate-400 mb-1">Date</label>
                  <input name="date" required type="date" defaultValue={new Date().toISOString().split('T')[0]} className="w-full border rounded-xl p-3 outline-none" />
                </div>
                <div>
                  <label className="block text-xs font-semibold uppercase text-slate-400 mb-1">Payment Mode</label>
                  <div className="flex gap-2">
                    {['UPI', 'Card', 'Cash'].map(m => (
                        <label key={m} className="flex-1">
                            <input type="radio" name="mode" value={m} defaultChecked={m === 'UPI'} className="hidden peer" />
                            <div className="p-2 border rounded-xl text-center text-sm cursor-pointer peer-checked:bg-blue-50 peer-checked:border-blue-600 peer-checked:text-blue-600">
                                {m}
                            </div>
                        </label>
                    ))}
                  </div>
                </div>
                <button type="submit" className="w-full bg-blue-600 text-white font-bold py-3 rounded-xl mt-4 hover:bg-blue-700 transition-all shadow-lg shadow-blue-500/30">
                  Save Expense
                </button>
              </form>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}

// --- HELPER VIEWS ---

function StatCard({ title, value, color, suffix = "" }) {
  const colors = {
    blue: "text-blue-600 bg-blue-50 border-blue-100",
    green: "text-emerald-600 bg-emerald-50 border-emerald-100",
    red: "text-rose-600 bg-rose-50 border-rose-100",
    purple: "text-violet-600 bg-violet-50 border-violet-100"
  };
  return (
    <div className={`p-6 rounded-2xl border ${colors[color]} shadow-sm`}>
      <p className="text-xs font-bold uppercase opacity-80 mb-2">{title}</p>
      <div className="flex items-baseline gap-1">
        <span className="text-2xl font-black">
          {suffix === "%" ? "" : "₹"}{value.toLocaleString()}{suffix}
        </span>
      </div>
    </div>
  );
}

function IncomeTrackingView({ income, setIncome, totalIncome }) {
    const handleAddIncome = (e) => {
        e.preventDefault();
        const fd = new FormData(e.target);
        setIncome([...income, { id: Date.now(), source: fd.get('source'), amount: fd.get('amount'), date: fd.get('date') }]);
        e.target.reset();
    };

    return (
        <div className="space-y-6">
            <h2 className="text-2xl font-bold">Income Tracking</h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className="bg-white p-6 rounded-2xl border shadow-sm h-fit">
                    <h3 className="font-bold mb-4">Add Income Source</h3>
                    <form onSubmit={handleAddIncome} className="space-y-4">
                        <input name="source" required placeholder="Source (e.g. Salary)" className="w-full border rounded-lg p-2 text-sm" />
                        <input name="amount" required type="number" placeholder="Amount" className="w-full border rounded-lg p-2 text-sm" />
                        <input name="date" required type="date" defaultValue={new Date().toISOString().split('T')[0]} className="w-full border rounded-lg p-2 text-sm" />
                        <button className="w-full bg-emerald-600 text-white font-bold py-2 rounded-lg text-sm">Add Income</button>
                    </form>
                </div>
                <div className="md:col-span-2 bg-white rounded-2xl border shadow-sm overflow-hidden">
                    <table className="w-full text-left">
                        <thead className="bg-slate-50 border-b text-xs uppercase text-slate-500">
                            <tr><th className="px-6 py-3">Source</th><th className="px-6 py-3">Date</th><th className="px-6 py-3 text-right">Amount</th></tr>
                        </thead>
                        <tbody className="divide-y text-sm">
                            {income.map(inc => (
                                <tr key={inc.id}><td className="px-6 py-3 font-medium">{inc.source}</td><td className="px-6 py-3">{inc.date}</td><td className="px-6 py-3 text-right font-bold text-emerald-600">₹{Number(inc.amount).toLocaleString()}</td></tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    )
}

function BudgetView({ budgets, setBudgets, categorySpending }) {
    return (
        <div className="space-y-6">
            <h2 className="text-2xl font-bold">Monthly Budgets</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {CATEGORIES.map(cat => {
                    const limit = budgets[cat] || 0;
                    const spent = categorySpending.find(s => s.name === cat)?.value || 0;
                    const percent = limit > 0 ? (spent / limit) * 100 : 0;
                    const statusColor = percent > 100 ? 'bg-rose-500' : percent > 80 ? 'bg-amber-500' : 'bg-emerald-500';

                    return (
                        <div key={cat} className="bg-white p-6 rounded-2xl border shadow-sm">
                            <div className="flex justify-between items-center mb-4">
                                <h3 className="font-bold text-slate-700">{cat}</h3>
                                <div className="text-xs font-mono bg-slate-100 px-2 py-1 rounded">
                                    {Math.round(percent)}% used
                                </div>
                            </div>
                            <div className="space-y-4">
                                <div className="flex justify-between text-sm">
                                    <span className="text-slate-400 italic">Limit</span>
                                    <input 
                                        type="number" 
                                        defaultValue={limit}
                                        onBlur={(e) => setBudgets({...budgets, [cat]: Number(e.target.value)})}
                                        className="w-24 text-right border-b focus:border-blue-500 outline-none font-bold"
                                    />
                                </div>
                                <div className="h-2 w-full bg-slate-100 rounded-full overflow-hidden">
                                    <div className={`h-full ${statusColor} transition-all duration-500`} style={{width: `${Math.min(percent, 100)}%`}}></div>
                                </div>
                                <div className="flex justify-between text-xs font-bold uppercase tracking-tighter">
                                    <span className="text-slate-400">Spent: ₹{spent}</span>
                                    <span className="text-slate-400">Left: ₹{Math.max(limit - spent, 0)}</span>
                                </div>
                            </div>
                        </div>
                    );
                })}
            </div>
        </div>
    )
}

function ReportsView({ expenses, categorySpending }) {
    return (
        <div className="space-y-6">
            <div className="flex justify-between items-center">
                <h2 className="text-2xl font-bold">Analytics & Reports</h2>
                <div className="flex gap-2">
                    <button className="text-xs bg-white border px-3 py-1 rounded-lg">Month</button>
                    <button className="text-xs bg-white border px-3 py-1 rounded-lg">Year</button>
                </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className="bg-white p-6 rounded-2xl border shadow-sm md:col-span-1">
                    <h3 className="text-sm font-bold mb-6 text-slate-500 uppercase">Category Distribution</h3>
                    <div className="h-[250px]">
                        <ResponsiveContainer width="100%" height="100%">
                            <RePieChart>
                                <Pie 
                                    data={categorySpending} 
                                    innerRadius={60} 
                                    outerRadius={80} 
                                    paddingAngle={5} 
                                    dataKey="value"
                                >
                                    {categorySpending.map((entry, index) => (
                                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                                    ))}
                                </Pie>
                                <Tooltip />
                            </RePieChart>
                        </ResponsiveContainer>
                    </div>
                </div>

                <div className="bg-white p-6 rounded-2xl border shadow-sm md:col-span-2">
                    <h3 className="text-sm font-bold mb-6 text-slate-500 uppercase">Spending Frequency (Daily)</h3>
                    <div className="h-[250px]">
                        <ResponsiveContainer width="100%" height="100%">
                            <AreaChart data={expenses.slice(-10)}>
                                <defs>
                                    <linearGradient id="colorAmt" x1="0" y1="0" x2="0" y2="1">
                                    <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.1}/>
                                    <stop offset="95%" stopColor="#3b82f6" stopOpacity={0}/>
                                    </linearGradient>
                                </defs>
                                <XAxis dataKey="date" hide />
                                <YAxis hide />
                                <Tooltip />
                                <Area type="monotone" dataKey="amount" stroke="#3b82f6" fillOpacity={1} fill="url(#colorAmt)" strokeWidth={2} />
                            </AreaChart>
                        </ResponsiveContainer>
                    </div>
                </div>
            </div>
        </div>
    )
}
