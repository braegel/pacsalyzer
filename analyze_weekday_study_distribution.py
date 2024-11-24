import argparse
import json
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
from datetime import datetime, timedelta
import re


def clean_value(value):
    """
    Extracts the raw value from a formatted DICOM tag value string, e.g., "DA: '20241006'" -> "20241006".
    """
    match = re.search(r"'([^']*)'", value)
    return match.group(1) if match else None


def load_data(input_file):
    try:
        with open(input_file, "r") as f:
            data = json.load(f)
        return data
    except Exception as e:
        print(f"Error reading the input file: {e}")
        return []


def preprocess_data(data):
    records = []
    for entry in data:
        # Clean and extract date and time values
        study_date = clean_value(entry.get("(0008,0020)", ""))
        study_time = clean_value(entry.get("(0008,0030)", ""))
        if study_date and study_time:
            try:
                # Combine date and time into a datetime object
                datetime_obj = datetime.strptime(study_date + study_time.split(".")[0], "%Y%m%d%H%M%S")
                records.append({
                    "weekday": datetime_obj.strftime("%A"),
                    "hour": datetime_obj.hour,
                    "date": datetime_obj.date()
                })
            except ValueError:
                print(f"Invalid date/time format for entry: {entry}")
    return pd.DataFrame(records)


def filter_data_by_timeframe(df, timeframe):
    """
    Filters the DataFrame based on the provided timeframe.
    """
    if timeframe == "all":
        return df  # Return all data
    days_mapping = {"6m": 180, "3m": 90, "1m": 30}
    if timeframe in days_mapping:
        cutoff_date = datetime.now().date() - timedelta(days=days_mapping[timeframe])
        return df[df["date"] >= cutoff_date]
    else:
        raise ValueError("Invalid timeframe. Choose from 'all', '6m', '3m', or '1m'.")


def plot_boxplots_per_weekday_hour(df, output_folder, timeframe):
    # Ensure output folder ends with a slash
    if not output_folder.endswith("/"):
        output_folder += "/"

    # Get the unique weekdays in order
    weekdays = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    df = df.copy()  # Ensure we're working on a copy to avoid warnings
    df["weekday"] = pd.Categorical(df["weekday"], categories=weekdays, ordered=True)

    for weekday in weekdays:
        weekday_data = df[df["weekday"] == weekday]

        if not weekday_data.empty:
            # Group data by date and hour
            hourly_counts = weekday_data.groupby(["date", "hour"]).size().reset_index(name="count")

            # Pivot data for boxplot-friendly format
            boxplot_data = []
            for hour in range(24):
                hour_data = hourly_counts[hourly_counts["hour"] == hour]["count"]
                boxplot_data.append(hour_data.values)

            # Create boxplot
            plt.figure(figsize=(12, 6))
            plt.boxplot(boxplot_data, positions=range(24), showfliers=True, widths=0.6, patch_artist=True, boxprops=dict(facecolor="lightblue"))

            # Finalize plot
            plt.title(f"Study Distribution per Hour for {weekday} ({timeframe})")
            plt.xlabel("Hour of Day")
            plt.ylabel("Number of Studies")
            plt.xticks(range(24))
            plt.tight_layout()
            output_file = f"{output_folder}{weekday}_boxplot_{timeframe}.png"
            plt.savefig(output_file)
            print(f"Saved boxplot for {weekday} to {output_file}")
            plt.close()


if __name__ == "__main__":
    # Define the command-line arguments
    parser = argparse.ArgumentParser(
        description="Analyze studies per hour by weekday and create separate boxplots",
        epilog="Example usage: python3 script.py input.json output_folder/ --timeframe 3m"
    )
    parser.add_argument(
        "input_file",
        help="Path to the input JSON file containing study data"
    )
    parser.add_argument(
        "output_folder",
        help="Folder to save the boxplot images"
    )
    parser.add_argument(
        "--timeframe",
        choices=["all", "6m", "3m", "1m"],
        default="3m",
        help="Timeframe to filter data: 'all' (all data), '6m' (last six months), '3m' (last three months, default), '1m' (last one month)"
    )
    
    # Parse arguments
    args = parser.parse_args()

    # Load data from JSON
    data = load_data(args.input_file)
    if not data:
        print("No valid data to process. Exiting.")
        exit(1)

    # Preprocess data into a DataFrame
    df = preprocess_data(data)
    if df.empty:
        print("No valid datetime records found in the data. Exiting.")
        exit(1)

    # Filter data by timeframe
    try:
        filtered_df = filter_data_by_timeframe(df, args.timeframe)
    except ValueError as e:
        print(e)
        exit(1)

    # Plot separate boxplots for each weekday and hour
    plot_boxplots_per_weekday_hour(filtered_df, args.output_folder, args.timeframe)
