import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { 
  Beaker, 
  Database, 
  Thermometer, 
  Activity, 
  TrendingUp, 
  Users, 
  AlertTriangle,
  CheckCircle,
  Clock,
  Search,
  Plus,
  Settings,
  BarChart3,
  Zap,
  Snowflake,
  Building,
  FlaskConical
} from 'lucide-react';

interface DashboardData {
  stats: {
    totalSamples: number;
    activeBatches: number;
    storageCapacity: number;
    systemStatus: string;
  };
  recentActivities: Array<{
    id: number;
    action: string;
    details: string;
    time: string;
    type: string;
    user: string;
  }>;
  storageLocations: Array<{
    name: string;
    capacity: number;
    total: number;
    available: number;
    color: string;
  }>;
}

const Dashboard = () => {
  const [currentTime, setCurrentTime] = useState(new Date());
  const [dashboardData, setDashboardData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentTime(new Date());
    }, 1000);

    // 从后端API获取仪表板数据
    const fetchDashboardData = async () => {
      try {
        const response = await fetch('/api/dashboard/stats');
        if (response.ok) {
          const data = await response.json();
          setDashboardData(data);
        } else {
          // 如果API不可用，显示空状态
          setDashboardData({
            stats: {
              totalSamples: 0,
              activeBatches: 0,
              storageCapacity: 0,
              systemStatus: 'Unknown'
            },
            recentActivities: [],
            storageLocations: []
          });
        }
      } catch (error) {
        console.error('Failed to fetch dashboard data:', error);
        // 错误状态
        setDashboardData({
          stats: {
            totalSamples: 0,
            activeBatches: 0,
            storageCapacity: 0,
            systemStatus: 'Error'
          },
          recentActivities: [],
          storageLocations: []
        });
      } finally {
        setLoading(false);
      }
    };

    fetchDashboardData();
    // 每30秒刷新一次数据
    const dataRefreshInterval = setInterval(fetchDashboardData, 30000);

    return () => {
      clearInterval(timer);
      clearInterval(dataRefreshInterval);
    };
  }, []);

  const getActivityIcon = (type: string) => {
    switch (type) {
      case 'success': return <CheckCircle className="w-4 h-4 text-green-400" />;
      case 'warning': return <AlertTriangle className="w-4 h-4 text-yellow-400" />;
      case 'info': return <Activity className="w-4 h-4 text-blue-400" />;
      default: return <Clock className="w-4 h-4 text-gray-400" />;
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-blue-900 to-slate-900 flex items-center justify-center">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-blue-500/30 border-t-blue-500 rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-white text-lg">Loading Dashboard...</p>
        </div>
      </div>
    );
  }

  if (!dashboardData) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-blue-900 to-slate-900 flex items-center justify-center">
        <div className="text-center">
          <AlertTriangle className="w-16 h-16 text-red-400 mx-auto mb-4" />
          <p className="text-white text-lg">Failed to load dashboard data</p>
          <Button 
            onClick={() => window.location.reload()} 
            className="mt-4 bg-blue-600 hover:bg-blue-700"
          >
            Retry
          </Button>
        </div>
      </div>
    );
  }

  const quickStats = [
    {
      title: "Total Samples",
      value: dashboardData.stats.totalSamples,
      icon: Beaker,
      color: "text-blue-400",
      bgColor: "bg-blue-500/10"
    },
    {
      title: "Active Batches",
      value: dashboardData.stats.activeBatches,
      icon: Database,
      color: "text-cyan-400",
      bgColor: "bg-cyan-500/10"
    },
    {
      title: "Storage Capacity",
      value: `${dashboardData.stats.storageCapacity}%`,
      icon: Thermometer,
      color: "text-purple-400",
      bgColor: "bg-purple-500/10"
    },
    {
      title: "System Status",
      value: dashboardData.stats.systemStatus,
      icon: Activity,
      color: "text-green-400",
      bgColor: "bg-green-500/10"
    }
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-blue-900 to-slate-900 relative overflow-hidden">
      {/* Animated Background Elements */}
      <div className="absolute inset-0 overflow-hidden">
        <div className="absolute -top-40 -right-40 w-80 h-80 bg-blue-500/20 rounded-full blur-3xl animate-pulse"></div>
        <div className="absolute -bottom-40 -left-40 w-80 h-80 bg-cyan-500/20 rounded-full blur-3xl animate-pulse delay-1000"></div>
        <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 w-96 h-96 bg-purple-500/10 rounded-full blur-3xl animate-pulse delay-2000"></div>
      </div>

      {/* Header */}
      <div className="relative z-10 p-6">
        <div className="flex items-center justify-between mb-8">
          <div className="flex items-center space-x-4">
            <div className="flex items-center space-x-3">
              <div className="p-3 bg-blue-500/20 rounded-xl backdrop-blur-sm border border-blue-500/30">
                <FlaskConical className="w-8 h-8 text-blue-400" />
              </div>
              <div>
                <h1 className="text-3xl font-bold text-white">CellStorage Dashboard</h1>
                <p className="text-blue-200">Professional Cell Line Management System</p>
              </div>
            </div>
          </div>
          <div className="flex items-center space-x-4">
            <div className="text-right">
              <p className="text-sm text-blue-200">Current Time</p>
              <p className="text-lg font-mono text-white">
                {currentTime.toLocaleTimeString()}
              </p>
            </div>
            <Badge variant="outline" className="border-green-500/50 text-green-400 bg-green-500/10">
              {dashboardData.stats.systemStatus === 'Operational' ? 'System Online' : dashboardData.stats.systemStatus}
            </Badge>
          </div>
        </div>

        {/* Quick Stats */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          {quickStats.map((stat, index) => (
            <Card key={index} className="bg-white/10 backdrop-blur-md border-white/20 hover:bg-white/15 transition-all duration-300 group">
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-blue-200 mb-1">{stat.title}</p>
                    <p className="text-2xl font-bold text-white">{stat.value}</p>
                  </div>
                  <div className={`p-3 rounded-xl ${stat.bgColor} group-hover:scale-110 transition-transform duration-300`}>
                    <stat.icon className={`w-6 h-6 ${stat.color}`} />
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>

        {/* Main Content Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Storage Overview */}
          <Card className="lg:col-span-2 bg-white/10 backdrop-blur-md border-white/20">
            <CardHeader>
              <CardTitle className="text-white flex items-center space-x-2">
                <Snowflake className="w-5 h-5 text-blue-400" />
                <span>Storage Overview</span>
              </CardTitle>
            </CardHeader>
            <CardContent>
              {dashboardData.storageLocations.length > 0 ? (
                <div className="space-y-4">
                  {dashboardData.storageLocations.map((location, index) => (
                    <div key={index} className="p-4 bg-white/5 rounded-lg border border-white/10">
                      <div className="flex items-center justify-between mb-2">
                        <div className="flex items-center space-x-3">
                          <div className={`w-3 h-3 rounded-full ${location.color}`}></div>
                          <span className="text-white font-medium">{location.name}</span>
                        </div>
                        <div className="text-right">
                          <span className="text-white font-bold">{location.available}</span>
                          <span className="text-blue-200 text-sm">/{location.total} available</span>
                        </div>
                      </div>
                      <Progress value={location.capacity} className="h-2" />
                      <p className="text-xs text-blue-200 mt-1">{location.capacity}% capacity</p>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-8">
                  <Building className="w-12 h-12 text-blue-400 mx-auto mb-4 opacity-50" />
                  <p className="text-blue-200">No storage locations configured</p>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Quick Actions */}
          <Card className="bg-white/10 backdrop-blur-md border-white/20">
            <CardHeader>
              <CardTitle className="text-white flex items-center space-x-2">
                <Zap className="w-5 h-5 text-yellow-400" />
                <span>Quick Actions</span>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 gap-3">
                <Button className="bg-blue-600 hover:bg-blue-700 text-white border-0 h-20 flex flex-col items-center justify-center space-y-2 hover:scale-105 transition-all duration-300">
                  <Plus className="w-6 h-6" />
                  <span className="text-xs text-center">Add Cryovial</span>
                </Button>
                <Button className="bg-cyan-600 hover:bg-cyan-700 text-white border-0 h-20 flex flex-col items-center justify-center space-y-2 hover:scale-105 transition-all duration-300">
                  <Search className="w-6 h-6" />
                  <span className="text-xs text-center">Search Inventory</span>
                </Button>
                <Button className="bg-purple-600 hover:bg-purple-700 text-white border-0 h-20 flex flex-col items-center justify-center space-y-2 hover:scale-105 transition-all duration-300">
                  <Database className="w-6 h-6" />
                  <span className="text-xs text-center">Manage Batches</span>
                </Button>
                <Button className="bg-indigo-600 hover:bg-indigo-700 text-white border-0 h-20 flex flex-col items-center justify-center space-y-2 hover:scale-105 transition-all duration-300">
                  <Settings className="w-6 h-6" />
                  <span className="text-xs text-center">System Settings</span>
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Recent Activities */}
        <Card className="mt-6 bg-white/10 backdrop-blur-md border-white/20">
          <CardHeader>
            <CardTitle className="text-white flex items-center space-x-2">
              <Activity className="w-5 h-5 text-green-400" />
              <span>Recent Activities</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            {dashboardData.recentActivities.length > 0 ? (
              <div className="space-y-4">
                {dashboardData.recentActivities.map((activity) => (
                  <div key={activity.id} className="flex items-start space-x-4 p-3 bg-white/5 rounded-lg border border-white/10 hover:bg-white/10 transition-colors duration-200">
                    <div className="flex-shrink-0 mt-1">
                      {getActivityIcon(activity.type)}
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center justify-between">
                        <p className="text-white font-medium">{activity.action}</p>
                        <span className="text-xs text-blue-200">{activity.time}</span>
                      </div>
                      <p className="text-sm text-blue-200 mt-1">{activity.details}</p>
                      <p className="text-xs text-blue-300 mt-1">by {activity.user}</p>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-8">
                <Activity className="w-12 h-12 text-blue-400 mx-auto mb-4 opacity-50" />
                <p className="text-blue-200">No recent activities</p>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default Dashboard;