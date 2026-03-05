import os
import zipfile
import io
import argparse
import pandas as pd
import osxphotos
import subprocess
import logging
from datetime import datetime
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def normalize_date(date_str):
    """
    Converts 'Sunday December 13,2015 7:13 PM GMT' to EXIF format 'YYYY:MM:DD HH:MM:SS'.
    """
    try:
        # Strip ' GMT' if present as it might complicate simple parsing if not handled
        clean_date = date_str.replace(' GMT', '').strip()
        # Example: Sunday December 13,2015 7:13 PM
        dt = datetime.strptime(clean_date, "%A %B %d,%Y %I:%M %p")
        return dt.strftime("%Y:%m:%d %H:%M:%S")
    except Exception as e:
        logger.warning(f"Failed to normalize date '{date_str}': {e}")
        return None

def get_gps_coordinates(photos_db, filename, checksum):
    """
    Queries the macOS Photos database for GPS coordinates using osxphotos.
    """
    # Attempt to find the photo by filename. 
    # Note: checksum in Photos DB might not match iCloud ZIP checksum directly if modified.
    # osxphotos search by filename is a good starting point.
    photos = photos_db.photos(filename=[filename])
    if not photos:
        # Try without extension if first attempt fails
        stem = Path(filename).stem
        photos = photos_db.photos(filename=[stem])
    
    if photos:
        photo = photos[0]
        # In osxphotos, photo.location is a tuple (latitude, longitude)
        if photo.location[0] is not None and photo.location[1] is not None:
            return photo.location[0], photo.location[1]
    
    return None, None

def apply_metadata(file_path, creation_date, lat, lon):
    """
    Applies metadata using exiftool.
    """
    args = ["exiftool", "-overwrite_original"]
    
    if creation_date:
        args.append(f"-AllDates={creation_date}")
        args.append(f"-FileModifyDate={creation_date}")
    
    if lat is not None and lon is not None:
        args.append(f"-GPSLatitude={lat}")
        args.append(f"-GPSLatitudeRef={'N' if lat >= 0 else 'S'}")
        args.append(f"-GPSLongitude={lon}")
        args.append(f"-GPSLongitudeRef={'E' if lon >= 0 else 'W'}")
    
    args.append(str(file_path))
    
    try:
        subprocess.run(args, check=True, capture_output=True)
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Exiftool failed for {file_path}: {e.stderr.decode()}")
        return False

def process_zip(zip_path, output_dir, photos_db):
    """
    Processes a single iCloud Photos ZIP file.
    """
    logger.info(f"Processing archive: {zip_path}")
    stats = {
        "extracted": 0,
        "date_matched": 0,
        "gps_matched": 0,
        "errors": 0
    }
    
    try:
        with zipfile.ZipFile(zip_path, 'r') as z:
            # Find all relevant Photo Details.csv files within the 'Photos/' directory
            # Pattern matches: Photos/Photo Details.csv AND Photos/Photo Details-1.csv, Photos/Photo Details-2.csv, etc.
            import re
            csv_pattern = re.compile(r'^Photos/Photo Details(-\d+)?\.csv$', re.IGNORECASE)
            csv_names = [name for name in z.namelist() if csv_pattern.match(name)]
            
            if not csv_names:
                logger.warning(f"No valid 'Photo Details.csv' found in 'Photos/' directory of {zip_path}")
                # Some ZIPs might have a different structure, but as per user request, we restrict to 'Photos/'
                return stats

            # Load all matching CSVs and merge them into one DataFrame
            dataframes = []
            for csv_name in csv_names:
                logger.info(f"  Reading manifest: {csv_name}")
                with z.open(csv_name) as f:
                    csv_content = f.read().decode('utf-8')
                    df = pd.read_csv(io.StringIO(csv_content))
                    dataframes.append(df)
            
            full_df = pd.concat(dataframes, ignore_index=True)
            
            # Create a lookup table
            # Note: We drop duplicates in case the same image is referenced in multiple CSVs
            full_df = full_df.drop_duplicates(subset=['imgName'])
            lookup = full_df.set_index('imgName').to_dict('index')
            
            # Iterate through files in ZIP
            for member in z.infolist():
                # Skip directories and the manifest files themselves
                if member.is_dir() or any(member.filename == name for name in csv_names):
                    continue
                
                filename = os.path.basename(member.filename)
                
                # Check if file is in the manifest
                if filename in lookup:
                    metadata = lookup[filename]
                    creation_date_raw = metadata.get('originalCreationDate')
                    checksum = metadata.get('fileChecksum')
                    
                    normalized_date = normalize_date(creation_date_raw) if creation_date_raw else None
                    
                    # Extract file
                    target_path = Path(output_dir) / filename
                    with z.open(member) as source, open(target_path, 'wb') as target:
                        target.write(source.read())
                    
                    stats["extracted"] += 1
                    if normalized_date:
                        stats["date_matched"] += 1
                    
                    # GPS Lookup
                    lat, lon = get_gps_coordinates(photos_db, filename, checksum)
                    if lat is not None:
                        stats["gps_matched"] += 1
                    
                    # Apply Metadata
                    if apply_metadata(target_path, normalized_date, lat, lon):
                        pass # Success
                    else:
                        stats["errors"] += 1
                else:
                    # Only log skipping for media files, not for system files or metadata
                    if not filename.startswith('.'):
                        logger.debug(f"Skipping {filename}, not in manifest.")
                    
    except Exception as e:
        logger.error(f"Error processing {zip_path}: {e}")
        stats["errors"] += 1
        
    return stats

def main():
    parser = argparse.ArgumentParser(description="iCloud Metadata Restoration Utility")
    parser.add_argument("--source", required=True, help="Directory containing iCloud Photos ZIP files")
    parser.add_argument("--output", required=True, help="Target directory for restored photos")
    args = parser.parse_args()
    
    source_dir = Path(args.source)
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Initialize osxphotos database
    logger.info("Initializing macOS Photos database connection...")
    photos_db = osxphotos.PhotosDB()
    
    # Correcting search pattern to match "iCloud Photos Part * of *.zip"
    zip_files = list(source_dir.glob("iCloud Photos Part * of *.zip"))
    if not zip_files:
        logger.warning(f"No ZIP files found matching 'iCloud Photos Part * of *.zip' in {source_dir}")
        return

    total_stats = {
        "extracted": 0,
        "date_matched": 0,
        "gps_matched": 0,
        "errors": 0
    }
    
    for zip_path in zip_files:
        zip_stats = process_zip(zip_path, output_dir, photos_db)
        for k in total_stats:
            total_stats[k] += zip_stats[k]
            
    logger.info("Processing complete.")
    logger.info(f"Summary: {total_stats}")

if __name__ == "__main__":
    main()
