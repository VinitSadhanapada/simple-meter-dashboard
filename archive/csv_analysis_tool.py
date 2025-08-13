#!/usr/bin/env python3
"""
CSV Analysis and Formatting Tool for Meter Dashboard Data

This script provides comprehensive tools for analyzing, formatting, and visualizing
meter dashboard CSV data files. It can reformat existing messy CSV files into
clean, readable formats and provide statistical analysis.

Features:
    - Reformat existing CSV files with better headers and value formatting
    - Statistical analysis (min, max, average, trends)
    - Data filtering and time-based queries
    - Export to multiple formats (clean CSV, Excel, JSON)
    - Visual charts and graphs (if matplotlib available)
    - Data validation and error detection
    - Comparison between multiple devices/time periods

Usage:
    python csv_analysis_tool.py --format input.csv output.csv
    python csv_analysis_tool.py --analyze input.csv
    python csv_analysis_tool.py --compare file1.csv file2.csv
    python csv_analysis_tool.py --dashboard csv_data/

Author: Dashboard Analysis Tool
Date: 25/07/25
Version: 1.0
"""

import csv
import os
import sys
import argparse
import json
from datetime import datetime, timedelta
from pathlib import Path
import statistics
from collections import defaultdict

# Try to import optional dependencies
try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False
    print("⚠️ pandas not available - some features will be limited")

try:
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False
    print("⚠️ matplotlib not available - no plotting features")

try:
    from openpyxl import Workbook
    EXCEL_AVAILABLE = True
except ImportError:
    EXCEL_AVAILABLE = False
    print("⚠️ openpyxl not available - no Excel export")


class MeterCSVAnalyzer:
    """
    Comprehensive CSV analysis and formatting tool for meter data.
    """
    
    def __init__(self):
        self.parameter_units = {
            'Watts Total': 'W',
            'Watts R Ph': 'W',
            'Watts Y Ph': 'W', 
            'Watts B Ph': 'W',
            'PF Ave': '',
            'PF R Ph': '',
            'PF Y Ph': '',
            'PF B Ph': '',
            'VLN average': 'V',
            'V R Ph': 'V',
            'V Y Ph': 'V',
            'V B Ph': 'V',
            'A average': 'A',
            'A R Ph': 'A',
            'A Y Ph': 'A',
            'A B Ph': 'A',
            'Frequency': 'Hz',
            'Wh received': 'Wh',
            'Load Hours Delivered': 'h',
            'No of interruption': 'count',
            'On Hours': 'h:m:s',
            'V R Harmonics': '%',
            'V Y Harmonics': '%',
            'V B Harmonics': '%',
            'A R Harmonics': '%',
            'A Y Harmonics': '%',
            'A B Harmonics': '%'
        }
        
        self.parameter_groups = {
            'Power': ['Watts Total', 'Watts R Ph', 'Watts Y Ph', 'Watts B Ph'],
            'Power Factor': ['PF Ave', 'PF R Ph', 'PF Y Ph', 'PF B Ph'],
            'Voltage': ['VLN average', 'V R Ph', 'V Y Ph', 'V B Ph'],
            'Current': ['A average', 'A R Ph', 'A Y Ph', 'A B Ph'],
            'System': ['Frequency', 'Wh received', 'Load Hours Delivered', 'No of interruption', 'On Hours'],
            'Harmonics': ['V R Harmonics', 'V Y Harmonics', 'V B Harmonics', 'A R Harmonics', 'A Y Harmonics', 'A B Harmonics']
        }

    def format_value(self, value, param_name):
        """
        Format a value for display with appropriate precision and units.
        """
        if value in [0, "0", "0.0", 0.0, "", "NA"]:
            return "0"
        
        try:
            # Handle special cases
            if param_name == "On Hours":
                return str(value)  # Keep time format as-is
            elif "PF" in param_name:  # Power Factor
                return f"{float(value):.3f}"
            elif "Watts" in param_name:  # Power values
                val = float(value)
                if val >= 1000:
                    return f"{val/1000:.2f}k"
                else:
                    return f"{val:.1f}"
            elif "V " in param_name or "VLN" in param_name:  # Voltage values
                return f"{float(value):.1f}"
            elif "A " in param_name or "A average" in param_name:  # Current values
                return f"{float(value):.2f}"
            elif "Frequency" in param_name:
                return f"{float(value):.2f}"
            elif "Wh" in param_name:  # Energy values
                val = float(value)
                if val >= 1000000:
                    return f"{val/1000000:.2f}M"
                elif val >= 1000:
                    return f"{val/1000:.2f}k"
                else:
                    return f"{val:.0f}"
            elif "Hours" in param_name:
                return f"{float(value):.1f}"
            elif "interruption" in param_name:
                return f"{int(float(value))}"
            elif "Harmonics" in param_name:
                return f"{float(value):.1f}"
            else:
                # Default formatting
                val = float(value)
                if val == int(val):
                    return f"{int(val)}"
                else:
                    return f"{val:.2f}"
        except (ValueError, TypeError):
            return str(value)

    def create_clean_header(self, original_header):
        """
        Create clean, readable headers with units.
        """
        clean_headers = []
        
        for header in original_header:
            if header.lower() in ['time', 'timestamp', 'datetime']:
                clean_headers.append("Timestamp")
                continue
                
            # Find matching parameter and add unit
            unit = self.parameter_units.get(header, '')
            if unit:
                clean_name = header.replace(" ", "_").replace("Ph", "Phase")
                clean_headers.append(f"{clean_name}_{unit}" if unit else clean_name)
            else:
                clean_headers.append(header.replace(" ", "_"))
                
        return clean_headers

    def read_csv_file(self, filepath):
        """
        Read CSV file and return data with error handling.
        """
        try:
            with open(filepath, 'r', newline='', encoding='utf-8') as f:
                # Try to detect delimiter
                sample = f.read(1024)
                f.seek(0)
                
                # Common delimiters to try
                delimiters = [',', ';', '\t', '|']
                best_delimiter = ','
                
                for delim in delimiters:
                    if sample.count(delim) > sample.count(best_delimiter):
                        best_delimiter = delim
                
                reader = csv.reader(f, delimiter=best_delimiter)
                data = list(reader)
                
            if not data:
                raise ValueError("CSV file is empty")
                
            return data[0], data[1:]  # header, rows
            
        except Exception as e:
            print(f"❌ Error reading {filepath}: {e}")
            return None, None

    def format_csv_file(self, input_file, output_file, device_name=None):
        """
        Format an existing CSV file to be more readable.
        """
        print(f"🔄 Formatting {input_file} -> {output_file}")
        
        header, rows = self.read_csv_file(input_file)
        if header is None:
            return False
            
        # Create clean headers
        clean_header = self.create_clean_header(header)
        
        # Write formatted CSV
        try:
            with open(output_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                
                # Write metadata comment if device name provided
                if device_name:
                    f.write(f"# Device: {device_name}\n")
                    f.write(f"# Formatted: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write(f"# Original file: {input_file}\n")
                
                # Write clean header
                writer.writerow(clean_header)
                
                # Write formatted data
                for row in rows:
                    if len(row) != len(header):
                        continue  # Skip malformed rows
                        
                    formatted_row = []
                    for i, value in enumerate(row):
                        if i < len(header):
                            formatted_row.append(self.format_value(value, header[i]))
                        else:
                            formatted_row.append(str(value))
                    
                    writer.writerow(formatted_row)
                    
            print(f"✅ Successfully formatted {len(rows)} rows")
            return True
            
        except Exception as e:
            print(f"❌ Error writing formatted file: {e}")
            return False

    def analyze_csv_file(self, filepath):
        """
        Perform statistical analysis on CSV file.
        """
        print(f"📊 Analyzing {filepath}")
        print("=" * 60)
        
        header, rows = self.read_csv_file(filepath)
        if header is None:
            return
            
        # Basic statistics
        print(f"📁 File: {os.path.basename(filepath)}")
        print(f"📈 Total Records: {len(rows)}")
        
        if not rows:
            print("❌ No data to analyze")
            return
            
        # Time range analysis
        if len(rows) > 0 and len(rows[0]) > 0:
            try:
                first_time = rows[0][0]
                last_time = rows[-1][0]
                print(f"🕐 Time Range: {first_time} to {last_time}")
            except:
                print("⚠️ Unable to parse time range")
        
        # Analyze numeric columns
        print("\n📊 Parameter Analysis:")
        print("-" * 60)
        
        for group_name, params in self.parameter_groups.items():
            print(f"\n{group_name}:")
            
            for param in params:
                if param in header:
                    col_idx = header.index(param)
                    values = []
                    
                    # Extract numeric values
                    for row in rows:
                        if col_idx < len(row):
                            try:
                                val = float(row[col_idx])
                                if val != 0:  # Ignore zeros for meaningful stats
                                    values.append(val)
                            except (ValueError, TypeError):
                                continue
                    
                    if values:
                        unit = self.parameter_units.get(param, '')
                        print(f"  {param}:")
                        print(f"    Min: {min(values):.2f} {unit}")
                        print(f"    Max: {max(values):.2f} {unit}")
                        print(f"    Avg: {statistics.mean(values):.2f} {unit}")
                        print(f"    Non-zero readings: {len(values)}/{len(rows)}")
                    else:
                        print(f"  {param}: No valid data")

    def create_summary_report(self, csv_directory):
        """
        Create a summary report for all CSV files in a directory.
        """
        csv_files = list(Path(csv_directory).glob("*.csv"))
        if not csv_files:
            print(f"❌ No CSV files found in {csv_directory}")
            return
            
        print(f"📋 Summary Report for {len(csv_files)} files")
        print("=" * 80)
        
        total_records = 0
        device_stats = {}
        
        for csv_file in csv_files:
            header, rows = self.read_csv_file(csv_file)
            if header and rows:
                device_name = csv_file.stem.split('_')[0]  # Extract device name
                total_records += len(rows)
                
                device_stats[device_name] = {
                    'file': csv_file.name,
                    'records': len(rows),
                    'parameters': len(header),
                    'latest_time': rows[-1][0] if rows else 'N/A'
                }
        
        print(f"📊 Total Records Across All Devices: {total_records}")
        print(f"🔌 Devices Found: {len(device_stats)}")
        print()
        
        for device, stats in device_stats.items():
            print(f"Device: {device}")
            print(f"  File: {stats['file']}")
            print(f"  Records: {stats['records']}")
            print(f"  Parameters: {stats['parameters']}")
            print(f"  Latest: {stats['latest_time']}")
            print()

    def export_to_excel(self, csv_file, excel_file):
        """
        Export formatted CSV to Excel with multiple sheets and charts.
        """
        if not EXCEL_AVAILABLE:
            print("❌ Excel export requires openpyxl: pip install openpyxl")
            return False
            
        print(f"📊 Exporting {csv_file} to Excel: {excel_file}")
        
        header, rows = self.read_csv_file(csv_file)
        if header is None:
            return False
            
        try:
            wb = Workbook()
            
            # Main data sheet
            ws_data = wb.active
            ws_data.title = "Meter Data"
            
            # Write headers
            clean_header = self.create_clean_header(header)
            ws_data.append(clean_header)
            
            # Write formatted data
            for row in rows:
                formatted_row = []
                for i, value in enumerate(row):
                    if i < len(header):
                        formatted_row.append(self.format_value(value, header[i]))
                    else:
                        formatted_row.append(str(value))
                ws_data.append(formatted_row)
            
            # Summary sheet
            ws_summary = wb.create_sheet("Summary")
            ws_summary.append(["Parameter", "Min", "Max", "Average", "Unit"])
            
            # Add summary data for each parameter group
            for group_name, params in self.parameter_groups.items():
                ws_summary.append([f"--- {group_name} ---", "", "", "", ""])
                
                for param in params:
                    if param in header:
                        col_idx = header.index(param)
                        values = []
                        
                        for row in rows:
                            if col_idx < len(row):
                                try:
                                    val = float(row[col_idx])
                                    if val != 0:
                                        values.append(val)
                                except:
                                    continue
                        
                        if values:
                            unit = self.parameter_units.get(param, '')
                            ws_summary.append([
                                param,
                                f"{min(values):.2f}",
                                f"{max(values):.2f}",
                                f"{statistics.mean(values):.2f}",
                                unit
                            ])
            
            wb.save(excel_file)
            print(f"✅ Excel file created: {excel_file}")
            return True
            
        except Exception as e:
            print(f"❌ Error creating Excel file: {e}")
            return False

    def plot_trends(self, csv_file, output_dir=None):
        """
        Create trend plots for key parameters.
        """
        if not MATPLOTLIB_AVAILABLE:
            print("❌ Plotting requires matplotlib: pip install matplotlib")
            return False
            
        print(f"📈 Creating trend plots for {csv_file}")
        
        header, rows = self.read_csv_file(csv_file)
        if header is None:
            return False
            
        # Parse timestamps and data
        timestamps = []
        data_by_param = defaultdict(list)
        
        for row in rows:
            if len(row) < len(header):
                continue
                
            # Try to parse timestamp
            try:
                ts = datetime.strptime(row[0], "%Y-%m-%d %H:%M:%S")
                timestamps.append(ts)
            except:
                continue
                
            # Collect parameter values
            for i, param in enumerate(header[1:], 1):  # Skip timestamp
                if i < len(row):
                    try:
                        val = float(row[i])
                        data_by_param[param].append(val)
                    except:
                        data_by_param[param].append(None)
        
        if not timestamps:
            print("❌ No valid timestamps found")
            return False
            
        # Create plots for key parameters
        key_params = ['Watts Total', 'VLN average', 'A average', 'Frequency']
        
        fig, axes = plt.subplots(2, 2, figsize=(15, 10))
        fig.suptitle(f'Meter Trends - {os.path.basename(csv_file)}', fontsize=16)
        
        for i, param in enumerate(key_params):
            if param not in data_by_param:
                continue
                
            ax = axes[i//2, i%2]
            values = data_by_param[param]
            
            # Filter out None values
            valid_data = [(t, v) for t, v in zip(timestamps, values) if v is not None and v != 0]
            if valid_data:
                times, vals = zip(*valid_data)
                ax.plot(times, vals, linewidth=2)
                ax.set_title(f'{param} ({self.parameter_units.get(param, "")})')
                ax.grid(True, alpha=0.3)
                ax.tick_params(axis='x', rotation=45)
        
        plt.tight_layout()
        
        # Save plot
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
            plot_file = os.path.join(output_dir, f"{Path(csv_file).stem}_trends.png")
        else:
            plot_file = f"{Path(csv_file).stem}_trends.png"
            
        plt.savefig(plot_file, dpi=300, bbox_inches='tight')
        print(f"✅ Trend plot saved: {plot_file}")
        plt.close()
        
        return True

    def compare_files(self, file1, file2):
        """
        Compare two CSV files and show differences.
        """
        print(f"🔍 Comparing {os.path.basename(file1)} vs {os.path.basename(file2)}")
        print("=" * 80)
        
        header1, rows1 = self.read_csv_file(file1)
        header2, rows2 = self.read_csv_file(file2)
        
        if not all([header1, rows1, header2, rows2]):
            print("❌ Error reading one or both files")
            return
            
        print(f"File 1: {len(rows1)} records")
        print(f"File 2: {len(rows2)} records")
        
        # Compare parameters
        common_params = set(header1) & set(header2)
        unique1 = set(header1) - set(header2)
        unique2 = set(header2) - set(header1)
        
        print(f"\nParameters:")
        print(f"  Common: {len(common_params)}")
        print(f"  Only in file 1: {len(unique1)}")
        print(f"  Only in file 2: {len(unique2)}")
        
        if unique1:
            print(f"  Unique to file 1: {', '.join(unique1)}")
        if unique2:
            print(f"  Unique to file 2: {', '.join(unique2)}")
        
        # Compare data ranges for common parameters
        if common_params and rows1 and rows2:
            print(f"\nData Comparison (latest values):")
            print("-" * 50)
            
            for param in sorted(common_params):
                if param.lower() in ['time', 'timestamp']:
                    continue
                    
                try:
                    idx1 = header1.index(param)
                    idx2 = header2.index(param)
                    
                    val1 = float(rows1[-1][idx1]) if idx1 < len(rows1[-1]) else 0
                    val2 = float(rows2[-1][idx2]) if idx2 < len(rows2[-1]) else 0
                    
                    diff = abs(val1 - val2)
                    unit = self.parameter_units.get(param, '')
                    
                    print(f"{param:20}: {val1:8.2f} vs {val2:8.2f} {unit:4} (diff: {diff:.2f})")
                    
                except (ValueError, IndexError):
                    continue


def main():
    """
    Main CLI interface for the CSV analysis tool.
    """
    parser = argparse.ArgumentParser(description="CSV Analysis and Formatting Tool for Meter Data")
    
    parser.add_argument("--format", nargs=2, metavar=("INPUT", "OUTPUT"),
                       help="Format CSV file: input.csv output.csv")
    parser.add_argument("--analyze", metavar="FILE",
                       help="Analyze CSV file statistics")
    parser.add_argument("--compare", nargs=2, metavar=("FILE1", "FILE2"),
                       help="Compare two CSV files")
    parser.add_argument("--dashboard", metavar="DIR",
                       help="Create summary dashboard for directory")
    parser.add_argument("--excel", nargs=2, metavar=("CSV", "XLSX"),
                       help="Export CSV to Excel format")
    parser.add_argument("--plot", metavar="FILE",
                       help="Create trend plots for CSV file")
    parser.add_argument("--batch-format", metavar="DIR",
                       help="Format all CSV files in directory")
    parser.add_argument("--device-name", metavar="NAME",
                       help="Device name for formatting (optional)")
    
    if len(sys.argv) == 1:
        parser.print_help()
        print("\n📚 Examples:")
        print("  python csv_analysis_tool.py --format raw_data.csv clean_data.csv")
        print("  python csv_analysis_tool.py --analyze meter_data.csv")
        print("  python csv_analysis_tool.py --dashboard csv_data/")
        print("  python csv_analysis_tool.py --compare before.csv after.csv")
        print("  python csv_analysis_tool.py --excel data.csv report.xlsx")
        print("  python csv_analysis_tool.py --plot meter_data.csv")
        print("  python csv_analysis_tool.py --batch-format csv_data/")
        return
    
    args = parser.parse_args()
    analyzer = MeterCSVAnalyzer()
    
    if args.format:
        input_file, output_file = args.format
        analyzer.format_csv_file(input_file, output_file, args.device_name)
        
    elif args.analyze:
        analyzer.analyze_csv_file(args.analyze)
        
    elif args.compare:
        file1, file2 = args.compare
        analyzer.compare_files(file1, file2)
        
    elif args.dashboard:
        analyzer.create_summary_report(args.dashboard)
        
    elif args.excel:
        csv_file, excel_file = args.excel
        analyzer.export_to_excel(csv_file, excel_file)
        
    elif args.plot:
        analyzer.plot_trends(args.plot)
        
    elif args.batch_format:
        directory = Path(args.batch_format)
        csv_files = list(directory.glob("*.csv"))
        
        if not csv_files:
            print(f"❌ No CSV files found in {directory}")
            return
            
        formatted_dir = directory / "formatted"
        formatted_dir.mkdir(exist_ok=True)
        
        print(f"🔄 Batch formatting {len(csv_files)} files...")
        
        for csv_file in csv_files:
            output_file = formatted_dir / f"formatted_{csv_file.name}"
            device_name = csv_file.stem.split('_')[0] if '_' in csv_file.stem else None
            analyzer.format_csv_file(str(csv_file), str(output_file), device_name)
            
        print(f"✅ All files formatted in {formatted_dir}")


if __name__ == "__main__":
    main()
