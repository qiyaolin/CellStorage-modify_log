const express = require('express');
const cors = require('cors');
const logger = require('./logger');
const config = require('./config');
const PrintJobManager = require('./print-job-manager');

class PrintServer {
  constructor() {
    this.app = express();
    this.printJobManager = new PrintJobManager();
    this.setupMiddleware();
    this.setupRoutes();
    this.setupErrorHandling();
  }

  /**
   * Setup Express middleware
   */
  setupMiddleware() {
    // CORS support
    this.app.use(cors());
    
    // JSON parsing
    this.app.use(express.json({ limit: '10mb' }));
    this.app.use(express.urlencoded({ extended: true }));
    
    // Request logging
    this.app.use(logger.requestMiddleware);
    
    // Health check endpoint (no authentication required)
    this.app.get('/health', (req, res) => {
      res.json({ 
        status: 'healthy', 
        timestamp: new Date().toISOString(),
        uptime: process.uptime()
      });
    });
  }

  /**
   * Setup API routes
   */
  setupRoutes() {
    // Get server status
    this.app.get('/api/status', async (req, res) => {
      try {
        const status = await this.printJobManager.getStatus();
        res.json(status);
      } catch (error) {
        logger.error('Error getting status:', error);
        res.status(500).json({ error: 'Failed to get status' });
      }
    });

    // Test print endpoint
    this.app.post('/api/test-print', async (req, res) => {
      try {
        const result = await this.printJobManager.testPrint();
        res.json(result);
      } catch (error) {
        logger.error('Error in test print:', error);
        res.status(500).json({ 
          success: false, 
          message: 'Test print failed',
          error: error.message 
        });
      }
    });

    // Get server statistics
    this.app.get('/api/stats', async (req, res) => {
      try {
        const status = await this.printJobManager.getStatus();
        res.json({
          server_info: status.server,
          print_stats: status.stats,
          dymo_status: status.dymo,
          backend_connection: status.backend
        });
      } catch (error) {
        logger.error('Error getting stats:', error);
        res.status(500).json({ error: 'Failed to get statistics' });
      }
    });

    // Shutdown endpoint (for graceful shutdown)
    this.app.post('/api/shutdown', async (req, res) => {
      logger.info('Shutdown requested via API');
      res.json({ message: 'Shutdown initiated' });
      
      setTimeout(async () => {
        await this.shutdown();
        process.exit(0);
      }, 1000);
    });

    // Get configuration (non-sensitive parts)
    this.app.get('/api/config', (req, res) => {
      res.json({
        server: {
          id: config.server.id,
          name: config.server.name,
          location: config.server.location
        },
        print: {
          printerName: config.print.printerName,
          pollInterval: config.print.pollInterval
        },
        dymo: {
          serviceUrl: config.dymo.serviceUrl
        },
        backend: {
          url: config.backend.url
        }
      });
    });

    // Root endpoint
    this.app.get('/', (req, res) => {
      res.json({
        name: 'DYMO Print Server for Cell Storage',
        version: '1.0.0',
        status: 'running',
        endpoints: {
          status: '/api/status',
          stats: '/api/stats',
          config: '/api/config',
          testPrint: '/api/test-print',
          health: '/health'
        }
      });
    });
  }

  /**
   * Setup error handling
   */
  setupErrorHandling() {
    // 404 handler
    this.app.use('*', (req, res) => {
      res.status(404).json({ 
        error: 'Endpoint not found',
        requested: req.originalUrl,
        method: req.method
      });
    });

    // Global error handler
    this.app.use((error, req, res, next) => {
      logger.error('Unhandled error:', error);
      
      res.status(500).json({
        error: 'Internal server error',
        message: error.message,
        timestamp: new Date().toISOString()
      });
    });

    // Process error handlers
    process.on('uncaughtException', (error) => {
      logger.error('Uncaught Exception:', error);
      this.shutdown().then(() => process.exit(1));
    });

    process.on('unhandledRejection', (reason, promise) => {
      logger.error('Unhandled Rejection at:', promise, 'reason:', reason);
    });

    process.on('SIGTERM', () => {
      logger.info('SIGTERM received, shutting down gracefully');
      this.shutdown().then(() => process.exit(0));
    });

    process.on('SIGINT', () => {
      logger.info('SIGINT received, shutting down gracefully');
      this.shutdown().then(() => process.exit(0));
    });
  }

  /**
   * Start the server
   */
  async start() {
    try {
      // Initialize print job manager
      await this.printJobManager.initialize();

      // Start HTTP server
      const port = config.server.port;
      this.server = this.app.listen(port, () => {
        logger.info(`Print server started on port ${port}`);
        logger.info(`Server ID: ${config.server.id}`);
        logger.info(`Server Name: ${config.server.name}`);
        logger.info(`Backend URL: ${config.backend.url}`);
        logger.info(`DYMO Service URL: ${config.dymo.serviceUrl}`);
        logger.info(`Printer: ${config.print.printerName}`);
        logger.info('Print server is ready to process jobs');
      });

      return this.server;
    } catch (error) {
      logger.error('Failed to start print server:', error);
      throw error;
    }
  }

  /**
   * Graceful shutdown
   */
  async shutdown() {
    logger.info('Initiating graceful shutdown...');

    // Stop accepting new connections
    if (this.server) {
      this.server.close(() => {
        logger.info('HTTP server closed');
      });
    }

    // Shutdown print job manager
    await this.printJobManager.shutdown();

    logger.info('Graceful shutdown completed');
  }
}

// Start the server if this file is run directly
if (require.main === module) {
  const printServer = new PrintServer();
  
  printServer.start().catch((error) => {
    logger.error('Failed to start print server:', error);
    process.exit(1);
  });
}

module.exports = PrintServer;