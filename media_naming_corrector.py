import csv
import os
import shutil
import datetime
import sys

def read_csv_report(file_path):
    """Read the media naming report CSV file and return the data."""
    data = []
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                data.append(row)
        return data
    except FileNotFoundError:
        print(f"Error: The file {file_path} was not found.")
        sys.exit(1)
    except Exception as e:
        print(f"Error reading CSV file: {e}")
        sys.exit(1)

def check_naming_issues(data):
    """Check for naming issues in the CSV data."""
    issues = []
    for row in data:
        # Using column names from media_naming_ai.py generated CSV
        if 'Recommended Name' not in row or not row['Recommended Name']:
            issues.append({
                'original_path': row.get('Original Path', ''),
                'original_name': row.get('Original Name', ''),
                'new_name': row.get('Recommended Name', ''),
                'issue': "Recommended name is empty or not provided"
            })
        else:
            # Check for invalid characters or patterns in the new name
            invalid_chars = ['/', '\\', ':', '*', '?', '"', '<', '>', '|']
            if any(char in row['Recommended Name'] for char in invalid_chars):
                issues.append({
                    'original_path': row.get('Original Path', ''),
                    'original_name': row.get('Original Name', ''),
                    'new_name': row['Recommended Name'],
                    'issue': f"Invalid characters in recommended name: {row['Recommended Name']}"
                })
            # Check for duplicate new names in the same directory
            duplicates = [r for r in data if r != row and 'Recommended Name' in r and r['Recommended Name'] == row['Recommended Name'] and os.path.dirname(r.get('Original Path', '')) == os.path.dirname(row.get('Original Path', ''))]
            if duplicates:
                issues.append({
                    'original_path': row.get('Original Path', ''),
                    'original_name': row.get('Original Name', ''),
                    'new_name': row['Recommended Name'],
                    'issue': f"Duplicate recommended name in the same directory: {row['Recommended Name']} already exists"
                })
            # Add more checks as needed (e.g., length, format)
    return issues

def get_user_consent(issues):
    """Get user consent to modify problematic names."""
    if not issues:
        print("No naming issues found.")
        return []
    
    print("\nThe following naming issues were found:")
    for i, issue in enumerate(issues, 1):
        print(f"{i}. Original Path: {issue['original_path']}")
        print(f"   Original Name: {issue['original_name']}")
        print(f"   Recommended Name: {issue['new_name']}")
        print(f"   Issue: {issue['issue']}")
    
    response = input("\nDo you want to modify these names? (y/n): ").lower()
    if response == 'y':
        return issues
    else:
        print("No modifications will be made.")
        return []

def modify_names(issues):
    """Modify the names based on user consent. For now, just simulate the modification."""
    modified = []
    for issue in issues:
        # Here you would implement logic to suggest or generate a corrected name
        # For simplicity, we'll just remove invalid characters as an example
        invalid_chars = ['/', '\\', ':', '*', '?', '"', '<', '>', '|']
        corrected_name = issue['new_name']
        for char in invalid_chars:
            corrected_name = corrected_name.replace(char, '_')
        # Handle duplicates by appending a counter if needed
        if "Duplicate recommended name" in issue['issue']:
            base_name, ext = os.path.splitext(corrected_name)
            corrected_name = f"{base_name}_duplicate{ext}"
        # Ensure the original file extension is preserved
        original_ext = os.path.splitext(issue['original_name'])[1]
        if not corrected_name.endswith(original_ext):
            corrected_name = f"{corrected_name}{original_ext}"
        modified.append({
            'original_path': issue['original_path'],
            'original_name': issue['original_name'],
            'old_new_name': issue['new_name'],
            'corrected_name': corrected_name
        })
    return modified

def is_media_file(filename):
    """Check if the file is a media file based on its extension."""
    media_extensions = {
        # Video formats
        '.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.mpeg', '.mpg', '.m4v', '.3gp', '.rmvb', '.iso',
        # Audio formats
        '.mp3', '.wav', '.ogg', '.flac', '.aac', '.wma', '.m4a'
    }
    return os.path.splitext(filename.lower())[1] in media_extensions

def backup_file_names(directory):
    """Backup the original file names in the specified directory."""
    backup_dir = os.path.join(directory, 'backup_names')
    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir)
    
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = os.path.join(backup_dir, f'original_names_{timestamp}.txt')
    
    with open(backup_file, 'w', encoding='utf-8') as f:
        for root, _, files in os.walk(directory):
            for file in files:
                if is_media_file(file):
                    full_path = os.path.join(root, file)
                    f.write(f"{full_path}\n")
    print(f"Backup of original file names created at: {backup_file}")

def rename_files(directory, modified_data):
    """Rename files in the directory based on the modified data, prioritizing fixing files that lost extensions."""
    path_mapping = {item['original_path']: item['corrected_name'] for item in modified_data}
    renamed_count = 0
    error_count = 0
    already_renamed_count = 0
    
    for original_path, new_name in path_mapping.items():
        original_dir = os.path.dirname(original_path)
        original_base_name = os.path.splitext(os.path.basename(original_path))[0]
        new_base_name = os.path.splitext(new_name)[0]
        new_path = os.path.join(original_dir, new_name)
        
        if os.path.exists(original_path):
            if os.path.exists(new_path):
                print(f"Warning: Target name already exists, skipping: {new_path}")
                error_count += 1
                continue
            try:
                os.rename(original_path, new_path)
                print(f"Renamed: {original_path} -> {new_path}")
                renamed_count += 1
            except Exception as e:
                print(f"Error renaming {original_path}: {e}")
                error_count += 1
        else:
            # Check for files with the same base name as the corrected name (likely renamed without extension)
            found_file = None
            for file in os.listdir(original_dir):
                if file == new_base_name or file.startswith(new_base_name):
                    potential_path = os.path.join(original_dir, file)
                    if os.path.isfile(potential_path):
                        found_file = potential_path
                        break
            
            if found_file:
                if os.path.exists(new_path):
                    print(f"Warning: Target name already exists, skipping: {new_path}")
                    error_count += 1
                    continue
                try:
                    os.rename(found_file, new_path)
                    print(f"Fixed extension for previously renamed file: {found_file} -> {new_path}")
                    renamed_count += 1
                except Exception as e:
                    print(f"Error fixing extension for {found_file}: {e}")
                    error_count += 1
            else:
                # Fallback to checking for original base name
                for file in os.listdir(original_dir):
                    if file.startswith(original_base_name):
                        potential_path = os.path.join(original_dir, file)
                        if os.path.isfile(potential_path):
                            found_file = potential_path
                            break
                
                if found_file:
                    if os.path.exists(new_path):
                        print(f"Warning: Target name already exists, skipping: {new_path}")
                        error_count += 1
                        continue
                    try:
                        os.rename(found_file, new_path)
                        print(f"Renamed previously modified file: {found_file} -> {new_path}")
                        renamed_count += 1
                    except Exception as e:
                        print(f"Error renaming previously modified file {found_file}: {e}")
                        error_count += 1
                else:
                    print(f"Note: Original file not found at {original_path}, it may have already been renamed. Skipping.")
                    already_renamed_count += 1
    
    print(f"\nRenaming Summary: {renamed_count} files renamed, {error_count} errors encountered, {already_renamed_count} files possibly already renamed.")

def main():
    csv_file = "media_naming_report.csv"
    media_directory = input("Enter the directory path containing media files: ")
    
    if not os.path.exists(media_directory):
        print(f"Error: Directory {media_directory} does not exist.")
        sys.exit(1)
    
    # Step 1: Read CSV report
    data = read_csv_report(csv_file)
    
    # Step 2: Check for naming issues
    issues = check_naming_issues(data)
    
    modified_data = []
    if issues:
        # Step 3: Get user consent to modify names if there are issues
        issues_to_modify = get_user_consent(issues)
        if not issues_to_modify:
            print("Exiting without making changes.")
            return
        
        # Step 4: Modify names for problematic entries
        modified_data = modify_names(issues_to_modify)
        print("\nThe following modifications will be applied for problematic names:")
        for item in modified_data:
            print(f"Original Path: {item['original_path']}")
            print(f"Original Name: {item['original_name']}")
            print(f"Old Recommended Name: {item['old_new_name']}")
            print(f"Corrected Name: {item['corrected_name']}\n")
    else:
        print("No naming issues found. Proceeding with recommended names from the CSV report.")
        # Use recommended names directly if no issues, preserving original extension
        for row in data:
            if 'Recommended Name' in row and row['Recommended Name']:
                original_ext = os.path.splitext(row['Original Name'])[1]
                corrected_name = row['Recommended Name']
                if not corrected_name.endswith(original_ext):
                    corrected_name = f"{corrected_name}{original_ext}"
                modified_data.append({
                    'original_path': row['Original Path'],
                    'original_name': row['Original Name'],
                    'old_new_name': row['Recommended Name'],
                    'corrected_name': corrected_name
                })
    
    if not modified_data:
        print("No files to rename.")
        return
    
    # Step 5: Backup original file names
    backup_file_names(media_directory)
    
    # Step 6: Rename files
    rename_files(media_directory, modified_data)
    print("File renaming completed.")

if __name__ == "__main__":
    main()
