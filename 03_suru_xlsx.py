import os
from pathlib import Path
import xml.etree.ElementTree as ET
from typing import List, Dict, Any
import pandas as pd

def get_xml_files(directory_path: str) -> list[str]:
    dir_path = Path(directory_path)
    if not dir_path.exists():
        raise FileNotFoundError(f"Directory not found: {directory_path}")
    xml_files = list(dir_path.glob("*.xml"))
    return sorted([str(file) for file in xml_files])

def process_xml_entries(xml_files: list[str]) -> List[Dict[str, Any]]:
    results = []
    
    for xml_file in xml_files:
        try:
            tree = ET.parse(xml_file)
            root = tree.getroot()
            entries = root.findall('.//DictionaryEntry')
            
            print(f"Processing file: {xml_file}")
            print(f"Found {len(entries)} DictionaryEntry elements")
            
            for entry in entries:
                entry_dict = {
                    'suru_id': entry.get('id'),
                    'headword': None,
                    'subcategorisation': None,
                    'ks': None,
                    'seealso': None,
                    'translations': [],
                    'sense_groups': []
                }
                
                # Process HeadwordCtn
                headword_ctn = entry.find('.//HeadwordCtn')
                if headword_ctn is not None:
                    headword = headword_ctn.find('Headword')
                    if headword is not None:
                        entry_dict['headword'] = headword.text
                    
                    subcat = headword_ctn.find('Subcategorisation')
                    if subcat is not None:
                        entry_dict['subcategorisation'] = subcat.text
                    
                    ks = headword_ctn.find('SeeAlso')
                    if ks is not None:
                        entry_dict['ks'] = ks.get('style', '')
                
                seealso = entry.find('.//SeeAlso/Ptr')
                if seealso is not None and seealso.get('style') == 'viittaus':
                    entry_dict['seealso'] = seealso.text
                    print(f"SeeAlso: {seealso.text}")

                translation_blocks = entry.findall('.//TranslationBlock')
                for translation_block in translation_blocks:
                    translations = translation_block.findall('.//TranslationCtn/Translation')
                    translations_list = [trans.text for trans in translations if trans.text]
                    if translations_list:
                        entry_dict['translations'].append(translations_list)

                # Process SenseGrp
                sense_groups = entry.findall('.//SenseGrp')
                for sense_group in sense_groups:
                    translations = sense_group.findall('.//TranslationCtn')
                    translations_list = [trans.text for trans in translations if trans.text]
                    if translations_list:
                        entry_dict['sense_groups'].append(translations_list)
                
                results.append(entry_dict)
                
        except ET.ParseError as e:
            print(f"Error parsing {xml_file}: {e}")
        except Exception as e:
            print(f"Error processing {xml_file}: {e}")
    
    return results

def save_to_xlsx(results: List[Dict[str, Any]], output_file: str) -> None:
    flat_data = []
    for entry in results:
        # Create a base entry with the main fields
        base_entry = {
            'suru_id': entry['suru_id'],
            'headword': entry['headword'],
            'subcategorisation': entry['subcategorisation'],
            'ks': entry['ks'],
            'seealso': entry['seealso']
        }
        
        # Combine all translations into a single string
        all_translations = []
        for trans_list in entry['translations']:
            all_translations.extend(trans_list)
        base_entry['translations'] = '; '.join(all_translations)
        
        # Combine all sense groups into a single string
        all_senses = []
        for sense_list in entry['sense_groups']:
            all_senses.extend(sense_list)
        base_entry['sense_groups'] = '; '.join(all_senses)
            
        flat_data.append(base_entry)
    
    # Create DataFrame and save to Excel
    df = pd.DataFrame(flat_data)
    df.to_excel(output_file, index=False)
    print(f"Results saved to {output_file}")

xml_files = get_xml_files("suru")
results = process_xml_entries(xml_files)

print("First 5 results:")
for result in results[:5]:
    print(result)

print(f"Total results: {len(results)}")

# Count entries with 'ks' value
ks_count = sum(1 for result in results if result['ks'] is not None)
print(f"Number of entries with 'ks' value: {ks_count}")

# Count entries with 'seealso' value
seealso_count = sum(1 for result in results if result['seealso'] is not None)
print(f"Number of entries with 'seealso' value: {seealso_count}")

# Count entries with translations
translations_count = sum(1 for result in results if result['translations'])
print(f"Number of entries with translations: {translations_count}")

# Count entries with sense_groups
sense_groups_count = sum(1 for result in results if result['sense_groups'])
print(f"Number of entries with sense_groups: {sense_groups_count}")

save_to_xlsx(results, "03_suru.xlsx")