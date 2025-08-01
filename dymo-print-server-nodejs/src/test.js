/**
 * Test script for DYMO Print Server
 * Tests various components and functionality
 */

const config = require('./config');
const logger = require('./logger');
const DymoService = require('./dymo-service');
const BackendClient = require('./backend-client');
const PrintJobManager = require('./print-job-manager');

class PrintServerTester {
  constructor() {
    this.results = [];
  }

  /**
   * Run a test and record results
   */
  async runTest(testName, testFunction) {
    logger.info(`Running test: ${testName}`);
    const startTime = Date.now();
    
    try {
      await testFunction();
      const duration = Date.now() - startTime;
      this.results.push({
        name: testName,
        status: 'PASS',
        duration: `${duration}ms`,
        error: null
      });
      logger.info(`✅ ${testName} - PASSED (${duration}ms)`);
    } catch (error) {
      const duration = Date.now() - startTime;
      this.results.push({
        name: testName,
        status: 'FAIL',
        duration: `${duration}ms`,
        error: error.message
      });
      logger.error(`❌ ${testName} - FAILED (${duration}ms): ${error.message}`);
    }
  }

  /**
   * Test configuration loading
   */
  async testConfig() {
    if (!config.backend.url) {
      throw new Error('Backend URL not configured');
    }
    
    if (!config.server.id) {
      throw new Error('Server ID not configured');
    }
    
    if (!config.print.printerName) {
      throw new Error('Printer name not configured');
    }
    
    logger.info('Configuration loaded successfully');
  }

  /**
   * Test DYMO service connection
   */
  async testDymoService() {
    const dymoService = new DymoService();
    
    const isConnected = await dymoService.checkConnection();
    if (!isConnected) {
      throw new Error('DYMO service is not available');
    }
    
    const printers = await dymoService.updateAvailablePrinters();
    if (printers.length === 0) {
      throw new Error('No DYMO printers found');
    }
    
    const status = await dymoService.getPrinterStatus();
    if (!status.isPrinterAvailable) {
      throw new Error(`Configured printer "${config.print.printerName}" is not available`);
    }
    
    logger.info(`DYMO service connected with ${printers.length} printer(s)`);
  }

  /**
   * Test backend client connection
   */
  async testBackendClient() {
    const backendClient = new BackendClient();
    
    const isConnected = await backendClient.testConnection();
    if (!isConnected) {
      throw new Error('Backend connection failed');
    }
    
    // Test heartbeat
    const heartbeatSent = await backendClient.sendHeartbeat();
    if (!heartbeatSent) {
      throw new Error('Heartbeat failed');
    }
    
    logger.info('Backend client connected successfully');
  }

  /**
   * Test label XML generation
   */
  async testLabelGeneration() {
    const dymoService = new DymoService();
    
    const testLabelData = {
      batch_name: 'Test Batch Name',
      batch_id: 'TEST001',
      vial_number: '5',
      location: 'Tower1/Drawer2/Box3',
      position: 'R2C3',
      date_created: '2024-01-01'
    };
    
    const labelXml = dymoService.generateVialLabelXml(testLabelData);
    
    if (!labelXml || labelXml.length === 0) {
      throw new Error('Label XML generation failed');
    }
    
    // Check if XML contains our test data
    if (!labelXml.includes(testLabelData.batch_name)) {
      throw new Error('Label XML does not contain batch name');
    }
    
    if (!labelXml.includes(testLabelData.batch_id)) {
      throw new Error('Label XML does not contain batch ID');
    }
    
    logger.info('Label XML generation successful');
  }

  /**
   * Test print functionality (if DYMO is available)
   */
  async testPrintFunctionality() {
    const dymoService = new DymoService();
    
    const isConnected = await dymoService.checkConnection();
    if (!isConnected) {
      throw new Error('DYMO service not available for print test');
    }
    
    if (!dymoService.isPrinterAvailable()) {
      throw new Error('Configured printer not available for print test');
    }
    
    const testLabelData = {
      batch_name: 'TEST PRINT',
      batch_id: 'TEST001',
      vial_number: '1',
      location: 'Test/Location/Box1',
      position: 'R1C1',
      date_created: new Date().toISOString().split('T')[0]
    };
    
    logger.warn('⚠️  About to print test label - make sure printer has labels loaded!');
    await new Promise(resolve => setTimeout(resolve, 3000)); // 3 second delay
    
    const result = await dymoService.printLabel(testLabelData);
    if (!result.success) {
      throw new Error(`Print test failed: ${result.message}`);
    }
    
    logger.info('Test print completed successfully');
  }

  /**
   * Test job polling mechanism
   */
  async testJobPolling() {
    const backendClient = new BackendClient();
    
    // This should return null if no jobs are pending (which is expected)
    const job = await backendClient.fetchPendingJob();
    
    // If we get a job, that's fine too - just log it
    if (job) {
      logger.info(`Found pending job: ${job.id}`);
    } else {
      logger.info('No pending jobs found (expected)');
    }
  }

  /**
   * Run all tests
   */
  async runAllTests() {
    logger.info('🧪 Starting Print Server Tests');
    logger.info('=====================================');
    
    await this.runTest('Configuration Loading', () => this.testConfig());
    await this.runTest('DYMO Service Connection', () => this.testDymoService());
    await this.runTest('Backend Client Connection', () => this.testBackendClient());
    await this.runTest('Label XML Generation', () => this.testLabelGeneration());
    await this.runTest('Job Polling Mechanism', () => this.testJobPolling());
    
    // Optional print test - only run if explicitly requested
    if (process.argv.includes('--print-test')) {
      logger.info('⚠️  Print test requested - this will print an actual label!');
      await this.runTest('Print Functionality', () => this.testPrintFunctionality());
    } else {
      logger.info('ℹ️  Skipping print test (use --print-test to run)');
    }
    
    this.printResults();
  }

  /**
   * Print test results summary
   */
  printResults() {
    logger.info('');
    logger.info('🧪 Test Results Summary');
    logger.info('=======================');
    
    const passed = this.results.filter(r => r.status === 'PASS').length;
    const failed = this.results.filter(r => r.status === 'FAIL').length;
    const total = this.results.length;
    
    this.results.forEach(result => {
      const icon = result.status === 'PASS' ? '✅' : '❌';
      logger.info(`${icon} ${result.name} - ${result.status} (${result.duration})`);
      if (result.error) {
        logger.info(`   Error: ${result.error}`);
      }
    });
    
    logger.info('');
    logger.info(`Total: ${total} | Passed: ${passed} | Failed: ${failed}`);
    
    if (failed === 0) {
      logger.info('🎉 All tests passed!');
    } else {
      logger.warn(`⚠️  ${failed} test(s) failed`);
    }
    
    return failed === 0;
  }
}

// Run tests if this file is executed directly
if (require.main === module) {
  const tester = new PrintServerTester();
  
  tester.runAllTests().then((allPassed) => {
    process.exit(allPassed ? 0 : 1);
  }).catch((error) => {
    logger.error('Test runner failed:', error);
    process.exit(1);
  });
}

module.exports = PrintServerTester;