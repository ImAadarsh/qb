import re
import xml.etree.ElementTree as ET
import xml.dom.minidom as minidom
import os
import sys

def fix_xml_file(input_xml, output_xml=None):
    """
    Direct fixes for the malformed XML file
    """
    if output_xml is None:
        output_xml = input_xml.replace('.xml', '_fixed.xml')
    
    print(f"Loading XML file: {input_xml}")
    try:
        tree = ET.parse(input_xml)
        root = tree.getroot()
    except Exception as e:
        print(f"Error loading XML: {e}")
        return False
    
    # Process each section
    for section in root.findall('section'):
        section_name = section.get('name')
        print(f"Processing section: {section_name}")
        
        # Track questions to remove (those that are actually options of previous questions)
        questions_to_remove = []
        prev_question = None
        
        # First pass: fix individual questions
        for question in section.findall('question'):
            q_num = question.get('number')
            text_elem = question.find('text')
            options_elem = question.find('options')
            
            if text_elem is None or options_elem is None:
                continue
            
            # Original values
            q_text = text_elem.text or ""
            options = []
            for opt in options_elem.findall('option'):
                letter = opt.get('letter')
                text = opt.text or ""
                options.append((letter, text))
            
            print(f"Question {q_num}: {q_text[:40]}...")
            
            # Fix 1: For questions with numbered options in the text
            numbered_opts_match = re.search(r'(.*?)(?:\n\s*1[).]\s+(.*?))?(?:\n\s*2[).]\s+(.*?))?(?:\n\s*3[).]\s+(.*?))?$', q_text, re.DOTALL)
            if numbered_opts_match and (numbered_opts_match.group(2) or numbered_opts_match.group(3) or numbered_opts_match.group(4)):
                print(f"  Fixing numbered options for question {q_num}")
                # Extract the actual question text and options
                new_text = numbered_opts_match.group(1).strip()
                new_options = []
                
                if numbered_opts_match.group(2):
                    new_options.append(("a", numbered_opts_match.group(2).strip()))
                if numbered_opts_match.group(3):
                    new_options.append(("b", numbered_opts_match.group(3).strip()))
                if numbered_opts_match.group(4):
                    new_options.append(("c", numbered_opts_match.group(4).strip()))
                
                # Update the question
                text_elem.text = new_text
                
                # Clear existing options
                for child in list(options_elem):
                    options_elem.remove(child)
                    
                # Add new options
                for letter, text in new_options:
                    opt_elem = ET.SubElement(options_elem, "option", letter=letter)
                    opt_elem.text = text
                
                # Update our local copy
                q_text = new_text
                options = new_options
            
            # Fix 2: Check for options with full questions or question fragments
            for i, (letter, opt_text) in enumerate(options):
                # Skip placeholder options
                if opt_text in ["Option A", "Option B", "Option C"]:
                    continue
                
                # Check if this option contains question text with a/b/c options
                embedded_opts_match = re.search(r'(.*?)(?:\s*|\n)(?:([a-c])\)|\(([a-c])\))\s+(.*?)(?:\s*|\n)(?:([a-c])\)|\(([a-c])\))\s+(.*?)(?:\s*|\n)?(?:(?:([a-c])\)|\(([a-c])\))\s+(.*?))?$', opt_text)
                if embedded_opts_match:
                    print(f"  Fixing embedded options in option {letter} for question {q_num}")
                    # Extract new question text
                    new_text_part = embedded_opts_match.group(1).strip()
                    
                    # Complete the question text
                    if new_text_part:
                        text_elem.text = (q_text + " " + new_text_part).strip()
                    
                    # Extract embedded options
                    new_options = []
                    for j in range(1, 4):  # For a, b, c
                        letter_idx = 2*j
                        text_idx = letter_idx + 2
                        
                        if letter_idx < len(embedded_opts_match.groups()):
                            option_letter = embedded_opts_match.group(letter_idx) or embedded_opts_match.group(letter_idx+1)
                            if option_letter and text_idx < len(embedded_opts_match.groups()):
                                option_text = embedded_opts_match.group(text_idx)
                                if option_text:
                                    new_options.append((option_letter, option_text.strip()))
                    
                    # Only update if we found at least 2 options
                    if len(new_options) >= 2:
                        # Clear existing options
                        for child in list(options_elem):
                            options_elem.remove(child)
                            
                        # Add new options
                        for opt_letter, opt_text in new_options:
                            opt_elem = ET.SubElement(options_elem, "option", letter=opt_letter)
                            opt_elem.text = opt_text
                        
                        # Update our local copy
                        options = new_options
                        break
            
            # Fix 3: Check for fragmented question text that continues into options
            continuation_found = False
            for i, (letter, opt_text) in enumerate(options):
                # If it's a generic option, skip
                if opt_text in ["Option A", "Option B", "Option C"]:
                    continue
                
                # Is this a continuation of the question text?
                # - Starts with lowercase
                # - No a)/b)/c) format
                # - Doesn't contain common option words like "the" at beginning
                if (opt_text and opt_text[0].islower() and not re.match(r'^[a-z][\)]\s', opt_text) and 
                    not re.match(r'^(the|a|an|that|this|these|those|it|its)\b', opt_text.lower())):
                    print(f"  Fixing text continuation in option {letter} for question {q_num}")
                    # Merge with question text
                    text_elem.text = (q_text + " " + opt_text).strip()
                    
                    # Remove this option
                    options_elem.remove(options_elem.findall('option')[i])
                    continuation_found = True
                    break
            
            if continuation_found:
                # Ensure we have 3 options
                current_options = options_elem.findall('option')
                if len(current_options) < 3:
                    # Add placeholder options for missing ones
                    existing_letters = [opt.get('letter') for opt in current_options]
                    for letter in ['a', 'b', 'c']:
                        if letter not in existing_letters:
                            opt_elem = ET.SubElement(options_elem, "option", letter=letter)
                            opt_elem.text = f"Option {letter.upper()}"
            
            # Remember this question for the second pass
            prev_question = question
        
        # Second pass: Fix specific issues based on question numbers
        for question in section.findall('question'):
            q_num = question.get('number')
            
            # Fix specific issues for section "VISUAL ARTS/PAINTINGS"
            if section_name == "VISUAL ARTS/PAINTINGS":
                # Fix question 2
                if q_num == "2":
                    text_elem = question.find('text')
                    if text_elem is not None and text_elem.text and "Diego Rivera" in text_elem.text:
                        # This is malformed - fix the text
                        text_elem.text = "\"Guernica,\" a powerful anti-war painting depicting the bombing of a Basque town, was created by which influential Spanish artist?"
                        
                        # Fix options
                        options_elem = question.find('options')
                        if options_elem is not None:
                            # Clear existing options
                            for child in list(options_elem):
                                options_elem.remove(child)
                            
                            # Add correct options
                            opt_a = ET.SubElement(options_elem, "option", letter="a")
                            opt_a.text = "Diego Rivera"
                            
                            opt_b = ET.SubElement(options_elem, "option", letter="b")
                            opt_b.text = "Francisco Goya"
                            
                            opt_c = ET.SubElement(options_elem, "option", letter="c")
                            opt_c.text = "Pablo Picasso"
                
                # Fix question 3
                if q_num == "3":
                    text_elem = question.find('text')
                    if text_elem is not None and text_elem.text and "artisti" in text_elem.text:
                        # Fix the typo
                        text_elem.text = "Which artistic style, using small, distinct dots of color applied in patterns to form an image, is famously employed in Georges Seurat's \"A Sunday on La Grande Jatte\"?"
                        
                        # Fix options
                        options_elem = question.find('options')
                        if options_elem is not None:
                            # Clear existing options
                            for child in list(options_elem):
                                options_elem.remove(child)
                            
                            # Add correct options
                            opt_a = ET.SubElement(options_elem, "option", letter="a")
                            opt_a.text = "Pointillism"
                            
                            opt_b = ET.SubElement(options_elem, "option", letter="b")
                            opt_b.text = "Fauvism"
                            
                            opt_c = ET.SubElement(options_elem, "option", letter="c")
                            opt_c.text = "Expressionism"
    
    # Ensure all questions have answers
    for section in root.findall('section'):
        for question in section.findall('question'):
            q_num = question.get('number')
            answer_elem = question.find('answer')
            
            # If no answer or empty answer, add a default
            if answer_elem is None:
                answer_elem = ET.SubElement(question, "answer")
                answer_elem.text = "a"  # Default answer
            elif not answer_elem.text:
                answer_elem.text = "a"  # Default answer
    
    # Pretty print the XML
    rough_string = ET.tostring(root, 'utf-8')
    reparsed = minidom.parseString(rough_string)
    pretty_xml = reparsed.toprettyxml(indent="  ")
    
    # Remove empty lines
    pretty_xml = '\n'.join([line for line in pretty_xml.split('\n') if line.strip()])
    
    # Write to file
    with open(output_xml, 'w', encoding='utf-8') as f:
        f.write(pretty_xml)
    
    print(f"Successfully fixed XML file: {output_xml}")
    return True

def fix_specific_questions(xml_file, output_file=None):
    """
    Fix specific questions that we know are problematic
    """
    if output_file is None:
        output_file = xml_file
    
    # Load XML
    tree = ET.parse(xml_file)
    root = tree.getroot()
    
    # Define fixes for specific questions by section and number
    fixes = {
        "VISUAL ARTS/PAINTINGS": {
            "2": {
                "text": "\"Guernica,\" a powerful anti-war painting depicting the bombing of a Basque town, was created by which influential Spanish artist?",
                "options": [
                    ("a", "Diego Rivera"),
                    ("b", "Francisco Goya"),
                    ("c", "Pablo Picasso")
                ],
                "answer": "c"
            },
            "3": {
                "text": "Which artistic style, using small, distinct dots of color applied in patterns to form an image, is famously employed in Georges Seurat's \"A Sunday on La Grande Jatte\"?",
                "options": [
                    ("a", "Pointillism"),
                    ("b", "Fauvism"),
                    ("c", "Expressionism")
                ],
                "answer": "a"
            },
            # Add more fixes as needed
        }
        # Add more sections as needed
    }
    
    # Apply fixes
    for section in root.findall('section'):
        section_name = section.get('name')
        if section_name in fixes:
            print(f"Applying fixes to section: {section_name}")
            
            for question in section.findall('question'):
                q_num = question.get('number')
                if q_num in fixes[section_name]:
                    fix = fixes[section_name][q_num]
                    print(f"  Fixing question {q_num}")
                    
                    # Fix text
                    if "text" in fix:
                        text_elem = question.find('text')
                        if text_elem is not None:
                            text_elem.text = fix["text"]
                    
                    # Fix options
                    if "options" in fix:
                        options_elem = question.find('options')
                        if options_elem is not None:
                            # Clear existing options
                            for child in list(options_elem):
                                options_elem.remove(child)
                            
                            # Add correct options
                            for letter, text in fix["options"]:
                                opt_elem = ET.SubElement(options_elem, "option", letter=letter)
                                opt_elem.text = text
                    
                    # Fix answer
                    if "answer" in fix:
                        answer_elem = question.find('answer')
                        if answer_elem is None:
                            answer_elem = ET.SubElement(question, "answer")
                        answer_elem.text = fix["answer"]
    
    # Pretty print the XML
    rough_string = ET.tostring(root, 'utf-8')
    reparsed = minidom.parseString(rough_string)
    pretty_xml = reparsed.toprettyxml(indent="  ")
    
    # Remove empty lines
    pretty_xml = '\n'.join([line for line in pretty_xml.split('\n') if line.strip()])
    
    # Write to file
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(pretty_xml)
    
    print(f"Successfully applied specific fixes to: {output_file}")
    return True

if __name__ == "__main__":
    input_xml = "arts_400_quiz.xml"
    output_xml = "arts_400_quiz_fixed.xml"
    
    if len(sys.argv) > 1:
        input_xml = sys.argv[1]
    
    if len(sys.argv) > 2:
        output_xml = sys.argv[2]
    
    # Fix the XML file
    if not fix_xml_file(input_xml, output_xml):
        print("Failed to fix XML file.")
        sys.exit(1)
    
    # Apply specific fixes to known problematic questions
    fix_specific_questions(output_xml)
    
    print("XML fixing completed successfully.") 