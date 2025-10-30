# Quick Start Guide

## 1. Prerequisites Check
- [ ] DYMO Label Framework installed
- [ ] DYMO printer connected and powered on
- [ ] Python 3.7+ installed
- [ ] `requests` library installed: `pip install requests`

## 2. Configuration (2 minutes)
1. Copy `print_agent_config.example.json` to `print_agent_config.json`
2. Edit the new file and update:
   ```json
   {
     "backend_url": "https://your-api-server.com",
     "api_token": "your-token-here"
   }
   ```

## 3. Test Your Setup
1. Open `config_test.html` in your browser
2. Click "🔍 Detect Printers"
3. Select your printer mode (usually "Specific Printer")
4. Click "🧪 Test Configuration"
5. If successful, click "🖨️ Simulate Print Job"

## 4. Start the Service
Double-click `start_print_agent.bat` or run:
```bash
python production_print_agent.py
```

## 5. Verify It's Working
You should see:
```
INFO - Printer selection mode: specific
INFO - Preferred printer: [Your Printer Name]
INFO - Health check passed
```

## Troubleshooting
- **No printers found**: Check DYMO software installation
- **Configuration errors**: Verify JSON syntax in config file
- **Connection issues**: Check your backend_url and api_token
- **Wrong printer**: Use config_test.html to find correct printer name

## Common Printer Names
- DYMO LabelWriter 450 DUO Label
- DYMO LabelWriter 450 DUO Tape
- DYMO LabelWriter 450

For detailed documentation, see `README.md`.