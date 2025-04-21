import re
import xml.etree.ElementTree as ET
import xml.dom.minidom as minidom

def convert_quiz_doc_to_xml(input_file, output_file):
    """
    Convert the quiz document to XML format
    """
    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Split the content into sections based on headings
    sections = []
    current_section = None
    current_content = []
    
    lines = content.split('\n')
    
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        
        # Check for section headings (they're usually in all caps and/or surrounded by asterisks)
        if line.startswith('**') and line.endswith('**'):
            section_name = line.strip('*').strip()
            
            # If we were already processing a section, save it
            if current_section:
                sections.append((current_section, '\n'.join(current_content)))
            
            # Start a new section
            current_section = section_name
            current_content = []
        
        # Check for answer key sections
        elif line.startswith('**ANSWER KEY:') or line.startswith('**Answer Key:'):
            # If we were already processing a section, save it
            if current_section:
                sections.append((current_section, '\n'.join(current_content)))
            
            # Extract the section name from the answer key heading
            section_name = line.replace('**ANSWER KEY:', '').replace('**Answer Key:', '').strip()
            
            # Start collecting answer key content
            answer_key_content = []
            j = i + 1
            while j < len(lines) and not (lines[j].startswith('**') and lines[j].endswith('**')):
                if lines[j].strip():  # Skip empty lines
                    answer_key_content.append(lines[j].strip())
                j += 1
            
            # Save the answer key as a special section
            sections.append((f"{section_name} ANSWER KEY", '\n'.join(answer_key_content)))
            
            # Move the index past the answer key content
            i = j - 1
        
        # Regular content line
        elif current_section:
            current_content.append(line)
        
        i += 1
    
    # Don't forget the last section
    if current_section and current_content:
        sections.append((current_section, '\n'.join(current_content)))
    
    # Create XML structure
    quiz = ET.Element("quiz")
    
    # Process each section to extract questions, options, and answers
    for section_name, section_content in sections:
        # Skip processing answer key sections for now
        if "ANSWER KEY" in section_name:
            continue
        
        section = ET.SubElement(quiz, "section", name=section_name)
        
        # Extract questions and options using regex
        question_pattern = r'(\d+)\.\s+(.*?)(?=\s+(?:\d+\.|$))'
        option_pattern = r'(?:^|\n)\s*([a-c])\)\s+(.*?)(?=\s+(?:[a-c]\)|$))'
        
        questions = re.findall(question_pattern, section_content, re.DOTALL)
        
        for q_num, q_text in questions:
            question = ET.SubElement(section, "question", number=q_num)
            
            # Clean the question text
            q_text = q_text.strip()
            
            # Extract options if they exist
            options_match = re.findall(option_pattern, q_text, re.DOTALL)
            
            if options_match:
                # Remove options from question text
                q_text = re.sub(r'\s*[a-c]\)\s+.*?(?=\s+[a-c]\)|$)', '', q_text, flags=re.DOTALL).strip()
            
            text_elem = ET.SubElement(question, "text")
            text_elem.text = q_text
            
            options_elem = ET.SubElement(question, "options")
            
            for opt_letter, opt_text in options_match:
                option = ET.SubElement(options_elem, "option", letter=opt_letter)
                option.text = opt_text.strip()
            
            # Add placeholder for answer (to be filled in later)
            answer = ET.SubElement(question, "answer")
            answer.text = ""
    
    # Now process answer key sections to fill in the answers
    for section_name, section_content in sections:
        if "ANSWER KEY" not in section_name:
            continue
        
        original_section_name = section_name.replace(" ANSWER KEY", "")
        
        # Find matching section in the XML
        for section in quiz.findall('section'):
            if section.get('name') == original_section_name:
                # Parse the answer key content
                answer_lines = section_content.split('\n')
                
                for line in answer_lines:
                    line = line.strip()
                    if not line:
                        continue
                    
                    # Try to extract question number and answer
                    match = re.match(r'(\d+)\.\s*(?:\([a-c]\)|[a-c])\s*-?\s*(.*)', line)
                    if match:
                        q_num, ans_text = match.groups()
                        
                        # Extract just the letter answer
                        ans_letter = None
                        letter_match = re.search(r'\(([a-c])\)', line)
                        if letter_match:
                            ans_letter = letter_match.group(1)
                        else:
                            letter_match = re.search(r'^([a-c])\s*-', line)
                            if letter_match:
                                ans_letter = letter_match.group(1)
                        
                        if ans_letter:
                            # Find the corresponding question in the XML
                            for question in section.findall(f"question[@number='{q_num}']"):
                                answer = question.find('answer')
                                if answer is not None:
                                    answer.text = ans_letter
    
    # Pretty print the XML
    rough_string = ET.tostring(quiz, 'utf-8')
    reparsed = minidom.parseString(rough_string)
    pretty_xml = reparsed.toprettyxml(indent="  ")
    
    # Remove empty lines
    pretty_xml = '\n'.join([line for line in pretty_xml.split('\n') if line.strip()])
    
    # Write to file
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(pretty_xml)
    
    return pretty_xml

def extract_questions_manually(input_file, output_file):
    """
    Alternative approach: extract questions manually
    This may be more reliable for structured formats but requires specific format knowledge
    """
    # Create root element
    quiz = ET.Element("quiz")
    
    # Example of manually adding a section with questions
    section = ET.SubElement(quiz, "section", name="VISUAL ARTS/PAINTINGS")
    
    # Question 1
    q1 = ET.SubElement(section, "question", number="1")
    q1_text = ET.SubElement(q1, "text")
    q1_text.text = "Which art movement, characterized by dreamlike imagery and irrational scenes, is exemplified by Salvador Dalí's \"The Persistence of Memory,\" featuring melting clocks?"
    
    q1_options = ET.SubElement(q1, "options")
    q1_opt_a = ET.SubElement(q1_options, "option", letter="a")
    q1_opt_a.text = "Impressionism"
    q1_opt_b = ET.SubElement(q1_options, "option", letter="b")
    q1_opt_b.text = "Surrealism"
    q1_opt_c = ET.SubElement(q1_options, "option", letter="c")
    q1_opt_c.text = "Cubism"
    
    q1_answer = ET.SubElement(q1, "answer")
    q1_answer.text = "b"
    
    # Add more questions...
    
    # Pretty print and save
    rough_string = ET.tostring(quiz, 'utf-8')
    reparsed = minidom.parseString(rough_string)
    pretty_xml = reparsed.toprettyxml(indent="  ")
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(pretty_xml)
    
    return "Created example XML structure"

if __name__ == "__main__":
    # Try to convert the document
    try:
        print("Converting quiz document to XML...")
        convert_quiz_doc_to_xml("Question/ARTS 400 questions.md", "quiz.xml")
        print("Conversion complete! XML saved to quiz.xml")
    except Exception as e:
        print(f"Error during conversion: {e}")
        print("Falling back to manual example...")
        extract_questions_manually("", "example_quiz.xml")
        print("Example XML created as example_quiz.xml") 