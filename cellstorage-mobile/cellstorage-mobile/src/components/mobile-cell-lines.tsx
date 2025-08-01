import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { 
  ArrowLeft, 
  Microscope, 
  Search, 
  Plus,
  Edit,
  Trash2,
  Home,
  MapPin,
  Loader2,
  AlertCircle,
  Calendar,
  User,
  FileText
} from 'lucide-react';
import { apiService } from '@/services/api';

interface MobileCellLinesProps {
  onNavigate: (page: 'dashboard' | 'locations' | 'celllines') => void;
}

const MobileCellLines = ({ onNavigate }: MobileCellLinesProps) => {
  const [cellLines, setCellLines] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('all');

  useEffect(() => {
    const fetchCellLines = async () => {
      try {
        setLoading(true);
        setError(null);
        const data = await apiService.getCellLines();
        setCellLines(Array.isArray(data) ? data : []);
      } catch (err) {
        setError('Failed to load cell lines. Please check your connection.');
        console.error('Cell lines error:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchCellLines();
  }, []);

  const categories = [
    { id: 'all', label: 'All', count: cellLines.length },
    { id: 'active', label: 'Active', count: cellLines.filter(cl => cl.status === 'active').length },
    { id: 'limited', label: 'Limited', count: cellLines.filter(cl => cl.status === 'limited').length },
    { id: 'inactive', label: 'Inactive', count: cellLines.filter(cl => cl.status === 'inactive').length }
  ];

  const filteredCellLines = cellLines.filter(cellLine => {
    const matchesSearch = cellLine.name?.toLowerCase().includes(searchQuery.toLowerCase()) ||
                         cellLine.description?.toLowerCase().includes(searchQuery.toLowerCase()) ||
                         cellLine.source?.toLowerCase().includes(searchQuery.toLowerCase());
    
    const matchesCategory = selectedCategory === 'all' || cellLine.status === selectedCategory;
    
    return matchesSearch && matchesCategory;
  });

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <Loader2 className="h-8 w-8 animate-spin mx-auto mb-4 text-blue-600" />
          <p className="text-gray-600">Loading cell lines...</p>
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

  const getStatusColor = (status: string) => {
    switch (status?.toLowerCase()) {
      case 'active':
        return 'bg-green-100 text-green-800';
      case 'limited':
        return 'bg-yellow-100 text-yellow-800';
      case 'inactive':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const handleEdit = (cellLineId: string) => {
    console.log('Edit cell line:', cellLineId);
    // TODO: Navigate to edit form
  };

  const handleDelete = async (cellLineId: string) => {
    if (window.confirm('Are you sure you want to delete this cell line?')) {
      try {
        await apiService.deleteCellLine(cellLineId);
        setCellLines(cellLines.filter(cl => cl.id !== cellLineId));
      } catch (err) {
        console.error('Delete error:', err);
        alert('Failed to delete cell line. Please try again.');
      }
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow-sm border-b">
        <div className="px-4 py-3">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center space-x-3">
              <Button 
                variant="ghost" 
                size="sm" 
                onClick={() => onNavigate('dashboard')}
              >
                <ArrowLeft className="h-5 w-5" />
              </Button>
              <h1 className="text-xl font-semibold text-gray-900">Cell Lines</h1>
            </div>
            
            <Button 
              size="sm" 
              className="bg-blue-600 hover:bg-blue-700"
              onClick={() => console.log('Add new cell line')}
            >
              <Plus className="h-4 w-4 mr-1" />
              Add
            </Button>
          </div>
          
          {/* Search Bar */}
          <div className="relative mb-3">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4" />
            <input
              type="text"
              placeholder="Search cell lines..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>

          {/* Category Tabs */}
          <div className="flex space-x-1 overflow-x-auto">
            {categories.map((category) => (
              <button
                key={category.id}
                onClick={() => setSelectedCategory(category.id)}
                className={`px-3 py-1.5 rounded-full text-sm font-medium whitespace-nowrap ${
                  selectedCategory === category.id
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                }`}
              >
                {category.label} ({category.count})
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="p-4 pb-20">
        {filteredCellLines.length === 0 ? (
          <div className="text-center py-12">
            <Microscope className="h-12 w-12 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">No Cell Lines</h3>
            <p className="text-gray-500">
              {searchQuery ? 'No cell lines match your search.' : 'No cell lines found.'}
            </p>
          </div>
        ) : (
          <div className="space-y-4">
            {filteredCellLines.map((cellLine, index) => (
              <Card key={cellLine.id || index} className="border-0 shadow-sm">
                <CardContent className="p-4">
                  <div className="flex items-start justify-between mb-3">
                    <div className="flex-1">
                      <div className="flex items-center space-x-2 mb-2">
                        <h3 className="font-semibold text-gray-900">
                          {cellLine.name || `Cell Line ${index + 1}`}
                        </h3>
                        <Badge className={getStatusColor(cellLine.status || 'active')}>
                          {cellLine.status || 'Active'}
                        </Badge>
                      </div>
                      
                      {cellLine.description && (
                        <p className="text-sm text-gray-600 mb-2">{cellLine.description}</p>
                      )}
                      
                      <div className="space-y-1 text-sm text-gray-600">
                        {cellLine.source && (
                          <div className="flex items-center space-x-1">
                            <User className="h-4 w-4" />
                            <span>Source: {cellLine.source}</span>
                          </div>
                        )}
                        
                        {cellLine.passage && (
                          <div className="flex items-center space-x-1">
                            <FileText className="h-4 w-4" />
                            <span>Passage: {cellLine.passage}</span>
                          </div>
                        )}
                        
                        {cellLine.dateCreated && (
                          <div className="flex items-center space-x-1">
                            <Calendar className="h-4 w-4" />
                            <span>Created: {new Date(cellLine.dateCreated).toLocaleDateString()}</span>
                          </div>
                        )}
                      </div>
                    </div>
                    
                    <div className="flex space-x-1 ml-2">
                      <Button
                        size="sm"
                        variant="ghost"
                        onClick={() => handleEdit(cellLine.id)}
                        className="p-2"
                      >
                        <Edit className="h-4 w-4" />
                      </Button>
                      <Button
                        size="sm"
                        variant="ghost"
                        onClick={() => handleDelete(cellLine.id)}
                        className="p-2 text-red-600 hover:text-red-700 hover:bg-red-50"
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>

                  {/* Additional Info */}
                  {(cellLine.notes || cellLine.characteristics) && (
                    <div className="border-t pt-3 mt-3">
                      {cellLine.characteristics && (
                        <div className="mb-2">
                          <p className="text-xs font-medium text-gray-700 mb-1">Characteristics:</p>
                          <p className="text-sm text-gray-600">{cellLine.characteristics}</p>
                        </div>
                      )}
                      
                      {cellLine.notes && (
                        <div>
                          <p className="text-xs font-medium text-gray-700 mb-1">Notes:</p>
                          <p className="text-sm text-gray-600">{cellLine.notes}</p>
                        </div>
                      )}
                    </div>
                  )}

                  {/* Action Buttons */}
                  <div className="flex space-x-2 mt-3">
                    <Button 
                      size="sm" 
                      className="flex-1 bg-blue-600 hover:bg-blue-700"
                      onClick={() => console.log('View details:', cellLine.id)}
                    >
                      View Details
                    </Button>
                    <Button 
                      size="sm" 
                      variant="outline" 
                      className="flex-1"
                      onClick={() => console.log('View samples:', cellLine.id)}
                    >
                      View Samples
                    </Button>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </div>

      {/* Summary Stats */}
      {cellLines.length > 0 && (
        <div className="fixed bottom-16 left-4 right-4">
          <Card className="border-0 shadow-lg bg-white/95 backdrop-blur-sm">
            <CardContent className="p-3">
              <div className="grid grid-cols-3 gap-4 text-center">
                <div>
                  <p className="text-lg font-bold text-gray-900">{cellLines.length}</p>
                  <p className="text-xs text-gray-600">Total</p>
                </div>
                <div>
                  <p className="text-lg font-bold text-green-600">
                    {cellLines.filter(cl => cl.status === 'active').length}
                  </p>
                  <p className="text-xs text-gray-600">Active</p>
                </div>
                <div>
                  <p className="text-lg font-bold text-yellow-600">
                    {cellLines.filter(cl => cl.status === 'limited').length}
                  </p>
                  <p className="text-xs text-gray-600">Limited</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Bottom Navigation */}
      <div className="fixed bottom-0 left-0 right-0 bg-white border-t border-gray-200">
        <div className="grid grid-cols-3">
          <button
            onClick={() => onNavigate('dashboard')}
            className="flex flex-col items-center justify-center py-3 text-gray-400 hover:text-gray-600"
          >
            <Home className="h-5 w-5 mb-1" />
            <span className="text-xs">Home</span>
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
            className="flex flex-col items-center justify-center py-3 text-blue-600"
          >
            <Microscope className="h-5 w-5 mb-1" />
            <span className="text-xs font-medium">Cell Lines</span>
          </button>
        </div>
      </div>
    </div>
  );
};

export default MobileCellLines;