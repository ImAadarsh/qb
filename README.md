# The Ultimate Quest - Quiz Book

A LaTeX template for "The Ultimate Quest" quiz book covering Science, Technology, Engineering, Arts & Mathematics (STEAM).

## Project Structure

- `main.tex` - Main document
- `titlepage.tex` - Title page design
- `mcq_style.tex` - MCQ styling and formatting
- `section_cover.tex` - Section cover page template

## How to Compile

1. Ensure you have a LaTeX distribution installed (e.g., TeX Live, MiKTeX).
2. Compile the document using pdfLaTeX:

```bash
pdflatex main.tex
pdflatex main.tex  # Run twice for proper TOC generation
```

Or use a LaTeX editor like TeXstudio, Overleaf, or VS Code with LaTeX Workshop extension.

## Features

- Professional book design with styled chapter and section headings
- Enhanced MCQ format with boxed questions
- Section cover pages
- Answer key
- Consistent styling throughout the document
- Headers and footers with book title and page numbers

## Customization

- Modify color scheme by changing RGB values for `questblue` and `questorange`
- Add custom graphics/logos by uncommenting image code in section covers
- Adjust spacing and formatting in the style files

## Required LaTeX Packages

- graphicx
- xcolor
- geometry
- fancyhdr
- titlesec
- enumitem
- amsmath, amssymb
- multicol
- etoolbox
- tcolorbox

## Author

Gaurava Yadav 