import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { 
  Package, 
  MapPin, 
  Microscope, 
  BarChart3,
  Search,
  Plus,
  Bell,
  User,
  Loader2,
  AlertCircle,
  Home,
  Settings
} from 'lucide-react';
import { apiService } from '@/services/api';

interface MobileDashboardProps {
  onNavigate: (page: 'dashboard' | 'locations' | 'celllines') => void;
}

const MobileDashboard = ({ onNavigate }: MobileDashboardProps) => {
  const [stats, setStats] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchStats = async () => {
      try {
        setLoading(true);
        setError(null);
        const data = await apiService.getStats();
        setStats(data);
      } catch (err) {
        setError('Failed to load dashboard data. Please check your connection.');
        console.error('Dashboard error:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchStats();
  }, []);

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <Loader2 className="h-8 w-8 animate-spin mx-auto mb-4 text-blue-600" />
          <p className="text-gray-600">Loading dashboard...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center p-6">
          <AlertCircle className="h-12 w-12 text-red-500 mx-auto mb-4" />
          <h2 className="text-lg font-semibold text-gray-900 mb-2">Connection Error</h2>
          <p className="text-gray-600 mb-4">{error}</p>
          <Button onClick={() => window.location.reload()} className="bg-blue-600 hover:bg-blue-700">
            Retry
          </Button>
        </div>
      </div>
    );
  }

  const statsDisplay = stats ? [
    { 
      label: 'Storage Locations', 
      value: stats.storageLocations?.toString() || '0', 
      icon: MapPin, 
      color: 'bg-green-500' 
    },
    { 
      label: 'Active Cell Lines', 
      value: stats.activeCellLines?.toString() || '0', 
      icon: Microscope, 
      color: 'bg-purple-500' 
    },
    { 
      label: 'Occupied Positions', 
      value: stats.occupiedPositions?.toString() || '0', 
      icon: Package, 
      color: 'bg-blue-500' 
    },
    { 
      label: 'Available Space', 
      value: `${stats.availableSpace || 0}%`, 
      icon: BarChart3, 
      color: 'bg-orange-500' 
    }
  ] : [];

  const quickActions = [
    { 
      title: 'Storage Locations', 
      icon: MapPin, 
      color: 'bg-blue-600', 
      action: () => onNavigate('locations') 
    },
    { 
      title: 'Cell Lines', 
      icon: Microscope, 
      color: 'bg-purple-600', 
      action: () => onNavigate('celllines') 
    },
    { 
      title: 'Statistics', 
      icon: BarChart3, 
      color: 'bg-green-600', 
      action: () => {} 
    },
    { 
      title: 'Settings', 
      icon: Settings, 
      color: 'bg-gray-600', 
      action: () => {} 
    }
  ];

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow-sm border-b">
        <div className="px-4 py-3">
          <div className="flex items-center justify-between mb-3">
            <h1 className="text-xl font-semibold text-gray-900">Cell Storage</h1>
            <div className="flex items-center space-x-2">
              <Button variant="ghost" size="sm">
                <Bell className="h-5 w-5" />
              </Button>
              <Button variant="ghost" size="sm">
                <User className="h-5 w-5" />
              </Button>
            </div>
          </div>
          
          {/* Search Bar */}
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4" />
            <input
              type="text"
              placeholder="Search cell lines, locations..."
              className="w-full pl-10 pr-4 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="p-4">
        <div className="grid grid-cols-2 gap-3 mb-6">
          {statsDisplay.map((stat, index) => (
            <Card key={index} className="border-0 shadow-sm">
              <CardContent className="p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-600 mb-1">{stat.label}</p>
                    <p className="text-2xl font-bold text-gray-900">{stat.value}</p>
                  </div>
                  <div className={`p-2 rounded-lg ${stat.color}`}>
                    <stat.icon className="h-5 w-5 text-white" />
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>

        {/* Quick Actions */}
        <div className="mb-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-3">Quick Actions</h2>
          <div className="grid grid-cols-2 gap-3">
            {quickActions.map((action, index) => (
              <Button
                key={index}
                onClick={action.action}
                className={`${action.color} hover:opacity-90 h-20 flex flex-col items-center justify-center space-y-2`}
              >
                <action.icon className="h-6 w-6 text-white" />
                <span className="text-sm text-white font-medium">{action.title}</span>
              </Button>
            ))}
          </div>
        </div>

        {/* Recent Activity */}
        <div className="mb-20">
          <h2 className="text-lg font-semibold text-gray-900 mb-3">Recent Activity</h2>
          <Card className="border-0 shadow-sm">
            <CardContent className="p-4">
              {stats?.recentActivity && stats.recentActivity.length > 0 ? (
                <div className="space-y-3">
                  {stats.recentActivity.map((activity: any, index: number) => (
                    <div key={index} className="flex items-center space-x-3 py-2">
                      <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
                      <div className="flex-1">
                        <p className="text-sm text-gray-900">{activity.description}</p>
                        <p className="text-xs text-gray-500">{activity.timestamp}</p>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-gray-500 text-center py-4">No recent activity</p>
              )}
            </CardContent>
          </Card>
        </div>
      </div>

      {/* Bottom Navigation */}
      <div className="fixed bottom-0 left-0 right-0 bg-white border-t border-gray-200">
        <div className="grid grid-cols-3">
          <button
            onClick={() => onNavigate('dashboard')}
            className="flex flex-col items-center justify-center py-3 text-blue-600"
          >
            <Home className="h-5 w-5 mb-1" />
            <span className="text-xs font-medium">Home</span>
          </button>
          <button
            onClick={() => onNavigate('locations')}
            className="flex flex-col items-center justify-center py-3 text-gray-400 hover:text-gray-600"
          >
            <MapPin className="h-5 w-5 mb-1" />
            <span className="text-xs">Locations</span>
          </button>
          <button
            onClick={() => onNavigate('celllines')}
            className="flex flex-col items-center justify-center py-3 text-gray-400 hover:text-gray-600"
          >
            <Microscope className="h-5 w-5 mb-1" />
            <span className="text-xs">Cell Lines</span>
          </button>
        </div>
      </div>
    </div>
  );
};

export default MobileDashboard;