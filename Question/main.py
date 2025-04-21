import re
import xml.etree.ElementTree as ET
import xml.dom.minidom as minidom
from pathlib import Path

class QuizConverter:
    def __init__(self, input_file, output_file):
        self.input_file = input_file
        self.output_file = output_file
        self.current_section = None
        self.questions = []
        self.answer_keys = {}
        
    def parse_markdown(self):
        """Parse the markdown file and extract questions, options, and answers."""
        print(f"Parsing markdown file: {self.input_file}")
        
        with open(self.input_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Split content by sections (marked by ** or # headers)
        sections = re.split(r'\*\*(.*?)\*\*|\n# (.*?)\n', content)
        sections = [s for s in sections if s and s.strip()]
        
        i = 0
        while i < len(sections):
            if "ANSWER KEY" in sections[i].upper():
                # Process answer key section
                self.extract_answer_key(sections[i], sections[i+1] if i+1 < len(sections) else "")
                i += 2
            else:
                # Process regular section
                section_name = sections[i].strip()
                if i + 1 < len(sections) and "ANSWER KEY" not in sections[i+1].upper():
                    section_content = sections[i+1]
                    self.process_section(section_name, section_content)
                i += 2
        
        # Match answers to questions
        self.match_answers_to_questions()
        
        print(f"Parsed {len(self.questions)} questions across {len(set(q['section'] for q in self.questions))} sections")
    
    def process_section(self, section_name, content):
        """Process a section of content to extract questions."""
        # Clean section name
        section_name = section_name.replace("**", "").strip()
        self.current_section = section_name
        
        # Split into individual questions
        questions_raw = re.split(r'\n\s*\d+[\.\)]\s+', content)
        questions_raw = [q for q in questions_raw if q and q.strip()]
        
        for i, q_raw in enumerate(questions_raw):
            self.extract_question(q_raw, i+1)
    
    def extract_question(self, question_text, question_number):
        """Extract a question, its options, and potentially embedded answer."""
        # Try to match question with options in various formats
        option_pattern = r'(?:a\)|a\s*\)|1\)|1\.\s*|\(a\)|\s+a\s+)(.*?)(?:b\)|b\s*\)|2\)|2\.\s*|\(b\)|\s+b\s+)(.*?)(?:c\)|c\s*\)|3\)|3\.\s*|\(c\)|\s+c\s+)(.*?)(?:\n|$)'
        
        match = re.search(option_pattern, question_text, re.DOTALL | re.IGNORECASE)
        
        if match:
            # Extract question text (everything before the first option)
            q_text = question_text[:match.start()].strip()
            
            # Extract options
            options = [
                {'id': 'a', 'text': match.group(1).strip()},
                {'id': 'b', 'text': match.group(2).strip()},
                {'id': 'c', 'text': match.group(3).strip()}
            ]
        else:
            # If no options found, use the entire text as question
            q_text = question_text.strip()
            options = [
                {'id': 'a', 'text': 'Option a'},
                {'id': 'b', 'text': 'Option b'},
                {'id': 'c', 'text': 'Option c'}
            ]
        
        # Create question data
        question_data = {
            'number': question_number,
            'text': q_text,
            'options': options,
            'section': self.current_section,
            'answer': None
        }
        
        self.questions.append(question_data)
    
    def extract_answer_key(self, section_name, content):
        """Extract answers from an answer key section."""
        section_name = section_name.replace("ANSWER KEY:", "").replace("Answer Key:", "").strip()
        
        # Extract answers using regex
        answers = re.findall(r'(\d+)\.?\s*(?:Answer:\s*)?(?:\()?([a-c])(?:\))?\s*(?:-|–)\s*(.*?)(?:\n|$)', content, re.DOTALL | re.IGNORECASE)
        
        if not answers:
            # Try alternative format
            answers = re.findall(r'(\d+)\.?\s*\*\*\(([a-c])\)\s+(.*?)\*\*', content, re.DOTALL | re.IGNORECASE)
        
        if answers:
            self.answer_keys[section_name] = {int(q_num): {'option': opt.lower(), 'text': text.strip()} 
                                             for q_num, opt, text in answers}
    
    def match_answers_to_questions(self):
        """Match extracted answers to their corresponding questions."""
        for question in self.questions:
            section = question['section']
            q_num = question['number']
            
            # Find the corresponding answer key
            for key_section, answers in self.answer_keys.items():
                if section in key_section or key_section in section:
                    if q_num in answers:
                        question['answer'] = answers[q_num]['option']
                        break
            
            # If no answer found, default to option 'a'
            if not question['answer']:
                question['answer'] = 'a'
    
    def generate_xml(self):
        """Generate XML from the parsed questions."""
        print("Generating XML...")
        
        # Create root element
        root = ET.Element("quiz")
        
        # Group questions by section
        sections = {}
        for question in self.questions:
            section_name = question['section']
            if section_name not in sections:
                sections[section_name] = []
            sections[section_name].append(question)
        
        # Create section elements
        for section_name, questions in sections.items():
            section_elem = ET.SubElement(root, "category")
            section_elem.set("name", section_name)
            
            # Add questions to section
            for question in questions:
                q_elem = ET.SubElement(section_elem, "question")
                
                # Add question text
                text_elem = ET.SubElement(q_elem, "text")
                text_elem.text = question['text']
                
                # Add options
                for option in question['options']:
                    opt_elem = ET.SubElement(q_elem, "option")
                    opt_elem.set("id", option['id'])
                    opt_elem.text = option['text']
                
                # Add answer
                answer_elem = ET.SubElement(q_elem, "answer")
                answer_elem.text = question['answer']
        
        # Convert to pretty XML string
        rough_string = ET.tostring(root, 'utf-8')
        reparsed = minidom.parseString(rough_string)
        pretty_xml = reparsed.toprettyxml(indent="  ")
        
        # Write to file
        with open(self.output_file, 'w', encoding='utf-8') as f:
            f.write(pretty_xml)
        
        print(f"XML generated successfully: {self.output_file}")
    
    def convert(self):
        """Run the full conversion process."""
        self.parse_markdown()
        self.generate_xml()
        return self.output_file

def fix_xml(input_file, output_file):
    """Fix common issues in the generated XML."""
    print(f"Fixing XML file: {input_file}")
    
    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Fix issues with answer keys being parsed as questions
    content = re.sub(r'<question>\s*<text>Answer Key:.*?</question>', '', content, flags=re.DOTALL)
    
    # Fix issues with missing options
    option_tags = re.findall(r'<option id="([a-c])">(.*?)</option>', content)
    option_ids = set(tag[0] for tag in option_tags)
    
    if len(option_ids) < 3:
        missing_ids = set(['a', 'b', 'c']) - option_ids
        for missing_id in missing_ids:
            content = re.sub(r'</text>\s*', f'</text>\n    <option id="{missing_id}">Option {missing_id}</option>\n    ', content)
    
    # Write fixed content
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"XML fixed successfully: {output_file}")
    return output_file

def main():
    # Define input and output files
    input_file = "arts_chapter.text"
    output_file = "arts_quiz.xml"
    fixed_file = "arts_quiz_fixed.xml"
    
    # Create output directory if it doesn't exist
    output_dir = Path(output_file).parent
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Convert markdown to XML
    converter = QuizConverter(input_file, output_file)
    converter.convert()
    
    # Fix common issues in the XML
    fix_xml(output_file, fixed_file)
    
    print("Conversion completed successfully!")

if __name__ == "__main__":
    main()
