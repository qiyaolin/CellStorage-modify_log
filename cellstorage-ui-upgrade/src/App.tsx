import React, { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { 
  LayoutDashboard, 
  Beaker, 
  Building, 
  FlaskConical,
  Menu,
  X
} from 'lucide-react';
import Dashboard from './components/dashboard';
import InventoryManagement from './components/inventory-management';
import StorageLocations from './components/storage-locations';
import CellLines from './components/cell-lines';

type ActivePage = 'dashboard' | 'inventory' | 'storage' | 'celllines';

function App() {
  const [activePage, setActivePage] = useState<ActivePage>('dashboard');
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const navigation = [
    {
      id: 'dashboard' as ActivePage,
      name: 'Dashboard',
      icon: LayoutDashboard,
      component: Dashboard
    },
    {
      id: 'inventory' as ActivePage,
      name: 'Cryovial Inventory',
      icon: Beaker,
      component: InventoryManagement
    },
    {
      id: 'storage' as ActivePage,
      name: 'Storage Locations',
      icon: Building,
      component: StorageLocations
    },
    {
      id: 'celllines' as ActivePage,
      name: 'Cell Lines',
      icon: FlaskConical,
      component: CellLines
    }
  ];

  const ActiveComponent = navigation.find(nav => nav.id === activePage)?.component || Dashboard;

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-blue-900 to-slate-900">
      {/* Mobile Sidebar Overlay */}
      {sidebarOpen && (
        <div 
          className="fixed inset-0 bg-black/50 z-40 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Sidebar */}
      <div className={`fixed inset-y-0 left-0 z-50 w-64 bg-slate-900/95 backdrop-blur-md border-r border-white/10 transform transition-transform duration-300 ease-in-out lg:translate-x-0 ${
        sidebarOpen ? 'translate-x-0' : '-translate-x-full'
      }`}>
        <div className="flex items-center justify-between p-6 border-b border-white/10">
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-blue-500/20 rounded-lg">
              <FlaskConical className="w-6 h-6 text-blue-400" />
            </div>
            <div>
              <h1 className="text-lg font-bold text-white">CellStorage</h1>
              <p className="text-xs text-blue-200">Lab Management</p>
            </div>
          </div>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setSidebarOpen(false)}
            className="lg:hidden text-white hover:bg-white/10"
          >
            <X className="w-4 h-4" />
          </Button>
        </div>

        <nav className="p-4 space-y-2">
          {navigation.map((item) => (
            <Button
              key={item.id}
              variant={activePage === item.id ? "default" : "ghost"}
              className={`w-full justify-start text-left ${
                activePage === item.id
                  ? 'bg-blue-600 text-white hover:bg-blue-700'
                  : 'text-blue-200 hover:bg-white/10 hover:text-white'
              }`}
              onClick={() => {
                setActivePage(item.id);
                setSidebarOpen(false);
              }}
            >
              <item.icon className="w-4 h-4 mr-3" />
              {item.name}
            </Button>
          ))}
        </nav>

        {/* System Status */}
        <div className="absolute bottom-4 left-4 right-4">
          <Card className="bg-white/5 border-white/10">
            <CardContent className="p-4">
              <div className="flex items-center space-x-2">
                <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
                <span className="text-sm text-green-400">System Online</span>
              </div>
              <p className="text-xs text-blue-200 mt-1">All services operational</p>
            </CardContent>
          </Card>
        </div>
      </div>

      {/* Main Content */}
      <div className="lg:ml-64">
        {/* Mobile Header */}
        <div className="lg:hidden flex items-center justify-between p-4 bg-slate-900/95 backdrop-blur-md border-b border-white/10">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setSidebarOpen(true)}
            className="text-white hover:bg-white/10"
          >
            <Menu className="w-5 h-5" />
          </Button>
          <div className="flex items-center space-x-2">
            <FlaskConical className="w-5 h-5 text-blue-400" />
            <span className="text-white font-semibold">CellStorage</span>
          </div>
          <div className="w-8" /> {/* Spacer for centering */}
        </div>

        {/* Page Content */}
        <main className="min-h-screen">
          <ActiveComponent />
        </main>
      </div>
    </div>
  );
}

export default App;