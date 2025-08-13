#!/usr/bin/env python3
"""
CSV Formatter and Analyzer for Meter Dashboard Data

This script provides tools to:
1. Format existing CSV files for better readability
2. Analyze and summarize meter data
3. Create reports from CSV data
4. Convert old format CSV to new improved format

Usage:
    python csv_formatter.py --format <csv_file>     # Format a single CSV file
    python csv_formatter.py --format-all            # Format all CSV files in csv_data/
    python csv_formatter.py --analyze <csv_file>    # Analyze data in CSV file
    python csv_formatter.py --summary <csv_file>    # Generate data summary
    python csv_formatter.py --view <csv_file>       # View formatted data (last 20 rows)
"""

import csv
import sys
import os
from pathlib import Path
import argparse
from datetime import datetime
import pandas as pd

def format_value_for_display(value, param_name):
    """Format a value for display with appropriate precision and units."""
    if value in [0, "0", "0.0", 0.0, "0.00"]:
        return "0"
    
    try:
        # Handle special cases
        if param_name == "On Hours" or "Runtime" in param_name:
            return str(value)  # Keep time format as-is
        elif "PF" in param_name or "PowerFactor" in param_name:
            return f"{float(value):.3f}"
        elif "Watts" in param_name or "Power" in param_name:
            return f"{float(value):.1f} W"
        elif ("V " in param_name or "VLN" in param_name or "Voltage" in param_name) and "Harmonics" not in param_name:
            return f"{float(value):.1f} V"
        elif ("A " in param_name or "Current" in param_name) and "Harmonics" not in param_name:
            return f"{float(value):.2f} A"
        elif "Frequency" in param_name:
            return f"{float(value):.2f} Hz"
        elif "Wh" in param_name or "Energy" in param_name:
            return f"{float(value):.0f} Wh"
        elif "Hours" in param_name and "On" not in param_name:
            return f"{float(value):.1f} h"
        elif "interruption" in param_name or "Interruptions" in param_name:
            return f"{int(float(value))}"
        elif "Harmonics" in param_name:
            return f"{float(value):.1f}%"
        else:
            # Default formatting
            if float(value) == int(float(value)):
                return f"{int(float(value))}"
            else:
                return f"{float(value):.2f}"
    except:
        return str(value)

def create_readable_headers(headers):
    """Convert technical headers to more readable format."""
    readable = []
    for header in headers:
        if header == "Time":
            readable.append("Timestamp")
        elif "Watts Total" in header:
            readable.append("Total Power")
        elif "Watts R Ph" in header:
            readable.append("R-Phase Power")
        elif "Watts Y Ph" in header:
            readable.append("Y-Phase Power")
        elif "Watts B Ph" in header:
            readable.append("B-Phase Power")
        elif "PF Ave" in header:
            readable.append("Avg Power Factor")
        elif "PF R Ph" in header:
            readable.append("R-Phase PF")
        elif "PF Y Ph" in header:
            readable.append("Y-Phase PF")
        elif "PF B Ph" in header:
            readable.append("B-Phase PF")
        elif "VLN average" in header:
            readable.append("Avg Voltage")
        elif "V R Ph" in header:
            readable.append("R-Phase Voltage")
        elif "V Y Ph" in header:
            readable.append("Y-Phase Voltage")
        elif "V B Ph" in header:
            readable.append("B-Phase Voltage")
        elif "A average" in header:
            readable.append("Avg Current")
        elif "A R Ph" in header:
            readable.append("R-Phase Current")
        elif "A Y Ph" in header:
            readable.append("Y-Phase Current")
        elif "A B Ph" in header:
            readable.append("B-Phase Current")
        elif "Frequency" in header:
            readable.append("Frequency")
        elif "Wh received" in header:
            readable.append("Energy Received")
        elif "Load Hours Delivered" in header:
            readable.append("Load Hours")
        elif "No of interruption" in header:
            readable.append("Interruptions")
        elif "On Hours" in header:
            readable.append("Runtime")
        else:
            readable.append(header)
    
    return readable

def format_csv_file(input_file, output_file=None):
    """Format a CSV file for better readability."""
    try:
        if not os.path.exists(input_file):
            print(f"❌ File not found: {input_file}")
            return False
        
        # Read the CSV file
        with open(input_file, 'r') as f:
            reader = csv.reader(f)
            rows = list(reader)
        
        if len(rows) < 2:
            print(f"❌ CSV file has insufficient data: {input_file}")
            return False
        
        headers = rows[0]
        data_rows = rows[1:]
        
        # Create readable headers
        readable_headers = create_readable_headers(headers)
        
        # Determine output file
        if output_file is None:
            path = Path(input_file)
            output_file = path.parent / f"{path.stem}_formatted{path.suffix}"
        
        # Write formatted CSV
        with open(output_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(readable_headers)
            
            for row in data_rows:
                formatted_row = []
                for i, value in enumerate(row):
                    if i == 0:  # Timestamp
                        formatted_row.append(value)
                    else:
                        param_name = headers[i] if i < len(headers) else "Unknown"
                        formatted_value = format_value_for_display(value, param_name)
                        formatted_row.append(formatted_value)
                writer.writerow(formatted_row)
        
        print(f"✅ Formatted CSV saved to: {output_file}")
        return True
        
    except Exception as e:
        print(f"❌ Error formatting CSV file: {e}")
        return False

def analyze_csv_file(csv_file):
    """Analyze CSV data and provide insights."""
    try:
        df = pd.read_csv(csv_file)
        
        print(f"📊 Analysis of {csv_file}")
        print("=" * 60)
        print(f"📅 Time Range: {df.iloc[0, 0]} to {df.iloc[-1, 0]}")
        print(f"📈 Total Records: {len(df)}")
        print(f"🕐 Duration: ~{len(df) * 5 / 60:.1f} minutes (assuming 5s intervals)")
        
        # Find non-zero columns
        numeric_cols = df.select_dtypes(include=['float64', 'int64']).columns
        active_data = {}
        
        for col in numeric_cols:
            non_zero_values = df[col][df[col] != 0]
            if len(non_zero_values) > 0:
                active_data[col] = {
                    'min': non_zero_values.min(),
                    'max': non_zero_values.max(),  
                    'avg': non_zero_values.mean(),
                    'count': len(non_zero_values)
                }
        
        if active_data:
            print("\n🔍 Active Parameters (non-zero values):")
            print("-" * 50)
            for param, stats in active_data.items():
                print(f"{param:20} | Min: {stats['min']:8.2f} | Max: {stats['max']:8.2f} | Avg: {stats['avg']:8.2f} | Count: {stats['count']}")
        else:
            print("\n⚠️  No active data found (all values are zero)")
        
        return True
        
    except Exception as e:
        print(f"❌ Error analyzing CSV file: {e}")
        return False

def view_csv_file(csv_file, num_rows=20):
    """Display the last N rows of CSV file in a formatted way."""
    try:
        df = pd.read_csv(csv_file)
        
        print(f"📋 Last {num_rows} rows of {csv_file}")
        print("=" * 100)
        
        # Show last N rows
        recent_data = df.tail(num_rows)
        
        # Print in a more readable format
        for index, row in recent_data.iterrows():
            print(f"\n⏰ {row.iloc[0]}")  # Timestamp
            print("-" * 40)
            
            # Group related parameters
            power_params = [col for col in df.columns if 'Watts' in col or 'Power' in col]
            voltage_params = [col for col in df.columns if 'V ' in col or 'Voltage' in col]
            current_params = [col for col in df.columns if 'A ' in col or 'Current' in col]
            
            if power_params:
                print("🔌 Power:")
                for param in power_params:
                    if param in row and row[param] != 0:
                        print(f"   {param}: {row[param]}")
            
            if voltage_params:
                print("⚡ Voltage:")
                for param in voltage_params:
                    if param in row and row[param] != 0:
                        print(f"   {param}: {row[param]}")
            
            if current_params:
                print("🔋 Current:")
                for param in current_params:
                    if param in row and row[param] != 0:
                        print(f"   {param}: {row[param]}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error viewing CSV file: {e}")
        return False

def format_all_csv_files():
    """Format all CSV files in the csv_data directory."""
    csv_dir = Path("csv_data")
    if not csv_dir.exists():
        print("❌ csv_data directory not found")
        return False
    
    csv_files = list(csv_dir.glob("*.csv"))
    if not csv_files:
        print("❌ No CSV files found in csv_data directory")
        return False
    
    print(f"🔄 Found {len(csv_files)} CSV files to format...")
    
    success_count = 0
    for csv_file in csv_files:
        if "_formatted" not in csv_file.stem:  # Skip already formatted files
            print(f"\n📄 Processing: {csv_file.name}")
            if format_csv_file(str(csv_file)):
                success_count += 1
    
    print(f"\n✅ Successfully formatted {success_count}/{len(csv_files)} files")
    return True

def main():
    parser = argparse.ArgumentParser(description="CSV Formatter and Analyzer for Meter Data")
    parser.add_argument("--format", help="Format a specific CSV file")
    parser.add_argument("--format-all", action="store_true", help="Format all CSV files in csv_data/")
    parser.add_argument("--analyze", help="Analyze a CSV file")
    parser.add_argument("--summary", help="Generate summary of CSV file")
    parser.add_argument("--view", help="View last 20 rows of CSV file")
    parser.add_argument("--rows", type=int, default=20, help="Number of rows to view (default: 20)")
    
    args = parser.parse_args()
    
    if args.format:
        format_csv_file(args.format)
    elif args.format_all:
        format_all_csv_files()
    elif args.analyze:
        analyze_csv_file(args.analyze)
    elif args.summary:
        analyze_csv_file(args.summary)  # Same as analyze for now
    elif args.view:
        view_csv_file(args.view, args.rows)
    else:
        print("CSV Formatter and Analyzer")
        print("=" * 30)
        print("Available commands:")
        print("  --format <file>     Format a CSV file")
        print("  --format-all        Format all CSV files")
        print("  --analyze <file>    Analyze CSV data")
        print("  --view <file>       View recent data")
        print("")
        print("Example:")
        print("  python csv_formatter.py --view csv_data/MainPanel_20250725.csv")

if __name__ == "__main__":
    main()
