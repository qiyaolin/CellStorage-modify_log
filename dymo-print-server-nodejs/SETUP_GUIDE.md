# DYMO Centralized Print System - Setup Guide

## Overview
This system allows any Windows computer to function as a centralized print station for DYMO label printers. It polls a remote backend server for print jobs and automatically prints labels.

## System Requirements
- **Operating System**: Windows 10/11 (recommended)
- **Python**: Version 3.7 or higher
- **DYMO Hardware**: LabelWriter printer connected via USB
- **DYMO Software**: DYMO Label Framework installed
- **Network**: Internet connection to reach backend server

## Quick Setup Steps

### Step 1: Download and Extract
1. Download this entire folder to your print station computer
2. Extract to any location (e.g., `C:\PrintStation\dymo-print-server-nodejs\`)

### Step 2: Install Dependencies
1. **Install Python 3.7+**:
   - Download from [python.org](https://python.org)
   - During installation, check "Add Python to PATH"

2. **Install DYMO Label Framework**:
   - Download from DYMO website
   - Install the complete framework package
   - Ensure DYMO Web Service is running

3. **Install required Python packages**:
   ```cmd
   pip install requests
   ```

### Step 3: Setup DYMO Printer
1. Connect your DYMO LabelWriter printer via USB
2. Install printer drivers if not automatically detected
3. Test printing from DYMO software to ensure printer works

### Step 4: Configure Backend Connection
1. Navigate to the `src` folder
2. Copy `print_agent_config.example.json` to `print_agent_config.json`
3. Edit `print_agent_config.json` with your settings:

```json
{
  "backend_url": "https://your-backend-server.com",
  "api_token": "your-authentication-token-here",
  "api_endpoints": {
    "get_jobs": "/api/printing/api/jobs/",
    "update_status": "/api/printing/api/jobs/{job_id}/update_status/"
  },
  "poll_interval": 3,
  "template_path": "auto_print_template.html",
  "max_retry_count": 3,
  "browser_timeout": 30,
  "auto_close_browser": true,
  "concurrent_jobs": 1,
  "debug_mode": false
}
```

### Step 5: Start the Print Agent
1. Open Command Prompt or PowerShell
2. Navigate to the src folder:
   ```cmd
   cd path\to\dymo-print-server-nodejs\src
   ```
3. Run the print agent:
   ```cmd
   python production_print_agent.py
   ```

## Configuration Parameters

| Parameter | Description | Default | Notes |
|-----------|-------------|---------|-------|
| `backend_url` | Your backend server URL | Required | Must include https:// |
| `api_token` | Authentication token | Optional | Leave empty if no auth needed |
| `poll_interval` | Seconds between job checks | 3 | Lower = more responsive |
| `max_retry_count` | Max retries for failed jobs | 3 | Prevents infinite loops |
| `browser_timeout` | Browser close delay (seconds) | 30 | Time for printing to complete |
| `auto_close_browser` | Auto-close browser windows | true | Recommended for headless operation |
| `concurrent_jobs` | Simultaneous print jobs | 1 | Keep at 1 for reliability |
| `debug_mode` | Enable detailed logging | false | Set true for troubleshooting |

## Backend API Requirements

Your backend server must provide these endpoints:

### GET /api/printing/api/jobs/
Returns pending print jobs in JSON format:
```json
{
  "results": [
    {
      "id": 123,
      "status": "pending",
      "label_data": {
        "itemName": "Sample Item",
        "barcode": "SAMPLE-123",
        "customText": "Optional text",
        "fontSize": 8,
        "isBold": false
      }
    }
  ]
}
```

### POST /api/printing/api/jobs/{job_id}/update_status/
Accepts status updates from print agent:
```json
{
  "status": "completed",
  "updated_at": "2025-01-01T12:00:00.000Z"
}
```

Valid status transitions:
- `pending` → `processing` or `failed`
- `processing` → `completed` or `failed`
- `failed` → `processing` (retry)

## Troubleshooting

### Common Issues

**1. "DYMO Label Framework not found"**
- Verify DYMO Label Framework is installed
- Restart DYMO Web Service
- Check Windows Services for "DYMO Label Web Service"

**2. "No DYMO printers found"**
- Ensure printer is connected and powered on
- Check printer appears in DYMO software
- Verify USB connection and drivers

**3. "Backend connection failed"**
- Check `backend_url` in configuration
- Verify internet connection
- Test API endpoints manually with curl/browser

**4. "Jobs not processing"**
- Check `print_agent.log` for errors
- Verify API token is correct
- Ensure backend returns jobs in correct format

**5. "Python not found"**
- Install Python 3.7+ from python.org
- Ensure "Add Python to PATH" was selected during installation
- Restart command prompt after Python installation

### Log Files
- Print agent logs are saved to `print_agent.log` in the src folder
- Check logs for detailed error information and troubleshooting

### Testing Setup
1. Start the print agent
2. Look for successful connection messages in console
3. Create a test print job in your backend system
4. Verify job is detected and printed
5. Check job status updates in backend

## Production Deployment

### Running as Windows Service
For unattended operation, install as Windows service:

1. Install service wrapper:
   ```cmd
   pip install pywin32
   ```

2. Create service script and install using Windows Service Manager

### Auto-Start on Boot
1. Create batch file with startup command
2. Add to Windows Startup folder or Task Scheduler
3. Configure to run with appropriate user permissions

### Security Considerations
- Use HTTPS for all backend communication
- Implement proper API authentication
- Restrict network access to print station computer
- Keep DYMO framework and system updated
- Monitor log files for security events

## File Structure
```
dymo-print-server-nodejs/
├── src/
│   ├── production_print_agent.py      # Main print agent
│   ├── auto_print_template.html       # Print template
│   ├── dymo.connect.framework.js      # DYMO framework
│   ├── print_agent_config.json        # Configuration (create from example)
│   └── print_agent_config.example.json # Configuration template
├── start_print_agent.bat              # Windows startup script
├── SETUP_GUIDE.md                     # This file
├── README.md                           # Quick reference
└── DEPLOYMENT_GUIDE.md                 # Detailed deployment info
```

## Support
For technical support:
1. Check log files for error details
2. Verify all system requirements are met  
3. Test components individually (Python, DYMO, network)
4. Contact your system administrator with log files

## Version
Production v1.0.0 - Portable deployment ready