import re

def extract_section_questions(content, section_title):
    """Extract questions from a specific section in the arts_chapter.md file."""
    # Try both with and without asterisks
    patterns = [
        fr"\*\*{section_title}\*\*\n\n(.*?)(?=\n\n\*\*ANSWER KEY: {section_title}\*\*|\n\n\*\*)",
        fr"\*\*{section_title}\*\*\n\n(.*?)(?=\n\nANSWER KEY: {section_title}|\n\n\*\*)",
        fr"{section_title}\n\n(.*?)(?=\n\n\*\*ANSWER KEY: {section_title}\*\*|\n\n\*\*)",
        fr"{section_title}\n\n(.*?)(?=\n\nANSWER KEY: {section_title}|\n\n\*\*)"
    ]
    
    section_content = None
    for pattern in patterns:
        match = re.search(pattern, content, re.DOTALL)
        if match:
            section_content = match.group(1)
            break
    
    if not section_content:
        return []
    
    # Extract questions with options
    questions = []
    current_question = None
    current_options = []
    
    for line in section_content.split('\n'):
        # New question starts with a number
        if re.match(r'^\d+\.', line):
            # Save previous question if exists
            if current_question is not None:
                questions.append((current_question, current_options))
            
            # Start new question
            current_question = line.strip()
            current_options = []
        # Options start with a letter
        elif re.match(r'^\s*[abc]\)', line):
            current_options.append(line.strip())
    
    # Add the last question
    if current_question is not None:
        questions.append((current_question, current_options))
    
    return questions

def extract_section_answers(content, section_title):
    """Extract answers for a specific section."""
    # Try both with and without asterisks
    patterns = [
        fr"\*\*ANSWER KEY: {section_title}\*\*\n\n(.*?)(?=\n\n\*\*|\Z)",
        fr"ANSWER KEY: {section_title}\n\n(.*?)(?=\n\n\*\*|\Z)"
    ]
    
    answer_section = None
    for pattern in patterns:
        match = re.search(pattern, content, re.DOTALL)
        if match:
            answer_section = match.group(1)
            break
    
    if not answer_section:
        return {}
    
    answers = {}
    
    for line in answer_section.split('\n'):
        if line.strip():
            # Try different answer formats
            formats = [
                r'(\d+)\.\s+Answer:\s+([abc])\s+-\s+(.*)',
                r'(\d+)\.\s+([abc])\s+-\s+(.*)',
                r'(\d+)\.\s+([abc])\s*-\s*(.*)'
            ]
            
            for format in formats:
                match = re.search(format, line.strip())
                if match:
                    question_num, option, explanation = match.groups()
                    answers[int(question_num)] = (option, explanation.strip())
                    break
    
    return answers

def format_latex_mcq(questions, answers, start_counter=1):
    """Format questions and answers as LaTeX enhancedmcq environments."""
    latex_mcqs = []
    
    for i, (question, options) in enumerate(questions, start_counter):
        # Extract question number and text
        q_match = re.match(r'(\d+)\.\s+(.*)', question)
        if not q_match:
            continue
            
        q_num, q_text = q_match.groups()
        
        # Get the answer for this question
        q_num_int = int(q_num)
        answer_info = answers.get(q_num_int, None)
        
        if not answer_info:
            continue
            
        correct_option, explanation = answer_info
        
        # Format as LaTeX
        latex_question = f"\\begin{{enhancedmcq}}[Question {q_num}]{{{q_text}}}\n"
        
        for option in options:
            option_match = re.match(r'\s*([abc])\)\s+(.*)', option)
            if option_match:
                opt_letter, opt_text = option_match.groups()
                
                if opt_letter == correct_option:
                    latex_question += f"    \\correctoption{{{opt_text}}}\n"
                else:
                    latex_question += f"    \\incorrectoption{{{opt_text}}}\n"
        
        latex_question += "\\end{enhancedmcq}\n\n"
        latex_mcqs.append(latex_question)
    
    return ''.join(latex_mcqs)

def create_answer_key(answers, num_questions):
    """Create the answer key section in LaTeX format."""
    latex_answers = "\\answerkey\n"
    
    for i in range(1, num_questions + 1):
        if i in answers:
            option, _ = answers[i]
            if option == 'a':
                latex_option = 'a'
            elif option == 'b':
                latex_option = 'b'
            else:
                latex_option = 'c'
            latex_answers += f"\\answer{{{latex_option}}} % Question {i}\n"
    
    latex_answers += "\\endanswerkey\n"
    return latex_answers

def update_main_tex():
    # Read arts_chapter.md
    with open('Question/arts_chapter.md', 'r', encoding='utf-8') as file:
        arts_content = file.read()
    
    # Read current main.tex
    with open('main.tex', 'r', encoding='utf-8') as file:
        main_tex = file.read()
    
    # Extract sections from arts_chapter.md with correct names
    sections = [
        "VISUAL ARTS AND PAINTINGS", 
        "LITERATURE", 
        "FILMS AND MEDIA", 
        "FOLK DANCES AND FESTIVALS OF INDIA", 
        "POP CULTURE",
        "ARTS MIXED BAG One",
        "ARTS MIXED BAG Two",
        "ARTS MIXED BAG Three"
    ]
    
    all_questions = []
    all_answers = {}
    question_counter = 1
    
    for section in sections:
        questions = extract_section_questions(arts_content, section)
        answers = extract_section_answers(arts_content, section)
        
        if questions:
            # Update answers with sequential numbers across sections
            section_answers = {}
            for q_num, answer in answers.items():
                adjusted_q_num = question_counter + (q_num - 1)
                section_answers[adjusted_q_num] = answer
                all_answers[adjusted_q_num] = answer
            
            formatted_section = format_latex_mcq(questions, answers, 1)
            all_questions.append((section, formatted_section))
            question_counter += len(questions)
    
    # Create the updated main.tex with only Arts chapter
    updated_main_tex = """% The Ultimate Quest - LaTeX Book
\\documentclass[12pt,a4paper]{book}

% Essential packages
\\usepackage[utf8]{inputenc}
\\usepackage{graphicx}
\\usepackage{xcolor}
\\usepackage{geometry}
\\usepackage{fancyhdr}
\\usepackage{titlesec}
\\usepackage{enumitem}
\\usepackage{amsmath,amssymb}
\\usepackage{multicol}
\\usepackage{etoolbox}
\\usepackage{lipsum} % For demo text

% Page geometry - tighter margins for more content per page
\\geometry{margin=0.8in}

% Color definitions
\\definecolor{questblue}{RGB}{0,72,153}
\\definecolor{questorange}{RGB}{255,127,0}

% Header and footer styling - more compact
\\pagestyle{fancy}
\\fancyhf{}
\\fancyhead[LO,RE]{The Ultimate Quest}
\\fancyhead[RO,LE]{\\thepage}
\\fancyfoot[C]{\\textit{Engage | Explore | Excel}}
\\renewcommand{\\headrulewidth}{0.4pt}
\\renewcommand{\\footrulewidth}{0.4pt}
\\setlength{\\headheight}{13.6pt}

% Custom chapter and section styling - more compact
\\titleformat{\\chapter}[display]
{\\normalfont\\huge\\bfseries\\color{questblue}}
{\\chaptertitlename\\ \\thechapter}{10pt}{\\Huge}
\\titlespacing*{\\chapter}{0pt}{30pt}{20pt}

\\titleformat{\\section}
{\\normalfont\\Large\\bfseries\\color{questblue}}
{\\thesection}{1em}{}
\\titlespacing*{\\section}{0pt}{2.5ex plus 1ex minus .2ex}{1.3ex plus .2ex}

% Global paragraph spacing reduction
\\setlength{\\parskip}{0.5em}
\\setlength{\\parindent}{0em}

% Adjust float placement to be less strict
\\renewcommand{\\topfraction}{0.9}
\\renewcommand{\\bottomfraction}{0.8}
\\renewcommand{\\textfraction}{0.07}
\\renewcommand{\\floatpagefraction}{0.7}

% MCQ counter setup
\\newcounter{questioncounter}[section]
\\newcounter{totalcounter}
\\setcounter{totalcounter}{1} % Starting from 1

% Choose MCQ style: 
% For squares, uncomment the next line:
\\input{mcq_style}
% For circles, uncomment the next line and comment the one above:
%\\input{mcq_style_alt}
% For arrows, uncomment the next line and comment the two above:
%\\input{mcq_style_arrow}

\\input{section_cover}

% Adjust section cover spacing
\\makeatletter
\\renewcommand{\\sectioncover}[3]{%
  \\cleardoublepage
  \\thispagestyle{empty}
  \\begin{center}
    \\vspace*{2cm}
    {\\huge\\bfseries\\textcolor{questblue}{#1}\\par}
    \\vspace{0.7cm}
    {\\Large\\textit{#2}\\par}
    \\vspace{1.2cm}
    \\begin{tcolorbox}[
      enhanced,
      colback=white,
      colframe=questorange,
      arc=5mm,
      boxrule=0.5mm,
      width=0.7\\textwidth,
      halign=center,
      valign=center,
      height=5cm
    ]
      \\begin{center}
        {\\large #3\\par}
      \\end{center}
    \\end{tcolorbox}
    \\vspace{1.5cm}
  \\end{center}
  \\cleardoublepage
}
\\makeatother

\\begin{document}

\\frontmatter
\\input{titlepage}
\\tableofcontents

\\mainmatter

\\chapter{Introduction to The Ultimate Quest}
\\section{About This Book}
This book is designed to challenge your knowledge across Art & Culture. Each section contains multiple-choice questions to test your understanding and expand your horizons.

\\sectioncover{ARTS}{Celebrating human creativity}{From visual arts to literature, music, and history, explore the expressions of human creativity and cultural heritage.}

\\chapter{Art & Culture}
"""

    # Add each section as a separate section in the LaTeX document
    for section_title, section_content in all_questions:
        # Format the section title for LaTeX
        formatted_title = section_title.replace('/', ' and ')
        updated_main_tex += f"\\section{{{formatted_title}}}\n\n{section_content}\n"

    # Add answer key section
    updated_main_tex += """
% Answer key section
\\sectioncover{ANSWER KEY}{Check your knowledge}{Review your answers and track your progress through each section of The Ultimate Quest.}

"""
    updated_main_tex += create_answer_key(all_answers, question_counter - 1)
    updated_main_tex += "\n\\end{document} "

    # Write the updated content to main.tex
    with open('main.tex', 'w', encoding='utf-8') as file:
        file.write(updated_main_tex)
    
    print(f"Successfully updated main.tex with {question_counter - 1} questions from Arts chapter.")

if __name__ == "__main__":
    update_main_tex() 