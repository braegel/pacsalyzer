import argparse
from pynetdicom import AE, debug_logger
from pynetdicom.sop_class import PatientRootQueryRetrieveInformationModelFind
from pydicom.dataset import Dataset
import json
import sys

# Optional: Enable debugging for troubleshooting
# debug_logger()

def perform_c_find(ip, port, ae_title, output_file="query_results.json"):
    # Create an Application Entity (AE)
    ae = AE()
    
    # Add requested context for C-FIND
    ae.add_requested_context(PatientRootQueryRetrieveInformationModelFind)
    
    # Establish connection
    assoc = ae.associate(ip, port, ae_title=ae_title)
    
    if assoc.is_established:
        print(f"Connected to PACS server {ip}:{port} with AE Title '{ae_title}'.")
        
        # Prepare the query dataset
        query = Dataset()
        query.QueryRetrieveLevel = "SERIES"
        query.PatientID = ""               # (0010,0020): Patient ID
        query.InstitutionName = ""         # (0008,0080): Institution Name
        query.StudyDate = ""               # (0008,0020): Study Date
        query.StudyTime = ""               # (0008,0030): Study Time
        query.StudyDescription = ""        # (0008,1030): Study Description
        query.Modality = ""                # (0008,0060): Modality
        query.StudyInstanceUID = ""  # (0020,000D): Study Instance UID
        
        # Send the C-FIND query
        responses = assoc.send_c_find(query, PatientRootQueryRetrieveInformationModelFind)
        
        results = []
        for (status, identifier) in responses:
            if status and status.Status in (0xFF00, 0x0000):
                if identifier:
                    # Convert DICOM DataElement values to strings or None
                    result = {
                        "(0010,0020)": str(identifier.get((0x0010, 0x0020), "")).strip(),  # Patient ID
                        "(0008,0080)": str(identifier.get((0x0008, 0x0080), "")).strip(),  # Institution Name
                        "(0008,0020)": str(identifier.get((0x0008, 0x0020), "")).strip(),  # Study Date
                        "(0008,0030)": str(identifier.get((0x0008, 0x0030), "")).strip(),  # Study Time
                        "(0008,1030)": str(identifier.get((0x0008, 0x1030), "")).strip(),  # Study Description
                        "(0008,0060)": str(identifier.get((0x0008, 0x0060), "")).strip(),  # Modality
                        "(0020,000D)": str(identifier.get((0x0020, 0x000D), "")).strip(),  # Study Instance UID
                    }
                    results.append(result)
        
        if results:
            # Save results to file (overwrites existing file)
            with open(output_file, "w") as f:
                json.dump(results, f, indent=4)
            print(f"Results saved to '{output_file}' (existing file overwritten).")
        else:
            print("No results received from the PACS server.")
        
        # Release the association
        assoc.release()
    else:
        print("Failed to connect to the PACS server.")
        sys.exit(1)


if __name__ == "__main__":
    # Define the command-line arguments
    parser = argparse.ArgumentParser(
        description="DICOM C-FIND PACS Query Script",
        epilog="Example usage: python3 script.py 127.0.0.1 11112 MY_AE_TITLE -o output.json"
    )
    parser.add_argument(
        "ip",
        help="IP address of the PACS server"
    )
    parser.add_argument(
        "port",
        type=int,
        help="Port of the PACS server"
    )
    parser.add_argument(
        "aet",
        help="AE Title of the PACS server"
    )
    parser.add_argument(
        "-o", "--output",
        default="query_results.json",
        help="Output file name for the query results (default: query_results.json)"
    )
    
    # Parse arguments
    try:
        args = parser.parse_args()
    except SystemExit as e:
        # Handle parsing error or --help
        if e.code != 0:
            print("\nError: Invalid or missing arguments. Use -h for usage information.")
        sys.exit(e.code)
    
    # Call the function with parsed arguments
    try:
        perform_c_find(args.ip, args.port, args.aet, args.output)
    except Exception as e:
        print(f"An error occurred during execution: {e}")
        sys.exit(1)
