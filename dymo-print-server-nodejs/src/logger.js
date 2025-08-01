const winston = require('winston');
const path = require('path');
const fs = require('fs');
const config = require('./config');

// Create logs directory if it doesn't exist
const logsDir = path.dirname(config.logging.file);
if (!fs.existsSync(logsDir)) {
  fs.mkdirSync(logsDir, { recursive: true });
}

// Custom format for log messages
const logFormat = winston.format.combine(
  winston.format.timestamp({ format: 'YYYY-MM-DD HH:mm:ss' }),
  winston.format.errors({ stack: true }),
  winston.format.printf(({ timestamp, level, message, stack }) => {
    return `${timestamp} [${level.toUpperCase()}]: ${stack || message}`;
  })
);

// Create logger instance
const logger = winston.createLogger({
  level: config.logging.level,
  format: logFormat,
  transports: [
    // Console output with colors
    new winston.transports.Console({
      format: winston.format.combine(
        winston.format.colorize(),
        logFormat
      )
    }),
    
    // File output
    new winston.transports.File({
      filename: config.logging.file,
      maxsize: config.logging.maxSize,
      maxFiles: config.logging.maxFiles
    }),
    
    // Error file (errors only)
    new winston.transports.File({
      filename: path.join(logsDir, 'error.log'),
      level: 'error',
      maxsize: config.logging.maxSize,
      maxFiles: config.logging.maxFiles
    })
  ]
});

// Add request logging middleware
logger.requestMiddleware = (req, res, next) => {
  const start = Date.now();
  
  res.on('finish', () => {
    const duration = Date.now() - start;
    const logLevel = res.statusCode >= 400 ? 'warn' : 'info';
    
    logger.log(logLevel, `${req.method} ${req.url} - ${res.statusCode} (${duration}ms)`);
  });
  
  next();
};

// Print job specific logging
logger.printJob = {
  started: (jobId, labelData) => {
    logger.info(`Print job ${jobId} started`, { jobId, labelData });
  },
  
  completed: (jobId, duration) => {
    logger.info(`Print job ${jobId} completed in ${duration}ms`);
  },
  
  failed: (jobId, error) => {
    logger.error(`Print job ${jobId} failed: ${error.message}`, { jobId, error: error.stack });
  },
  
  queued: (jobId, priority) => {
    logger.info(`Print job ${jobId} queued with priority: ${priority}`);
  }
};

// DYMO specific logging
logger.dymo = {
  connected: (printers) => {
    logger.info(`DYMO service connected. Found ${printers.length} printer(s): ${printers.join(', ')}`);
  },
  
  disconnected: () => {
    logger.warn('DYMO service disconnected');
  },
  
  error: (error) => {
    logger.error(`DYMO service error: ${error.message}`, { error: error.stack });
  }
};

// Backend communication logging
logger.backend = {
  connected: (url) => {
    logger.info(`Connected to backend at ${url}`);
  },
  
  jobFetched: (jobId) => {
    logger.debug(`Fetched job ${jobId} from backend`);
  },
  
  jobUpdated: (jobId, status) => {
    logger.debug(`Updated job ${jobId} status to ${status}`);
  },
  
  heartbeatSent: () => {
    logger.debug('Heartbeat sent to backend');
  },
  
  error: (operation, error) => {
    logger.error(`Backend ${operation} failed: ${error.message}`, { error: error.stack });
  }
};

module.exports = logger;