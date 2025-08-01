// API service for connecting to Flask backend
const API_BASE_URL = process.env.NODE_ENV === 'production' 
  ? '' // Use relative URLs in production (same domain)
  : 'http://localhost:5000'; // Development Flask server

class ApiService {
  private async request(endpoint: string, options: RequestInit = {}) {
    const url = `${API_BASE_URL}${endpoint}`;
    
    const config: RequestInit = {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    };

    try {
      const response = await fetch(url, config);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error(`API request failed: ${endpoint}`, error);
      throw error;
    }
  }

  // Dashboard statistics
  async getStats() {
    return this.request('/api/stats');
  }

  // Storage locations
  async getStorageLocations() {
    return this.request('/api/storage-locations');
  }

  async getLocationDetails(locationId: string) {
    return this.request(`/api/storage-locations/${locationId}`);
  }

  // Cell lines
  async getCellLines() {
    return this.request('/api/cell-lines');
  }

  async getCellLineDetails(cellLineId: string) {
    return this.request(`/api/cell-lines/${cellLineId}`);
  }

  async createCellLine(data: any) {
    return this.request('/api/cell-lines', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async updateCellLine(cellLineId: string, data: any) {
    return this.request(`/api/cell-lines/${cellLineId}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  }

  async deleteCellLine(cellLineId: string) {
    return this.request(`/api/cell-lines/${cellLineId}`, {
      method: 'DELETE',
    });
  }

  // Search functionality
  async search(query: string) {
    return this.request(`/api/search?q=${encodeURIComponent(query)}`);
  }
}

export const apiService = new ApiService();