#!/usr/bin/env python3
"""
CSV Data Viewer - Interactive table viewer for meter CSV data

This utility provides a clean, formatted view of CSV meter data with:
- Grouped parameters by type (Power, Voltage, Current, etc.)
- Color coding for different value ranges
- Summary statistics
- Filtering options
- Real-time data monitoring

Usage:
    python csv_viewer.py filename.csv
    python csv_viewer.py --live csv_data/  # Monitor directory for new data
    python csv_viewer.py --summary csv_data/  # Summary of all files

Author: CSV Viewer Utility
Date: 25/07/25
"""

import csv
import os
import sys
import time
from datetime import datetime
from pathlib import Path

# Try to import optional dependencies
try:
    from termcolor import colored
    COLORS_AVAILABLE = True
except ImportError:
    COLORS_AVAILABLE = False
    def colored(text, color=None):
        return text

class CSVViewer:
    """
    Interactive CSV viewer with formatting and analysis capabilities.
    """
    
    def __init__(self):
        self.parameter_groups = {
            'Power (W)': ['Watts Total', 'Watts R Ph', 'Watts Y Ph', 'Watts B Ph'],
            'Power Factor': ['PF Ave', 'PF R Ph', 'PF Y Ph', 'PF B Ph'],
            'Voltage (V)': ['VLN average', 'V R Ph', 'V Y Ph', 'V B Ph'],
            'Current (A)': ['A average', 'A R Ph', 'A Y Ph', 'A B Ph'],
            'System': ['Frequency', 'On Hours', 'No of interruption'],
            'Energy': ['Wh received', 'Load Hours Delivered'],
            'Harmonics (%)': ['V R Harmonics', 'V Y Harmonics', 'V B Harmonics', 
                             'A R Harmonics', 'A Y Harmonics', 'A B Harmonics']
        }
        
        self.value_ranges = {
            'Power': {'good': (0, 5000), 'warning': (5000, 10000), 'critical': (10000, float('inf'))},
            'Voltage': {'good': (220, 250), 'warning': (200, 220), 'critical': (0, 200)},
            'Current': {'good': (0, 10), 'warning': (10, 20), 'critical': (20, float('inf'))},
            'Frequency': {'good': (49.5, 50.5), 'warning': (48, 49.5), 'critical': (0, 48)},
        }

    def read_csv_file(self, filepath):
        """Read CSV file with basic error handling."""
        try:
            with open(filepath, 'r', newline='', encoding='utf-8') as f:
                # Skip comment lines
                lines = []
                for line in f:
                    if not line.startswith('#'):
                        lines.append(line)
                
                reader = csv.reader(lines)
                data = list(reader)
                
            if not data:
                return None, None
                
            return data[0], data[1:]
            
        except Exception as e:
            print(f"❌ Error reading {filepath}: {e}")
            return None, None

    def format_value(self, value, param_name, use_colors=True):
        """Format value with appropriate colors and units."""
        try:
            val = float(value)
        except (ValueError, TypeError):
            return str(value)
        
        # Handle special cases
        if val == -1:
            return colored("NO_DATA", "red") if use_colors else "NO_DATA"
        elif val == 0:
            return colored("0", "blue") if use_colors else "0"
        
        # Format based on parameter type
        if "Watts" in param_name:
            formatted = f"{val:.1f}W"
            if use_colors:
                if val < 100:
                    formatted = colored(formatted, "green")
                elif val < 1000:
                    formatted = colored(formatted, "yellow")
                else:
                    formatted = colored(formatted, "red")
        elif "PF" in param_name:
            formatted = f"{val:.3f}"
            if use_colors:
                if val > 0.9:
                    formatted = colored(formatted, "green")
                elif val > 0.7:
                    formatted = colored(formatted, "yellow")
                else:
                    formatted = colored(formatted, "red")
        elif "V " in param_name or "VLN" in param_name:
            formatted = f"{val:.1f}V"
            if use_colors:
                if 220 <= val <= 250:
                    formatted = colored(formatted, "green")
                elif 200 <= val < 220:
                    formatted = colored(formatted, "yellow")
                else:
                    formatted = colored(formatted, "red")
        elif "A " in param_name:
            formatted = f"{val:.2f}A"
            if use_colors:
                if val < 10:
                    formatted = colored(formatted, "green")
                elif val < 20:
                    formatted = colored(formatted, "yellow")
                else:
                    formatted = colored(formatted, "red")
        elif "Frequency" in param_name:
            formatted = f"{val:.2f}Hz"
            if use_colors:
                if 49.5 <= val <= 50.5:
                    formatted = colored(formatted, "green")
                elif 48 <= val < 49.5:
                    formatted = colored(formatted, "yellow")
                else:
                    formatted = colored(formatted, "red")
        elif "Harmonics" in param_name:
            formatted = f"{val:.1f}%"
            if use_colors:
                if val < 3:
                    formatted = colored(formatted, "green")
                elif val < 5:
                    formatted = colored(formatted, "yellow")
                else:
                    formatted = colored(formatted, "red")
        elif "interruption" in param_name:
            formatted = f"{int(val)}"
            if use_colors:
                if val == 0:
                    formatted = colored(formatted, "green")
                else:
                    formatted = colored(formatted, "red")
        else:
            formatted = f"{val:.2f}"
        
        return formatted

    def display_latest_readings(self, filepath, num_readings=5):
        """Display the latest readings in a formatted table."""
        header, rows = self.read_csv_file(filepath)
        if not header or not rows:
            print(f"❌ Unable to read data from {filepath}")
            return
        
        print(f"\n📊 Latest {num_readings} readings from: {os.path.basename(filepath)}")
        print("=" * 100)
        
        # Get latest readings
        latest_rows = rows[-num_readings:] if len(rows) >= num_readings else rows
        
        # Display by parameter groups
        for group_name, params in self.parameter_groups.items():
            relevant_params = [p for p in params if p in header]
            if not relevant_params:
                continue
                
            print(f"\n{colored(group_name, 'cyan', attrs=['bold'])}")
            print("-" * len(group_name))
            
            # Create table header
            table_header = ["Time"] + relevant_params
            print(f"{'Time':<20}", end="")
            for param in relevant_params:
                print(f"{param:<15}", end="")
            print()
            
            # Print data rows
            for row in latest_rows:
                if len(row) <= len(header):
                    continue
                    
                # Extract time
                timestamp = row[0][-8:] if len(row[0]) > 8 else row[0]  # Show only time part
                print(f"{timestamp:<20}", end="")
                
                # Print parameter values
                for param in relevant_params:
                    if param in header:
                        idx = header.index(param)
                        if idx < len(row):
                            formatted_val = self.format_value(row[idx], param)
                            print(f"{formatted_val:<15}", end="")
                        else:
                            print(f"{'N/A':<15}", end="")
                print()

    def display_summary_stats(self, filepath):
        """Display summary statistics for the CSV file."""
        header, rows = self.read_csv_file(filepath)
        if not header or not rows:
            return
            
        print(f"\n📈 Summary Statistics: {os.path.basename(filepath)}")
        print("=" * 80)
        
        # Basic info
        print(f"📁 Total Records: {len(rows)}")
        if rows:
            print(f"🕐 Time Range: {rows[0][0]} to {rows[-1][0]}")
        
        # Calculate stats for key parameters
        key_params = ['Watts Total', 'VLN average', 'A average', 'Frequency', 'PF Ave']
        
        for param in key_params:
            if param not in header:
                continue
                
            idx = header.index(param)
            values = []
            
            for row in rows:
                if idx < len(row):
                    try:
                        val = float(row[idx])
                        if val > -1:  # Exclude error values
                            values.append(val)
                    except:
                        continue
            
            if values:
                print(f"\n{param}:")
                print(f"  Min: {self.format_value(min(values), param, False)}")
                print(f"  Max: {self.format_value(max(values), param, False)}")
                print(f"  Avg: {self.format_value(sum(values)/len(values), param, False)}")
                print(f"  Valid readings: {len(values)}/{len(rows)} ({len(values)/len(rows)*100:.1f}%)")

    def monitor_directory(self, directory, refresh_seconds=30):
        """Monitor a directory for new CSV data and display updates."""
        directory = Path(directory)
        if not directory.exists():
            print(f"❌ Directory not found: {directory}")
            return
            
        print(f"👁️ Monitoring {directory} for CSV updates (refresh every {refresh_seconds}s)")
        print("Press Ctrl+C to stop")
        print("=" * 80)
        
        last_update = {}
        
        try:
            while True:
                csv_files = list(directory.glob("*.csv"))
                updated_files = []
                
                for csv_file in csv_files:
                    # Skip formatted files
                    if "formatted" in csv_file.name:
                        continue
                        
                    mtime = csv_file.stat().st_mtime
                    if csv_file not in last_update or mtime > last_update[csv_file]:
                        last_update[csv_file] = mtime
                        updated_files.append(csv_file)
                
                if updated_files:
                    os.system('clear' if os.name == 'posix' else 'cls')
                    print(f"🔄 Updates detected at {datetime.now().strftime('%H:%M:%S')}")
                    
                    for csv_file in updated_files:
                        self.display_latest_readings(csv_file, 3)
                
                time.sleep(refresh_seconds)
                
        except KeyboardInterrupt:
            print("\n👋 Monitoring stopped")

    def compare_files(self, file1, file2):
        """Compare latest readings from two CSV files."""
        print(f"🔍 Comparing {os.path.basename(file1)} vs {os.path.basename(file2)}")
        print("=" * 80)
        
        header1, rows1 = self.read_csv_file(file1)
        header2, rows2 = self.read_csv_file(file2)
        
        if not all([header1, rows1, header2, rows2]):
            print("❌ Error reading one or both files")
            return
        
        # Get latest readings
        latest1 = rows1[-1] if rows1 else []
        latest2 = rows2[-1] if rows2 else []
        
        print(f"File 1 latest: {latest1[0] if latest1 else 'N/A'}")
        print(f"File 2 latest: {latest2[0] if latest2 else 'N/A'}")
        print()
        
        # Compare key parameters
        key_params = ['Watts Total', 'VLN average', 'A average', 'Frequency']
        
        for param in key_params:
            if param in header1 and param in header2:
                idx1 = header1.index(param)
                idx2 = header2.index(param)
                
                val1 = latest1[idx1] if idx1 < len(latest1) else "N/A"
                val2 = latest2[idx2] if idx2 < len(latest2) else "N/A"
                
                print(f"{param:20}: {self.format_value(val1, param)} vs {self.format_value(val2, param)}")


def main():
    """Main CLI interface."""
    if len(sys.argv) < 2:
        print("CSV Data Viewer")
        print("=" * 50)
        print("Usage:")
        print("  python csv_viewer.py file.csv              # View latest readings")
        print("  python csv_viewer.py --summary file.csv    # Show statistics")
        print("  python csv_viewer.py --live directory/     # Monitor for updates")
        print("  python csv_viewer.py --compare f1.csv f2.csv  # Compare files")
        print()
        print("Examples:")
        print("  python csv_viewer.py csv_data/SP3UPS_20250725.csv")
        print("  python csv_viewer.py --live csv_data/")
        print("  python csv_viewer.py --summary csv_data/SP3UPS_20250725.csv")
        return
    
    viewer = CSVViewer()
    
    if sys.argv[1] == "--live" and len(sys.argv) > 2:
        viewer.monitor_directory(sys.argv[2])
    elif sys.argv[1] == "--summary" and len(sys.argv) > 2:
        viewer.display_summary_stats(sys.argv[2])
    elif sys.argv[1] == "--compare" and len(sys.argv) > 3:
        viewer.compare_files(sys.argv[2], sys.argv[3])
    else:
        # Default: show latest readings
        filepath = sys.argv[1]
        viewer.display_latest_readings(filepath, 10)
        viewer.display_summary_stats(filepath)


if __name__ == "__main__":
    main()
