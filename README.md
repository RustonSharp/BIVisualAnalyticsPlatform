# BI Data Visualization and Analytics Platform

A complete BI data visualization and analytics platform supporting multiple data source connections, drag-and-drop chart configuration, and interactive dashboard management.

## Features

### 1. Data Source Management
- ✅ **Local File Upload**: Support CSV, Excel (.xls, .xlsx) file uploads
- ✅ **Database Connection**: Support PostgreSQL, MySQL database connections
- ✅ **REST API**: Support fetching JSON data via API
- ✅ **Automatic Field Recognition**: Automatically identify field types (text, numeric, date)
- ✅ **Data Preview**: Real-time data content preview

### 2. Chart Designer
- ✅ **Multiple Chart Types**: Line chart, bar chart, pie chart, table, combo chart
- ✅ **Drag-and-Drop Configuration**: Configure X-axis, Y-axis, and grouping by dragging fields
- ✅ **Aggregation Functions**: Support sum, average, count, maximum, minimum
- ✅ **Style Customization**: Customize chart title, color theme, display options
- ✅ **Real-time Preview**: View chart effects in real-time after configuration

### 3. Dashboard Management
- ✅ **Grid Layout**: Flexible chart grid layout
- ✅ **Time Filtering**: Support quick time range filtering (today, last 7 days, last 30 days, etc.)
- ✅ **Custom Date Range**: Support custom start and end dates
- ✅ **Multiple Charts Display**: Display multiple charts on one page
- ✅ **Data Table**: Display detailed data tables
- ✅ **Chart Interaction**: Click chart data points to filter other charts
- ✅ **Data Drill-Down**: Click chart data points to view detailed data
- ✅ **Export Functionality**: Support export as PNG, PDF, HTML formats

### 4. Configuration Management
- ✅ **Data Source Configuration**: Save data source configurations to YAML files
- ✅ **Chart Configuration**: Save chart configurations to JSON files
- ✅ **Dashboard Configuration**: Save dashboard configurations to JSON files
- ✅ **Import/Export**: Support configuration import and export
- ✅ **Language Settings**: Support Chinese/English language switching

### 5. Data Processing
- ✅ **Field Type Recognition**: Automatically identify text, numeric, and date types (supports multiple date formats)
- ✅ **Data Aggregation**: Support multiple aggregation functions
- ✅ **Data Filtering**: Support conditional filtering and time filtering
- ✅ **Caching Mechanism**: Data source adapter caching to improve performance
- ✅ **Performance Monitoring**: Built-in performance logging

## Tech Stack

- **Frontend Framework**: Plotly Dash + Dash Bootstrap Components
- **Visualization Library**: Plotly
- **Data Processing**: Pandas
- **Database Connection**: SQLAlchemy
- **Configuration Management**: PyYAML
- **File Processing**: openpyxl (Excel)
- **Logging Management**: Python logging (supports log rotation)
- **Export Tools**: Kaleido / Playwright / imgkit (optional)

## Installation

```bash
pip install -r requirements.txt
```

## Running the Application

```bash
python app.py
```

The application will start at `http://localhost:8050`.

## Project Structure

```
BIVisualAnalyticsPlatform/
├── app.py                  # Main application file (Dash app)
├── config_manager.py       # Configuration manager (save/load configurations)
├── data_adapter.py         # Data source adapter (unified data source interface)
├── chart_engine.py         # Chart generation engine (generate various charts)
├── logger.py              # Logging module
├── language_manager.py    # Language management module (Chinese/English support)
├── requirements.txt       # Python dependencies list
├── pages/                 # Page modules
│   ├── datasource_page.py    # Data source management page
│   ├── chart_designer_page.py # Chart designer page
│   ├── dashboard_page.py     # Dashboard page
│   └── settings_page.py      # Settings page
├── components/            # UI components
│   ├── sidebar.py         # Sidebar component
│   └── common.py          # Common components
├── tools/                 # Utility modules
│   ├── load_data.py       # Data loading utilities (file, database, API)
│   └── export_utils.py    # Export utilities (PNG, PDF, HTML)
├── styles/                # Style files
│   └── custom.py          # Custom styles
├── assets/                # Static resources
│   ├── chart_designer.css  # Chart designer styles
│   └── chart_designer.js   # Chart designer scripts
├── config/               # Configuration directory (auto-created)
│   ├── datasources.yaml  # Data source configurations
│   ├── charts.json       # Chart configurations
│   ├── dashboards.json   # Dashboard configurations
│   └── language.json     # Language settings
├── uploads/              # Upload directory (auto-created)
├── exports/              # Export directory (auto-created)
├── logs/                 # Log directory (auto-created)
├── test_data/            # Test data
│   ├── sample_data.csv   # Example data
│   └── combo_chart_data.csv # Combo chart example data
└── examples/             # Configuration examples
    ├── datasource_config.yaml    # Data source configuration example
    ├── datasource_config_en.yaml # Data source configuration example (English)
    ├── chart_config.json         # Chart configuration example
    └── chart_config_en.json      # Chart configuration example (English)
```

## User Guide

### 1. Add Data Source

#### Upload Local File
1. Click "Data Source Management" → "Add Data Source"
2. Select the "Local File" tab
3. Drag and drop or select CSV/Excel file
4. Enter data source name
5. Click "Test Connection" to verify
6. Click "Save" to complete configuration

#### Connect to Database
1. Select the "Database" tab
2. Choose database type (PostgreSQL/MySQL)
3. Fill in connection information (host, port, database name, username, password)
4. Enter data source name
5. Click "Test Connection" to verify
6. Click "Save" to complete configuration

#### Connect to API
1. Select the "REST API" tab
2. Enter API URL
3. Select request method (GET/POST)
4. Configure request headers and parameters (optional, JSON format)
5. Enter data source name
6. Click "Test Connection" to verify
7. Click "Save" to complete configuration

### 2. Create Chart

1. Click "Chart Designer"
2. Select data source
3. Choose chart type (line chart/bar chart/pie chart/table/combo chart)
4. Configure fields:
   - X-axis: Drag date or category field
   - Y-axis: Drag numeric field
   - Group/Color: Drag category field (optional)
5. Select aggregation function (sum/average/count, etc.)
6. Configure style:
   - Chart title
   - Color theme
   - Display options (data labels, legend)
7. View preview effect on the right
8. Click "Save Chart" to save configuration

### 3. Create Dashboard

1. Click "Dashboard"
2. Select or create a dashboard
3. Use time filter to filter data (today, last 7 days, last 30 days, custom range, etc.)
4. View saved charts
5. **Chart Interaction**:
   - Switch to "Filter Mode" to filter other charts by clicking chart data points
   - Switch to "Drill-Down Mode" to view detailed data by clicking chart data points
6. Click "Export" to export as PNG/PDF/HTML

### 4. Configuration Management

1. Click "Settings"
2. **General Settings**:
   - Configure auto-refresh interval
   - Set default chart theme
3. **Data Source Configuration**:
   - Export all data source configurations
   - Import data source configurations
4. **Language Settings**:
   - Switch interface language (Chinese/English)

## Configuration

### Data Source Configuration (config/datasources.yaml)

```yaml
datasources:
  - id: ds_1_1234567890
    type: file
    name: Sales Data CSV
    file_path: uploads/sales.csv
    created_at: "2025-01-10T10:00:00"
    updated_at: "2025-01-10T10:00:00"
```

### Chart Configuration (config/charts.json)

```json
{
  "charts": [
    {
      "id": "chart_1_1234567890",
      "datasource_id": "ds_1_1234567890",
      "type": "line",
      "x": "date",
      "y": "value",
      "title": "Sales Trend",
      "color_theme": "default",
      "agg_function": "sum"
    }
  ]
}
```

## Performance Optimization

- **Data Limiting**: Default limit of 1000 rows (adjustable in configuration)
- **Caching Mechanism**: Data source adapter caches data to avoid repeated loading
- **Pagination**: Automatic pagination for large datasets

## Notes

1. **File Upload**: Uploaded files are saved in the `uploads/` directory
2. **Configuration Saving**: All configurations are automatically saved to the `config/` directory
3. **Database Connection**: Ensure the database allows remote connections (if needed)
4. **API Requests**: API must return JSON format data
5. **Export Functionality**:
   - PNG/PDF export requires one of the following libraries: `kaleido`, `playwright`, or `imgkit`
   - Recommended: `pip install kaleido`
   - Or use Playwright: `pip install playwright && playwright install chromium`
6. **Log Files**: Log files are saved in the `logs/` directory with date-based rotation support
7. **Language Switching**: Language settings are saved in `config/language.json` and take effect after restarting the application

## Development Roadmap

### Completed ✅
- Data source management (file, database, API)
- Chart generation engine (multiple chart types)
- Configuration management (save/load)
- Basic dashboard functionality
- Field type recognition (supports multiple date formats)
- **Chart interaction functionality** (click to filter)
- **Data drill-down functionality**
- **Export functionality** (PNG/PDF/HTML)
- **Language support** (Chinese/English)
- **Logging management** (supports log rotation and performance monitoring)
- **Code refactoring** (type safety, modularization)

### In Progress 🚧
- Real-time data refresh (scheduled auto-refresh)
- Anomaly data marking (highlight data exceeding thresholds)
- Advanced filtering options (multi-condition filtering)
- Custom date format configuration

## License

This project is for learning and demonstration purposes only.

## Changelog

### v1.0.0 (2025-01-10)
- Initial version release
- Complete data source management functionality
- Complete chart designer functionality
- Basic dashboard functionality
- Configuration management functionality

### v1.1.0 (2025-12-07)
- ✅ Added export functionality (PNG/PDF/HTML)
- ✅ Added chart interaction functionality (click to filter)
- ✅ Added data drill-down functionality
- ✅ Added language support (Chinese/English switching)
- ✅ Improved date field type recognition (supports multiple date formats)
- ✅ Code refactoring and type safety improvements
- ✅ Logging system optimization (supports log rotation)
- ✅ Project structure optimization (modularized utilities)

