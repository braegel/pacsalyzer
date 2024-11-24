# DICOM PACS Analysis Toolkit

This toolkit consists of three Python scripts for querying a PACS system, analyzing institution names, and visualizing study distributions by weekday and hour. These tools are designed to work together, allowing you to process DICOM metadata and extract meaningful insights.

---

## Workflow Overview

1. **Query the PACS system** using `query_pacs.py` to retrieve study data in JSON format.
2. **Analyze institution names** from the JSON data using `list_institution_names.py`.
3. **Visualize study distribution** by weekday and hour using `analyze_weekday_study_distribution.py`.

---

## Scripts Overview

### 1. `query_pacs.py`

This script queries a PACS server using the DICOM C-FIND operation and retrieves metadata for studies. The retrieved data is saved in a JSON file, which can be analyzed by the subsequent scripts.

#### Features:
- Connects to a PACS server using IP, port, and AE title.
- Queries the PACS for metadata such as Patient ID, Institution Name, Study Date, and Modality.
- Saves the results in a JSON file.

#### Usage:
```bash
python3 query_pacs.py <ip> <port> <aet> [-o OUTPUT]
```

#### Arguments:
| Argument        | Description                                                                                       |
|------------------|---------------------------------------------------------------------------------------------------|
| `<ip>`           | IP address of the PACS server.                                                                   |
| `<port>`         | Port of the PACS server.                                                                         |
| `<aet>`          | AE Title of the PACS server.                                                                     |
| `-o, --output`   | Output file name for the query results (default: `query_results.json`).                           |

#### Example:
```bash
python3 query_pacs.py 127.0.0.1 11112 MY_AE_TITLE -o pacs_results.json
```

#### Output:
A JSON file containing DICOM metadata for all retrieved studies.

---

### 2. `list_institution_names.py`

This script processes the JSON file created by `query_pacs.py` and counts the occurrences of institution names (`(0008,0080)` tags). It supports filtering based on a timeframe (e.g., last three months) and outputs the results in a tab-separated format for easy import into spreadsheet applications.

#### Features:
- Extracts and cleans institution names.
- Counts occurrences and sorts by frequency.
- Filters data by timeframe:
  - All data (`all`)
  - Last six months (`6m`)
  - Last three months (`3m` - default)
  - Last one month (`1m`)
- Outputs tab-separated results.

#### Usage:
```bash
python3 list_institution_names.py <input_file> [--timeframe TIMEFRAME]
```

#### Arguments:
| Argument          | Description                                                                                     |
|--------------------|-------------------------------------------------------------------------------------------------|
| `<input_file>`     | Path to the JSON file containing DICOM metadata (from `query_pacs.py`).                         |
| `--timeframe`      | Timeframe to filter data: `all`, `6m`, `3m` (default), or `1m`.                                 |

#### Example:
```bash
python3 list_institution_names.py pacs_results.json --timeframe 3m > institutions.tsv
```

#### Output:
Tab-separated values listing institution names and their counts. Example:
```
Institution Name	Count
Example Hospital	20
Unknown	3
```

---

### 3. `analyze_weekday_study_distribution.py`

This script processes the JSON file created by `query_pacs.py` and visualizes the distribution of studies by weekday and hour. It generates separate boxplots for each weekday, showing the spread of study counts.

#### Features:
- Filters data by timeframe:
  - All data (`all`)
  - Last six months (`6m`)
  - Last three months (`3m` - default)
  - Last one month (`1m`)
- Generates boxplots for each weekday, showing hourly study distribution.
- Saves the plots as PNG files.

#### Usage:
```bash
python3 analyze_weekday_study_distribution.py <input_file> <output_folder> [--timeframe TIMEFRAME]
```

#### Arguments:
| Argument          | Description                                                                                     |
|--------------------|-------------------------------------------------------------------------------------------------|
| `<input_file>`     | Path to the JSON file containing DICOM metadata (from `query_pacs.py`).                         |
| `<output_folder>`  | Folder to save the generated boxplot images.                                                    |
| `--timeframe`      | Timeframe to filter data: `all`, `6m`, `3m` (default), or `1m`.                                 |

#### Example:
```bash
python3 analyze_weekday_study_distribution.py pacs_results.json plots/ --timeframe 3m
```

#### Output:
Generates PNG boxplots for each weekday, saved in the specified folder.

---

## Input File Format

All scripts expect the input JSON file to follow this format:
```json
[
    {
        "(0008,0080)": "(0008, 0080) Institution Name LO: 'Example Hospital'",
        "(0008,0020)": "(0008, 0020) Study Date DA: '20231101'",
        "(0008,0030)": "(0008, 0030) Study Time TM: '083000'"
    },
    {
        "(0008,0080)": "(0008, 0080) Institution Name LO: 'LUKAS KRANKKENHAUS'",
        "(0008,0020)": "(0008, 0020) Study Date DA: '20231015'",
        "(0008,0030)": "(0008, 0030) Study Time TM: '091500'"
    }
]
```

---

## Workflow Example

1. Query the PACS system:
   ```bash
   python3 query_pacs.py 127.0.0.1 11112 MY_AE_TITLE -o pacs_results.json
   ```

2. Analyze institution names:
   ```bash
   python3 list_institution_names.py pacs_results.json --timeframe 3m > institutions.tsv
   ```

3. Visualize study distribution:
   ```bash
   python3 analyze_weekday_study_distribution.py pacs_results.json plots/ --timeframe 3m
   ```

---

## Requirements

- Python 3.6 or later
- `pynetdicom` for `query_pacs.py`

Install dependencies for `query_pacs.py`:
```bash
pip install pynetdicom
```

---

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.

## Contributing

Contributions are welcome! Feel free to open issues or submit pull requests.

## Author

[Bernd Brägelmann](https://berndbraegelmann.de/)
