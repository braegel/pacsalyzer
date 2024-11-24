import argparse
import json
from collections import Counter

def count_institution_names(input_file):
    try:
        # Load the JSON data from the input file
        with open(input_file, "r") as f:
            data = json.load(f)
        
        # Extract the "(0008,0080)" tags (Institution Name)
        institution_names = [entry.get("(0008,0080)", "Unknown") for entry in data]
        
        # Count occurrences of each Institution Name
        counts = Counter(institution_names)
        
        # Sort the results by occurrence count in descending order
        sorted_counts = sorted(counts.items(), key=lambda x: x[1], reverse=True)
        
        # Display results
        print("Institution Name Counts (sorted by occurrences):")
        for institution, count in sorted_counts:
            print(f"{institution}: {count}")
        
        # Return the sorted results as a list of tuples
        return sorted_counts
    except Exception as e:
        print(f"Error processing the file: {e}")
        return []

if __name__ == "__main__":
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Count occurrences of (0008,0080) tags in a JSON file")
    parser.add_argument("input_file", help="Path to the input JSON file")
    args = parser.parse_args()
    
    # Call the function with the input file
    count_institution_names(args.input_file)
