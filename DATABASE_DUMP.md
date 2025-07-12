# Database Dump Script

This document explains how to use the database dump functionality for the Notion Processing Pipeline.

## Overview

The `dump_database.py` script provides comprehensive database export capabilities for both local PostgreSQL and Supabase databases. It supports multiple output formats and can export specific tables or the entire database.

## Features

- **Multiple Formats**: SQL, CSV, JSON, and custom format exports
- **Flexible Output**: Export all tables or specific tables
- **Database Info**: Get database statistics and table information
- **Cross-Platform**: Works with both local PostgreSQL and Supabase
- **Automatic Timestamps**: Auto-generates timestamped output files
- **Error Handling**: Robust error handling with detailed error messages

## Quick Start

### Using Makefile Commands (Recommended)

```bash
# Show database information
make dump-info

# Create SQL dump
make dump-sql

# Export to CSV
make dump-csv

# Export to JSON
make dump-json

# Create custom format dump
make dump-custom

# Create all format dumps
make dump-all

# Dump specific tables
make dump-documents
make dump-summaries
```

### Using the Script Directly

```bash
# Basic SQL dump
python dump_database.py --format sql

# Export specific tables to CSV
python dump_database.py --format csv --output exports/ --tables notion_documents weekly_summaries

# Show database info
python dump_database.py --info

# Custom database URL
python dump_database.py --database-url "postgresql://user:pass@localhost:5432/db" --format sql
```

## Output Formats

### 1. SQL Format
Creates a standard PostgreSQL dump file that can be used to restore the database.

```bash
python dump_database.py --format sql --output database_backup.sql
```

**Features:**
- Includes CREATE TABLE statements
- Includes INSERT statements for all data
- Can be restored with `psql` or pgAdmin
- Compatible with PostgreSQL and Supabase

### 2. CSV Format
Exports each table to a separate CSV file in a directory.

```bash
python dump_database.py --format csv --output exports/
```

**Output:**
```
exports/
├── notion_documents.csv
├── document_classifications.csv
├── weekly_summaries.csv
└── processing_records.csv
```

### 3. JSON Format
Exports each table to a separate JSON file with records format.

```bash
python dump_database.py --format json --output exports/
```

**Output:**
```
exports/
├── notion_documents.json
├── document_classifications.json
├── weekly_summaries.json
└── processing_records.json
```

### 4. Custom Format
Creates a single JSON file with metadata and all table data.

```bash
python dump_database.py --format custom --output database_dump.json
```

**Features:**
- Includes metadata (timestamp, database info, table list)
- Handles datetime serialization
- Includes row counts and column information
- Single file containing all data

## Command Line Options

| Option | Short | Description | Default |
|--------|-------|-------------|---------|
| `--format` | `-f` | Output format (sql, csv, json, custom) | sql |
| `--output` | `-o` | Output file or directory | auto-generated |
| `--tables` | `-t` | Specific tables to export | all tables |
| `--database-url` | `-d` | Custom database URL | DATABASE_URL env var |
| `--info` | `-i` | Show database info only | false |
| `--verbose` | `-v` | Verbose output | false |

## Examples

### Export Only Notion Documents
```bash
python dump_database.py --format csv --output notion_docs/ --tables notion_documents
```

### Create Timestamped Backup
```bash
python dump_database.py --format sql --output backup_$(date +%Y%m%d_%H%M%S).sql
```

### Export Weekly Summaries for Analysis
```bash
python dump_database.py --format json --output analysis/ --tables weekly_summaries document_classifications
```

### Check Database Status
```bash
python dump_database.py --info --verbose
```

## Environment Variables

The script uses the following environment variables:

- `DATABASE_URL`: PostgreSQL connection string (default: localhost)
- `PGPASSWORD`: PostgreSQL password (set automatically for pg_dump)

## Prerequisites

### For SQL Dumps
- PostgreSQL client tools (`pg_dump`) installed
- Available on most systems via package managers:
  - **macOS**: `brew install postgresql`
  - **Ubuntu/Debian**: `sudo apt-get install postgresql-client`
  - **Windows**: Install PostgreSQL from official website

### For CSV/JSON Dumps
- Python dependencies (already included in project):
  - `pandas`
  - `sqlalchemy`
  - `psycopg2-binary`

## Error Handling

The script provides detailed error messages for common issues:

- **Connection errors**: Check database URL and credentials
- **Missing pg_dump**: Install PostgreSQL client tools
- **Permission errors**: Check file/directory permissions
- **Table not found**: Verify table names exist in database

## Integration with CI/CD

You can integrate database dumps into your CI/CD pipeline:

```yaml
# Example GitHub Actions step
- name: Database Backup
  run: |
    make dump-sql
    # Upload to cloud storage
    aws s3 cp database_dump_*.sql s3://backups/
```

## Troubleshooting

### Common Issues

1. **pg_dump not found**
   ```bash
   # Install PostgreSQL client tools
   brew install postgresql  # macOS
   sudo apt-get install postgresql-client  # Ubuntu
   ```

2. **SSL connection issues with Supabase**
   - The script automatically handles SSL for Supabase
   - Ensure your DATABASE_URL is correct

3. **Permission denied**
   ```bash
   # Make script executable
   chmod +x dump_database.py
   ```

4. **Large database timeouts**
   ```bash
   # Use specific tables or add timeout
   python dump_database.py --tables notion_documents --format csv
   ```

## Security Considerations

- Database passwords are masked in logs and metadata
- Use environment variables for sensitive information
- Consider encrypting backup files for production use
- Regularly rotate database credentials

## Support

For issues or questions:
1. Check the error messages for specific guidance
2. Verify your database connection
3. Ensure all dependencies are installed
4. Review the examples in this document 