import xml.etree.ElementTree as ET
import random
import json

def load_quiz_from_xml(xml_file):
    """
    Load a quiz from XML file
    """
    tree = ET.parse(xml_file)
    root = tree.getroot()
    return root

def display_quiz_statistics(quiz_root):
    """
    Display statistics about the quiz
    """
    sections = quiz_root.findall('section')
    
    print("Quiz Statistics:")
    print("--------------")
    print(f"Total sections: {len(sections)}")
    
    total_questions = 0
    
    for section in sections:
        section_name = section.get('name')
        questions = section.findall('question')
        total_questions += len(questions)
        
        print(f"\nSection: {section_name}")
        print(f"Number of questions: {len(questions)}")
        
        # Count how many questions have answers
        answered = sum(1 for q in questions if q.find('answer').text.strip())
        print(f"Questions with answers: {answered}/{len(questions)}")
    
    print(f"\nTotal questions in quiz: {total_questions}")

def take_quiz_from_section(quiz_root, section_name, num_questions=10, randomize=True):
    """
    Generate a quiz from a specific section
    """
    # Find the requested section
    section = None
    for s in quiz_root.findall('section'):
        if s.get('name') == section_name:
            section = s
            break
    
    if not section:
        print(f"Section '{section_name}' not found in the quiz.")
        return
    
    # Get all questions from the section
    questions = section.findall('question')
    
    if randomize:
        # Randomize questions
        selected_questions = random.sample(questions, min(num_questions, len(questions)))
    else:
        # Take the first N questions
        selected_questions = questions[:min(num_questions, len(questions))]
    
    # Present the quiz
    print(f"\n=== Quiz from {section_name} ===\n")
    
    score = 0
    for i, question in enumerate(selected_questions, 1):
        q_num = question.get('number')
        q_text = question.find('text').text
        
        print(f"Question {i} (#{q_num}): {q_text}")
        
        # Display options
        options = question.find('options')
        if options is not None:
            for option in options.findall('option'):
                letter = option.get('letter')
                text = option.text
                print(f"  {letter}) {text}")
        
        # Get answer if available
        correct_answer = question.find('answer').text.strip()
        
        # In an interactive environment, you could get user input here
        # For this example, we'll just display the correct answer
        if correct_answer:
            print(f"Correct answer: {correct_answer}")
            # In a real implementation, you'd compare with user input
            # and increment score if correct
        else:
            print("Answer not available")
        
        print()  # Empty line between questions
    
    print(f"Quiz complete! Your score: {score}/{len(selected_questions)}")

def generate_quiz_app_json(quiz_root, output_file):
    """
    Generate a JSON file that could be used by a quiz app
    """
    quiz_data = {
        "title": "ARTS 400 Quiz",
        "sections": []
    }
    
    for section in quiz_root.findall('section'):
        section_data = {
            "name": section.get('name'),
            "questions": []
        }
        
        for question in section.findall('question'):
            question_data = {
                "id": question.get('number'),
                "text": question.find('text').text,
                "options": [],
                "correctAnswer": question.find('answer').text
            }
            
            options = question.find('options')
            if options is not None:
                for option in options.findall('option'):
                    question_data["options"].append({
                        "id": option.get('letter'),
                        "text": option.text
                    })
            
            section_data["questions"].append(question_data)
        
        quiz_data["sections"].append(section_data)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(quiz_data, f, indent=2, ensure_ascii=False)
    
    print(f"Quiz app JSON generated: {output_file}")

if __name__ == "__main__":
    try:
        # Try to load the generated XML
        quiz = load_quiz_from_xml("arts_400_quiz.xml")
        
        # Display statistics
        display_quiz_statistics(quiz)
        
        # Take a sample quiz from a section
        # You'd typically ask the user which section they want to quiz on
        take_quiz_from_section(quiz, "VISUAL ARTS/PAINTINGS", num_questions=5)
        
        # Generate JSON for a hypothetical quiz app
        generate_quiz_app_json(quiz, "quiz_app_data.json")
        
    except FileNotFoundError:
        print("Quiz XML file not found. Please run scrape_and_create_xml.py first.")
    except Exception as e:
        print(f"Error: {e}") 