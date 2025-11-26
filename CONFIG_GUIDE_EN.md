# BI Data Visualization & Analytics Platform - Configuration Guide

This document provides detailed instructions on how to configure datasources and charts to help you quickly get started with the BI platform.

## 📋 Table of Contents

1. [Datasource Configuration](#datasource-configuration)
2. [Chart Configuration](#chart-configuration)
3. [Configuration Examples](#configuration-examples)
4. [Frequently Asked Questions](#frequently-asked-questions)

---

## Datasource Configuration

Datasource configuration file: `datasource_config.yaml` or `config/datasources.yaml`

### 1. Local File Datasource

Supports CSV and Excel (.xls, .xlsx) files.

```yaml
- id: ds_file_001
  type: file
  name: Sales_Data_CSV
  file_path: uploads/sales_data.csv
  # Optional: Field mapping
  field_mapping:
    date: date
    amount: numeric
    category: text
```

**Configuration Notes:**
- `id`: Unique identifier for the datasource (auto-generated or manually specified)
- `type`: Must be `file`
- `name`: Display name for the datasource
- `file_path`: Relative file path (relative to project root)
- `field_mapping`: Optional, used to specify field types

### 2. Database Datasource

Supports PostgreSQL and MySQL databases.

```yaml
- id: ds_db_001
  type: database
  name: Production_DB_PostgreSQL
  engine: postgresql        # or mysql
  host: localhost
  port: 5432                # PostgreSQL: 5432, MySQL: 3306
  database: sales_db
  user: admin
  password: "your_password"
  sql: "SELECT * FROM sales WHERE date >= CURRENT_DATE - INTERVAL '30 days'"
  table: sales              # Required if using default query
```

**Configuration Notes:**
- `engine`: Database type, `postgresql` or `mysql`
- `host`: Database host address
- `port`: Database port number
- `database`: Database name
- `user`: Database username
- `password`: Database password (recommended to use environment variables)
- `sql`: Optional, custom SQL query statement
- `table`: Optional, table name (when using default query)

**Security Tips:**
- Use environment variables for passwords, do not write them directly in configuration files
- Use read-only database users in production environments

### 3. REST API Datasource

Supports GET and POST requests.

```yaml
- id: ds_api_001
  type: api
  name: Sales_API_Data
  url: https://api.example.com/sales/data
  method: GET              # or POST
  params:                  # GET request parameters
    start_date: "2025-01-01"
    end_date: "2025-01-31"
  headers:                 # Request headers
    Authorization: "Bearer your_token_here"
    Content-Type: "application/json"
  json_body: null          # JSON body for POST requests
  data_path: "data.results"  # Optional, if data is in nested object
```

**Configuration Notes:**
- `url`: API endpoint URL
- `method`: Request method, `GET` or `POST`
- `params`: Query parameters for GET requests (dictionary format)
- `headers`: HTTP request headers (dictionary format)
- `json_body`: JSON request body for POST requests (dictionary format)
- `data_path`: Optional, if API returns data in nested object, specify the path (e.g., `"data.results"`)

**API Data Format Requirements:**
- API must return JSON format data
- Data should be in array format, or accessible via `data_path`
- Each element in the array should be an object containing field names and values

---

## Chart Configuration

Chart configuration file: `chart_config.json` or `config/charts.json`

### Basic Configuration Structure

```json
{
  "id": "chart_001",
  "name": "Chart Name",
  "datasource_id": "ds_file_001",
  "type": "line",
  "x": "date",
  "y": "amount",
  "title": "Chart Title",
  "color_theme": "default",
  "agg_function": "sum"
}
```

### Field Descriptions

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | Yes | Unique identifier for the chart |
| `name` | string | Yes | Chart name |
| `datasource_id` | string | Yes | Associated datasource ID |
| `type` | string | Yes | Chart type: `line`, `bar`, `pie`, `table`, `combo` |
| `x` | string | Yes | X-axis field name |
| `y` | string | Yes | Y-axis field name (except for pie charts and tables) |
| `group` | string/null | No | Grouping field (for multi-series charts) |
| `title` | string | Yes | Chart title |
| `color_theme` | string | Yes | Color theme: `default`, `blue`, `green`, `purple` |
| `custom_colors` | object | No | Custom color mapping |
| `show_labels` | boolean | No | Whether to show data labels |
| `show_legend` | boolean | No | Whether to show legend |
| `agg_function` | string | Yes | Aggregation function: `sum`, `avg`, `count`, `max`, `min`, `none` |

### Chart Type Details

#### 1. Line Chart (line)

Used to display data trends over time or categories.

```json
{
  "type": "line",
  "x": "date",
  "y": "amount",
  "group": "category"  // Optional, for multi-series
}
```

**Use Cases:**
- Time series data
- Trend analysis
- Multi-series comparison

#### 2. Bar Chart (bar)

Used to compare values across different categories.

```json
{
  "type": "bar",
  "x": "category",
  "y": "amount",
  "group": null
}
```

**Use Cases:**
- Category comparison
- Ranking analysis
- Category statistics

#### 3. Pie Chart (pie)

Used to display proportions of parts to the whole.

```json
{
  "type": "pie",
  "x": "category",
  "y": "amount",
  "group": null
}
```

**Use Cases:**
- Proportion analysis
- Composition structure
- Percentage display

#### 4. Table (table)

Used to display detailed data records.

```json
{
  "type": "table",
  "table_columns": ["date", "category", "amount", "quantity"],
  "table_orientation": "horizontal"
}
```

**Field Descriptions:**
- `table_columns`: Array of column names to display
- `table_orientation`: Table orientation, `horizontal` or `vertical`

#### 5. Combo Chart (combo)

Display two different chart types simultaneously (e.g., bar chart + line chart).

```json
{
  "type": "combo",
  "x": "date",
  "y": "revenue",      // Primary Y-axis (bar chart)
  "y2": "order_count", // Secondary Y-axis (line chart)
  "group": null
}
```

**Use Cases:**
- Multi-metric comparison
- Correlation analysis
- Dual-axis display

### Style Configuration

#### Color Themes

The system provides the following preset themes:
- `default`: Default theme (10 colors)
- `blue`: Blue theme
- `green`: Green theme
- `purple`: Purple theme

#### Custom Colors

You can specify colors for specific categories:

```json
{
  "custom_colors": {
    "Electronics": "#1f77b4",
    "Clothing": "#ff7f0e",
    "Food": "#2ca02c"
  }
}
```

### Filter Rules

You can configure filter rules for charts:

```json
{
  "filters": {
    "date_range": {
      "enabled": true,
      "start": "2025-01-01",
      "end": "2025-01-31"
    },
    "value_filters": {
      "enabled": true,
      "min_value": 100,
      "max_value": 10000
    },
    "category_filters": {
      "enabled": true,
      "included_categories": ["Electronics", "Clothing"]
    }
  }
}
```

### Interaction Rules

#### Chart Linking

Configure relationships between charts:

```json
{
  "interaction_rules": {
    "chart_linking": {
      "enabled": true,
      "source_chart_id": "chart_001",
      "target_chart_ids": ["chart_002", "chart_003"],
      "link_type": "filter"
    }
  }
}
```

#### Drill Down

Configure drill-down functionality:

```json
{
  "interaction_rules": {
    "drill_down": {
      "enabled": true,
      "drill_levels": ["Country", "Province", "City"],
      "drill_field": "region"
    }
  }
}
```

---

## Configuration Examples

### Complete Example: Sales Data Analysis

#### 1. Datasource Configuration

```yaml
datasources:
  - id: ds_sales_001
    type: file
    name: Sales_Data
    file_path: uploads/sales_data.csv
```

#### 2. Chart Configuration

```json
{
  "charts": [
    {
      "id": "chart_sales_trend",
      "name": "Sales Trend",
      "datasource_id": "ds_sales_001",
      "type": "line",
      "x": "date",
      "y": "amount",
      "title": "Sales Trend Analysis",
      "color_theme": "default",
      "agg_function": "sum"
    },
    {
      "id": "chart_category_pie",
      "name": "Category Distribution",
      "datasource_id": "ds_sales_001",
      "type": "pie",
      "x": "category",
      "y": "amount",
      "title": "Sales Distribution by Category",
      "color_theme": "default",
      "agg_function": "sum"
    }
  ]
}
```

---

## Frequently Asked Questions

### Q1: How to configure database connection?

A: Add database configuration in `datasource_config.yaml`, ensure:
1. Database service is running
2. Network connection is normal
3. Username and password are correct
4. Database user has appropriate permissions

### Q2: What if the API datasource returns incorrect data format?

A: Check the following:
1. API returns JSON format
2. Data is in array format or accessible via `data_path`
3. If data is in nested object, use `data_path` to specify the path

### Q3: How to customize chart colors?

A: Use the `custom_colors` field in chart configuration, specify color values (hexadecimal format) for each category.

### Q4: What if charts don't display data?

A: Check the following:
1. Is the datasource ID correct?
2. Do field names exist in the datasource?
3. Are field types matched? (e.g., date fields need to be date type)
4. Is the datasource connection normal?

### Q5: How to configure chart linking?

A: Configure in `interaction_rules.chart_linking` of chart configuration:
- `source_chart_id`: Source chart ID
- `target_chart_ids`: Array of target chart IDs
- `link_type`: Link type (e.g., `filter`)

### Q6: What aggregation functions are supported?

A: The following aggregation functions are supported:
- `sum`: Sum
- `avg`: Average
- `count`: Count
- `max`: Maximum
- `min`: Minimum
- `none`: No aggregation (display raw data)

---

## Additional Resources

- View `datasource_config.yaml` for complete datasource configuration examples
- View `chart_config.json` for complete chart configuration examples
- View `README-CN.md` for platform usage guide

---

**Last Updated:** 2025-01-10

