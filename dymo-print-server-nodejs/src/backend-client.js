const axios = require('axios');
const logger = require('./logger');
const config = require('./config');

class BackendClient {
  constructor() {
    this.baseUrl = config.backend.url;
    this.apiToken = config.backend.apiToken;
    this.serverId = config.server.id;
    this.serverName = config.server.name;
    this.serverLocation = config.server.location;
    
    // Create axios instance with default config
    this.client = axios.create({
      baseURL: this.baseUrl,
      timeout: 10000,
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${this.apiToken}`
      }
    });

    // Add request/response interceptors for logging
    this.client.interceptors.request.use(
      (config) => {
        logger.debug(`Backend request: ${config.method?.toUpperCase()} ${config.url}`);
        return config;
      },
      (error) => {
        logger.backend.error('request', error);
        return Promise.reject(error);
      }
    );

    this.client.interceptors.response.use(
      (response) => {
        logger.debug(`Backend response: ${response.status} ${response.config.url}`);
        return response;
      },
      (error) => {
        const operation = error.config?.url || 'unknown';
        logger.backend.error(`response from ${operation}`, error);
        return Promise.reject(error);
      }
    );
  }

  /**
   * Test connection to backend
   */
  async testConnection() {
    try {
      const response = await this.client.get('/api/print/status');
      logger.backend.connected(this.baseUrl);
      return true;
    } catch (error) {
      logger.backend.error('connection test', error);
      return false;
    }
  }

  /**
   * Send heartbeat to backend to indicate server is alive
   */
  async sendHeartbeat() {
    try {
      const heartbeatData = {
        server_id: this.serverId,
        server_name: this.serverName,
        location: this.serverLocation,
        status: 'online',
        timestamp: new Date().toISOString()
      };

      await this.client.post(config.backend.endpoints.heartbeat, heartbeatData);
      logger.backend.heartbeatSent();
      return true;
    } catch (error) {
      logger.backend.error('heartbeat', error);
      return false;
    }
  }

  /**
   * Fetch pending print job from backend
   */
  async fetchPendingJob() {
    try {
      const response = await this.client.get(config.backend.endpoints.fetchJob, {
        params: {
          server_id: this.serverId
        }
      });

      if (response.data && response.data.job) {
        const job = response.data.job;
        logger.backend.jobFetched(job.id);
        return job;
      }

      return null;
    } catch (error) {
      if (error.response?.status === 404) {
        // No pending jobs - this is normal
        return null;
      }
      logger.backend.error('fetch job', error);
      return null;
    }
  }

  /**
   * Update job status in backend
   */
  async updateJobStatus(jobId, status, errorMessage = null) {
    try {
      const updateData = {
        status: status,
        server_id: this.serverId,
        timestamp: new Date().toISOString()
      };

      if (errorMessage) {
        updateData.error_message = errorMessage;
      }

      await this.client.post(
        `/api/print/update-job-status/${jobId}`,
        updateData
      );

      logger.backend.jobUpdated(jobId, status);
      return true;
    } catch (error) {
      logger.backend.error(`update job ${jobId}`, error);
      return false;
    }
  }

  /**
   * Register this print server with the backend
   */
  async registerServer() {
    try {
      const serverData = {
        server_id: this.serverId,
        name: this.serverName,
        location: this.serverLocation,
        status: 'online',
        capabilities: {
          printer_types: ['DYMO'],
          label_types: ['vial', 'batch'],
          max_concurrent_jobs: 5
        }
      };

      await this.client.post('/api/print/register-server', serverData);
      logger.info(`Print server registered: ${this.serverName} (${this.serverId})`);
      return true;
    } catch (error) {
      logger.backend.error('server registration', error);
      return false;
    }
  }

  /**
   * Get server statistics
   */
  getServerStats() {
    return {
      server_id: this.serverId,
      name: this.serverName,
      location: this.serverLocation,
      uptime: process.uptime(),
      memory_usage: process.memoryUsage(),
      backend_url: this.baseUrl
    };
  }
}

module.exports = BackendClient;