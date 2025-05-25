# Naming_AI

Naming_AI is a tool designed to help you organize your media files by suggesting normalized file names using AI. It scans directories for video and audio files, generates AI-suggested names, and provides a mechanism to review and apply these names to your files.

## Overview

This project consists of two main scripts:
- **media_naming_ai.py**: Scans for media files and uses AI (currently Grok from xAI) to suggest normalized file names, outputting the results to a CSV report.
- **media_naming_corrector.py**: Reads the CSV report, checks for naming issues, allows for modifications if needed, and renames the media files accordingly.

## Prerequisites

- Python 3.x installed on your system.
- Required Python packages: `requests`, `openai` (for Grok API access). You can install them using pip:
  ```
  pip install requests openai
  ```

## Installation

1. Clone this repository to your local machine:
   ```
   git clone https://github.com/chonglou1988/Naming_AI.git
   cd Naming_AI
   ```

2. Ensure you have the necessary dependencies installed as mentioned in the Prerequisites section.

## Usage Instructions

Follow these steps to use Naming_AI to rename your media files:

### Step 1: Generate AI-Suggested Names

1. Open a terminal or command prompt in the `Naming_AI` directory.
2. Run the `media_naming_ai.py` script:
   ```
   python media_naming_ai.py
   ```
3. When prompted, enter the path to the directory containing your media files (e.g., videos or audio files).
4. The script will scan the directory and subdirectories for media files and use AI to suggest normalized names.
5. After processing, a CSV file named `media_naming_report.csv` will be generated in the project directory. This file lists the original file paths, original names, and AI-suggested names.

### Step 2: Review and Apply Names

1. Run the `media_naming_corrector.py` script to review the suggested names and apply them to your files:
   ```
   python media_naming_corrector.py
   ```
2. When prompted, enter the path to the directory containing your media files (same as in Step 1).
3. The script will read the `media_naming_report.csv` file and check for any naming issues in the suggested names (e.g., invalid characters or duplicate names in the same directory).
4. If issues are found, you will be presented with a list of problematic names and asked if you want to modify them:
   - If you choose 'y' (yes), the script will suggest corrections (e.g., replacing invalid characters with underscores).
   - If you choose 'n' (no), no modifications will be made, and the process will stop.
5. If no issues are found or after modifications are agreed upon, the script will create a backup of the original file names in a `backup_names` folder within the media directory.
6. Finally, the script will rename the media files based on the corrected or AI-suggested names. A summary of renamed files and any errors will be displayed.

### Notes

- Ensure that the `media_naming_report.csv` file is in the project directory when running `media_naming_corrector.py`.
- The backup of original file names is created automatically before any renaming occurs, allowing you to revert changes if needed.
- The AI model used for name suggestions is currently set to Grok from xAI. The API key for Grok is hardcoded in the script for simplicity, but for security, it's recommended to use environment variables or a secure configuration file for API keys in a production environment.

## Supported Media Formats

- **Video**: .mp4, .avi, .mkv, .mov, .wmv, .flv, .mpeg, .mpg, .m4v, .3gp, .rmvb, .iso
- **Audio**: .mp3, .wav, .ogg, .flac, .aac, .wma, .m4a

## Contributing

If you have suggestions for improving this tool or want to add support for other AI models or features, feel free to open an issue or submit a pull request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
