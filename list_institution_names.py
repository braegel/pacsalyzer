import argparse
import json
from collections import Counter
import re
from datetime import datetime, timedelta
import sys


def extract_institution_name(value):
    """
    Extracts the institution name from a formatted DICOM tag string.
    Example: "(0008, 0080) Institution Name LO: 'LUKAS KRANKKENHAUS'" -> "LUKAS KRANKKENHAUS"
    """
    match = re.search(r"LO: '([^']*)'", value)
    return match.group(1) if match else "Unknown"


def extract_study_date(entry):
    """
    Extracts the study date from the (0008,0020) tag if present.
    Example: "(0008, 0020) Study Date DA: '20231101'" -> "20231101"
    """
    raw_date = entry.get("(0008,0020)", None)
    if raw_date:
        match = re.search(r"DA: '([^']*)'", raw_date)
        return match.group(1) if match else None
    return None


def filter_data_by_timeframe(data, timeframe):
    """
    Filters the data based on the provided timeframe.
    """
    if timeframe == "all":
        return data  # Return all data
    
    # Determine the cutoff date
    days_mapping = {"6m": 180, "3m": 90, "1m": 30}
    cutoff_date = datetime.now() - timedelta(days=days_mapping.get(timeframe, 90))
    
    filtered_data = []
    for entry in data:
        study_date = extract_study_date(entry)
        if study_date:
            try:
                study_datetime = datetime.strptime(study_date, "%Y%m%d")
                if study_datetime >= cutoff_date:
                    filtered_data.append(entry)
            except ValueError:
                continue  # Skip entries with invalid dates
    return filtered_data


def count_institution_names(input_file, timeframe):
    try:
        # Load the JSON data from the input file
        with open(input_file, "r") as f:
            data = json.load(f)
        
        # Filter data by timeframe
        filtered_data = filter_data_by_timeframe(data, timeframe)
        
        # Extract and clean the "(0008,0080)" tags (Institution Name)
        institution_names = [extract_institution_name(entry.get("(0008,0080)", "Unknown")) for entry in filtered_data]
        
        # Count occurrences of each Institution Name
        counts = Counter(institution_names)
        
        # Sort the results by occurrence count in descending order
        sorted_counts = sorted(counts.items(), key=lambda x: x[1], reverse=True)
        
        # Output results in tab-separated format
        print("Institution Name\tCount")
        for institution, count in sorted_counts:
            print(f"{institution}\t{count}")
        
        return sorted_counts
    except FileNotFoundError:
        print(f"Error: The file '{input_file}' does not exist.")
        sys.exit(1)
    except json.JSONDecodeError:
        print(f"Error: The file '{input_file}' is not a valid JSON file.")
        sys.exit(1)
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        sys.exit(1)


if __name__ == "__main__":
    # Define command-line arguments
    parser = argparse.ArgumentParser(
        description="Count occurrences of (0008,0080) tags in a JSON file with optional timeframe filtering",
        epilog="Example usage: python3 script.py input.json --timeframe 3m > output.tsv"
    )
    parser.add_argument(
        "input_file",
        help="Path to the input JSON file containing DICOM tag data"
    )
    parser.add_argument(
        "--timeframe",
        choices=["all", "6m", "3m", "1m"],
        default="3m",
        help="Timeframe to filter data: 'all' (all data), '6m' (last six months), '3m' (last three months, default), '1m' (last one month)"
    )
    
    # Parse arguments
    try:
        args = parser.parse_args()
    except SystemExit as e:
        if e.code != 0:
            print("\nError: Invalid or missing arguments. Use -h for usage information.")
        sys.exit(e.code)
    
    # Process the input file
    try:
        count_institution_names(args.input_file, args.timeframe)
    except Exception as e:
        print(f"An error occurred during execution: {e}")
        sys.exit(1)
