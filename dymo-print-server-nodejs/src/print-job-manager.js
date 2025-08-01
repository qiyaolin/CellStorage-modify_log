const logger = require('./logger');
const DymoService = require('./dymo-service');
const BackendClient = require('./backend-client');
const config = require('./config');

class PrintJobManager {
  constructor() {
    this.dymoService = new DymoService();
    this.backendClient = new BackendClient();
    this.isProcessing = false;
    this.jobQueue = [];
    this.stats = {
      totalJobs: 0,
      successfulJobs: 0,
      failedJobs: 0,
      startTime: new Date()
    };
  }

  /**
   * Initialize the print job manager
   */
  async initialize() {
    logger.info('Initializing Print Job Manager...');
    
    // Test backend connection
    const backendConnected = await this.backendClient.testConnection();
    if (!backendConnected) {
      logger.warn('Backend connection failed - will retry periodically');
    }

    // Register server with backend
    await this.backendClient.registerServer();

    // Initialize DYMO service
    this.dymoService.startHealthCheck();

    // Start job polling
    this.startJobPolling();

    // Start heartbeat
    this.startHeartbeat();

    logger.info('Print Job Manager initialized successfully');
  }

  /**
   * Start polling for jobs from backend
   */
  startJobPolling() {
    setInterval(async () => {
      if (!this.isProcessing) {
        await this.pollForJobs();
      }
    }, config.print.pollInterval);

    logger.info(`Job polling started (interval: ${config.print.pollInterval}ms)`);
  }

  /**
   * Start sending heartbeats to backend
   */
  startHeartbeat() {
    setInterval(async () => {
      await this.backendClient.sendHeartbeat();
    }, config.print.heartbeatInterval);

    logger.info(`Heartbeat started (interval: ${config.print.heartbeatInterval}ms)`);
  }

  /**
   * Poll backend for pending jobs
   */
  async pollForJobs() {
    try {
      const job = await this.backendClient.fetchPendingJob();
      
      if (job) {
        await this.processJob(job);
      }
    } catch (error) {
      logger.error('Error polling for jobs:', error);
    }
  }

  /**
   * Process a single print job
   */
  async processJob(job) {
    this.isProcessing = true;
    const startTime = Date.now();
    
    try {
      logger.printJob.started(job.id, job.label_data);
      this.stats.totalJobs++;

      // Update job status to processing
      await this.backendClient.updateJobStatus(job.id, 'processing');

      // Validate job data
      if (!this.isValidJob(job)) {
        throw new Error('Invalid job data');
      }

      // Check DYMO printer availability
      if (!this.dymoService.isPrinterAvailable()) {
        throw new Error(`DYMO printer "${config.print.printerName}" is not available`);
      }

      // Print the label
      const printResult = await this.dymoService.printLabel(job.label_data);
      
      if (printResult.success) {
        // Update job status to completed
        await this.backendClient.updateJobStatus(job.id, 'completed');
        
        const duration = Date.now() - startTime;
        logger.printJob.completed(job.id, duration);
        this.stats.successfulJobs++;
      } else {
        throw new Error(printResult.message || 'Print failed');
      }

    } catch (error) {
      // Update job status to failed
      await this.backendClient.updateJobStatus(job.id, 'failed', error.message);
      
      logger.printJob.failed(job.id, error);
      this.stats.failedJobs++;
    } finally {
      this.isProcessing = false;
    }
  }

  /**
   * Validate job data
   */
  isValidJob(job) {
    if (!job || !job.id || !job.label_data) {
      logger.warn('Job missing required fields', { job });
      return false;
    }

    const requiredFields = ['batch_name', 'batch_id'];
    const missingFields = requiredFields.filter(field => !job.label_data[field]);
    
    if (missingFields.length > 0) {
      logger.warn(`Job ${job.id} missing required label data:`, missingFields);
      return false;
    }

    return true;
  }

  /**
   * Get current system status
   */
  async getStatus() {
    const dymoStatus = await this.dymoService.getPrinterStatus();
    
    return {
      server: {
        id: config.server.id,
        name: config.server.name,
        location: config.server.location,
        uptime: process.uptime()
      },
      dymo: dymoStatus,
      backend: {
        url: config.backend.url,
        connected: await this.backendClient.testConnection()
      },
      processing: {
        isProcessing: this.isProcessing,
        queueLength: this.jobQueue.length
      },
      stats: {
        ...this.stats,
        uptime: Date.now() - this.stats.startTime.getTime(),
        successRate: this.stats.totalJobs > 0 
          ? Math.round((this.stats.successfulJobs / this.stats.totalJobs) * 100)
          : 0
      }
    };
  }

  /**
   * Manually test print functionality
   */
  async testPrint() {
    const testLabelData = {
      batch_name: 'Test Batch',
      batch_id: 'TEST001',
      vial_number: '1',
      location: 'Test/Location/Box1',
      position: 'R1C1',
      date_created: new Date().toISOString().split('T')[0]
    };

    try {
      logger.info('Starting test print...');
      const result = await this.dymoService.printLabel(testLabelData);
      logger.info('Test print completed successfully');
      return { success: true, message: 'Test print successful' };
    } catch (error) {
      logger.error('Test print failed:', error);
      return { success: false, message: error.message };
    }
  }

  /**
   * Graceful shutdown
   */
  async shutdown() {
    logger.info('Shutting down Print Job Manager...');
    
    // Wait for current job to complete
    while (this.isProcessing) {
      logger.info('Waiting for current job to complete...');
      await new Promise(resolve => setTimeout(resolve, 1000));
    }

    logger.info('Print Job Manager shutdown complete');
  }
}

module.exports = PrintJobManager;