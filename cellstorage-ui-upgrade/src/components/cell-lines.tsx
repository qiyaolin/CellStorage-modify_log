import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { 
  FlaskConical, 
  Search, 
  Filter, 
  Plus, 
  Edit, 
  Trash2, 
  Eye,
  Calendar,
  User,
  Beaker,
  TestTube,
  Microscope,
  Activity,
  TrendingUp,
  AlertCircle,
  CheckCircle,
  Clock,
  BarChart3,
  AlertTriangle
} from 'lucide-react';

interface CellLine {
  id: string;
  name: string;
  description: string;
  origin: string;
  morphology: string;
  totalSamples: number;
  availableSamples: number;
  lastUpdated: string;
  addedBy: string;
  status: 'active' | 'inactive' | 'archived';
  growthRate: number;
  passages: number;
}

interface CellLineStats {
  totalCellLines: number;
  activeLines: number;
  totalSamples: number;
  availableSamples: number;
}

const CellLines = () => {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedFilter, setSelectedFilter] = useState('all');
  const [cellLines, setCellLines] = useState<CellLine[]>([]);
  const [stats, setStats] = useState<CellLineStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchCellLineData = async () => {
      try {
        setLoading(true);
        setError(null);

        const cellLinesResponse = await fetch('/api/celllines/list');
        const statsResponse = await fetch('/api/celllines/stats');

        if (cellLinesResponse.ok && statsResponse.ok) {
          const cellLinesData = await cellLinesResponse.json();
          const statsData = await statsResponse.json();
          
          setCellLines(cellLinesData.cellLines || []);
          setStats(statsData.stats || {
            totalCellLines: 0,
            activeLines: 0,
            totalSamples: 0,
            availableSamples: 0
          });
        } else {
          throw new Error('Failed to fetch cell line data');
        }
      } catch (error) {
        console.error('Error fetching cell line data:', error);
        setError('Failed to load cell line data');
        setCellLines([]);
        setStats({
          totalCellLines: 0,
          activeLines: 0,
          totalSamples: 0,
          availableSamples: 0
        });
      } finally {
        setLoading(false);
      }
    };

    fetchCellLineData();
  }, []);

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active': return 'bg-green-500/20 text-green-400 border-green-500/30';
      case 'inactive': return 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30';
      case 'archived': return 'bg-gray-500/20 text-gray-400 border-gray-500/30';
      default: return 'bg-blue-500/20 text-blue-400 border-blue-500/30';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'active': return <CheckCircle className="w-4 h-4 text-green-400" />;
      case 'inactive': return <Clock className="w-4 h-4 text-yellow-400" />;
      case 'archived': return <AlertCircle className="w-4 h-4 text-gray-400" />;
      default: return <Activity className="w-4 h-4 text-blue-400" />;
    }
  };

  const filteredData = cellLines.filter(item => {
    const matchesSearch = item.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         item.description.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         item.origin.toLowerCase().includes(searchTerm.toLowerCase());
    
    const matchesFilter = selectedFilter === 'all' || item.status === selectedFilter;
    
    return matchesSearch && matchesFilter;
  });

  const statsCards = stats ? [
    { 
      label: 'Total Cell Lines', 
      value: stats.totalCellLines.toString(), 
      icon: FlaskConical, 
      color: 'text-blue-400'
    },
    { 
      label: 'Active Lines', 
      value: stats.activeLines.toString(), 
      icon: CheckCircle, 
      color: 'text-green-400'
    },
    { 
      label: 'Total Samples', 
      value: stats.totalSamples.toString(), 
      icon: TestTube, 
      color: 'text-purple-400'
    },
    { 
      label: 'Available Samples', 
      value: stats.availableSamples.toString(), 
      icon: Beaker, 
      color: 'text-cyan-400'
    }
  ] : [];

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-blue-900 to-slate-900 flex items-center justify-center">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-blue-500/30 border-t-blue-500 rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-white text-lg">Loading Cell Lines...</p>
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
              <FlaskConical className="w-8 h-8 text-blue-400" />
            </div>
            <div>
              <h1 className="text-3xl font-bold text-white">Cell Lines</h1>
              <p className="text-blue-200">Manage your laboratory cell line collection</p>
            </div>
          </div>
          <div className="flex items-center space-x-3">
            <Button className="bg-green-600 hover:bg-green-700 text-white">
              <Plus className="w-4 h-4 mr-2" />
              Add Cell Line
            </Button>
            <Button variant="outline" className="border-blue-500/50 text-blue-400 hover:bg-blue-500/10">
              <BarChart3 className="w-4 h-4 mr-2" />
              Analytics
            </Button>
          </div>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          {statsCards.map((stat, index) => (
            <Card key={index} className="bg-white/10 backdrop-blur-md border-white/20 hover:bg-white/15 transition-all duration-300 group">
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-blue-200 mb-1">{stat.label}</p>
                    <p className="text-2xl font-bold text-white">{stat.value}</p>
                  </div>
                  <div className="p-3 bg-white/10 rounded-xl group-hover:scale-110 transition-transform duration-300">
                    <stat.icon className={`w-6 h-6 ${stat.color}`} />
                  </div>
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
                  placeholder="Search by cell line name, description, or origin..."
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
                  <option value="active">Active</option>
                  <option value="inactive">Inactive</option>
                  <option value="archived">Archived</option>
                </select>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Cell Lines Grid */}
        {filteredData.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {filteredData.map((cellLine) => (
              <Card key={cellLine.id} className="bg-white/10 backdrop-blur-md border-white/20 hover:bg-white/15 transition-all duration-300 group">
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-white flex items-center space-x-2">
                      <Microscope className="w-5 h-5 text-blue-400" />
                      <span>{cellLine.name}</span>
                    </CardTitle>
                    <Badge className={getStatusColor(cellLine.status)}>
                      {getStatusIcon(cellLine.status)}
                      <span className="ml-1 capitalize">{cellLine.status}</span>
                    </Badge>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    <div>
                      <p className="text-sm text-blue-200 mb-1">Description</p>
                      <p className="text-white text-sm">{cellLine.description}</p>
                    </div>

                    <div>
                      <p className="text-sm text-blue-200 mb-1">Origin</p>
                      <p className="text-white text-sm">{cellLine.origin}</p>
                    </div>

                    <div>
                      <p className="text-sm text-blue-200 mb-1">Morphology</p>
                      <Badge variant="outline" className="border-purple-500/50 text-purple-400 bg-purple-500/10">
                        {cellLine.morphology}
                      </Badge>
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <p className="text-sm text-blue-200 mb-1">Total Samples</p>
                        <p className="text-lg font-bold text-white">{cellLine.totalSamples}</p>
                      </div>
                      <div>
                        <p className="text-sm text-blue-200 mb-1">Available</p>
                        <p className="text-lg font-bold text-green-400">{cellLine.availableSamples}</p>
                      </div>
                    </div>

                    <div>
                      <div className="flex items-center justify-between mb-2">
                        <p className="text-sm text-blue-200">Sample Availability</p>
                        <span className="text-sm text-white">
                          {cellLine.totalSamples > 0 ? ((cellLine.availableSamples / cellLine.totalSamples) * 100).toFixed(0) : 0}%
                        </span>
                      </div>
                      <Progress 
                        value={cellLine.totalSamples > 0 ? (cellLine.availableSamples / cellLine.totalSamples) * 100 : 0} 
                        className="h-2" 
                      />
                    </div>

                    <div>
                      <div className="flex items-center justify-between mb-2">
                        <p className="text-sm text-blue-200">Growth Rate</p>
                        <span className="text-sm text-white">{cellLine.growthRate}%</span>
                      </div>
                      <Progress value={cellLine.growthRate} className="h-2" />
                    </div>

                    <div className="grid grid-cols-2 gap-4 text-sm">
                      <div>
                        <p className="text-blue-200 mb-1">Passages</p>
                        <p className="text-white font-medium">{cellLine.passages}</p>
                      </div>
                      <div>
                        <p className="text-blue-200 mb-1">Last Updated</p>
                        <div className="flex items-center space-x-1">
                          <Calendar className="w-3 h-3 text-blue-400" />
                          <p className="text-white font-medium">{cellLine.lastUpdated}</p>
                        </div>
                      </div>
                    </div>

                    <div>
                      <p className="text-blue-200 mb-1 text-sm">Added By</p>
                      <div className="flex items-center space-x-1">
                        <User className="w-3 h-3 text-blue-400" />
                        <p className="text-white font-medium text-sm">{cellLine.addedBy}</p>
                      </div>
                    </div>

                    <div className="flex items-center space-x-2 pt-4 border-t border-white/10">
                      <Button size="sm" variant="outline" className="flex-1 border-blue-500/50 text-blue-400 hover:bg-blue-500/10">
                        <Eye className="w-3 h-3 mr-1" />
                        View
                      </Button>
                      <Button size="sm" variant="outline" className="flex-1 border-yellow-500/50 text-yellow-400 hover:bg-yellow-500/10">
                        <Edit className="w-3 h-3 mr-1" />
                        Edit
                      </Button>
                      <Button size="sm" variant="outline" className="border-red-500/50 text-red-400 hover:bg-red-500/10">
                        <Trash2 className="w-3 h-3" />
                      </Button>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        ) : (
          <Card className="bg-white/10 backdrop-blur-md border-white/20">
            <CardContent className="p-12 text-center">
              <FlaskConical className="w-16 h-16 text-blue-400 mx-auto mb-4 opacity-50" />
              <h3 className="text-xl font-semibold text-white mb-2">No Cell Lines Found</h3>
              <p className="text-blue-200 mb-6">
                {searchTerm || selectedFilter !== 'all' 
                  ? 'Try adjusting your search criteria or filters.'
                  : 'Get started by adding your first cell line to the system.'
                }
              </p>
              <Button className="bg-blue-600 hover:bg-blue-700 text-white">
                <Plus className="w-4 h-4 mr-2" />
                Add Cell Line
              </Button>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
};

export default CellLines;