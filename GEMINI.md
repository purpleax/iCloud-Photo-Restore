# iCloud Metadata Restoration & Extraction Utility

This project is a utility designed to process segmented iCloud Photos export files (`iCloud Photos Part X of Y.zip`), extract media assets, and restore missing EXIF metadata.

## Project Overview

- **Goal:** Extract assets from iCloud ZIP exports and inject original creation dates (from internal CSVs) and GPS coordinates (from the macOS Photos Library).
- **Core Workflow:**
  - Recursively scan for iCloud ZIP files.
  - Read `Photo Details.csv` directly from within each ZIP.
  - Query the macOS `Photos.sqlite` database via `osxphotos` for GPS coordinates.
  - Use `exiftool` to update metadata (Date and Location) on the extracted files.
- **Target Environment:** macOS (Required for native Photos.sqlite access).

## Tech Stack (Proposed)

- **Language:** Python 3.10+
- **Key Libraries:**
  - `osxphotos`: For macOS Photos database interaction.
  - `exiftool`: Backend for writing EXIF metadata.
  - `pandas`: For CSV data handling and lookup.
  - `zipfile` & `io`: For in-memory archive processing.

## Key Files

- `icloudbackupPRD.txt`: The Product Requirements Document (PRD) detailing the project scope, technical requirements, and execution workflow.
- `Photo Details.csv`: A sample metadata manifest exported by iCloud, containing fields like `imgName`, `fileChecksum`, and `originalCreationDate`.

## Building and Running

*TODO: No implementation files (.py) exist yet. The PRD suggests a CLI interface.*

### Potential Execution:
```bash
python main.py --source /path/to/zips --output /path/to/restored
```

## Development Conventions

- **Disk Efficiency:** Process ZIP files one by one to minimize disk overhead.
- **Resilience:** Log errors for corrupted ZIPs or missing CSVs and continue processing.
- **Auditing:** Maintain a log of total extractions, successful metadata matches, and orphaned files.
