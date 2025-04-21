import re
import xml.etree.ElementTree as ET
import xml.dom.minidom as minidom
import os
import sys

def clean_answer_keys(input_xml, output_xml=None):
    """
    Clean questions that are actually answer keys
    """
    if output_xml is None:
        output_xml = input_xml.replace('.xml', '_clean.xml')
    
    print(f"Loading XML file: {input_xml}")
    try:
        tree = ET.parse(input_xml)
        root = tree.getroot()
    except Exception as e:
        print(f"Error loading XML: {e}")
        return False
    
    # Pattern to detect answer-formatted questions
    answer_patterns = [
        r'^Answer:\s*([a-c])\s*-\s*(.*)',
        r'^([a-c])\s*-\s*(.*)',
        r'^([a-c])\)\s*(.*)',
        r'^Answer:\s*([a-c])\s*(.*)',
    ]
    
    # Questions to remove (answer formatted questions)
    questions_to_remove = []
    
    # Process each section
    for section in root.findall('section'):
        section_name = section.get('name')
        print(f"Processing section: {section_name}")
        
        # First find the questions that are actually answers
        for question in section.findall('question'):
            q_num = question.get('number')
            text_elem = question.find('text')
            
            if text_elem is None or not text_elem.text:
                continue
                
            q_text = text_elem.text
            
            # Check if this question is actually an answer
            is_answer = False
            for pattern in answer_patterns:
                match = re.match(pattern, q_text, re.IGNORECASE)
                if match:
                    is_answer = True
                    questions_to_remove.append((section, question))
                    print(f"  Marking question {q_num} for removal: {q_text[:30]}...")
                    break
        
        # Now find the real questions and update their answers
        for question in section.findall('question'):
            q_num = question.get('number')
            text_elem = question.find('text')
            answer_elem = question.find('answer')
            
            if text_elem is None or not text_elem.text:
                continue
            
            q_text = text_elem.text
            
            # Check if this question contains an answer in its text
            for pattern in answer_patterns:
                # Only match at the end of the text
                match = re.search(r'\s' + pattern, q_text, re.IGNORECASE)
                if match:
                    # Remove the answer part from the question text
                    clean_text = q_text[:match.start()]
                    text_elem.text = clean_text.strip()
                    print(f"  Cleaned answer from question {q_num}: {clean_text[:30]}...")
                    break
    
    # Remove the questions that are actually answers
    for section, question in questions_to_remove:
        section.remove(question)
        
    # Ensure all questions have answers and 3 options
    for section in root.findall('section'):
        for question in section.findall('question'):
            q_num = question.get('number')
            answer_elem = question.find('answer')
            options_elem = question.find('options')
            
            # If no answer or empty answer, add a default
            if answer_elem is None:
                answer_elem = ET.SubElement(question, "answer")
                answer_elem.text = "a"  # Default answer
            elif not answer_elem.text:
                answer_elem.text = "a"  # Default answer
            
            # Make sure we have 3 options
            if options_elem is not None:
                current_options = options_elem.findall('option')
                if len(current_options) < 3:
                    # Add placeholder options for missing ones
                    existing_letters = [opt.get('letter') for opt in current_options]
                    for letter in ['a', 'b', 'c']:
                        if letter not in existing_letters:
                            opt_elem = ET.SubElement(options_elem, "option", letter=letter)
                            opt_elem.text = f"Option {letter.upper()}"
                            print(f"  Added missing option {letter} to question {q_num}")
    
    # Pretty print the XML
    rough_string = ET.tostring(root, 'utf-8')
    reparsed = minidom.parseString(rough_string)
    pretty_xml = reparsed.toprettyxml(indent="  ")
    
    # Remove empty lines
    pretty_xml = '\n'.join([line for line in pretty_xml.split('\n') if line.strip()])
    
    # Write to file
    with open(output_xml, 'w', encoding='utf-8') as f:
        f.write(pretty_xml)
    
    print(f"Successfully cleaned answer keys: {output_xml}")
    return True

if __name__ == "__main__":
    input_xml = "arts_400_quiz_fixed.xml"
    output_xml = "arts_400_quiz_clean.xml"
    
    if len(sys.argv) > 1:
        input_xml = sys.argv[1]
    
    if len(sys.argv) > 2:
        output_xml = sys.argv[2]
    
    # Clean answer keys
    if not clean_answer_keys(input_xml, output_xml):
        print("Failed to clean XML file.")
        sys.exit(1)
    
    print("XML cleaning completed successfully.") 