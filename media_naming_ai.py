import os
import csv
from pathlib import Path

def is_media_file(filename):
    """Check if the file is a media file based on its extension."""
    media_extensions = {
        # Video formats
        '.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.mpeg', '.mpg', '.m4v', '.3gp',
        # Audio formats
        '.mp3', '.wav', '.ogg', '.flac', '.aac', '.wma', '.m4a'
    }
    return os.path.splitext(filename.lower())[1] in media_extensions

def get_media_files(directory):
    """Get a list of media files in the specified directory and subdirectories."""
    media_files = []
    for root, _, files in os.walk(directory):
        for file in files:
            if is_media_file(file):
                full_path = os.path.join(root, file)
                media_files.append(full_path)
    return media_files

def suggest_normalized_name(file_path):
    """Suggest a normalized name for the file (placeholder for AI integration)."""
    # For now, just return a placeholder normalized name
    # In the future, this will call an AI tool to suggest a name based on file or folder context
    file_name = os.path.basename(file_path)
    folder_name = os.path.basename(os.path.dirname(file_path))
    return f"Normalized_{file_name}_from_{folder_name}"

def generate_csv_report(media_files, output_file):
    """Generate a CSV report with original and recommended file names."""
    with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['Original Path', 'Original Name', 'Recommended Name'])
        for file_path in media_files:
            original_name = os.path.basename(file_path)
            recommended_name = suggest_normalized_name(file_path)
            writer.writerow([file_path, original_name, recommended_name])

def main():
    """Main function to scan for media files and generate a naming report."""
    print("Starting media file naming analysis...")
    directory = input("Enter the directory path to scan for media files: ")
    if not os.path.isdir(directory):
        print(f"Error: '{directory}' is not a valid directory.")
        return
    
    media_files = get_media_files(directory)
    if not media_files:
        print("No media files found in the specified directory.")
        return
    
    print(f"Found {len(media_files)} media files.")
    output_file = "media_naming_report.csv"
    generate_csv_report(media_files, output_file)
    print(f"CSV report generated: {output_file}")

if __name__ == "__main__":
    main()
