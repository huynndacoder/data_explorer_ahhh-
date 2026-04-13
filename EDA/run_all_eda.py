#!/usr/bin/env python3
"""
Insurance Data Explorer - Main Runner
Execute all EDA scripts and generate comprehensive report
"""

import subprocess
import sys
from pathlib import Path
from datetime import datetime

EDA_PATH = Path("/home/huynnz/GetAJob/DataExplorer/EDA")


def run_script(script_name):
    """Run a single EDA script."""
    print(f"\n{'=' * 80}")
    print(f"Running: {script_name}")
    print("=" * 80)

    script_path = EDA_PATH / script_name
    try:
        result = subprocess.run(
            [sys.executable, str(script_path)],
            capture_output=True,
            text=True,
            timeout=300,
        )

        if result.returncode == 0:
            print(result.stdout)
            return True
        else:
            print(f"Error running {script_name}:")
            print(result.stderr)
            return False
    except subprocess.TimeoutExpired:
        print(f"Timeout running {script_name}")
        return False
    except Exception as e:
        print(f"Exception running {script_name}: {e}")
        return False


def main():
    """Main execution function."""
    print("=" * 80)
    print("INSURANCE DATA EXPLORATION - COMPREHENSIVE EDA")
    print("=" * 80)
    print(f"Execution started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    scripts = [
        "00_comprehensive_summary.py",
        "01_data_overview.py",
        "02_customer_analysis.py",
        "03_contract_order_analysis.py",
        "04_vehicle_analysis.py",
        "05_employee_branch_analysis.py",
        "06_product_channel_analysis.py",
    ]

    results = {}
    for script in scripts:
        results[script] = run_script(script)

    print("\n" + "=" * 80)
    print("EXECUTION SUMMARY")
    print("=" * 80)

    for script, success in results.items():
        status = "PASSED" if success else "FAILED"
        print(f"  {script}: {status}")

    passed = sum(1 for success in results.values() if success)
    total = len(results)

    print(f"\nOverall: {passed}/{total} scripts executed successfully")
    print(f"Execution completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)


if __name__ == "__main__":
    main()
