import React, { useState } from 'react';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { 
  Search, 
  Filter, 
  Plus, 
  ArrowLeft,
  Package,
  MapPin,
  Calendar,
  Thermometer,
  MoreVertical,
  Edit,
  Trash2
} from 'lucide-react';

interface MobileInventoryProps {
  onNavigate: (page: 'dashboard' | 'inventory' | 'locations' | 'celllines') => void;
}

const MobileInventory = ({ onNavigate }: MobileInventoryProps) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [showFilters, setShowFilters] = useState(false);

  const inventoryItems = [
    {
      id: 'HeLa-001',
      cellLine: 'HeLa',
      location: 'Freezer A-1-3',
      date: '2024-01-15',
      temperature: '-80°C',
      status: 'Available',
      passage: 'P15',
      volume: '1.5ml'
    },
    {
      id: 'MCF7-002',
      cellLine: 'MCF-7',
      location: 'Freezer B-2-1',
      date: '2024-01-10',
      temperature: '-80°C',
      status: 'In Use',
      passage: 'P8',
      volume: '1.0ml'
    },
    {
      id: 'A549-003',
      cellLine: 'A549',
      location: 'Freezer A-3-5',
      date: '2024-01-08',
      temperature: '-80°C',
      status: 'Available',
      passage: 'P12',
      volume: '2.0ml'
    }
  ];

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'Available': return 'bg-green-100 text-green-800';
      case 'In Use': return 'bg-yellow-100 text-yellow-800';
      case 'Reserved': return 'bg-blue-100 text-blue-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 p-4">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center space-x-3">
            <Button variant="ghost" size="sm" onClick={() => onNavigate('dashboard')}>
              <ArrowLeft className="w-5 h-5" />
            </Button>
            <h1 className="text-lg font-semibold text-gray-900">Inventory Management</h1>
          </div>
          <Button size="sm" className="bg-blue-600 hover:bg-blue-700">
            <Plus className="w-4 h-4 mr-2" />
            Add
          </Button>
        </div>

        {/* Search and Filter */}
        <div className="flex space-x-2">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
            <Input
              type="text"
              placeholder="Search by ID, cell line..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-10"
            />
          </div>
          <Button 
            variant="outline" 
            size="sm"
            onClick={() => setShowFilters(!showFilters)}
            className="px-3"
          >
            <Filter className="w-4 h-4" />
          </Button>
        </div>

        {/* Filter Panel */}
        {showFilters && (
          <div className="mt-4 p-4 bg-gray-50 rounded-lg">
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="text-sm font-medium text-gray-700 mb-1 block">Status</label>
                <select className="w-full p-2 border border-gray-300 rounded-md text-sm">
                  <option>All Status</option>
                  <option>Available</option>
                  <option>In Use</option>
                  <option>Reserved</option>
                </select>
              </div>
              <div>
                <label className="text-sm font-medium text-gray-700 mb-1 block">Location</label>
                <select className="w-full p-2 border border-gray-300 rounded-md text-sm">
                  <option>All Locations</option>
                  <option>Freezer A</option>
                  <option>Freezer B</option>
                  <option>Freezer C</option>
                </select>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Inventory List */}
      <div className="p-4 space-y-3 pb-20">
        {inventoryItems.map((item, index) => (
          <Card key={index} className="bg-white shadow-sm">
            <CardContent className="p-4">
              <div className="flex items-start justify-between mb-3">
                <div className="flex-1">
                  <div className="flex items-center space-x-2 mb-1">
                    <h3 className="font-semibold text-gray-900">{item.id}</h3>
                    <Badge className={`text-xs ${getStatusColor(item.status)}`}>
                      {item.status}
                    </Badge>
                  </div>
                  <p className="text-sm text-gray-600 mb-2">{item.cellLine} • Passage {item.passage}</p>
                </div>
                <Button variant="ghost" size="sm" className="p-1">
                  <MoreVertical className="w-4 h-4" />
                </Button>
              </div>

              <div className="grid grid-cols-2 gap-4 text-sm">
                <div className="flex items-center space-x-2">
                  <MapPin className="w-4 h-4 text-gray-400" />
                  <span className="text-gray-600">{item.location}</span>
                </div>
                <div className="flex items-center space-x-2">
                  <Thermometer className="w-4 h-4 text-gray-400" />
                  <span className="text-gray-600">{item.temperature}</span>
                </div>
                <div className="flex items-center space-x-2">
                  <Calendar className="w-4 h-4 text-gray-400" />
                  <span className="text-gray-600">{item.date}</span>
                </div>
                <div className="flex items-center space-x-2">
                  <Package className="w-4 h-4 text-gray-400" />
                  <span className="text-gray-600">{item.volume}</span>
                </div>
              </div>

              {/* Quick Actions */}
              <div className="flex space-x-2 mt-4 pt-3 border-t border-gray-100">
                <Button variant="outline" size="sm" className="flex-1">
                  <Edit className="w-4 h-4 mr-2" />
                  Edit
                </Button>
                <Button variant="outline" size="sm" className="flex-1 text-red-600 border-red-200 hover:bg-red-50">
                  <Trash2 className="w-4 h-4 mr-2" />
                  Remove
                </Button>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Floating Action Button */}
      <div className="fixed bottom-20 right-4">
        <Button className="w-14 h-14 rounded-full bg-blue-600 hover:bg-blue-700 shadow-lg">
          <Plus className="w-6 h-6" />
        </Button>
      </div>

      {/* Bottom Navigation */}
      <div className="fixed bottom-0 left-0 right-0 bg-white border-t border-gray-200 px-4 py-2">
        <div className="flex justify-around">
          {[
            { icon: Package, label: 'Home', page: 'dashboard' as const, active: false },
            { icon: Package, label: 'Inventory', page: 'inventory' as const, active: true },
            { icon: MapPin, label: 'Locations', page: 'locations' as const, active: false },
            { icon: Package, label: 'Cell Lines', page: 'celllines' as const, active: false }
          ].map((tab, index) => (
            <Button
              key={index}
              variant="ghost"
              onClick={() => onNavigate(tab.page)}
              className={`flex flex-col items-center space-y-1 h-auto py-2 ${
                tab.active ? 'text-blue-600' : 'text-gray-600'
              }`}
            >
              <tab.icon className="w-5 h-5" />
              <span className="text-xs">{tab.label}</span>
            </Button>
          ))}
        </div>
      </div>
    </div>
  );
};

export default MobileInventory;