# Enhanced Dashboard UI - Feature Guide

## URL
http://localhost:8000/meter_readings/latest/

## New Features

### 1. View Mode Toggle
- **Latest Reading**: Shows the most recent reading per meter (DISTINCT ON)
- **Time Series**: Shows historical data with configurable time range

### 2. Time Range Filter (Time Series mode only)
- Configurable lookback period in hours (1-168 hours, default 24)
- Limits results to 1000 rows for performance

### 3. Meter Selection
- Multi-select checkboxes for filtering specific meters
- Leave empty to show all meters
- Currently available meters:
  - SnakeSideTower (192.168.112.71)
  - 20_WAY_UPS_DB_2 (.91)
  - 20WAY_UPS_LIGHTING_DB_3 (.91)
  - 24_WAY_UPS_DB_1 (.91)
  - 6WAY_7_SEG_PDB_1 (.91)
  - EB_INCOMER (.91)

### 4. Column Selection (Grouped)
Columns are organized into 6 logical groups:

#### Basic Info
- ID, Meter Name, Device ID, Time, Model

#### Voltage Phases
- Average (vln_average)
- V_R (v_r_ph)
- V_Y (v_y_ph)
- V_B (v_b_ph)

#### Current Phases
- Average (a_average)
- I_R (a_r_ph)
- I_Y (a_y_ph)
- I_B (a_b_ph)

#### Power
- Total (watts_total)
- R Phase (watts_r_ph)
- Y Phase (watts_y_ph)
- B Phase (watts_b_ph)

#### Power Factor
- Average (pf_ave)
- R Phase (pf_r_ph)
- Y Phase (pf_y_ph)
- B Phase (pf_b_ph)

#### Other
- Frequency
- Wh Received
- Location
- Pi Name
- Pi IP

### 5. Column Toggle (JavaScript)
- Click checkboxes to show/hide columns dynamically
- No page reload required
- Persists for current session only

### 6. Search Box
- Real-time text search across all visible table data
- Case-insensitive
- Updates record count dynamically

### 7. Excel Export
- **Filename format**: `meter_readings_{view_mode}_{timestamp}.xlsx`
- **Styling**: Orange headers with white text, auto-sized columns
- **Filters applied**: Exports only visible meters and time range
- **Column filtering**: Exports only selected columns (from checkboxes)
- **Requirements**: openpyxl library (already installed)

### 8. Modern UI
- Orange/white color scheme matching SMP branding
- Responsive design (works on tablets, laptops)
- Sticky table headers
- Row hover effects
- Gradient header
- Clean filter panel with rounded corners

## Backend Changes

### views.py
- Enhanced `latest_readings()` with filtering parameters:
  - `view_mode` (GET): 'latest' | 'timeseries'
  - `meters` (GET list): selected meter names
  - `hours` (GET): lookback hours for timeseries
- Added `export_excel()` function:
  - Queries filtered data
  - Builds Excel workbook with openpyxl
  - Applies column filters from `columns` GET parameter
  - Returns BytesIO download

### urls.py
- Added route: `/meter_readings/export/excel/`

### templatetags/meter_filters.py (NEW)
- Custom Django template filters:
  - `get_item`: Get list item by index (for data-col attributes)
  - `zip_lists`: Zip two lists (currently unused, available for future use)

## Usage Examples

### Filter to specific meters in time series mode
1. Click "Time Series" button
2. Set hours to 48
3. Check only "SnakeSideTower" and "EB_INCOMER"
4. Click "Apply Filters"

### Export voltage phases only
1. Uncheck all columns except: Meter Name, Time, Voltage Phases group
2. Click "Download Excel"
3. Excel will contain only selected columns

### Search for specific meter
1. Type meter name in search box (e.g., "Snake")
2. Table filters immediately to matching rows

## Performance Notes
- Latest mode: Fast (1 row per meter with DISTINCT ON)
- Time series mode: Limited to 1000 rows
- Excel export: Same performance as table view
- Search: Client-side (no server query)

## Future Enhancements (Optional)
- Save column preferences to browser localStorage
- Add date range picker (instead of hours)
- Export to CSV option
- Sortable columns (click header to sort)
- Row highlighting for out-of-range values
- Chart view toggle (Plotly or Chart.js)
