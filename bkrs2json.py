import json
import re
import os
import argparse

# Precompiled regular expressions
CHINESE_CHARS_REGEX = re.compile(r'^[\u4E00-\u9FFF]+$')
EXAMPLES_REGEX = re.compile(r'\[ex].*?\[/ex]')
TAGS_REGEX = re.compile(r'\[/?(?:c|p|ref|b|i|\*)\]')
MEANINGS_REGEX = re.compile(r'\[m\d?\](.*?)\[/m\]')
RUSSIAN_CHARS_REGEX = re.compile(r'[\u0400-\u04FF]')
LATIN_CHARS_REGEX = re.compile(r'[a-zA-Z]')

def parse_dsl_file(dsl_file_path, alt_format):
    """Parse a single DSL file and yield processed dictionary entries."""
    try:
        with open(dsl_file_path, 'r', encoding='utf-16') as file:
            entry_lines = []

            # Skip the first three lines (file metadata)
            for _ in range(3):
                next(file, None)

            for line in file:
                line = line.strip()
                if not line:
                    continue

                # Check if this line starts a new entry (Chinese word)
                if CHINESE_CHARS_REGEX.match(line):
                    if entry_lines:
                        entry = process_entry(entry_lines, alt_format)
                        if entry:
                            yield entry
                    entry_lines = [line]  # Start a new entry
                else:
                    entry_lines.append(line)

            # Process the last entry, if any
            if entry_lines:
                entry = process_entry(entry_lines, alt_format)
                if entry:
                    yield entry
    except UnicodeDecodeError as e:
        print(f"Error decoding file {dsl_file_path}: {e}. Ensure the file is UTF-16 encoded.")

def process_entry(entry_lines, alt_format):
    """Process and clean an entry split into lines."""
    headword = entry_lines[0].strip()
    # Clean tags from pinyin
    pinyin = TAGS_REGEX.sub('', entry_lines[1].strip())

    # Remove examples and unnecessary tags from content
    content = ' '.join(entry_lines[2:])
    content = EXAMPLES_REGEX.sub('', content)
    content = TAGS_REGEX.sub('', content)

    # Extract meanings from the content
    meanings = [m.strip() for m in MEANINGS_REGEX.findall(content) if m.strip()]

    # Normalize spaces and character escaping, parse only Russian-language meanings
    cleaned_meanings = [
        re.sub(r'\s+', ' ',
               meaning.replace('\\[', '[').replace('\\]', ']').replace('\"', '"')
               ).strip()
        for meaning in meanings if is_mainly_russian(meaning)
    ]

    if cleaned_meanings:
        if alt_format:
            return {
                "word": headword,
                "pinyin": pinyin,
                "meanings": cleaned_meanings
            }
        else:
            return {headword: [pinyin, cleaned_meanings]}
    return None

def is_mainly_russian(meaning):
    """Determine if a meaning is mainly in Russian, considering Roman numerals as section markers."""
    if meaning.startswith(('I', 'V')):
        return True

    # Count the number of Russian and Latin characters.
    russian_chars = len(RUSSIAN_CHARS_REGEX.findall(meaning))
    latin_chars = len(LATIN_CHARS_REGEX.findall(meaning))
    total_letters = russian_chars + latin_chars

    # If there are any Russian and Latin letters, calculate the ratio.
    if total_letters > 0:
        return (russian_chars / total_letters) > 0.1

    return False

def write_entry_to_json(entry, json_file, is_first_entry):
    """Write one entry to JSON file with correct comma placement."""
    if not is_first_entry:
        json_file.write(',\n')
    json.dump(entry, json_file, ensure_ascii=False, indent=2)

def parse_directory(directory_path, json_file_path, alt_format):
    """Parse all DSL files in a directory and write the output to a JSON file."""
    dsl_files = [entry.path for entry in os.scandir(directory_path) if entry.name.endswith('.dsl')]

    if not dsl_files:
        print(f"Error: No .dsl files found in directory: {directory_path}")
        return False

    first_entry = True

    with open(json_file_path, 'w', encoding='utf-8') as json_file:
        json_file.write('[\n')

        for dsl_file in dsl_files:
            try:
                print(f"Parsing file: {dsl_file}")
                for entry in parse_dsl_file(dsl_file, alt_format):
                    if entry:
                        write_entry_to_json(entry, json_file, first_entry)
                        first_entry = False
            except Exception as e:
                print(f"Error processing file {dsl_file}: {e}")

        json_file.write('\n]')

    return True

def main(input_directory, output_file, alt_format=False):
    """Main function to handle user input and start the parsing process."""
    if not os.path.isdir(input_directory):
        print(f"Error: The specified input directory does not exist: {input_directory}")
        return

    output_dir = os.path.dirname(output_file)
    if output_dir and not os.path.exists(output_dir):
        print(f"Error: The directory for the output file does not exist: {output_dir}")
        return

    if parse_directory(input_directory, output_file, alt_format):
        print(f"Successfully converted files from directory {input_directory} to {output_file}")
    else:
        print("Conversion failed.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="""
    Convert bkrs.info DSL files to JSON format.
    This script processes bkrs.info dictionary files in DSL format and outputs a JSON file.
    
    Default output structure:
    [
        {
            "some word": ["pinyin of the word", ["meaning_1", "meaning_2", ...]]
        },
        ...
    ]
    """,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument("input_directory", help="Directory containing .dsl files to be processed")
    parser.add_argument("output_file", help="Path and filename for the output JSON file")
    parser.add_argument(
        "--alt-format",
        action="store_true",
        help="""
        Use alternative output format. 
        When enabled, the output structure will be:
        [
            {
                "word": "some word",
                "pinyin": "pinyin of the word",
                "meanings": ["meaning_1", "meaning_2", ...]
            },
            ...
        ]
        """
    )

    args = parser.parse_args()
    main(args.input_directory, args.output_file, args.alt_format)
