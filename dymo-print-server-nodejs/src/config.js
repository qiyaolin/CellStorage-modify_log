const dotenv = require('dotenv');
const path = require('path');

// Load environment variables
dotenv.config();

const config = {
  // Backend Configuration
  backend: {
    url: process.env.BACKEND_URL || 'http://localhost:5000',
    apiToken: process.env.API_TOKEN || '',
    endpoints: {
      fetchJob: '/api/print/fetch-pending-job',
      updateJob: '/api/print/update-job-status/{id}',
      heartbeat: '/api/print/heartbeat',
      register: '/api/print/register-server'
    }
  },

  // Server Configuration
  server: {
    id: process.env.SERVER_ID || `print-server-${Date.now()}`,
    name: process.env.SERVER_NAME || 'Cell Storage Print Server',
    location: process.env.SERVER_LOCATION || 'Biology Lab',
    port: process.env.PORT || 3001
  },

  // Print Configuration
  print: {
    printerName: process.env.PRINTER_NAME || 'DYMO LabelWriter 450',
    pollInterval: parseInt(process.env.POLL_INTERVAL) || 5000,
    heartbeatInterval: parseInt(process.env.HEARTBEAT_INTERVAL) || 60000
  },

  // DYMO Configuration
  dymo: {
    serviceUrl: process.env.DYMO_SERVICE_URL || 'http://127.0.0.1:41951',
    checkInterval: parseInt(process.env.DYMO_CHECK_INTERVAL) || 30000
  },

  // Logging Configuration
  logging: {
    level: process.env.LOG_LEVEL || 'info',
    file: process.env.LOG_FILE || './logs/print-server.log',
    maxSize: '10m',
    maxFiles: 5
  }
};

// Validation
if (!config.backend.apiToken) {
  console.warn('WARNING: API_TOKEN not set. Please configure authentication.');
}

if (!config.backend.url) {
  throw new Error('BACKEND_URL is required');
}

module.exports = config;