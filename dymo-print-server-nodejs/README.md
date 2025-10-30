# DYMO Centralized Print System for Cell Storage

A production-ready centralized printing solution for DYMO label printers, specifically adapted for the Cell Storage project. This system enables automatic printing of vial labels with Batch ID, Batch Name, and location information.

## Features
- ✅ **Portable**: Works on any Windows computer
- ✅ **Centralized**: Print job management from remote backend
- ✅ **Automatic**: Polls backend server for new jobs
- ✅ **Reliable**: Embedded data transmission method
- ✅ **Clean**: Auto-close browser windows after printing
- ✅ **Robust**: Comprehensive error handling and logging
- ✅ **Flexible**: Support for custom text and barcode printing
- ✅ **Production-ready**: Stable configuration and deployment

## Quick Start

1. **Setup Requirements**
   - Install DYMO Label Framework from DYMO website
   - Install Python 3.7+ from python.org (check "Add to PATH")
   - Connect DYMO printer via USB

2. **Configure System**
   - Edit `src/print_agent_config.json` with your backend server settings:
     ```json
     {
       "backend_url": "https://your-cell-storage-backend.appspot.com",
       "api_token": "your-api-token-here"
     }
     ```

3. **Start Print Station**
   - Double-click `start_print_agent.bat`
   - Or run manually: `python src/production_print_agent.py`

## File Structure
```
dymo-print-server-nodejs/
├── src/
│   ├── production_print_agent.py    # Main print agent
│   ├── auto_print_template.html     # Print template
│   └── print_agent_config.json     # Configuration
├── DEPLOYMENT_GUIDE.md             # Detailed setup guide
└── README.md                       # This file
```

## Configuration
Edit `src/print_agent_config.json`:
```json
{
  "backend_url": "https://your-backend-server.com",
  "api_token": "",
  "poll_interval": 3,
  "auto_close_browser": true,
  "debug_mode": false
}
```

## API Integration
Your backend should provide:
- `GET /api/printing/api/jobs/` - Return pending print jobs
- `POST /api/printing/api/jobs/{id}/update-status/` - Receive status updates

## Print Job Format
```json
{
  "id": 123,
  "label_data": {
    "batch_name": "HEK293-P5",
    "batch_id": "B123",
    "vial_number": 1,
    "location": "Tower1/Drawer2/Box3",
    "position": "R1C1",
    "date_created": "2024-08-02"
  }
}
```

## Cell Storage Integration

This print server is specifically configured for the Cell Storage project workflow:

1. **Vial Label Workflow**:
   - User adds vials through the Cell Storage web interface
   - On confirmation page, user can choose "Print vial labels after saving"
   - Each vial gets a separate print job with Batch ID, Batch Name, and location
   - Print server automatically processes jobs and prints individual labels

2. **Label Content**:
   - **Batch Name**: Cell line name and passage (e.g., "HEK293-P5")
   - **Batch ID**: Unique batch identifier (e.g., "B123")
   - **Location**: Full storage location (Tower/Drawer/Box)
   - **Position**: Specific grid position (R1C1)
   - **Date**: Creation date

3. **API Endpoints**:
   - Backend: `https://ambient-decoder-467517-h8.nn.r.appspot.com`
   - Fetch jobs: `/api/print/fetch-pending-job`
   - Update status: `/api/print/update-job-status/{job_id}`

## Troubleshooting
- Check `print_agent.log` for detailed error information
- Verify DYMO framework installation and printer connection
- Ensure backend API endpoints are accessible
- Test with manual print jobs first

For detailed setup instructions, see [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md).

## Version
Production v1.0.0 - Stable release with embedded data method