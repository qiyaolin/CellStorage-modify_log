import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { 
  Search, 
  Filter, 
  Plus, 
  Edit, 
  Trash2, 
  Eye,
  Download,
  Upload,
  Beaker,
  FlaskConical,
  TestTube,
  Microscope,
  Thermometer,
  Calendar,
  User,
  MapPin,
  BarChart3,
  AlertTriangle
} from 'lucide-react';

interface Sample {
  id: string;
  cellLine: string;
  batch: string;
  location: string;
  status: string;
  volume: string;
  concentration: string;
  dateAdded: string;
  addedBy: string;
  temperature: string;
}

interface InventoryStats {
  totalSamples: number;
  availableSamples: number;
  reservedSamples: number;
  usedDepletedSamples: number;
}

const InventoryManagement = () => {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedFilter, setSelectedFilter] = useState('all');
  const [samples, setSamples] = useState<Sample[]>([]);
  const [stats, setStats] = useState<InventoryStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchInventoryData = async () => {
      try {
        setLoading(true);
        setError(null);

        // 获取样本数据
        const samplesResponse = await fetch('/api/inventory/samples');
        const statsResponse = await fetch('/api/inventory/stats');

        if (samplesResponse.ok && statsResponse.ok) {
          const samplesData = await samplesResponse.json();
          const statsData = await statsResponse.json();
          
          setSamples(samplesData.samples || []);
          setStats(statsData.stats || {
            totalSamples: 0,
            availableSamples: 0,
            reservedSamples: 0,
            usedDepletedSamples: 0
          });
        } else {
          throw new Error('Failed to fetch inventory data');
        }
      } catch (error) {
        console.error('Error fetching inventory data:', error);
        setError('Failed to load inventory data');
        setSamples([]);
        setStats({
          totalSamples: 0,
          availableSamples: 0,
          reservedSamples: 0,
          usedDepletedSamples: 0
        });
      } finally {
        setLoading(false);
      }
    };

    fetchInventoryData();
  }, []);

  const getStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case 'available': return 'bg-green-500/20 text-green-400 border-green-500/30';
      case 'reserved': return 'bg-blue-500/20 text-blue-400 border-blue-500/30';
      case 'used': return 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30';
      case 'depleted': return 'bg-red-500/20 text-red-400 border-red-500/30';
      default: return 'bg-gray-500/20 text-gray-400 border-gray-500/30';
    }
  };

  const filteredData = samples.filter(item => {
    const matchesSearch = item.cellLine.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         item.batch.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         item.id.toLowerCase().includes(searchTerm.toLowerCase());
    
    const matchesFilter = selectedFilter === 'all' || item.status.toLowerCase() === selectedFilter;
    
    return matchesSearch && matchesFilter;
  });

  const statsCards = stats ? [
    { label: 'Total Samples', value: stats.totalSamples.toString(), icon: TestTube, color: 'text-blue-400' },
    { label: 'Available', value: stats.availableSamples.toString(), icon: Beaker, color: 'text-green-400' },
    { label: 'Reserved', value: stats.reservedSamples.toString(), icon: FlaskConical, color: 'text-blue-400' },
    { label: 'Used/Depleted', value: stats.usedDepletedSamples.toString(), icon: Microscope, color: 'text-red-400' }
  ] : [];

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-blue-900 to-slate-900 flex items-center justify-center">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-blue-500/30 border-t-blue-500 rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-white text-lg">Loading Inventory...</p>
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
      </div>

      <div className="relative z-10 p-6">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div className="flex items-center space-x-4">
            <div className="p-3 bg-blue-500/20 rounded-xl backdrop-blur-sm border border-blue-500/30">
              <Beaker className="w-8 h-8 text-blue-400" />
            </div>
            <div>
              <h1 className="text-3xl font-bold text-white">Cryovial Inventory</h1>
              <p className="text-blue-200">Manage and track your cell line samples</p>
            </div>
          </div>
          <div className="flex items-center space-x-3">
            <Button className="bg-green-600 hover:bg-green-700 text-white">
              <Plus className="w-4 h-4 mr-2" />
              Add Sample
            </Button>
            <Button variant="outline" className="border-blue-500/50 text-blue-400 hover:bg-blue-500/10">
              <Upload className="w-4 h-4 mr-2" />
              Import
            </Button>
            <Button variant="outline" className="border-blue-500/50 text-blue-400 hover:bg-blue-500/10">
              <Download className="w-4 h-4 mr-2" />
              Export
            </Button>
          </div>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          {statsCards.map((stat, index) => (
            <Card key={index} className="bg-white/10 backdrop-blur-md border-white/20 hover:bg-white/15 transition-all duration-300">
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-blue-200 mb-1">{stat.label}</p>
                    <p className="text-2xl font-bold text-white">{stat.value}</p>
                  </div>
                  <stat.icon className={`w-8 h-8 ${stat.color}`} />
                </div>
              </CardContent>
            </Card>
          ))}
        </div>

        {/* Search and Filter */}
        <Card className="mb-6 bg-white/10 backdrop-blur-md border-white/20">
          <CardContent className="p-6">
            <div className="flex flex-col md:flex-row gap-4">
              <div className="flex-1 relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-blue-400 w-4 h-4" />
                <Input
                  placeholder="Search by cell line, batch, or sample ID..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-10 bg-white/10 border-white/20 text-white placeholder:text-blue-200"
                />
              </div>
              <div className="flex items-center space-x-2">
                <Filter className="text-blue-400 w-4 h-4" />
                <select
                  value={selectedFilter}
                  onChange={(e) => setSelectedFilter(e.target.value)}
                  className="bg-white/10 border border-white/20 rounded-md px-3 py-2 text-white"
                >
                  <option value="all">All Status</option>
                  <option value="available">Available</option>
                  <option value="reserved">Reserved</option>
                  <option value="used">Used</option>
                  <option value="depleted">Depleted</option>
                </select>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Inventory Table */}
        <Card className="bg-white/10 backdrop-blur-md border-white/20">
          <CardHeader>
            <CardTitle className="text-white flex items-center justify-between">
              <span>Sample Inventory ({filteredData.length} items)</span>
              <Button variant="outline" size="sm" className="border-blue-500/50 text-blue-400 hover:bg-blue-500/10">
                <BarChart3 className="w-4 h-4 mr-2" />
                Analytics
              </Button>
            </CardTitle>
          </CardHeader>
          <CardContent>
            {filteredData.length > 0 ? (
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="border-b border-white/20">
                      <th className="text-left py-3 px-4 text-blue-200 font-medium">Sample ID</th>
                      <th className="text-left py-3 px-4 text-blue-200 font-medium">Cell Line</th>
                      <th className="text-left py-3 px-4 text-blue-200 font-medium">Batch</th>
                      <th className="text-left py-3 px-4 text-blue-200 font-medium">Location</th>
                      <th className="text-left py-3 px-4 text-blue-200 font-medium">Status</th>
                      <th className="text-left py-3 px-4 text-blue-200 font-medium">Volume</th>
                      <th className="text-left py-3 px-4 text-blue-200 font-medium">Concentration</th>
                      <th className="text-left py-3 px-4 text-blue-200 font-medium">Date Added</th>
                      <th className="text-left py-3 px-4 text-blue-200 font-medium">Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {filteredData.map((item, index) => (
                      <tr key={item.id} className="border-b border-white/10 hover:bg-white/5 transition-colors duration-200">
                        <td className="py-4 px-4">
                          <div className="flex items-center space-x-2">
                            <TestTube className="w-4 h-4 text-blue-400" />
                            <span className="text-white font-mono">{item.id}</span>
                          </div>
                        </td>
                        <td className="py-4 px-4 text-white font-medium">{item.cellLine}</td>
                        <td className="py-4 px-4 text-blue-200">{item.batch}</td>
                        <td className="py-4 px-4">
                          <div className="flex items-center space-x-1">
                            <MapPin className="w-3 h-3 text-blue-400" />
                            <span className="text-blue-200 text-sm">{item.location}</span>
                          </div>
                        </td>
                        <td className="py-4 px-4">
                          <Badge className={getStatusColor(item.status)}>
                            {item.status}
                          </Badge>
                        </td>
                        <td className="py-4 px-4 text-blue-200">{item.volume}</td>
                        <td className="py-4 px-4 text-blue-200">{item.concentration}</td>
                        <td className="py-4 px-4">
                          <div className="flex items-center space-x-1">
                            <Calendar className="w-3 h-3 text-blue-400" />
                            <span className="text-blue-200 text-sm">{item.dateAdded}</span>
                          </div>
                        </td>
                        <td className="py-4 px-4">
                          <div className="flex items-center space-x-2">
                            <Button size="sm" variant="outline" className="border-blue-500/50 text-blue-400 hover:bg-blue-500/10">
                              <Eye className="w-3 h-3" />
                            </Button>
                            <Button size="sm" variant="outline" className="border-yellow-500/50 text-yellow-400 hover:bg-yellow-500/10">
                              <Edit className="w-3 h-3" />
                            </Button>
                            <Button size="sm" variant="outline" className="border-red-500/50 text-red-400 hover:bg-red-500/10">
                              <Trash2 className="w-3 h-3" />
                            </Button>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <div className="text-center py-12">
                <Beaker className="w-16 h-16 text-blue-400 mx-auto mb-4 opacity-50" />
                <h3 className="text-xl font-semibold text-white mb-2">No Samples Found</h3>
                <p className="text-blue-200 mb-6">
                  {searchTerm || selectedFilter !== 'all' 
                    ? 'Try adjusting your search criteria or filters.'
                    : 'No samples have been added to the inventory yet.'
                  }
                </p>
                <Button className="bg-blue-600 hover:bg-blue-700 text-white">
                  <Plus className="w-4 h-4 mr-2" />
                  Add First Sample
                </Button>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default InventoryManagement;