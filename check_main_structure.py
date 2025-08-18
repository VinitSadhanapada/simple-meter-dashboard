#!/usr/bin/env python3
"""
Quick check of main script structure and fix common issues
"""


def check_main_script_structure():
    """Check for structural issues in the main script"""

    script_path = '/home/isha/deepak/MFM_offline_setup/offline_rpi_dashboard_db.py'

    try:
        with open(script_path, 'r') as f:
            content = f.read()

        lines = content.split('\n')

        print("🔍 Checking main script structure...")

        # Check for duplicate "Starting dashboard DB version..."
        dashboard_starts = [i for i, line in enumerate(
            lines) if "Starting dashboard DB version" in line]
        if len(dashboard_starts) > 1:
            print(
                f"⚠️  Found {len(dashboard_starts)} duplicate 'Starting dashboard DB version' lines at lines: {dashboard_starts}")

        # Check for function structure
        function_starts = []
        for i, line in enumerate(lines):
            if line.strip().startswith('def '):
                function_starts.append((i+1, line.strip()))

        print(f"📋 Found {len(function_starts)} functions:")
        for line_num, func_line in function_starts:
            print(f"  Line {line_num}: {func_line}")

        # Check for main loop
        main_loop_found = False
        for i, line in enumerate(lines):
            if "while True:" in line:
                main_loop_found = True
                print(f"✅ Main loop found at line {i+1}")
                break

        if not main_loop_found:
            print("❌ No main loop found - this could be why data isn't being generated!")

        # Check run_dashboard function structure
        run_dashboard_start = None
        for i, line in enumerate(lines):
            if line.strip().startswith('def run_dashboard'):
                run_dashboard_start = i
                break

        if run_dashboard_start:
            print(
                f"✅ run_dashboard function found at line {run_dashboard_start + 1}")

            # Check if there's unreachable code after the function
            indented_lines = 0
            for i in range(run_dashboard_start + 1, len(lines)):
                if lines[i].strip() == '':
                    continue
                if lines[i].startswith('    ') or lines[i].startswith('\t'):
                    indented_lines += 1
                else:
                    # Found non-indented line - this should be end of function
                    remaining_code = len(
                        [l for l in lines[i:] if l.strip() and not l.strip().startswith('#')])
                    if remaining_code > 0:
                        print(
                            f"⚠️  Found {remaining_code} lines of code after run_dashboard function")
                        print(f"   This code might not be executed!")
                    break

        return True

    except Exception as e:
        print(f"❌ Error checking script structure: {e}")
        return False


if __name__ == "__main__":
    check_main_script_structure()
