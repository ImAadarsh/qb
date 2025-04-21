import xml.etree.ElementTree as ET
import json

def parse_quiz_xml(xml_file):
    """
    Parse the quiz XML file and return a structured dictionary
    """
    tree = ET.parse(xml_file)
    root = tree.getroot()
    
    quiz = {
        "sections": []
    }
    
    for section in root.findall('section'):
        section_data = {
            "name": section.get('name'),
            "questions": [],
            "answers": {}
        }
        
        for question in section.findall('question'):
            question_number = question.get('number')
            question_text = question.find('text').text.strip()
            
            options = {}
            for option in question.find('options').findall('option'):
                letter = option.get('letter')
                text = option.text.strip()
                options[letter] = text
            
            answer = question.find('answer').text.strip()
            
            section_data["questions"].append({
                "number": question_number,
                "text": question_text,
                "options": options
            })
            
            section_data["answers"][question_number] = answer
        
        quiz["sections"].append(section_data)
    
    return quiz

def save_quiz_to_json(quiz_data, output_file):
    """
    Save the parsed quiz data to a JSON file
    """
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(quiz_data, f, indent=2, ensure_ascii=False)

def extract_answer_key(quiz_data):
    """
    Extract just the answer keys from the quiz data
    """
    answer_keys = {}
    
    for section in quiz_data["sections"]:
        section_name = section["name"]
        answer_keys[section_name] = section["answers"]
    
    return answer_keys

def print_quiz_summary(quiz_data):
    """
    Print a summary of the quiz
    """
    print("Quiz Summary:")
    print("============")
    
    for section in quiz_data["sections"]:
        print(f"\nSection: {section['name']}")
        print(f"Number of questions: {len(section['questions'])}")
        
        # Print first question as example
        if section["questions"]:
            first_q = section["questions"][0]
            print("\nSample Question:")
            print(f"  {first_q['number']}. {first_q['text']}")
            for letter, text in first_q['options'].items():
                print(f"    {letter}) {text}")
            print(f"  Answer: {section['answers'][first_q['number']]}")

def convert_to_xml(quiz_data, output_file):
    """
    Convert a structured quiz dictionary back to XML format
    """
    root = ET.Element("quiz")
    
    for section in quiz_data["sections"]:
        section_elem = ET.SubElement(root, "section", name=section["name"])
        
        for question in section["questions"]:
            question_elem = ET.SubElement(section_elem, "question", number=question["number"])
            
            text_elem = ET.SubElement(question_elem, "text")
            text_elem.text = question["text"]
            
            options_elem = ET.SubElement(question_elem, "options")
            for letter, text in question["options"].items():
                option_elem = ET.SubElement(options_elem, "option", letter=letter)
                option_elem.text = text
            
            answer_elem = ET.SubElement(question_elem, "answer")
            answer_elem.text = section["answers"][question["number"]]
    
    tree = ET.ElementTree(root)
    tree.write(output_file, encoding="utf-8", xml_declaration=True)

if __name__ == "__main__":
    # Example usage:
    # 1. Parse an existing XML file
    try:
        quiz_data = parse_quiz_xml("quiz.xml")
        print_quiz_summary(quiz_data)
        
        # 2. Save to JSON
        save_quiz_to_json(quiz_data, "quiz.json")
        
        # 3. Extract answer key
        answer_key = extract_answer_key(quiz_data)
        save_quiz_to_json(answer_key, "answer_key.json")
        
        print("\nSuccessfully parsed quiz and saved to JSON files!")
    except FileNotFoundError:
        print("Quiz XML file not found. Please create it first.")
        
    # If you want to create a new XML file programmatically:
    # convert_to_xml(quiz_data, "new_quiz.xml") 