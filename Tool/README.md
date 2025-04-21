# ARTS 400 Quiz XML Parser

This system converts ARTS 400 quiz questions from Markdown format to a structured XML format, and provides tools for working with the resulting data.

## Files in this Project

- `scrape_and_create_xml.py` - Extracts questions from the Markdown file and creates an XML file
- `parse_quiz.py` - Parses the XML quiz format into a structured dictionary
- `use_quiz_xml.py` - Demonstrates how to use the XML quiz format for various applications
- `create_quiz_xml.py` - An alternative approach to generate quiz XML (more advanced pattern matching)

## XML Format

The XML format used is structured as follows:

```xml
<quiz>
  <section name="SECTION_NAME">
    <question number="1">
      <text>Question text goes here?</text>
      <options>
        <option letter="a">First option</option>
        <option letter="b">Second option</option>
        <option letter="c">Third option</option>
      </options>
      <answer>b</answer>
    </question>
    <!-- More questions -->
  </section>
  <!-- More sections -->
</quiz>
```

This structure organizes questions by section, with each question having text, options, and an answer.

## How to Use

### Step 1: Generate the XML

First, run the script to extract questions from the Markdown file and create the XML:

```bash
python scrape_and_create_xml.py
```

This will create a file called `arts_400_quiz.xml`.

### Step 2: Parse and Use the XML

You can use the resulting XML in various ways:

1. **Parse to Python Dictionary**:
   ```bash
   python parse_quiz.py
   ```
   This creates `quiz.json` and `answer_key.json` files.

2. **Take a Quiz**:
   ```bash
   python use_quiz_xml.py
   ```
   This provides statistics about the quiz and demonstrates how to create a quiz from a section.

3. **Generate Quiz App Data**:
   The `use_quiz_xml.py` script also shows how to generate JSON that could be used by a quiz application.

## Customizing the XML Generation

If the automatic extraction doesn't work perfectly (due to inconsistencies in the original format), you can:

1. Edit the XML file manually after generation
2. Adjust the regular expressions in `scrape_and_create_xml.py`
3. Use the `create_example_xml` function in `scrape_and_create_xml.py` to create a template

## Potential Applications

This XML format can be used for:

1. Creating web-based quiz applications
2. Building mobile quiz apps
3. Generating printable quiz sheets
4. Creating flashcards
5. Analyzing question difficulty based on user responses

## Troubleshooting

If the extraction doesn't work perfectly:

1. Check the original Markdown for inconsistencies in formatting
2. Examine the regular expressions in the extraction script
3. Consider manually creating or editing the XML

## Requirements

- Python 3.6 or higher
- Standard library modules: `xml.etree.ElementTree`, `xml.dom.minidom`, `re`, `json`, `os`, `random` 