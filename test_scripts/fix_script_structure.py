#!/usr/bin/env python3
"""
Fix the main script structure by removing duplicate code and organizing properly
"""


def fix_main_script_structure():
    """Fix structural issues in offline_rpi_dashboard_db.py"""

    script_path = '/home/isha/deepak/MFM_offline_setup/offline_rpi_dashboard_db.py'

    try:
        with open(script_path, 'r') as f:
            content = f.read()

        lines = content.split('\n')

        print("🔧 Fixing main script structure...")

        # Find the run_dashboard function
        run_dashboard_start = None
        for i, line in enumerate(lines):
            if line.strip().startswith('def run_dashboard'):
                run_dashboard_start = i
                break

        if not run_dashboard_start:
            print("❌ Could not find run_dashboard function")
            return False

        # Find the end of run_dashboard function (first non-indented line after it)
        run_dashboard_end = None
        for i in range(run_dashboard_start + 1, len(lines)):
            line = lines[i]
            if line.strip() == '':
                continue
            if not (line.startswith('    ') or line.startswith('\t')):
                run_dashboard_end = i
                break

        if not run_dashboard_end:
            run_dashboard_end = len(lines)

        print(
            f"📋 run_dashboard function: lines {run_dashboard_start + 1} to {run_dashboard_end}")

        # Keep everything before run_dashboard and the function itself
        before_function = lines[:run_dashboard_start]
        function_lines = lines[run_dashboard_start:run_dashboard_end]

        # Find the main execution block (if __name__ == "__main__":)
        main_block_start = None
        for i in range(run_dashboard_end, len(lines)):
            if 'if __name__ == "__main__":' in lines[i]:
                main_block_start = i
                break

        if main_block_start:
            main_block = lines[main_block_start:]
            print(
                f"✅ Found main execution block at line {main_block_start + 1}")
        else:
            # Create a proper main execution block
            main_block = [
                '',
                'if __name__ == "__main__":',
                '    import sys',
                '    import subprocess',
                '    if \'--install\' in sys.argv:',
                '        print("Delegating --install to offline_rpi_dashboard.py...")',
                '        script_dir = Path(__file__).parent.absolute()',
                '        dashboard_script = script_dir / \'offline_rpi_dashboard.py\'',
                '        result = subprocess.run(',
                '            [sys.executable, str(dashboard_script), \'--install\'])',
                '        sys.exit(result.returncode)',
                '    elif \'--run\' in sys.argv or len(sys.argv) == 1:',
                '        run_dashboard()',
                '    else:',
                '        print("Unknown argument. Use --install or --run.")'
            ]
            print("✅ Created proper main execution block")

        # Reconstruct the file with proper structure
        new_content = '\n'.join(
            before_function + function_lines + [''] + main_block)

        # Write the fixed content
        with open(script_path, 'w') as f:
            f.write(new_content)

        print("✅ Fixed script structure")
        print("🗑️  Removed duplicate code sections")
        print("📋 Proper main execution block created")

        return True

    except Exception as e:
        print(f"❌ Error fixing script structure: {e}")
        return False


if __name__ == "__main__":
    fix_main_script_structure()
