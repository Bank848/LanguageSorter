import os
import shutil
import re
import sys
import subprocess

# Check if tqdm is installed, and if not, install it
try:
    from tqdm import tqdm
except ImportError:
    print("tqdm not found! Installing tqdm...")
    subprocess.run([sys.executable, "-m", "pip", "install", "tqdm"])
    from tqdm import tqdm

def has_thai(text):
    return bool(re.search('[ก-๙]', text))

def has_english(text):
    return bool(re.search('[A-Za-z]', text))

def has_japanese(text):
    return bool(re.search('[\u3040-\u30FF\u4E00-\u9FFF\uFF66-\uFF9F]', text))

def extract_thai_sentences(text):
    # Extract sentences in Thai within double quotes
    matches = re.findall(r'"(.*?)"', text)
    return [match.strip() for match in matches if has_thai(match)]

def detect_and_notify_thai_sentences(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.readlines()
    
    lines_with_thai = []
    for i, line in enumerate(content, start=1):
        matches = re.findall(r'"(.*?)"', line)
        thai_exist = any(has_thai(match) for match in matches)
        if thai_exist:
            lines_with_thai.append((i, extract_thai_sentences(line)))
    
    return lines_with_thai

# Get the source directories and file extension from the user
source_directories = []

while True:
    source_directory = input("Enter a source directory path (or 'done' to finish): ").strip()
    
    if source_directory.lower() == "done" and not source_directories:
        print("Please enter at least one directory before proceeding.")
        continue
    elif source_directory.lower() == "done":
        break
    elif not os.path.exists(source_directory) or not os.path.isdir(source_directory):  # Check if path exists and is a directory
        print(f"Directory {source_directory} doesn't exist. Please enter a valid directory path.")
        continue
    elif source_directory in source_directories:  # Check if directory has already been added
        print(f"Directory {source_directory} has already been added. Please enter a different directory.")
        continue
    else:
        source_directories.append(source_directory)

file_extension = input("Enter the file extension you want to sort (e.g., txt or .txt): ").strip()
if not file_extension.startswith('.'):
    file_extension = '.' + file_extension

proceed = input("Do you want to sort the files? (yes/no): ").strip().lower()

if proceed == 'yes':
    for source_directory in source_directories:
        TH_ALL_directory = os.path.join(source_directory, 'TH ALL')
        TH_ENG_ALL_directory = os.path.join(source_directory, 'TH+ENG ALL')
        ENG_ALL_directory = os.path.join(source_directory, 'ENG ALL')
        JP_ALL_directory = os.path.join(source_directory, 'JP ALL')
        JP_TH_ALL_directory = os.path.join(source_directory, 'JP+TH')
        JP_ENG_ALL_directory = os.path.join(source_directory, 'JP+ENG')
        Other_ALL_directory = os.path.join(source_directory, 'Other ALL')

        # Create the directories if they don't exist
        for directory in [TH_ALL_directory, TH_ENG_ALL_directory, ENG_ALL_directory, JP_ALL_directory, JP_TH_ALL_directory, JP_ENG_ALL_directory, Other_ALL_directory]:
            if not os.path.exists(directory):
                os.makedirs(directory)

        all_files = [f for f in os.listdir(source_directory) if f.endswith(file_extension)]

        destination_mapping = {}

        for filename in tqdm(all_files, desc="Detecting file language", unit="file"):
            filepath = os.path.join(source_directory, filename)
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
                matches = re.findall(r'"(.*?)"', content)
                all_data_content = ' '.join(matches)

                thai_exist = any(has_thai(match) for match in matches)
                english_exist = any(has_english(match) for match in matches)
                japanese_exist = any(has_japanese(match) for match in matches)

                if japanese_exist and not thai_exist and not english_exist:
                    destination_mapping[filepath] = JP_ALL_directory
                elif japanese_exist and thai_exist:
                    destination_mapping[filepath] = JP_TH_ALL_directory
                elif japanese_exist and english_exist:
                    destination_mapping[filepath] = JP_ENG_ALL_directory
                elif thai_exist and not english_exist:
                    destination_mapping[filepath] = TH_ALL_directory
                elif thai_exist and english_exist:
                    destination_mapping[filepath] = TH_ENG_ALL_directory
                elif english_exist and not thai_exist:
                    destination_mapping[filepath] = ENG_ALL_directory
                else:
                    destination_mapping[filepath] = Other_ALL_directory

                # Newly added code to detect Thai sentences and record in result.txt
                lines_with_thai = detect_and_notify_thai_sentences(filepath)

                if lines_with_thai:
                    with open('result.txt', 'a', encoding='utf-8') as result_file:
                        result_file.write(f"{filename} - Thai sentences found:\n")
                        for line_number, thai_sentences in lines_with_thai:
                            result_file.write(f"  Line {line_number}: {', '.join(thai_sentences)}\n")

        for src, dest in tqdm(destination_mapping.items(), desc="Moving files", unit="file"):
            dest_path = os.path.join(dest, os.path.basename(src))
            if os.path.exists(dest_path):
                os.remove(dest_path)
            shutil.move(src, dest_path)

        print("\nFiles in", source_directory, "have been sorted!")

else:
    print("Exiting without sorting.")
