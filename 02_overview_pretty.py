import os
import xml.etree.ElementTree as ET
import xml.dom.minidom

def save_xml_pretty(input_file, output_dir):
    # Write pretty XML to file
    try:
        tree = ET.parse(input_file)
        
        xml_str = ET.tostring(tree.getroot(), encoding='unicode')
        dom = xml.dom.minidom.parseString(xml_str)
        pretty_xml = dom.toprettyxml(indent="    ")
        
        base_name = os.path.basename(input_file)
        output_file = os.path.join(output_dir, base_name)
        

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(pretty_xml)
            
        #print(f"Successfully pretty printed: {base_name}")
        
    except Exception as e:
        print(f"Error processing {input_file}: {str(e)}")

def iterate_xml_files(directory='.'):
    # Get all XML files in the directory and sort them alphabetically
    xml_files = sorted([f for f in os.listdir(directory) if f.endswith('.xml')])
    
    if not xml_files:
        print("No XML files found in the directory.")
        return
    
    total_items = 0
    
    # Create output directory if it doesn't exist
    output_dir = 'suru_pretty'
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    print(f"Prettified xml files will be saved in: {output_dir}")

    # Analyze each XML file
    for xml_file in xml_files:
        try:
            # Parse the XML file
            tree = ET.parse(os.path.join(directory, xml_file))
            root = tree.getroot()
            
            # Count DictionaryEntry elements in the XML file
            item_count = len(root.findall(".//DictionaryEntry"))
            
            print(f"{xml_file}, DictionaryEntry tags: {item_count}")
            total_items += item_count
            
            # Pretty print the XML file
            save_xml_pretty(os.path.join(directory, xml_file), output_dir)
            
        except ET.ParseError as e:
            print(f"Error parsing {xml_file}: {str(e)}")
        except Exception as e:
            print(f"Error processing {xml_file}: {str(e)}")

    print(f"Total DictionaryEntry items: {total_items} in {len(xml_files)} files")

def collect_tags(element):
    """Recursively collect unique tags and their structure from the XML element."""
    tag_structure = {}
    for child in element:
        tag_structure[child.tag] = collect_tags(child)  # Recur for sub-children
    return tag_structure

def write_template(tag_structure, file, indent=0):
    """Write the hierarchical template to the file."""
    for tag, children in tag_structure.items():
        file.write('  ' * indent + f'<{tag}>\n')
        if children:  # If there are sub-children, write them recursively
            write_template(children, file, indent + 1)
        file.write('  ' * indent + f'</{tag}>\n')

import os
import xml.etree.ElementTree as ET

def collect_tags(element):
    """
    Rekursivt samlar in taggstruktur.
    Returnerar en nästlad dict där varje tagg mappas till sina barn.
    """
    structure = {}
    for child in element:
        structure.setdefault(child.tag, {})
        child_structure = collect_tags(child)
        structure[child.tag] = merge_structures(structure[child.tag], child_structure)
    return structure

def merge_structures(base, new):
    """
    Rekursiv sammanslagning av två nästlade dict-strukturer.
    """
    for key, value in new.items():
        if key in base:
            base[key] = merge_structures(base[key], value)
        else:
            base[key] = value
    return base

def write_template(structure, f, indent=0):
    """
    Skriver ut XML-struktur med indrag.
    """
    spacing = '  ' * indent
    for tag, children in structure.items():
        f.write(f"{spacing}<{tag}>\n")
        write_template(children, f, indent + 1)
        f.write(f"{spacing}</{tag}>\n")

def create_structure_overview(input_dir_path="suru"):
    master_structure = {}
    
    for filename in sorted(f for f in os.listdir(input_dir_path) if f.endswith('.xml')):
        file_path = os.path.join(input_dir_path, filename)
        print(f'Processing for structure overview: {file_path}')
        tree = ET.parse(file_path)
        root = tree.getroot()

        for entry in root.findall('.//DictionaryEntry'):
            entry_structure = collect_tags(entry)
            master_structure = merge_structures(master_structure, entry_structure)

    with open('02_xml_structure.xml', 'w', encoding='utf-8') as f:
        f.write('<DictionaryEntry>\n')
        write_template(master_structure, f, indent=1)
        f.write('</DictionaryEntry>\n')

    print("Structure overview created: 02_xml_structure.xml")


if __name__ == "__main__":
    path = "suru"
    iterate_xml_files(path) # analyze and prettify 
    create_structure_overview(path) # create a structure overview