import argparse
import json
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import holidays
import re


def clean_value(value):
    """
    Extracts the raw value from a formatted DICOM tag value string.
    Handles strings like:
    "(0020, 000D) Study Instance UID UI: 1.2.40.0.13.0.11.5093.2.2011008744.25997.20110225112319"
    -> "1.2.40.0.13.0.11.5093.2.2011008744.25997.20110225112319"
    """
    # Extract value wrapped in single quotes
    match = re.search(r"'([^']*)'", value)
    if match:
        return match.group(1)
    
    # Extract value after "UI:" or other prefixes
    match = re.search(r'UI:\s*([^\s]+)', value)
    if match:
        return match.group(1)
    
    return None

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
        study_date = clean_value(entry.get("(0008,0020)", ""))
        study_time = clean_value(entry.get("(0008,0030)", ""))
        study_uid = clean_value(entry.get("(0020,000D)", ""))  # StudyInstanceUID

        # Debugging
        # print(f"Study Date: {study_date}, Study Time: {study_time}, Study UID: {study_uid}")

        if study_date and study_time and study_uid:
            try:
                # Combine date and time into a datetime object
                datetime_obj = datetime.strptime(study_date + study_time.split(".")[0], "%Y%m%d%H%M%S")
                records.append({
                    "study_uid": study_uid,
                    "weekday": datetime_obj.strftime("%A"),
                    "hour": datetime_obj.hour,
                    "date": datetime_obj.date()
                })
            except ValueError as e:
                print(f"Invalid date/time format for entry: {entry}. Error: {e}")
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


def separate_holidays(df, country="DE"):
    """
    Separates holiday data from the main DataFrame.
    """
    public_holidays = holidays.CountryHoliday(country)
    holiday_df = df[df["date"].isin(public_holidays)]
    non_holiday_df = df[~df["date"].isin(public_holidays)]
    return non_holiday_df, holiday_df



def get_top_10_counts(df, output_file=None):
    """
    Returns the top 10 highest counts of unique studies by date, weekday, and hour.
    """
    top_counts = (
        df.groupby(["date", "weekday", "hour"])["study_uid"]
        .nunique()  # Anzahl der einzigartigen Studien
        .reset_index(name="study_count")
        .sort_values(by="study_count", ascending=False)
        .head(10)
        .reset_index(drop=True)
    )
    if output_file:
        top_counts.to_csv(output_file, index=False)
        print(f"Top 10 counts saved to {output_file}")
    return top_counts

def plot_boxplots_per_weekday_hour(df, output_folder, timeframe, title_suffix=""):
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
            # Group data by date and hour, and count unique studies (StudyInstanceUID)
            hourly_counts = (
                weekday_data.groupby(["date", "hour"])["study_uid"]
                .nunique()  # Count unique StudyInstanceUIDs
                .reset_index(name="count")
            )

            # Pivot data for boxplot-friendly format
            boxplot_data = []
            for hour in range(24):
                hour_data = hourly_counts[hourly_counts["hour"] == hour]["count"]
                boxplot_data.append(hour_data.values)

            # Create boxplot
            plt.figure(figsize=(12, 6))
            plt.boxplot(boxplot_data, positions=range(24), showfliers=True, widths=0.6, patch_artist=True)

            # Add horizontal lines at y=6, 12, 18, and 21
            for y_value in [6, 12, 18, 24]:
                plt.axhline(y=y_value, color="gray", linestyle="--", linewidth=0.8)

            # Set integer ticks for y-axis
            plt.gca().yaxis.set_major_locator(plt.MaxNLocator(integer=True))

            # Finalize plot
            plt.title(f"Study Distribution per Hour for {weekday} ({timeframe}) {title_suffix}")
            plt.xlabel("Hour of Day")
            plt.ylabel("Number of Unique Studies")
            plt.xticks(range(24))
            plt.ylim(bottom=0)  # Ensure y-axis starts at 0
            plt.tight_layout()
            output_file = f"{output_folder}{weekday}_boxplot_{timeframe}{title_suffix.replace(' ', '_')}.png"
            plt.savefig(output_file)
            print(f"Saved boxplot for {weekday} to {output_file}")
            plt.close()
            
if __name__ == "__main__":
    # Define the command-line arguments
    parser = argparse.ArgumentParser(
        description="Analyze studies per hour by weekday, create separate boxplots, and identify top 10 study counts",
        epilog="Example usage: python3 script.py input.json output_folder/ --timeframe 3m --holiday-country DE"
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
    parser.add_argument(
        "--holiday-country",
        default="DE",
        help="Country code for public holidays (default: DE for Germany)"
    )
    parser.add_argument(
        "--top10-output",
        help="File to save the top 10 highest counts (optional)"
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

    # Separate holidays from the rest of the data
    non_holiday_df, holiday_df = separate_holidays(filtered_df, country=args.holiday_country)

    # Generate top 10 counts
    print("Generating top 10 highest counts...")
    top_10 = get_top_10_counts(filtered_df, args.top10_output)
    print("Top 10 counts:")
    print(top_10)

    # Plot separate boxplots for weekdays (non-holidays)
    print("Generating boxplots for non-holiday data...")
    plot_boxplots_per_weekday_hour(non_holiday_df, args.output_folder, args.timeframe, title_suffix="(Non-Holidays)")

    # Plot separate boxplots for holidays
    if not holiday_df.empty:
        print("Generating boxplots for holiday data...")
        plot_boxplots_per_weekday_hour(holiday_df, args.output_folder, args.timeframe, title_suffix="(Holidays)")
    else:
        print("No holiday data available for the selected timeframe and country.")
