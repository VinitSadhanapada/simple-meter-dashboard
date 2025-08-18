#!/usr/bin/env python3
"""
Clean up duplicate functions in the main script
"""


def remove_duplicate_functions():
    """Remove duplicate function definitions from the main script"""

    script_path = '/home/isha/deepak/MFM_offline_setup/offline_rpi_dashboard_db.py'

    try:
        with open(script_path, 'r') as f:
            content = f.read()

        lines = content.split('\n')

        # Find all function definitions
        function_defs = {}
        for i, line in enumerate(lines):
            if line.strip().startswith('def '):
                func_name = line.strip().split('(')[0].replace('def ', '')
                if func_name in function_defs:
                    print(
                        f"⚠️  Found duplicate function: {func_name} at lines {function_defs[func_name] + 1} and {i + 1}")
                    function_defs[func_name + '_duplicate'] = i
                else:
                    function_defs[func_name] = i

        # Remove duplicate create_pi_setup_table_simple and other functions
        duplicates_to_remove = [
            'create_pi_setup_table_simple_duplicate',
            'register_pi_simple_duplicate',
            'insert_meter_reading_with_pi_simple_duplicate',
            'float_or_none_duplicate',
            'post_to_server_duplicate'
        ]

        lines_to_remove = []
        for dup in duplicates_to_remove:
            if dup in function_defs:
                start_line = function_defs[dup]
                # Find end of function
                end_line = start_line + 1
                for i in range(start_line + 1, len(lines)):
                    if lines[i].strip() and not (lines[i].startswith('    ') or lines[i].startswith('\t')):
                        end_line = i
                        break

                lines_to_remove.extend(range(start_line, end_line))
                print(
                    f"📋 Will remove duplicate {dup.replace('_duplicate', '')} from lines {start_line + 1} to {end_line}")

        # Remove the duplicate lines
        if lines_to_remove:
            lines_to_remove.sort(reverse=True)  # Remove from end to beginning
            for line_num in lines_to_remove:
                if line_num < len(lines):
                    lines.pop(line_num)

            # Write back
            with open(script_path, 'w') as f:
                f.write('\n'.join(lines))

            print(f"✅ Removed {len(lines_to_remove)} duplicate lines")
        else:
            print("✅ No duplicates found to remove")

        return True

    except Exception as e:
        print(f"❌ Error removing duplicates: {e}")
        return False


if __name__ == "__main__":
    remove_duplicate_functions()
