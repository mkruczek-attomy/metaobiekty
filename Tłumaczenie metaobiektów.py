#!/usr/bin/env python3
"""
CSV File Translator: Polish to German
Translates content in CSV file from Polish to German based on Type and Field columns
Uses deep-translator library for reliable translations
"""

import csv
import json
import time
from deep_translator import GoogleTranslator
import sys
from typing import Any, Dict, List, Union
import random

# Global variables for progress tracking
total_translations = 0
completed_translations = 0

def count_value_fields(data: Any) -> int:
    """
    Count the total number of "value" fields that need translation in JSON
    
    Args:
        data: JSON data to analyze
    
    Returns:
        Number of "value" fields containing strings
    """
    count = 0
    if isinstance(data, dict):
        for key, value in data.items():
            if key == "value" and isinstance(value, str) and value.strip():
                count += 1
            else:
                count += count_value_fields(value)
    elif isinstance(data, list):
        for item in data:
            count += count_value_fields(item)
    return count

def print_progress(current: int, total: int, text_preview: str = ""):
    """
    Print translation progress
    
    Args:
        current: Current number of completed translations
        total: Total number of translations needed
        text_preview: Preview of current text being translated
    """
    if total == 0:
        percentage = 100
    else:
        percentage = (current / total) * 100
    
    bar_length = 30
    filled_length = int(bar_length * current // total) if total > 0 else bar_length
    bar = '█' * filled_length + '░' * (bar_length - filled_length)
    
    preview = f" | {text_preview[:40]}..." if text_preview else ""
    print(f"\rProgress: [{bar}] {current}/{total} ({percentage:.1f}%){preview}", end='', flush=True)

def translate_text(text: str, max_retries: int = 5) -> str:
    """
    Translate text from Polish to German with retry logic and exponential backoff
    
    Args:
        text: Text to translate
        max_retries: Maximum number of retry attempts
    
    Returns:
        Translated text or original text if translation fails
    """
    global completed_translations, total_translations
    
    if not text or not text.strip():
        return text
    
    # Update progress
    print_progress(completed_translations, total_translations, text)
    
    for attempt in range(max_retries):
        try:
            # Add delay with jitter to avoid rate limiting
            base_delay = 0.3 + (attempt * 0.3)
            jitter = random.uniform(0, 0.2)
            time.sleep(base_delay + jitter)
            
            # Create translator instance and translate
            translator = GoogleTranslator(source='pl', target='cs')
            result = translator.translate(text)
            
            # Update progress after successful translation
            completed_translations += 1
            print_progress(completed_translations, total_translations)
            
            return result
            
        except Exception as e:
            error_msg = str(e).lower()
            
            # Check for rate limiting or connection errors
            if 'too many requests' in error_msg or '429' in error_msg or 'timeout' in error_msg or 'timed out' in error_msg:
                wait_time = min(5 * (2 ** attempt), 60)
                print(f"\n⚠️  Rate limit/timeout on attempt {attempt + 1}/{max_retries}, waiting {wait_time}s...")
                time.sleep(wait_time)
                continue
            
            if attempt == 0:
                print(f"\n⚠️  Translation error for '{text[:30]}...': {e}")
            
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt  # Exponential backoff
                print(f"\n⚠️  Retrying in {wait_time}s...")
                time.sleep(wait_time)
            else:
                print(f"\n❌ Failed to translate after {max_retries} attempts: '{text[:30]}...', keeping original")
                completed_translations += 1
                print_progress(completed_translations, total_translations)
                return text
    
    return text

def translate_json_value(data: Any) -> Any:
    """
    Recursively process JSON and translate only "value" fields
    
    Args:
        data: JSON data to process
    
    Returns:
        Processed JSON data with translated "value" fields
    """
    if isinstance(data, dict):
        result = {}
        for key, value in data.items():
            if key == "value" and isinstance(value, str):
                # Translate only "value" fields that contain strings
                result[key] = translate_text(value)
            else:
                # Recursively process other fields without translating
                result[key] = translate_json_value(value)
        return result
    elif isinstance(data, list):
        return [translate_json_value(item) for item in data]
    else:
        # Return non-dict/list values as-is
        return data

def count_csv_translations(input_file: str) -> int:
    """
    Count total translations needed in CSV file
    
    Args:
        input_file: Path to input CSV file
    
    Returns:
        Total number of translations needed
    """
    count = 0
    with open(input_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            row_type = row.get('Type', '').strip()
            field = row.get('Field', '').strip()
            default_content = row.get('Default content', '').strip()
            
            if row_type == 'METAOBJECT' and default_content:
                if field == 'thumbnail_title':
                    # Simple text translation
                    count += 1
                elif field in ['description', 'tekst', 'text']:
                    # JSON translation - count value fields
                    try:
                        json_data = json.loads(default_content)
                        count += count_value_fields(json_data)
                    except json.JSONDecodeError:
                        # If not valid JSON, treat as simple text
                        count += 1
    
    return count

def translate_csv_file() -> None:
    """
    Translate a CSV file from Polish to German with hardcoded paths
    """
    global total_translations, completed_translations
    
    # Hardcoded file paths
    input_file = "C:/Users/micha/Downloads/test_tlumaczeń.csv"
    output_file = "output.csv"
    
    try:
        # Count total translations needed
        print(f"📖 Reading input file: {input_file}")
        total_translations = count_csv_translations(input_file)
        completed_translations = 0
        
        print(f"📊 Found {total_translations} text fields to translate")
        print("🌍 Starting translation from Polish to German...")
        print("📚 Using deep-translator library (Google Translate backend)...")
        print()
        
        # Initialize progress bar
        print_progress(0, total_translations)
        
        # Read and process CSV
        with open(input_file, 'r', encoding='utf-8') as infile:
            reader = csv.DictReader(infile)
            fieldnames = reader.fieldnames
            
            # Ensure 'Translated content' column exists
            if 'Translated content' not in fieldnames:
                fieldnames = list(fieldnames) + ['Translated content']
            
            rows = []
            for row in reader:
                row_type = row.get('Type', '').strip()
                field = row.get('Field', '').strip()
                default_content = row.get('Default content', '').strip()
                
                # Initialize translated content with empty string
                translated_content = ''
                
                # Process based on Type and Field
                if row_type == 'METAOBJECT' and default_content:
                    if field == 'thumbnail_title':
                        # Simple text translation
                        translated_content = translate_text(default_content)
                    
                    elif field in ['description', 'tekst', 'text']:
                        # JSON translation
                        try:
                            json_data = json.loads(default_content)
                            translated_json = translate_json_value(json_data)
                            translated_content = json.dumps(translated_json, ensure_ascii=False)
                        except json.JSONDecodeError:
                            # If not valid JSON, treat as simple text
                            print(f"\n⚠️  Warning: Field '{field}' contains invalid JSON, translating as plain text")
                            translated_content = translate_text(default_content)
                
                # Add translated content to row
                row['Translated content'] = translated_content
                rows.append(row)
        
        # Final progress update
        print()
        print()
        
        # Write output CSV
        print(f"💾 Writing translated data to: {output_file}")
        with open(output_file, 'w', encoding='utf-8', newline='') as outfile:
            writer = csv.DictWriter(outfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
        
        print("✅ Translation completed successfully!")
        print(f"📈 Translated {completed_translations}/{total_translations} text fields")
        
    except FileNotFoundError:
        print(f"❌ Error: Input file '{input_file}' not found.")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

def main():
    """Main function"""
    translate_csv_file()

if __name__ == "__main__":
    main()