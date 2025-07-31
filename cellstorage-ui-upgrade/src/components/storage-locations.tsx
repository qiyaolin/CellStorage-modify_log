import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { Badge } from '@/components/ui/badge';
import { 
  Building, 
  Snowflake, 
  Thermometer, 
  Plus, 
  Edit, 
  Trash2,
  ChevronRight,
  ChevronDown,
  MapPin,
  AlertTriangle,
  CheckCircle,
  Clock,
  BarChart3,
  Settings,
  Archive,
  HardDrive
} from 'lucide-react';

interface StorageLocation {
  id: string;
  name: string;
  type: 'building' | 'room' | 'freezer' | 'tower' | 'drawer' | 'box';
  capacity: number;
  used: number;
  temperature?: string;
  status: 'operational' | 'maintenance' | 'offline';
  children?: StorageLocation[];
  expanded?: boolean;
}

interface StorageStats {
  totalCapacity: number;
  totalUsed: number;
  availableSpace: number;
  usageRate: number;
  buildingCount: number;
}

const StorageLocations = () => {
  const [locations, setLocations] = useState<StorageLocation[]>([]);
  const [stats, setStats] = useState<StorageStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchStorageData = async () => {
      try {
        setLoading(true);
        setError(null);

        const locationsResponse = await fetch('/api/storage/locations');
        const statsResponse = await fetch('/api/storage/stats');

        if (locationsResponse.ok && statsResponse.ok) {
          const locationsData = await locationsResponse.json();
          const statsData = await statsResponse.json();
          
          setLocations(locationsData.locations || []);
          setStats(statsData.stats || {
            totalCapacity: 0,
            totalUsed: 0,
            availableSpace: 0,
            usageRate: 0,
            buildingCount: 0
          });
        } else {
          throw new Error('Failed to fetch storage data');
        }
      } catch (error) {
        console.error('Error fetching storage data:', error);
        setError('Failed to load storage data');
        setLocations([]);
        setStats({
          totalCapacity: 0,
          totalUsed: 0,
          availableSpace: 0,
          usageRate: 0,
          buildingCount: 0
        });
      } finally {
        setLoading(false);
      }
    };

    fetchStorageData();
  }, []);

  const toggleExpanded = (id: string) => {
    const updateExpanded = (items: StorageLocation[]): StorageLocation[] => {
      return items.map(item => {
        if (item.id === id) {
          return { ...item, expanded: !item.expanded };
        }
        if (item.children) {
          return { ...item, children: updateExpanded(item.children) };
        }
        return item;
      });
    };
    setLocations(updateExpanded(locations));
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'operational': return <CheckCircle className="w-4 h-4 text-green-400" />;
      case 'maintenance': return <Clock className="w-4 h-4 text-yellow-400" />;
      case 'offline': return <AlertTriangle className="w-4 h-4 text-red-400" />;
      default: return <CheckCircle className="w-4 h-4 text-gray-400" />;
    }
  };

  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'building': return <Building className="w-4 h-4 text-blue-400" />;
      case 'room': return <HardDrive className="w-4 h-4 text-cyan-400" />;
      case 'freezer': return <Snowflake className="w-4 h-4 text-purple-400" />;
      case 'tower': return <Archive className="w-4 h-4 text-indigo-400" />;
      case 'drawer': return <Archive className="w-4 h-4 text-green-400" />;
      case 'box': return <Archive className="w-4 h-4 text-yellow-400" />;
      default: return <MapPin className="w-4 h-4 text-gray-400" />;
    }
  };

  const getCapacityColor = (percentage: number) => {
    if (percentage >= 90) return 'text-red-400';
    if (percentage >= 75) return 'text-yellow-400';
    return 'text-green-400';
  };

  const renderLocationNode = (location: StorageLocation, level: number = 0) => {
    const usagePercentage = location.capacity > 0 ? (location.used / location.capacity) * 100 : 0;
    const hasChildren = location.children && location.children.length > 0;

    return (
      <div key={location.id} className={`ml-${level * 6}`}>
        <div className="flex items-center justify-between p-4 bg-white/5 rounded-lg border border-white/10 hover:bg-white/10 transition-all duration-200 mb-2">
          <div className="flex items-center space-x-3 flex-1">
            {hasChildren && (
              <Button
                variant="ghost"
                size="sm"
                onClick={() => toggleExpanded(location.id)}
                className="p-1 h-6 w-6 text-blue-400 hover:bg-blue-500/20"
              >
                {location.expanded ? 
                  <ChevronDown className="w-4 h-4" /> : 
                  <ChevronRight className="w-4 h-4" />
                }
              </Button>
            )}
            {!hasChildren && <div className="w-6" />}
            
            <div className="flex items-center space-x-2">
              {getTypeIcon(location.type)}
              <span className="text-white font-medium">{location.name}</span>
              {location.temperature && (
                <Badge variant="outline" className="border-blue-500/50 text-blue-400 bg-blue-500/10">
                  <Thermometer className="w-3 h-3 mr-1" />
                  {location.temperature}
                </Badge>
              )}
            </div>
          </div>

          <div className="flex items-center space-x-4">
            <div className="text-right min-w-[120px]">
              <div className="flex items-center justify-end space-x-2 mb-1">
                <span className={`text-sm font-medium ${getCapacityColor(usagePercentage)}`}>
                  {location.used}/{location.capacity}
                </span>
                <span className="text-xs text-blue-200">
                  ({usagePercentage.toFixed(1)}%)
                </span>
              </div>
              <Progress value={usagePercentage} className="h-2 w-24" />
            </div>

            <div className="flex items-center space-x-2">
              {getStatusIcon(location.status)}
              <span className="text-xs text-blue-200 capitalize">{location.status}</span>
            </div>

            <div className="flex items-center space-x-1">
              <Button size="sm" variant="outline" className="border-blue-500/50 text-blue-400 hover:bg-blue-500/10 h-8 w-8 p-0">
                <Edit className="w-3 h-3" />
              </Button>
              <Button size="sm" variant="outline" className="border-red-500/50 text-red-400 hover:bg-red-500/10 h-8 w-8 p-0">
                <Trash2 className="w-3 h-3" />
              </Button>
            </div>
          </div>
        </div>

        {hasChildren && location.expanded && (
          <div className="ml-4 space-y-2">
            {location.children!.map(child => renderLocationNode(child, level + 1))}
          </div>
        )}
      </div>
    );
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-blue-900 to-slate-900 flex items-center justify-center">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-blue-500/30 border-t-blue-500 rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-white text-lg">Loading Storage Locations...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-blue-900 to-slate-900 flex items-center justify-center">
        <div className="text-center">
          <AlertTriangle className="w-16 h-16 text-red-400 mx-auto mb-4" />
          <p className="text-white text-lg">{error}</p>
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

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-blue-900 to-slate-900 relative overflow-hidden">
      {/* Animated Background */}
      <div className="absolute inset-0 overflow-hidden">
        <div className="absolute -top-40 -right-40 w-80 h-80 bg-blue-500/20 rounded-full blur-3xl animate-pulse"></div>
        <div className="absolute -bottom-40 -left-40 w-80 h-80 bg-cyan-500/20 rounded-full blur-3xl animate-pulse delay-1000"></div>
        <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 w-96 h-96 bg-purple-500/10 rounded-full blur-3xl animate-pulse delay-2000"></div>
      </div>

      <div className="relative z-10 p-6">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div className="flex items-center space-x-4">
            <div className="p-3 bg-blue-500/20 rounded-xl backdrop-blur-sm border border-blue-500/30">
              <Building className="w-8 h-8 text-blue-400" />
            </div>
            <div>
              <h1 className="text-3xl font-bold text-white">Storage Locations</h1>
              <p className="text-blue-200">Manage your laboratory storage infrastructure</p>
            </div>
          </div>
          <div className="flex items-center space-x-3">
            <Button className="bg-green-600 hover:bg-green-700 text-white">
              <Plus className="w-4 h-4 mr-2" />
              Add Location
            </Button>
            <Button variant="outline" className="border-blue-500/50 text-blue-400 hover:bg-blue-500/10">
              <BarChart3 className="w-4 h-4 mr-2" />
              Analytics
            </Button>
            <Button variant="outline" className="border-blue-500/50 text-blue-400 hover:bg-blue-500/10">
              <Settings className="w-4 h-4 mr-2" />
              Settings
            </Button>
          </div>
        </div>

        {/* Overall Statistics */}
        {stats && (
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
            <Card className="bg-white/10 backdrop-blur-md border-white/20">
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-blue-200 mb-1">Total Capacity</p>
                    <p className="text-2xl font-bold text-white">{stats.totalCapacity.toLocaleString()}</p>
                  </div>
                  <Archive className="w-8 h-8 text-blue-400" />
                </div>
              </CardContent>
            </Card>

            <Card className="bg-white/10 backdrop-blur-md border-white/20">
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-blue-200 mb-1">Used Space</p>
                    <p className="text-2xl font-bold text-white">{stats.totalUsed.toLocaleString()}</p>
                  </div>
                  <HardDrive className="w-8 h-8 text-cyan-400" />
                </div>
              </CardContent>
            </Card>

            <Card className="bg-white/10 backdrop-blur-md border-white/20">
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-blue-200 mb-1">Available Space</p>
                    <p className="text-2xl font-bold text-white">{stats.availableSpace.toLocaleString()}</p>
                  </div>
                  <CheckCircle className="w-8 h-8 text-green-400" />
                </div>
              </CardContent>
            </Card>

            <Card className="bg-white/10 backdrop-blur-md border-white/20">
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-blue-200 mb-1">Usage Rate</p>
                    <p className="text-2xl font-bold text-white">{stats.usageRate.toFixed(1)}%</p>
                  </div>
                  <BarChart3 className="w-8 h-8 text-purple-400" />
                </div>
              </CardContent>
            </Card>
          </div>
        )}

        {/* Storage Tree */}
        <Card className="bg-white/10 backdrop-blur-md border-white/20">
          <CardHeader>
            <CardTitle className="text-white flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <MapPin className="w-5 h-5 text-blue-400" />
                <span>Storage Hierarchy</span>
              </div>
              <Badge variant="outline" className="border-green-500/50 text-green-400 bg-green-500/10">
                {locations.length} Buildings
              </Badge>
            </CardTitle>
          </CardHeader>
          <CardContent>
            {locations.length > 0 ? (
              <div className="space-y-2">
                {locations.map(location => renderLocationNode(location))}
              </div>
            ) : (
              <div className="text-center py-12">
                <Building className="w-16 h-16 text-blue-400 mx-auto mb-4 opacity-50" />
                <h3 className="text-xl font-semibold text-white mb-2">No Storage Locations</h3>
                <p className="text-blue-200 mb-6">
                  No storage locations have been configured yet.
                </p>
                <Button className="bg-blue-600 hover:bg-blue-700 text-white">
                  <Plus className="w-4 h-4 mr-2" />
                  Add First Location
                </Button>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default StorageLocations;