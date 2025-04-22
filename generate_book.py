import os
import re
from pathlib import Path

# Paths
ROOT = Path(__file__).resolve().parent
FORMATTED_DIR = ROOT / "formatted_quiz"
MAIN_TEX = ROOT / "main.tex"
SECTIONS_DIR = ROOT / "tex_sections"

# Ensure output dir exists
SECTIONS_DIR.mkdir(exist_ok=True)

# Order of STEAM chapters
CHAPTER_ORDER = [
    ("Science", "SCIENCE"),
    ("Technology", "TECHNOLOGY"),
    ("Engineering", "ENGINEERING"),
    ("Arts", "ARTS"),
    ("Mathematics", "MATHEMATICS"),
]

# Simple markdown to LaTeX replacements (minimal)  
MD_REPLACEMENTS = [
    (r"^\*\*([^*]+)\*\*$", r"\\section{\1}"),  # Bold heading -> section
    (r"\*\*(ANSWER KEY:[^*]+)\*\*", r"\\section{\1}"),
    (r"^\d+\. ", r"\\question{"),  # start of question line
]


def md_to_latex(md_text: str) -> str:
    """Very naive markdown to LaTeX converter for our limited quiz format."""
    lines = md_text.splitlines()
    out = []
    q_open = False
    for line in lines:
        # Replace bold headers
        m = re.match(r"\*\*([^*]+)\*\*", line)
        if m:
            # Close any open environment
            if q_open:
                out.append("}\\par")
                q_open = False
            out.append(f"\\section{{{m.group(1).strip()}}}")
            continue
        # Question lines start with number.
        qm = re.match(r"(\d+)\. (.+)", line)
        if qm:
            if q_open:
                out.append("}\\par")
            q_text = qm.group(2).strip()
            out.append(f"\\textbf{{Q{qm.group(1)}}} {q_text}\\par")
            q_open = False  # we treat as plain paragraph
            continue
        # Option lines 'a) text'
        opt = re.match(r"\s*[a-z]\) (.+)", line)
        if opt:
            out.append(f"\\quad - {opt.group(0).strip()}\\par")
            continue
        # otherwise plain
        out.append(line)
    if q_open:
        out.append("}\\par")
    return "\n".join(out)


def convert_md_file(md_path: Path) -> Path:
    tex_path = SECTIONS_DIR / (md_path.stem + ".tex")
    with md_path.open(encoding="utf-8") as f:
        md_content = f.read()
    latex_content = md_to_latex(md_content)
    tex_path.write_text(latex_content, encoding="utf-8")
    return tex_path


def gather_chapter_structure():
    chapters = []
    for folder_name, display in CHAPTER_ORDER:
        folder = FORMATTED_DIR / folder_name
        if not folder.exists():
            continue
        quizzes = []
        for md_file in sorted(folder.glob("*.md")):
            if md_file.name.endswith("_answers.md"):
                continue
            answer_file = md_file.with_name(md_file.stem + "_answers.md")
            quizzes.append((md_file, answer_file if answer_file.exists() else None))
        chapters.append((display, quizzes))
    return chapters


def build_sections():
    chapter_data = gather_chapter_structure()
    tex_entries = []
    for chap_title, quizzes in chapter_data:
        tex_entries.append(f"\\chapter{{{chap_title}}}")
        for quiz_md, ans_md in quizzes:
            # convert quiz and answer key
            quiz_tex = convert_md_file(quiz_md)
            tex_entries.append(f"\\section{{{quiz_md.stem.replace('_', ' ').title()}}}")
            tex_entries.append(f"\\input{{{quiz_tex.relative_to(ROOT)}}}")
            if ans_md:
                ans_tex = convert_md_file(ans_md)
                tex_entries.append(f"\\subsection*{{Answer Key}}")
                tex_entries.append(f"\\input{{{ans_tex.relative_to(ROOT)}}}")
    return "\n\n".join(tex_entries)


def rebuild_main_tex():
    with MAIN_TEX.open(encoding="utf-8") as f:
        content = f.read()
    # Keep everything up to \mainmatter
    pre, _sep, _rest = content.partition("\\mainmatter")
    if not _sep:
        raise ValueError("main.tex missing \\mainmatter marker")
    new_body = build_sections()
    new_content = f"{pre}\\mainmatter\n\n{new_body}\n\n\\end{{document}}\n"
    MAIN_TEX.write_text(new_content, encoding="utf-8")
    print("main.tex rebuilt successfully.")


if __name__ == "__main__":
    rebuild_main_tex() 