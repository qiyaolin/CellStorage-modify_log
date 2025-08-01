import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { 
  ArrowLeft, 
  MapPin, 
  Thermometer, 
  Package, 
  Grid3X3, 
  List,
  Search,
  Home,
  Microscope,
  Loader2,
  AlertCircle
} from 'lucide-react';
import { apiService } from '@/services/api';

interface MobileLocationsProps {
  onNavigate: (page: 'dashboard' | 'locations' | 'celllines') => void;
}

const MobileLocations = ({ onNavigate }: MobileLocationsProps) => {
  const [locations, setLocations] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');
  const [searchQuery, setSearchQuery] = useState('');

  useEffect(() => {
    const fetchLocations = async () => {
      try {
        setLoading(true);
        setError(null);
        const data = await apiService.getStorageLocations();
        setLocations(Array.isArray(data) ? data : []);
      } catch (err) {
        setError('Failed to load storage locations. Please check your connection.');
        console.error('Locations error:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchLocations();
  }, []);

  const filteredLocations = locations.filter(location =>
    location.name?.toLowerCase().includes(searchQuery.toLowerCase()) ||
    location.type?.toLowerCase().includes(searchQuery.toLowerCase())
  );

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <Loader2 className="h-8 w-8 animate-spin mx-auto mb-4 text-blue-600" />
          <p className="text-gray-600">Loading storage locations...</p>
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
      case 'occupied':
        return 'bg-red-100 text-red-800';
      case 'available':
        return 'bg-green-100 text-green-800';
      case 'reserved':
        return 'bg-yellow-100 text-yellow-800';
      case 'maintenance':
        return 'bg-gray-100 text-gray-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const getTemperatureColor = (temp: number) => {
    if (temp < -150) return 'text-blue-600';
    if (temp < -80) return 'text-cyan-600';
    if (temp < 0) return 'text-indigo-600';
    return 'text-gray-600';
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
              <h1 className="text-xl font-semibold text-gray-900">Storage Locations</h1>
            </div>
            
            <div className="flex items-center space-x-2">
              <Button
                variant={viewMode === 'grid' ? 'default' : 'ghost'}
                size="sm"
                onClick={() => setViewMode('grid')}
              >
                <Grid3X3 className="h-4 w-4" />
              </Button>
              <Button
                variant={viewMode === 'list' ? 'default' : 'ghost'}
                size="sm"
                onClick={() => setViewMode('list')}
              >
                <List className="h-4 w-4" />
              </Button>
            </div>
          </div>
          
          {/* Search Bar */}
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4" />
            <input
              type="text"
              placeholder="Search locations..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="p-4 pb-20">
        {filteredLocations.length === 0 ? (
          <div className="text-center py-12">
            <MapPin className="h-12 w-12 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">No Storage Locations</h3>
            <p className="text-gray-500">
              {searchQuery ? 'No locations match your search.' : 'No storage locations found.'}
            </p>
          </div>
        ) : (
          <div className={viewMode === 'grid' ? 'grid grid-cols-1 gap-4' : 'space-y-3'}>
            {filteredLocations.map((location, index) => (
              <Card key={location.id || index} className="border-0 shadow-sm">
                <CardContent className="p-4">
                  <div className="flex items-start justify-between mb-3">
                    <div className="flex-1">
                      <h3 className="font-semibold text-gray-900 mb-1">
                        {location.name || `Location ${index + 1}`}
                      </h3>
                      <p className="text-sm text-gray-600 mb-2">
                        {location.type || 'Storage Unit'}
                      </p>
                      
                      <div className="flex items-center space-x-4 text-sm text-gray-600">
                        <div className="flex items-center space-x-1">
                          <Thermometer className={`h-4 w-4 ${getTemperatureColor(location.temperature || -80)}`} />
                          <span>{location.temperature || -80}°C</span>
                        </div>
                        <div className="flex items-center space-x-1">
                          <Package className="h-4 w-4" />
                          <span>{location.occupiedPositions || 0}/{location.totalPositions || 0}</span>
                        </div>
                      </div>
                    </div>
                    
                    <Badge className={getStatusColor(location.status || 'available')}>
                      {location.status || 'Available'}
                    </Badge>
                  </div>

                  {/* Capacity Bar */}
                  <div className="mb-3">
                    <div className="flex justify-between text-xs text-gray-600 mb-1">
                      <span>Capacity</span>
                      <span>
                        {Math.round(((location.occupiedPositions || 0) / (location.totalPositions || 1)) * 100)}%
                      </span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div 
                        className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                        style={{ 
                          width: `${Math.min(((location.occupiedPositions || 0) / (location.totalPositions || 1)) * 100, 100)}%` 
                        }}
                      ></div>
                    </div>
                  </div>

                  {/* Location Details */}
                  {location.description && (
                    <p className="text-sm text-gray-600 mb-3">{location.description}</p>
                  )}

                  {/* Action Buttons */}
                  <div className="flex space-x-2">
                    <Button 
                      size="sm" 
                      className="flex-1 bg-blue-600 hover:bg-blue-700"
                      onClick={() => {
                        // Navigate to location details
                        console.log('View location details:', location.id);
                      }}
                    >
                      View Details
                    </Button>
                    {location.status === 'available' && (
                      <Button 
                        size="sm" 
                        variant="outline" 
                        className="flex-1"
                        onClick={() => {
                          // Navigate to add sample
                          console.log('Add sample to location:', location.id);
                        }}
                      >
                        Add Sample
                      </Button>
                    )}
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </div>

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
            className="flex flex-col items-center justify-center py-3 text-blue-600"
          >
            <MapPin className="h-5 w-5 mb-1" />
            <span className="text-xs font-medium">Locations</span>
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

export default MobileLocations;