# iCloud Metadata Restoration & Extraction Utility

A specialized tool for macOS designed to process segmented iCloud Photos exports (`iCloud Photos Part X of Y.zip`), extract media assets, and restore missing EXIF metadata by cross-referencing local manifests and your macOS Photos Library.

## 🌟 Features

- **In-Memory Processing:** Reads `Photo Details.csv` directly from ZIP archives to minimize disk overhead.
- **Incremental Manifest Support:** Automatically detects and merges multiple manifests (e.g., `Photo Details.csv`, `Photo Details-1.csv`) found within the `Photos/` directory of each archive.
- **Date Restoration:** Parses and injects the `originalCreationDate` from iCloud manifests into EXIF headers.
- **GPS Restoration:** Queries your local macOS Photos Library (`Photos.sqlite`) using `osxphotos` to recover Latitude and Longitude coordinates.
- **Automated Metadata Injection:** Uses `exiftool` to handle the heavy lifting of writing metadata to various file formats (JPEG, HEIC, MOV, etc.).

## 📋 Prerequisites

- **Operating System:** macOS (Required for native access to the Photos database).
- **Python:** 3.10 or higher.
- **External Tools:** [Exiftool](https://exiftool.org/) must be installed on your system.
  ```bash
  brew install exiftool
  ```

## 🚀 Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/yourusername/icloud-photo-restore.git
   cd icloud-photo-restore
   ```

2. **Set up a virtual environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install osxphotos pandas
   ```

4. **Grant Permissions:**
   To allow the script to read your GPS data, you must grant **Full Disk Access** to your terminal application (Terminal, iTerm2, or VS Code):
   - Open `System Settings` > `Privacy & Security` > `Full Disk Access`.
   - Toggle the switch for your terminal app.

## 🛠 Usage

Run the script by pointing it to the directory containing your iCloud ZIP files and a destination folder for the restored assets.

```bash
python3 restore_metadata.py --source /path/to/icloud/exports --output /path/to/restored/photos
```

### Arguments:
- `--source`: The directory containing files named `iCloud Photos Part X of Y.zip`.
- `--output`: The directory where the extracted and metadata-corrected files will be saved.

## ⚙️ How it Works

1. **Scan:** Identifies all matching iCloud ZIP archives in the source directory.
2. **Merge:** Locates all `Photo Details*.csv` files within the `Photos/` internal directory of each ZIP and merges them.
3. **Extract:** Extracts media files one by one.
4. **Enrich:** 
   - Matches the file to the manifest for the creation date.
   - Matches the file (via filename/stem) to the macOS Photos database for GPS coordinates.
5. **Inject:** Runs `exiftool` to update the file's internal metadata.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
