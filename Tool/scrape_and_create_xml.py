import re
import xml.etree.ElementTree as ET
import xml.dom.minidom as minidom
import os
import sys

def extract_questions_and_build_xml(input_file, output_file):
    """
    Read the input file, extract questions and answers, and build an XML structure
    """
    if not os.path.exists(input_file):
        print(f"Input file not found: {input_file}")
        return False
    
    print(f"Processing file: {input_file}")
    print(f"File size: {os.path.getsize(input_file)} bytes")
        
    # Read the content of the file
    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    print(f"Content length: {len(content)} characters")
    
    # Create the root element
    root = ET.Element("quiz")
    
    # Extract major sections (using a more specific pattern to match section headers)
    section_pattern = r'\*\*([\w\s/#]+?)\*\*\s*\n'
    sections = re.split(section_pattern, content)
    
    # Remove empty first element if it exists
    if not sections[0].strip():
        sections = sections[1:]
    
    # Process sections in pairs (section name + content)
    for i in range(0, len(sections), 2):
        if i+1 >= len(sections):
            break
            
        section_name = sections[i].strip()
        section_content = sections[i+1].strip()
        
        # Skip processing answer key sections
        if "ANSWER KEY" in section_name.upper():
            print(f"Found answer key section: {section_name}")
            continue
            
        print(f"Processing section: {section_name}")
        
        # Create section element
        section_elem = ET.SubElement(root, "section", name=section_name)
        
        # Find the corresponding answer key section if it exists
        answer_key_content = ""
        answer_key_pattern = rf'\*\*ANSWER KEY:?\s*{re.escape(section_name)}\*\*\s*([\s\S]*?)(?=\*\*[\w\s/#]+\*\*|\Z)'
        answer_key_match = re.search(answer_key_pattern, content, re.IGNORECASE)
        
        # If answer key not found by exact name, try a more general pattern
        if not answer_key_match:
            answer_key_pattern = r'\*\*ANSWER KEY:?.*?\*\*\s*([\s\S]*?)(?=\*\*[\w\s/#]+\*\*|\Z)'
            answer_key_match = re.search(answer_key_pattern, content, re.IGNORECASE)
        
        answers = {}
        
        if answer_key_match:
            answer_key_content = answer_key_match.group(1).strip()
            
            # Extract answers
            answer_lines = answer_key_content.split('\n')
            
            for line in answer_lines:
                line = line.strip()
                if not line:
                    continue
                    
                # Try different answer format patterns
                answer_patterns = [
                    r'(\d+)\.\s*(?:\(([a-c])\)|([a-c]))\s*(?:-?\s*(.*))?',  # Standard format with parentheses
                    r'(\d+)\.\s*Answer:\s*([a-c])\s*(?:-?\s*(.*))?',         # Format with "Answer: a"
                    r'(\d+)\.\s*\*\*\(([a-c])\)\*\*\s*(?:-?\s*(.*))?',      # Bold format
                    r'(\d+)\.\s*([a-c])\s*-\s*(.*)',                        # Simple format with dash
                ]
                
                for pattern in answer_patterns:
                    answer_match = re.search(pattern, line)
                    if answer_match:
                        q_num = answer_match.group(1)
                        
                        # Handle different group formats based on the pattern
                        if len(answer_match.groups()) >= 3 and answer_match.group(2) and answer_match.group(3):
                            ans_letter = answer_match.group(2) or answer_match.group(3)
                        else:
                            ans_letter = answer_match.group(2)
                            
                        if ans_letter:
                            answers[q_num] = ans_letter
                            print(f"Found answer for question {q_num}: {ans_letter}")
                        break
        
        print(f"Found {len(answers)} answers for section {section_name}")
        
        # Extract questions using a more robust pattern
        question_pattern = r'(\d+)\.\s+([\s\S]*?)(?=\n\s*\d+\.\s+|\Z)'
        question_matches = list(re.finditer(question_pattern, section_content))
        
        for idx, q_match in enumerate(question_matches):
            q_num = q_match.group(1)
            q_text = q_match.group(2).strip()
            
            # Create question element
            question_elem = ET.SubElement(section_elem, "question", number=q_num)
            
            # Create text element first (we'll update it after finding options)
            text_elem = ET.SubElement(question_elem, "text")
            
            # Create options element
            options_elem = ET.SubElement(question_elem, "options")
            
            # Extract options using different approaches
            
            # Approach 1: Look for multiple-choice format (a) Option1 (b) Option2 (c) Option3
            # This handles cases like "(a) Option1 (b) Option2 (c) Option3" in a single line
            options_match = re.search(r'\(?([a-c])\)?\s+(.*?)\s+\(?([a-c])\)?\s+(.*?)\s+\(?([a-c])\)?\s+(.*?)(?=$|\n)', q_text)
            if options_match:
                groups = options_match.groups()
                
                for i in range(0, len(groups), 2):
                    if i < len(groups) and groups[i]:
                        opt_letter = groups[i]
                        opt_text = groups[i+1] if i+1 < len(groups) and groups[i+1] else ""
                        opt_elem = ET.SubElement(options_elem, "option", letter=opt_letter)
                        opt_elem.text = opt_text.strip()
                
                # Update question text (everything before the options)
                options_start = options_match.start()
                text_elem.text = q_text[:options_start].strip()
                
                continue  # Skip other approaches if this one worked
            
            # Approach 2: Look for options in numbered or lettered list format
            # a) Option1 
            # b) Option2
            # c) Option3
            option_patterns = [
                r'(?:^|\n)\s*([a-c])\)\s+(.*?)(?=\s+(?:[a-c]\)|\d+\.|\Z))',  # Standard format: a) Option
                r'(?:^|\n)\s*\(([a-c])\)\s+(.*?)(?=\s+(?:\([a-c]\)|\d+\.|\Z))',  # Parentheses format: (a) Option
                r'(?:^|\n)\s*([1-3])\.?\s+(.*?)(?=\s+(?:[1-3]\.|\([a-c]\)|\Z))'  # Numeric format: 1. Option or 1 Option
            ]
            
            options_found = False
            first_option_start = None
            found_options = []
            
            for pattern in option_patterns:
                option_matches = list(re.finditer(pattern, q_text, re.DOTALL))
                if option_matches:
                    for opt_match in option_matches:
                        opt_id, opt_text = opt_match.groups()
                        
                        # Convert numeric options (1,2,3) to alphabetic (a,b,c) if needed
                        if opt_id in '123':
                            opt_letter = chr(ord('a') + int(opt_id) - 1)  # 1->a, 2->b, 3->c
                        else:
                            opt_letter = opt_id
                            
                        found_options.append((opt_letter, opt_text.strip()))
                        
                        # Record the start of the first option to separate question text
                        if first_option_start is None:
                            first_option_start = opt_match.start()
                    
                    options_found = True
                    break  # Stop if we found options with this pattern
            
            # If we found options, add them to the XML and update question text
            if options_found and first_option_start is not None:
                # Add options to XML
                for opt_letter, opt_text in found_options:
                    opt_elem = ET.SubElement(options_elem, "option", letter=opt_letter)
                    opt_elem.text = opt_text
                
                # Update question text (everything before the options)
                text_elem.text = q_text[:first_option_start].strip()
                
                continue  # Skip other approaches if this one worked
            
            # Approach 3: Handle questions like "Which is correct? a. Option1 b. Option2 c. Option3"
            # or "1) Option1 2) Option2 3) Option3"
            options_match = re.search(r'([a-c])[).]\s+(.*?)\s+([a-c])[).]\s+(.*?)\s+([a-c])[).]\s+(.*?)(?=$|\n)', q_text)
            if options_match:
                groups = options_match.groups()
                
                for i in range(0, len(groups), 2):
                    if i < len(groups) and groups[i]:
                        opt_letter = groups[i]
                        opt_text = groups[i+1] if i+1 < len(groups) and groups[i+1] else ""
                        opt_elem = ET.SubElement(options_elem, "option", letter=opt_letter)
                        opt_elem.text = opt_text.strip()
                
                # Update question text (everything before the options)
                options_start = options_match.start()
                text_elem.text = q_text[:options_start].strip()
                
                continue  # Skip other approaches if this one worked
            
            # Approach 4: For sections like ARTS MIXED BAG where options are explicitly labeled
            options_match = re.search(r'\(\s*([a-c])\s*\)\s*(\S.*?)(?:\s*\(\s*([a-c])\s*\)\s*(\S.*?))?(?:\s*\(\s*([a-c])\s*\)\s*(\S.*?))?', q_text, re.DOTALL)
            if options_match:
                groups = options_match.groups()
                for i in range(0, len(groups), 2):
                    if i < len(groups) and groups[i]:
                        opt_letter = groups[i]
                        opt_text = groups[i+1] if i+1 < len(groups) and groups[i+1] else ""
                        opt_elem = ET.SubElement(options_elem, "option", letter=opt_letter)
                        opt_elem.text = opt_text.strip()
                
                # Update question text (everything before the options)
                options_start = options_match.start()
                text_elem.text = q_text[:options_start].strip()
            else:
                # Default case: No options found or couldn't parse them
                # Just use the whole text as question text
                text_elem.text = q_text
            
            # For consistency, add default options if we didn't find any
            if len(options_elem) == 0:
                # Add standard options a, b, c if none were found but we expect them
                standard_options = [
                    ("a", "Option A"),
                    ("b", "Option B"),
                    ("c", "Option C")
                ]
                
                for opt_letter, opt_text in standard_options:
                    opt_elem = ET.SubElement(options_elem, "option", letter=opt_letter)
                    opt_elem.text = opt_text
            
            # Set answer if available
            answer_elem = ET.SubElement(question_elem, "answer")
            if q_num in answers:
                answer_elem.text = answers[q_num]
                print(f"Set answer for question {q_num}: {answers[q_num]}")
    
    # Pretty print the XML
    rough_string = ET.tostring(root, 'utf-8')
    reparsed = minidom.parseString(rough_string)
    pretty_xml = reparsed.toprettyxml(indent="  ")
    
    # Remove empty lines
    pretty_xml = '\n'.join([line for line in pretty_xml.split('\n') if line.strip()])
    
    # Write to file
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(pretty_xml)
    
    print(f"Successfully created XML file: {output_file}")
    print(f"Output file size: {os.path.getsize(output_file)} bytes")
    return True

def create_example_xml(output_file):
    """
    Create an example XML file with a few questions
    """
    # Create root element
    root = ET.Element("quiz")
    
    # Visual Arts section
    visual_arts = ET.SubElement(root, "section", name="VISUAL ARTS/PAINTINGS")
    
    # Question 1
    q1 = ET.SubElement(visual_arts, "question", number="1")
    
    q1_text = ET.SubElement(q1, "text")
    q1_text.text = "Which art movement, characterized by dreamlike imagery and irrational scenes, is exemplified by Salvador Dalí's \"The Persistence of Memory,\" featuring melting clocks?"
    
    q1_options = ET.SubElement(q1, "options")
    ET.SubElement(q1_options, "option", letter="a").text = "Impressionism"
    ET.SubElement(q1_options, "option", letter="b").text = "Surrealism"
    ET.SubElement(q1_options, "option", letter="c").text = "Cubism"
    
    q1_answer = ET.SubElement(q1, "answer")
    q1_answer.text = "b"
    
    # Question 2
    q2 = ET.SubElement(visual_arts, "question", number="2")
    
    q2_text = ET.SubElement(q2, "text")
    q2_text.text = "\"Guernica,\" a powerful anti-war painting depicting the bombing of a Basque town, was created by which influential Spanish artist?"
    
    q2_options = ET.SubElement(q2, "options")
    ET.SubElement(q2_options, "option", letter="a").text = "Diego Rivera"
    ET.SubElement(q2_options, "option", letter="b").text = "Francisco Goya"
    ET.SubElement(q2_options, "option", letter="c").text = "Pablo Picasso"
    
    q2_answer = ET.SubElement(q2, "answer")
    q2_answer.text = "c"
    
    # Literature section
    literature = ET.SubElement(root, "section", name="LITERATURE")
    
    # Question 1
    q1 = ET.SubElement(literature, "question", number="1")
    
    q1_text = ET.SubElement(q1, "text")
    q1_text.text = "Who wrote the epic poem \"The Aeneid\", and what is its significance in Roman literature?"
    
    q1_options = ET.SubElement(q1, "options")
    ET.SubElement(q1_options, "option", letter="a").text = "Virgil"
    ET.SubElement(q1_options, "option", letter="b").text = "Homer"
    ET.SubElement(q1_options, "option", letter="c").text = "Ovid"
    
    q1_answer = ET.SubElement(q1, "answer")
    q1_answer.text = "a"
    
    # Pretty print the XML
    rough_string = ET.tostring(root, 'utf-8')
    reparsed = minidom.parseString(rough_string)
    pretty_xml = reparsed.toprettyxml(indent="  ")
    
    # Write to file
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(pretty_xml)
    
    print(f"Created example XML file: {output_file}")
    return True

def manual_post_process_answers(xml_file, output_file=None):
    """
    Post-process an XML file to fix common issues with answers
    """
    if not output_file:
        output_file = xml_file
        
    if not os.path.exists(xml_file):
        print(f"XML file not found: {xml_file}")
        return False
        
    # Parse the XML
    tree = ET.parse(xml_file)
    root = tree.getroot()
    
    # Hardcoded answers from the answer keys
    section_answers = {
        "VISUAL ARTS/PAINTINGS": {
            "1": "b", "2": "c", "3": "a", "4": "b", "5": "c",
            "6": "b", "7": "b", "8": "c", "9": "a", "10": "b",
            "11": "b", "12": "b", "13": "b", "14": "b", "15": "b",
            "16": "b", "17": "b", "18": "b", "19": "b", "20": "b",
            "21": "b", "22": "b", "23": "b", "24": "a", "25": "a",
            "26": "b", "27": "b", "28": "b", "29": "b", "30": "b",
            "31": "a", "32": "b", "33": "c", "34": "a", "35": "b",
            "36": "b", "37": "b", "38": "b", "39": "a", "40": "b",
            "41": "b", "42": "b", "43": "c", "44": "a", "45": "a",
            "46": "b", "47": "c", "48": "c", "49": "a", "50": "c"
        },
        "LITERATURE": {
            "1": "a", "2": "a", "3": "a", "4": "a", "5": "a",
            "6": "a", "7": "a", "8": "a", "9": "a", "10": "a",
            "11": "a", "12": "a", "13": "a", "14": "a", "15": "a",
            "16": "b", "17": "a", "18": "a", "19": "a", "20": "a",
            "21": "a", "22": "a", "23": "a", "24": "a", "25": "a",
            "26": "a", "27": "a", "28": "a", "29": "a", "30": "a",
            "31": "a", "32": "a", "33": "a", "34": "a", "35": "a",
            "36": "a", "37": "a", "38": "a", "39": "a", "40": "a",
            "41": "a", "42": "a", "43": "a", "44": "a", "45": "a",
            "46": "a", "47": "a", "48": "a", "49": "a", "50": "a"
        },
        "FILMS AND MEDIA": {
            "1": "c", "2": "a", "3": "a", "4": "a", "5": "a",
            "6": "a", "7": "c", "8": "a", "9": "a", "10": "a",
            "11": "a", "12": "a", "13": "a", "14": "a", "15": "a",
            "16": "a", "17": "a", "18": "a", "19": "a", "20": "a",
            "21": "a", "22": "c", "23": "a", "24": "a", "25": "a",
            "26": "a", "27": "a", "28": "a", "29": "a", "30": "a",
            "31": "a", "32": "a", "33": "c", "34": "a", "35": "a",
            "36": "a", "37": "a", "38": "a", "39": "a", "40": "a",
            "41": "a", "42": "a", "43": "a", "44": "a", "45": "a",
            "46": "a", "47": "a", "48": "a", "49": "a", "50": "c"
        },
        "Pop Culture": {
            "1": "c", "2": "a", "3": "b", "4": "b", "5": "b",
            "6": "b", "7": "b", "8": "a", "9": "a", "10": "b",
            "11": "a", "12": "b", "13": "a", "14": "b", "15": "b",
            "16": "a", "17": "a", "18": "b", "19": "a", "20": "a",
            "21": "b", "22": "b", "23": "a", "24": "b", "25": "a",
            "26": "b", "27": "c", "28": "a", "29": "a", "30": "a",
            "31": "a", "32": "a", "33": "a", "34": "a", "35": "a",
            "36": "b", "37": "a", "38": "b", "39": "b", "40": "b",
            "41": "b", "42": "a", "43": "b", "44": "b", "45": "b",
            "46": "a", "47": "b", "48": "c", "49": "a", "50": "a"
        }
    }
    
    # Hardcoded options for specific sections
    section_options = {
        "VISUAL ARTS/PAINTINGS": {
            "1": [
                ("a", "Impressionism"),
                ("b", "Surrealism"),
                ("c", "Cubism")
            ],
            # Add more as needed
        }
    }
    
    # Update answers
    for section in root.findall('section'):
        section_name = section.get('name')
        
        # Apply hardcoded options if available
        if section_name in section_options:
            print(f"Updating options for section: {section_name}")
            for question in section.findall('question'):
                q_num = question.get('number')
                if q_num in section_options[section_name]:
                    options_elem = question.find('options')
                    if options_elem is not None:
                        # Clear existing options
                        for child in list(options_elem):
                            options_elem.remove(child)
                            
                        # Add new options
                        for opt_letter, opt_text in section_options[section_name][q_num]:
                            opt_elem = ET.SubElement(options_elem, "option", letter=opt_letter)
                            opt_elem.text = opt_text
                        
                        print(f"  Updated options for question {q_num}")
        
        # Apply hardcoded answers if available
        if section_name in section_answers:
            print(f"Updating answers for section: {section_name}")
            for question in section.findall('question'):
                q_num = question.get('number')
                if q_num in section_answers[section_name]:
                    answer = question.find('answer')
                    if answer is not None:
                        answer.text = section_answers[section_name][q_num]
                        print(f"  Updated answer for question {q_num}: {section_answers[section_name][q_num]}")
    
    # Pretty print the XML
    rough_string = ET.tostring(root, 'utf-8')
    reparsed = minidom.parseString(rough_string)
    pretty_xml = reparsed.toprettyxml(indent="  ")
    
    # Remove empty lines
    pretty_xml = '\n'.join([line for line in pretty_xml.split('\n') if line.strip()])
    
    # Write to file
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(pretty_xml)
    
    print(f"Successfully updated answers in: {output_file}")
    return True

def manual_update_options(xml_file, output_file=None):
    """
    Manually adds all three options (a,b,c) to every question that doesn't have them
    """
    if not output_file:
        output_file = xml_file
        
    if not os.path.exists(xml_file):
        print(f"XML file not found: {xml_file}")
        return False
        
    # Parse the XML
    tree = ET.parse(xml_file)
    root = tree.getroot()
    
    # Default options to use when missing
    default_options = {
        "VISUAL ARTS/PAINTINGS": {
            "a": "Option A",
            "b": "Option B", 
            "c": "Option C"
        },
        "LITERATURE": {
            "a": "Option A",
            "b": "Option B",
            "c": "Option C"
        },
        # Add more for other sections as needed
    }
    
    # Process all questions
    for section in root.findall('section'):
        section_name = section.get('name')
        print(f"Processing options for section: {section_name}")
        
        for question in section.findall('question'):
            q_num = question.get('number')
            options_elem = question.find('options')
            
            # Collect existing options
            existing_options = {}
            for opt in options_elem.findall('option'):
                letter = opt.get('letter')
                text = opt.text
                existing_options[letter] = text
            
            # If we're missing options, add them
            if len(existing_options) < 3:
                # Get default options for this section, or use generic ones
                section_defaults = default_options.get(section_name, {
                    "a": "Option A",
                    "b": "Option B",
                    "c": "Option C"
                })
                
                # Add missing options
                for letter in ['a', 'b', 'c']:
                    if letter not in existing_options:
                        opt_elem = ET.SubElement(options_elem, "option", letter=letter)
                        opt_elem.text = section_defaults[letter]
                        print(f"  Added missing option {letter} to question {q_num}")
    
    # Pretty print the XML
    rough_string = ET.tostring(root, 'utf-8')
    reparsed = minidom.parseString(rough_string)
    pretty_xml = reparsed.toprettyxml(indent="  ")
    
    # Remove empty lines
    pretty_xml = '\n'.join([line for line in pretty_xml.split('\n') if line.strip()])
    
    # Write to file
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(pretty_xml)
    
    print(f"Successfully updated options in: {output_file}")
    return True

def fix_malformed_questions(xml_file, output_file=None):
    """
    Fix common issues with question text and options:
    1. Question text incorrectly split into options
    2. Options containing parts of the question
    3. Numbered options in question text not properly parsed
    """
    if not output_file:
        output_file = xml_file
        
    if not os.path.exists(xml_file):
        print(f"XML file not found: {xml_file}")
        return False
        
    # Parse the XML
    tree = ET.parse(xml_file)
    root = tree.getroot()
    
    for section in root.findall('section'):
        section_name = section.get('name')
        print(f"Fixing malformed questions in section: {section_name}")
        
        for question in section.findall('question'):
            q_num = question.get('number')
            text_elem = question.find('text')
            options_elem = question.find('options')
            
            if text_elem is None or options_elem is None:
                continue
                
            # Get current text and options
            q_text = text_elem.text or ""
            options = []
            for opt in options_elem.findall('option'):
                letter = opt.get('letter')
                text = opt.text or ""
                options.append((letter, text))
            
            # Case 1: Look for questions with numbered options in the text (1, 2, 3)
            numbered_options_match = re.search(r'(.*?)(?:\n\s*1[).]\s+(.*?))?(?:\n\s*2[).]\s+(.*?))?(?:\n\s*3[).]\s+(.*?))?$', q_text, re.DOTALL)
            if numbered_options_match and (numbered_options_match.group(2) or numbered_options_match.group(3) or numbered_options_match.group(4)):
                # Extract the actual question text and options
                new_text = numbered_options_match.group(1).strip()
                new_options = []
                
                if numbered_options_match.group(2):
                    new_options.append(("a", numbered_options_match.group(2).strip()))
                if numbered_options_match.group(3):
                    new_options.append(("b", numbered_options_match.group(3).strip()))
                if numbered_options_match.group(4):
                    new_options.append(("c", numbered_options_match.group(4).strip()))
                
                # Update the question
                text_elem.text = new_text
                
                # Clear existing options
                for child in list(options_elem):
                    options_elem.remove(child)
                    
                # Add new options
                for letter, text in new_options:
                    opt_elem = ET.SubElement(options_elem, "option", letter=letter)
                    opt_elem.text = text
                
                print(f"  Fixed numbered options for question {q_num}")
                continue
            
            # Case 2: Check if option contains question text (e.g., when the option starts with the question)
            for i, (letter, opt_text) in enumerate(options):
                # Check if this option looks like it contains a full question
                if re.search(r'\?|\.$', opt_text) and any(keyword in opt_text.lower() for keyword in ["who", "what", "where", "when", "which", "how", "why"]):
                    # This option likely contains question text
                    # Try to find actual options within it
                    parts_match = re.search(r'(.*?)(?:([a-c])\)|\(([a-c])\))\s+(.*?)(?:([a-c])\)|\(([a-c])\))\s+(.*?)(?:([a-c])\)|\(([a-c])\))\s+(.*?)$', opt_text)
                    if parts_match:
                        # Extract question text and new options
                        new_text_part = parts_match.group(1).strip()
                        
                        # Update question text
                        text_elem.text = (q_text + " " + new_text_part).strip()
                        
                        # Determine option letters and texts
                        new_options = []
                        for j in range(1, 4):  # For each of the 3 potential options
                            idx = 2*j
                            letter = parts_match.group(idx) or parts_match.group(idx+1)
                            if letter and idx+2 <= len(parts_match.groups()):
                                text = parts_match.group(idx+2)
                                if text:
                                    new_options.append((letter, text.strip()))
                        
                        # If we found new options, update the option elements
                        if new_options:
                            # Clear existing options
                            for child in list(options_elem):
                                options_elem.remove(child)
                                
                            # Add new options
                            for letter, text in new_options:
                                opt_elem = ET.SubElement(options_elem, "option", letter=letter)
                                opt_elem.text = text
                            
                            print(f"  Fixed options within question text for question {q_num}")
                            break
            
            # Case 3: Check for options that are continuations of the question text
            continuations = []
            for i, (letter, opt_text) in enumerate(options):
                # If option starts with lowercase and doesn't look like a standalone option
                if opt_text and opt_text[0].islower() and not re.match(r'^[a-z][\)]\s', opt_text):
                    continuations.append((i, letter, opt_text))
            
            if continuations:
                # Merge continuations into question text
                for i, letter, opt_text in continuations:
                    q_text = (q_text + " " + opt_text).strip()
                
                # Update question text
                text_elem.text = q_text
                
                # Remove the continuation options
                for i, letter, _ in reversed(continuations):
                    options_elem.remove(options_elem.findall('option')[i])
                
                print(f"  Fixed continuations for question {q_num}")
            
            # Case 4: Look for options with embedded a) b) c) pattern
            for i, (letter, opt_text) in enumerate(options):
                embedded_match = re.search(r'(.*?)([a-c])\)(.*?)([a-c])\)(.*?)(?:([a-c])\)(.*?))?$', opt_text)
                if embedded_match:
                    # We have something like "...a) Option1 b) Option2 c) Option3"
                    # Extract new options
                    new_options = []
                    
                    for j in range(1, 4):  # For a, b, c
                        idx = 2*j
                        if idx < len(embedded_match.groups()) and embedded_match.group(idx):
                            letter = embedded_match.group(idx)
                            text_idx = idx + 1
                            if text_idx < len(embedded_match.groups()) and embedded_match.group(text_idx):
                                new_options.append((letter, embedded_match.group(text_idx).strip()))
                    
                    # If we found embedded options
                    if len(new_options) >= 2:
                        # Update question text
                        q_text = (q_text + " " + embedded_match.group(1)).strip()
                        text_elem.text = q_text
                        
                        # Clear existing options
                        for child in list(options_elem):
                            options_elem.remove(child)
                            
                        # Add new options
                        for letter, text in new_options:
                            opt_elem = ET.SubElement(options_elem, "option", letter=letter)
                            opt_elem.text = text
                        
                        print(f"  Fixed embedded options for question {q_num}")
                        break
    
    # Pretty print the XML
    rough_string = ET.tostring(root, 'utf-8')
    reparsed = minidom.parseString(rough_string)
    pretty_xml = reparsed.toprettyxml(indent="  ")
    
    # Remove empty lines
    pretty_xml = '\n'.join([line for line in pretty_xml.split('\n') if line.strip()])
    
    # Write to file
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(pretty_xml)
    
    print(f"Successfully fixed malformed questions in: {output_file}")
    return True

if __name__ == "__main__":
    # Possible file paths to try
    possible_paths = [
        "/Users/akumargupta/Documents/My_EXPERIMENTS/qb/Question/arts_chapter.md",
        "/Users/akumargupta/Documents/My_EXPERIMENTS/qb/Question/ARTS 400 questions.md",
        "Question/ARTS 400 questions.md",
        "Question/arts_chapter.md",
        "../Question/ARTS 400 questions.md"
    ]
    
    output_file = "arts_400_quiz.xml"
    success = False
    
    # Try each path until one works
    for input_file in possible_paths:
        print(f"Trying input file: {input_file}")
        if os.path.exists(input_file):
            print(f"Found file: {input_file}")
            try:
                success = extract_questions_and_build_xml(input_file, output_file)
                if success:
                    print(f"Successfully extracted questions from {input_file}")
                    
                    # Fix malformed questions and options
                    print("Fixing malformed questions and options...")
                    fix_malformed_questions(output_file)
                    
                    # Post-process to ensure all questions have 3 options
                    print("Adding missing options to all questions...")
                    manual_update_options(output_file)
                    
                    # Post-process to fix answers
                    print("Running post-processing to fix answers...")
                    manual_post_process_answers(output_file)
                    break
            except Exception as e:
                print(f"Error processing {input_file}: {e}")
                import traceback
                traceback.print_exc()
    
    # If all paths failed, create example file
    if not success:
        print("All file paths failed or no questions were extracted.")
        print("Creating example XML instead.")
        create_example_xml("example_" + output_file) 