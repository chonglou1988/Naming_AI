import os
import csv
import sys
import datetime
import requests
try:
    import openai
except ImportError:
    openai = None

def is_media_file(filename):
    """Check if the file is a media file based on its extension."""
    media_extensions = {
        # Video formats
        '.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.mpeg', '.mpg', '.m4v', '.3gp', '.rmvb', '.iso','.rm',
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

def call_grok(prompt, api_key=None, model="grok-3"):
    """Call Grok API to suggest a normalized file name."""
    if openai is None:
        raise ImportError("openai 库未安装。请运行 pip install openai")
    api_key = api_key or #enter your own api key
    try:
        client = openai.OpenAI(api_key=api_key, base_url="https://api.x.ai/v1")
        completion = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "请遵循以下规则：1. **仅输出建议的文件名本身，不要输出解释说明。**2. **名称应避免冗长，体现核心信息，便于整理归档。**3. **保留关键标识信息，例如片名、歌名、年份、季数/集数（如适用），但不包含无意义的英文或随机字符。例如：扫黑风暴（2021）S1 EP01**4. **使用中文命名，如果原名为英文且广为人知，可以保留或翻译为中文。**5. **不要添加扩展名（如 .mp4、.mp3），也不要添加多余标点。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=50
        )
        return completion.choices[0].message.content.strip()
    except Exception as e:
        print(f"[Grok Error] {e}")
        file_name_part = prompt.split('原文件名称: ')[1].splitlines()[0]
        return f"Grok_Suggested_{os.path.basename(file_name_part)}"

def suggest_normalized_name(file_path, backend="grok", **kwargs):
    """Suggest a normalized file name using the specified backend."""
    file_name = os.path.basename(file_path)
    folder_name = os.path.basename(os.path.dirname(file_path))
    prompt = (
        f"请根据以下信息，建议一个简洁、规范化的文件名，（只返回建议的文件名，不加解释）：**\n\n"
        f"文件地址：{file_path}"
        f"文件夹名称: {folder_name}\n"
        f"原文件名称: {file_name}"
    )
    return call_grok(prompt, **kwargs)

def generate_csv_report(media_files, output_file):
    """Generate a CSV report with original and recommended file names."""
    with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['Original Path', 'Original Name', 'Recommended Name'])
        for file_path in media_files:
            original_name = os.path.basename(file_path)
            recommended_name = suggest_normalized_name(file_path)
            if not recommended_name:
                recommended_name = f"Error_Suggesting_Name_{original_name}"
            writer.writerow([file_path, original_name, recommended_name])

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
        if 'Recommended Name' not in row or not row['Recommended Name']:
            issues.append({
                'original_path': row.get('Original Path', ''),
                'original_name': row.get('Original Name', ''),
                'new_name': row.get('Recommended Name', ''),
                'issue': "Recommended name is empty or not provided"
            })
        else:
            invalid_chars = ['/', '\\', ':', '*', '?', '"', '<', '>', '|']
            if any(char in row['Recommended Name'] for char in invalid_chars):
                issues.append({
                    'original_path': row.get('Original Path', ''),
                    'original_name': row.get('Original Name', ''),
                    'new_name': row['Recommended Name'],
                    'issue': f"Invalid characters in recommended name: {row['Recommended Name']}"
                })
            duplicates = [r for r in data if r != row and 'Recommended Name' in r and r['Recommended Name'] == row['Recommended Name'] and os.path.dirname(r.get('Original Path', '')) == os.path.dirname(row.get('Original Path', ''))]
            if duplicates:
                issues.append({
                    'original_path': row.get('Original Path', ''),
                    'original_name': row.get('Original Name', ''),
                    'new_name': row['Recommended Name'],
                    'issue': f"Duplicate recommended name in the same directory: {row['Recommended Name']} already exists"
                })
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
    """Modify the names based on user consent."""
    modified = []
    for issue in issues:
        invalid_chars = ['/', '\\', ':', '*', '?', '"', '<', '>', '|']
        corrected_name = issue['new_name']
        for char in invalid_chars:
            corrected_name = corrected_name.replace(char, '_')
        if "Duplicate recommended name" in issue['issue']:
            base_name, ext = os.path.splitext(corrected_name)
            corrected_name = f"{base_name}_duplicate{ext}"
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
    """Rename files in the directory based on the modified data."""
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
    """Main function to integrate media file naming and correction."""
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
    
    # Read the generated report
    data = read_csv_report(output_file)
    
    # Check for naming issues
    issues = check_naming_issues(data)
    modified_data = []
    if issues:
        issues_to_modify = get_user_consent(issues)
        if not issues_to_modify:
            print("Exiting without making changes.")
            return
        modified_data = modify_names(issues_to_modify)
        print("\nThe following modifications will be applied for problematic names:")
        for item in modified_data:
            print(f"Original Path: {item['original_path']}")
            print(f"Original Name: {item['original_name']}")
            print(f"Old Recommended Name: {item['old_new_name']}")
            print(f"Corrected Name: {item['corrected_name']}\n")
    else:
        print("No naming issues found. Proceeding with recommended names from the CSV report.")
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
    
    # Final confirmation before renaming, reload CSV to ensure latest changes
    print("Reloading CSV report to ensure the latest modifications are used for renaming.")
    data = read_csv_report(output_file)
    modified_data = []
    issues = check_naming_issues(data)
    if issues:
        issues_to_modify = get_user_consent(issues)
        if not issues_to_modify:
            print("Exiting without making changes.")
            return
        modified_data = modify_names(issues_to_modify)
        print("\nThe following modifications will be applied for problematic names:")
        for item in modified_data:
            print(f"Original Path: {item['original_path']}")
            print(f"Original Name: {item['original_name']}")
            print(f"Old Recommended Name: {item['old_new_name']}")
            print(f"Corrected Name: {item['corrected_name']}\n")
    else:
        print("No naming issues found. Proceeding with recommended names from the updated CSV report.")
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
        
    response = input("Confirm renaming of files? Enter 'Y' to proceed with renaming: ").strip().upper()
    if response != 'Y':
        print("Renaming cancelled.")
        return
    
    # Backup and rename
    backup_file_names(directory)
    rename_files(directory, modified_data)
    print("File renaming completed.")

if __name__ == "__main__":
    main()
