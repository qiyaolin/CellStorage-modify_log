# CSV Import Validation Guide

## Overview

I've created two CSV validation programs to help you check if your CSV files can be successfully imported before actually attempting the import.

## Programs

### 1. `csv_validator_standalone.py` (Recommended)
**Standalone version that works without database connection**

```bash
python csv_validator_standalone.py "path/to/your/file.csv"
```

### 2. `csv_import_validator.py` 
**Full version that requires Flask app and database connection**

```bash
python csv_import_validator.py "path/to/your/file.csv"
```

## What Gets Validated

### File-Level Checks
- ✅ File exists and is readable
- ✅ File size under 10MB limit
- ✅ File is not empty
- ✅ File encoding (UTF-8, Latin-1, or fallback)
- ✅ CSV format is parseable

### Header Validation
- ✅ Header matches expected format exactly
- ✅ Supports both Admin format (with Location) and User format (without Location)

**Expected Admin Header:**
```
Vial ID,Batch ID,Batch Name,Vial Tag,Cell Line,Passage Number,Date Frozen,Frozen By,Status,Location,Volume (ml),Concentration,Fluorescence Tag,Resistance,Parental Cell Line,Notes
```

**Expected User Header:**
```
Vial ID,Batch ID,Batch Name,Vial Tag,Cell Line,Passage Number,Date Frozen,Frozen By,Status,Volume (ml),Concentration,Fluorescence Tag,Resistance,Parental Cell Line,Notes
```

### Row-Level Validation

#### For New Records (no Vial ID or invalid Vial ID):
- ✅ **Required fields**: Batch Name, Cell Line, Vial Tag
- ✅ **Unique Vial Tag**: No duplicates within file
- ✅ **Location required**: If admin format, location must be provided
- ✅ **Cell Line exists**: Validates against database (full version only)

#### For Existing Records (valid Vial ID):
- ✅ **Vial Tag consistency**: Matches database record (full version only)
- ✅ **Valid updates**: All update fields are properly formatted

#### Data Format Validation:
- ✅ **Date Frozen**: Must be YYYY-MM-DD format if provided
- ✅ **Location format**: Must match "Tower Name/Drawer Name/Box Name R#C#"
- ✅ **Volume**: Must be valid number if provided
- ✅ **Status**: Should be one of: Available, Used, Depleted, Discarded
- ✅ **Field lengths**: All fields respect database length constraints
- ✅ **Row limits**: Maximum 10,000 rows per file

## Your CSV File Results

✅ **VALIDATION PASSED!** Your CSV file `inventory_summary (2).csv` is valid for import!

### Summary:
- **Total rows**: 2,790 data rows
- **Status**: All rows are valid
- **Format**: Admin format (includes Location column)
- **Unique vial tags**: 2,790 (no duplicates)
- **Unique vial IDs**: 2,790

### Warnings:
- **Location existence**: 2,790 warnings about location existence being unknown
  - This is normal for the standalone version since it can't check the database
  - The locations are properly formatted, they just need database verification

## Why Your Import Might Still Fail

Even though validation passes, import might still fail due to:

1. **Database-specific issues** (standalone version can't check):
   - Cell lines don't exist in database
   - Locations don't exist in database
   - Vial tags already exist in database
   - Vial IDs don't match database records

2. **Server/Network issues**:
   - Database connection problems
   - Server timeouts during large file processing
   - Memory limitations

3. **Authentication issues**:
   - Not logged in as admin user
   - Session expired

## Recommendations

1. **Your file is ready for import!** The validation shows no errors.

2. **Check locations**: Ensure all tower/drawer/box combinations exist in your system.

3. **Check cell lines**: Verify all cell line names exist in your database.

4. **For large files**: Consider importing in smaller batches if you experience timeouts.

5. **Test with small subset**: Try importing just the first 10-50 rows first to verify everything works.

## Common Issues and Solutions

### Header Mismatch
**Problem**: CSV header doesn't match expected format
**Solution**: Use an unmodified export file from Inventory Summary

### Invalid Date Format
**Problem**: Date Frozen not in YYYY-MM-DD format
**Solution**: Convert dates to YYYY-MM-DD format

### Location Format Issues
**Problem**: Location not in "Tower/Drawer/Box R#C#" format
**Solution**: Ensure proper format with spaces before R#C#

### Duplicate Vial Tags
**Problem**: Same vial tag appears multiple times
**Solution**: Ensure each vial tag is unique across the file

### Field Too Long
**Problem**: Text fields exceed database limits
**Solution**: Shorten text to fit within character limits

## Need Help?

If you encounter issues:
1. Run the validation program first to identify problems
2. Fix the reported errors
3. Re-run validation until it passes
4. Then attempt the actual import

The validation closely mirrors the actual import logic, so if validation passes, import should succeed (barring database/network issues).