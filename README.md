# Arts Chapter Extraction Script

This repository contains a script for extracting Arts & Culture questions from the original question bank and formatting them as a LaTeX book.

## Files

- `update_arts_chapter.py` - The main Python script that extracts questions from arts_chapter.md and updates main.tex
- `main.tex` - The LaTeX file containing the formatted book with only Arts & Culture questions
- `Question/arts_chapter.md` - The source file containing all Arts & Culture questions

## How to Use

1. Make sure you have the source files: `arts_chapter.md` in the `Question` directory and `main.tex` in the root directory.
2. Run the script:
   ```
   python update_arts_chapter.py
   ```
3. The script will:
   - Extract all sections from arts_chapter.md
   - Format each question with its options
   - Mark correct and incorrect answers
   - Generate an answer key
   - Update main.tex with only Arts & Culture content

4. After running the script, you can compile the LaTeX file to generate a PDF:
   ```
   pdflatex main.tex
   ```

## Sections Included

The following sections are extracted from the arts_chapter.md file:

1. VISUAL ARTS and PAINTINGS
2. LITERATURE
3. FILMS AND MEDIA
4. FOLK DANCES AND FESTIVALS OF INDIA
5. POP CULTURE
6. ARTS MIXED BAG 1
7. ARTS MIXED BAG 2
8. ARTS MIXED BAG 3

## Requirements

- Python 3.x
- A LaTeX distribution (e.g., TeX Live, MiKTeX) with necessary packages
- Required LaTeX style files: mcq_style.tex, section_cover.tex, titlepage.tex

## Notes

- The script automatically numbers questions sequentially across all sections
- Answer keys are generated based on the original answers in arts_chapter.md
- The LaTeX document is designed for optimal printing and readability 