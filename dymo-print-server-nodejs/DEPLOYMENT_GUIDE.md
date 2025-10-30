# DYMO Centralized Print System - Production Deployment Guide

## Overview
This system enables any computer to serve as a centralized print station for DYMO label printers, receiving print jobs from a remote backend server.

## System Requirements
- Windows 10/11 (recommended)
- DYMO Label Framework installed
- DYMO LabelWriter printer connected
- Internet connection
- Python 3.7+ installed

## Installation Steps

### 1. Prepare the Print Station Computer
1. Install DYMO Label Framework from DYMO website
2. Connect and test your DYMO printer
3. Ensure Python 3.7+ is installed
4. Download this print system folder to the computer

### 2. Setup DYMO Framework
1. The system includes `dymo.connect.framework.js` in the `src` folder
2. Ensure DYMO Label Framework is installed on the print station computer
3. No additional path configuration needed - the system uses relative paths

### 3. Configure Backend Connection
1. Edit `print_agent_config.json`:
   ```json
   {
     "backend_url": "https://your-backend-server.com",
     "api_token": "your-api-token-if-required",
     "poll_interval": 3
   }
   ```

### 4. Start the Print Agent
1. Open Command Prompt or PowerShell
2. Navigate to the src folder:
   ```cmd
   cd path\to\dymo-print-server-nodejs\src
   ```
3. Run the print agent:
   ```cmd
   python production_print_agent.py
   ```

### 5. Verify Operation
The system will:
- ✅ Check DYMO framework connection
- ✅ Connect to backend server
- ✅ Poll for pending print jobs every 3 seconds
- ✅ Automatically print labels when jobs are received
- ✅ Update job status back to server

## Configuration Options

### print_agent_config.json Parameters
- `backend_url`: Your backend server URL
- `api_token`: Authentication token (if required)
- `poll_interval`: How often to check for new jobs (seconds)
- `template_path`: HTML template file path
- `max_retry_count`: Maximum retry attempts for failed jobs
- `auto_close_browser`: Auto-close browser after printing
- `concurrent_jobs`: Number of simultaneous print jobs
- `debug_mode`: Enable debug logging

### API Endpoints
The system expects these backend endpoints:
- `GET /api/printing/api/jobs/` - Get pending print jobs
- `POST /api/printing/api/jobs/{job_id}/update-status/` - Update job status

### Print Job Data Format
Expected job data structure:
```json
{
  "id": 123,
  "label_data": {
    "itemName": "Sample Item",
    "barcode": "SAMPLE-123",
    "customText": "Custom Text",
    "fontSize": "8",
    "isBold": false
  }
}
```

## Troubleshooting

### Common Issues
1. **DYMO Framework Not Found**
   - Verify DYMO Label Framework is installed
   - Check the framework path in `auto_print_template.html`

2. **No Printers Found**
   - Ensure DYMO printer is connected and powered on
   - Check printer drivers are installed
   - Restart DYMO Web Service

3. **Backend Connection Failed**
   - Verify `backend_url` in configuration
   - Check internet connection
   - Verify API endpoints are accessible

4. **Print Jobs Not Processing**
   - Check backend API returns jobs in correct format
   - Verify job status update endpoint is working
   - Check logs for error messages

### Log Files
- Print agent logs are saved to `print_agent.log`
- Check logs for detailed error information

## Production Deployment

### Running as Windows Service
For production deployment, consider running the print agent as a Windows service:

1. Install `pywin32`:
   ```cmd
   pip install pywin32
   ```

2. Create service wrapper script
3. Install and start the service

### Auto-Start Configuration
To start the print agent automatically on system boot:
1. Create a batch file with the python command
2. Add to Windows Startup folder or Task Scheduler

### Security Considerations
- Use HTTPS for backend communication
- Implement API token authentication
- Restrict network access to print station computer
- Keep DYMO framework updated

## Support
For technical support or issues:
1. Check log files for error details
2. Verify all system requirements are met
3. Test with manual print jobs first
4. Contact system administrator

## Version History
- v1.0.0: Initial production release with embedded data method
- Fixed URL parameter passing issues
- Added automatic browser window management
- Improved error handling and logging