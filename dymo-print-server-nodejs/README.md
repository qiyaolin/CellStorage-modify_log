# DYMO Print Server for Cell Storage

A Node.js-based centralized printing server that monitors the Cell Storage backend for print jobs and prints vial labels using DYMO printers.

## 🏗️ Architecture

```
Frontend (Browser) → Backend (Flask) → Database (Print Jobs) ← Print Server (Node.js) → DYMO Printer
```

- **Frontend**: Users create vials and request label printing
- **Backend**: Manages print job queue in database
- **Print Server**: Monitors backend for jobs and prints labels via DYMO service
- **DYMO Service**: Local DYMO Label Software that controls the printer

## 📋 Requirements

### System Requirements
- **Windows** (DYMO Label Software requires Windows)
- **Node.js 14+**
- **DYMO Label Software** (free from DYMO website)
- **DYMO LabelWriter** printer (450, 450 Twin Turbo, 4XL, etc.)

### Labels
- Recommended: **DYMO 30252 Address Labels** (1-1/8" x 3-1/2")
- Compatible with other DYMO label sizes

### Network
- Access to Cell Storage backend server
- Same network as users who need labels printed

## 🚀 Quick Start

### 1. Install Dependencies
```bash
cd dymo-print-server-nodejs
npm install
```

### 2. Configure Environment
```bash
cp .env.example .env
```

Edit `.env`:
```env
# Backend Configuration
BACKEND_URL=http://your-cell-storage-server:5000
API_TOKEN=your-secure-api-token

# Server Configuration  
SERVER_ID=lab-print-server-001
SERVER_NAME=Biology Lab Print Server
SERVER_LOCATION=Biology Lab - Room 101

# DYMO Configuration
PRINTER_NAME=DYMO LabelWriter 450
```

### 3. Install DYMO Label Software
1. Download from [DYMO website](https://www.dymo.com/support/dymo-user-guides)
2. Install and configure your printer
3. Test printing with DYMO software first

### 4. Test Configuration
```bash
npm run test
```

### 5. Start Print Server
```bash
npm start
```

The server will:
- Connect to the backend
- Register itself as available
- Start monitoring for print jobs
- Send heartbeats every minute

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `BACKEND_URL` | Cell Storage backend URL | `http://localhost:5000` |
| `API_TOKEN` | Authentication token | *Required* |
| `SERVER_ID` | Unique server identifier | Auto-generated |
| `SERVER_NAME` | Display name | `Cell Storage Print Server` |
| `SERVER_LOCATION` | Physical location | `Biology Lab` |
| `PRINTER_NAME` | DYMO printer name | `DYMO LabelWriter 450` |
| `PORT` | Server port | `3001` |
| `POLL_INTERVAL` | Job polling interval (ms) | `5000` |
| `HEARTBEAT_INTERVAL` | Heartbeat interval (ms) | `60000` |
| `LOG_LEVEL` | Logging level | `info` |

### Printer Configuration

The server automatically detects available DYMO printers. To use a specific printer:

1. Open DYMO Label Software
2. Note the exact printer name
3. Set `PRINTER_NAME` in `.env`

## 📊 Monitoring

### Health Check
```bash
curl http://localhost:3001/health
```

### Server Status  
```bash
curl http://localhost:3001/api/status
```

### Statistics
```bash
curl http://localhost:3001/api/stats
```

### Test Print
```bash
curl -X POST http://localhost:3001/api/test-print
```
**⚠️ Warning**: This will print an actual label!

## 🏷️ Label Format

Each vial label contains:
- **Batch Name** (bold, top)
- **Batch ID + Vial Number** (bold, large)
- **Storage Location** (Tower/Drawer/Box)
- **Position** (Row/Column)
- **Date Created**

Example:
```
HEK293 Transfection
B123 - Vial 2
Tower1/Drawer2/Box3
Position: R2C3        2024-01-15
```

## 🔄 Workflow

### User Workflow
1. User creates vials in Cell Storage web interface
2. Clicks "Confirm and Save These X Vial(s)"
3. Chooses "Print vial labels after saving"
4. Vials are saved and print jobs are created
5. Print server processes jobs automatically
6. Labels print on lab printer

### Technical Workflow
1. **Job Creation**: Backend creates print jobs in database
2. **Job Polling**: Print server polls backend every 5 seconds
3. **Job Processing**: Server fetches job and prints label
4. **Status Updates**: Server updates job status in database
5. **Completion**: User sees print status in web interface

## 🛠️ Troubleshooting

### Common Issues

#### Print Server Can't Connect to Backend
```
Error: Backend connection failed
```

**Solutions:**
- Check `BACKEND_URL` in `.env`
- Verify Cell Storage server is running
- Check network connectivity
- Verify API token

#### DYMO Printer Not Found
```
Error: Printer "DYMO LabelWriter 450" is not available
```

**Solutions:**
- Install DYMO Label Software
- Connect and power on printer
- Check printer name with `PRINTER_NAME` setting
- Test with DYMO software first

#### Labels Not Printing
```
Job status: failed - Print request failed
```

**Solutions:**
- Check printer has labels loaded
- Verify DYMO service is running (port 41951)
- Restart DYMO Label Software
- Check printer drivers

#### Server Not Receiving Jobs
```
No pending jobs found
```

**Solutions:**
- Enable centralized printing in backend
- Check server registration in backend
- Verify heartbeat is being sent
- Check database for print jobs

### Logging

Logs are written to:
- **Console**: Real-time output with colors
- **File**: `./logs/print-server.log`
- **Errors**: `./logs/error.log`

View real-time logs:
```bash
tail -f logs/print-server.log
```

### Debug Mode

Run with debug logging:
```bash
LOG_LEVEL=debug npm start
```

## 🔒 Security

### API Authentication
The print server doesn't require authentication for internal endpoints, but should be on a secure network.

### Backend Communication
- Uses API token for backend authentication
- All communication over HTTP (consider HTTPS in production)

### Network Security
- Run on internal lab network
- Consider firewall rules
- Use VPN for remote access

## 📈 Production Deployment

### Windows Service
To run as Windows service:

1. Install `node-windows`:
```bash
npm install -g node-windows
```

2. Create service script (`install-service.js`):
```javascript
const Service = require('node-windows').Service;

const svc = new Service({
  name: 'Cell Storage Print Server',
  description: 'DYMO print server for Cell Storage application',
  script: 'D:\\path\\to\\dymo-print-server-nodejs\\src\\server.js'
});

svc.on('install', () => {
  console.log('Service installed');
  svc.start();
});

svc.install();
```

3. Install service:
```bash
node install-service.js
```

### Monitoring
- Monitor server uptime
- Track print success rates
- Alert on connection failures
- Monitor disk space for logs

### Backup
- Configuration files
- Log files (if needed for audit)
- Server registration info

## 🔧 Development

### Running in Development
```bash
npm run dev
```

Uses `nodemon` for auto-restart on file changes.

### Testing
```bash
# Run all tests
npm test

# Include actual print test (will print a label!)
npm test -- --print-test
```

### Project Structure
```
dymo-print-server-nodejs/
├── src/
│   ├── server.js          # Main server application
│   ├── config.js          # Configuration management
│   ├── logger.js          # Logging utilities
│   ├── dymo-service.js    # DYMO printer interface
│   ├── backend-client.js  # Backend communication
│   ├── print-job-manager.js # Job processing logic
│   └── test.js           # Test suite
├── logs/                  # Log files
├── package.json          # Dependencies and scripts
├── .env.example          # Configuration template
└── README.md             # This file
```

## 📞 Support

### Common Commands
```bash
# Start server
npm start

# Run tests
npm test

# Check status
curl http://localhost:3001/api/status

# Test print (WARNING: prints actual label)
curl -X POST http://localhost:3001/api/test-print

# View logs
tail -f logs/print-server.log

# Stop server
Ctrl+C (or kill process)
```

### Diagnostics
1. Check DYMO service: http://127.0.0.1:41951/DYMO/DLS/Printing/StatusConnected
2. List printers: http://127.0.0.1:41951/DYMO/DLS/Printing/GetPrinters
3. Backend connection: Check server logs
4. Print job queue: Check backend database

### Getting Help
1. Check logs first
2. Run test suite: `npm test`
3. Verify DYMO software works independently
4. Check network connectivity to backend
5. Review configuration settings

## 📝 License

MIT License - See LICENSE file for details.

---

For Cell Storage application support, refer to the main project documentation.