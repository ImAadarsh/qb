#!/bin/bash
# This script parses the markdown questions and compiles the LaTeX document

# Set variables
QUESTION_DIR="./Question"
OUTPUT_DIR="./output"
LATEX_FILE="$OUTPUT_DIR/quest_book.tex"

# Create output directory if it doesn't exist
mkdir -p "$OUTPUT_DIR"

# Copy style files to output directory
cp mcq_style.tex "$OUTPUT_DIR/"
cp section_cover.tex "$OUTPUT_DIR/"
cp titlepage.tex "$OUTPUT_DIR/"

# Run the parser to generate LaTeX
echo "Parsing question files..."
python3 parse_questions_improved.py "$QUESTION_DIR" "$LATEX_FILE" --questions 0

# Compile LaTeX document
echo "Compiling LaTeX document..."
cd "$OUTPUT_DIR"
pdflatex quest_book.tex
pdflatex quest_book.tex  # Run twice for proper TOC generation

echo "Done! Output saved to $OUTPUT_DIR/quest_book.pdf" 