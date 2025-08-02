# DYMO Dynamic Template Usage Guide

## Overview

The DYMO print system supports dynamic label templates. Simply configure a .label file and the system will automatically:
- Fill **textbox** objects with text content from backend
- Fill **labelbox** objects with barcode content from backend

## Features

1. **One-Click Configuration**: Just specify the .label file path in config
2. **Auto-Fill**: textbox ← text, labelbox ← barcode
3. **Caching**: Template parsing results are cached for performance
4. **Auto-Fallback**: Uses hardcoded template if .label file doesn't exist

## Usage Instructions

### 1. Prepare .label Template File

1. Create a label template in DYMO Label software
2. Add two objects:
   - **Text Object**: Name it `textbox` (will auto-fill with text content)
   - **Barcode Object**: Name it `labelbox` (will auto-fill with barcode)
3. Save as .label format file

### 2. Configure Print Agent

In `print_agent_config.json`, simply specify the .label file:

```json
{
  "label_file": "sample.label"
}
```

### 3. Deploy Template File

Place the .label file in the same directory as the print agent.

## How It Works

### Automatic Data Mapping
- **textbox** ← `custom_text` or `item_name` (if custom_text is empty)
- **labelbox** ← `barcode`

### Compatibility Support
The system also supports other object naming conventions:
- Objects containing `text` in name → text content
- Objects containing `barcode`, `code`, or `label` in name → barcode content

## Example Template Structure

```xml
<TextObject>
    <Name>textbox</Name>
    <IsVariable>True</IsVariable>
    <!-- other properties -->
</TextObject>

<BarcodeObject>
    <Name>labelbox</Name>
    <IsVariable>True</IsVariable>
    <!-- other properties -->
</BarcodeObject>
```

## Testing Dynamic Templates

Test the parser from command line:

```bash
python label_template_parser.py sample.label
```

## Troubleshooting

1. **Template not loading**: Check .label file path and permissions
2. **Content not updating**: Ensure objects have `IsVariable=True`
3. **Print failing**: Check console output in HTML template

## File Descriptions

- `label_template_parser.py`: Label template parser
- `sample.label`: Example template file
- `auto_print_template.html`: HTML print template
- `production_print_agent.py`: Main print agent program

## Advantages

1. **Minimal Configuration**: Just specify one .label file path
2. **Plug-and-Play**: textbox auto-fills text, labelbox auto-fills barcode
3. **Design Freedom**: Design label layout and styling freely in DYMO software
4. **Auto-Fallback**: Uses built-in template when configuration fails
5. **High Performance**: Template caching avoids repeated parsing

## Printer Configuration

### DYMO LabelWriter 450 Duo Support

DYMO LabelWriter 450 Duo has two printing functions, the system detects two printers:
- **Label Printer**: For printing label paper
- **Tape Printer**: For printing tape

### Printer Selection Modes

Configure `printer_selection` in `print_agent_config.json`:

#### 1. Auto Selection (Default)
```json
{
  "printer_selection": {
    "mode": "auto"
  }
}
```

#### 2. Specific Printer
```json
{
  "printer_selection": {
    "mode": "specific",
    "preferred_printer": "DYMO LabelWriter 450 DUO Label"
  }
}
```

#### 3. Prefer Label Printer
```json
{
  "printer_selection": {
    "mode": "label",
    "label_printer_keywords": ["Label", "LabelWriter"]
  }
}
```

#### 4. Prefer Tape Printer
```json
{
  "printer_selection": {
    "mode": "tape", 
    "tape_printer_keywords": ["Tape", "LabelManager"]
  }
}
```

### Printer Detection Tool

Use `config_test.html` to detect available printers:
1. Open `config_test.html` in browser
2. Click "🔍 Detect Printers" to see all available printers
3. View generated configuration examples
4. Test print functionality

## Complete Configuration Example

```json
{
  "backend_url": "https://your-backend.com",
  "api_token": "your-token",
  "label_file": "my_custom_label.label",
  "printer_selection": {
    "mode": "specific",
    "preferred_printer": "DYMO LabelWriter 450 DUO Tape",
    "label_printer_keywords": ["Label", "LabelWriter"],
    "tape_printer_keywords": ["Tape", "LabelManager"]
  },
  "poll_interval": 3,
  "auto_close_browser": false,
  "debug_mode": true
}
```