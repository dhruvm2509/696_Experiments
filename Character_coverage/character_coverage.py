import os
import re
import json
import csv
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("API_KEY")
client = OpenAI(api_key=api_key)

# --- Directories ---
sample_base = "sample_stories/Batch_2"              # Each story is a folder inside sample_stories (e.g. "3174", "23308", ...)
gpt_base = "Endings/Gemini_2.5pro/Batch_2"                # Each ending file is named "{story_id}.txt"
ref_base = "ref"                             # Folder containing expected/reference JSON files (if available)
# New output folders for JSON and CSV outputs:
json_folder = "json/Gemini_2.5pro"
csv_folder = "csv/Gemini_2.5pro/Batch_2"

os.makedirs(json_folder, exist_ok=True)
os.makedirs(csv_folder, exist_ok=True)

# --- Expert Prompt Template ---
prompt_template = """You are an expert narrative analyst. Your goal is to evaluate character development in a long-form story.
You are not allowed to introduce any new characters not present in the story. Do not hallucinate or invent new story elements.

Below is a long-form story composed of multiple chapters, except for the final chapter which has been generated separately.
Read all the chapters and identify all named characters. Then, classify them into three categories:

1. Primary Characters – central to the main plot arc, appear consistently across chapters.
2. Secondary Characters – appear multiple times but are not central to the resolution of the main plot.
3. Extras – mentioned once or play a minor role.

Do not include characters that are not in the story.

Once you classify the characters, examine the final chapter provided below. For each primary and secondary character, answer the following:

- Was the character mentioned in the final chapter? (Yes/No)
- Was their storyline resolved? (Yes/No)
- If unresolved, briefly explain what’s missing based on their prior arc in the earlier chapters.

Return your output as a structured report with sections for:
- Character Classification (one line per character: <Name>: <Category>)
- Resolution Check Summary (one line per primary and secondary character: <Name> | Mentioned in Ending: <Yes/No> | Resolved: <Yes/No>)
- Explanation for Unresolved Characters (if any)

Only base your response on the content of the story and final chapter. Do not create or assume anything outside the given text.
At the end of the prompt, add the following line:

    Number of characters in the story: {num_characters}
    Number of primary characters: {num_primary}
    Number of secondary characters: {num_secondary}
    Number of extras: {num_extras}
    Number of resolved characters: {num_resolved}
    Number of primary resolved characters: {num_primary_resolved}
    Number of secondary resolved characters: {num_secondary_resolved}
    Number of unresolved characters: {num_unresolved}
    Number of characters mentioned in the final chapter: {num_mentioned}
"""

# --- Data Loading Helpers ---
def read_chapters(story_id):
    """
    Reads chapter files from sample_stories/{story_id}/,
    expecting them to be named 1.txt, 2.txt, 3.txt, etc.
    """
    chapter_folder = os.path.join(sample_base, story_id)
    if not os.path.isdir(chapter_folder):
        raise ValueError(f"No chapter folder found for story {story_id} at {chapter_folder}")
    
    # Sort files numerically by the numeric part of the filename (e.g. "1.txt", "2.txt")
    chapter_files = sorted([file for file in os.listdir(chapter_folder) if file.endswith('.txt')],
                           key=lambda x: int(x.split('.')[0]))
    chapters = []
    for file in chapter_files:
        filepath = os.path.join(chapter_folder, file)
        with open(filepath, 'r', encoding='utf-8') as f:
            chapter_num = os.path.splitext(file)[0]  # e.g., "1" from "1.txt"
            chapters.append((chapter_num, f.read()))
    return chapters

def read_endings(story_id):
    """
    Reads the ending file from Endings/Claude_3.5/{story_id}.txt.
    """
    ending_file = os.path.join(gpt_base, f"{story_id}.txt")
    if not os.path.isfile(ending_file):
        raise ValueError(f"No ending file found for story {story_id} at {ending_file}")
    with open(ending_file, 'r', encoding='utf-8') as f:
        return f.read()

def split_endings(endings_text):
    """
    If there are multiple endings in the file separated by markers like "Ending 1:", "Ending 2:", etc.,
    this function will split them into (title, content) tuples.
    """
    parts = re.split(r'(Ending\s+\d+:)', endings_text)
    endings = []
    for i in range(1, len(parts), 2):
        title = parts[i].strip()
        content = parts[i + 1].strip()
        endings.append((title, content))
    return endings

# --- GPT Task ---
def analyze_character_coverage(full_story_text, final_chapter_text):
    combined_prompt = f"{prompt_template}\n\n--- STORY CHAPTERS ---\n{full_story_text}\n\n--- FINAL CHAPTER ---\n{final_chapter_text}"
    response = OpenAI(api_key=api_key).chat.completions.create(
        model="gpt-4-turbo",
        messages=[{"role": "user", "content": combined_prompt}],
        temperature=0.5
    )
    return response.choices[0].message.content.strip()

# --- Metric & Parsing Functions ---
def parse_analysis_output(text):
    """
    Parses the GPT output report and returns:
    - classification: {character_name: category} for all characters.
    - resolution: {character_name: "Resolved" or "Unresolved"} for primary and secondary characters.
    - metrics: a dictionary with raw numeric metric variables.
    """
    classification = {}
    resolution = {}
    metrics = {}

    classification_pattern = re.compile(r'^(\w+)\s*:\s*(Primary|Secondary|Extra)', re.IGNORECASE)
    resolution_pattern = re.compile(r'^(\w+)\s*\|\s*Mentioned in Ending:\s*(Yes|No)\s*\|\s*Resolved:\s*(Yes|No)', re.IGNORECASE)
    # Raw metric regex patterns:
    pattern_chars = re.compile(r"Number of characters in the story:\s*\*?\*?\s*(\d+)")
    pattern_primary = re.compile(r"Number of primary characters:\s*\*?\*?\s*(\d+)")
    pattern_secondary = re.compile(r"Number of secondary characters:\s*\*?\*?\s*(\d+)")
    pattern_extras = re.compile(r"Number of extras:\s*\*?\*?\s*(\d+)")
    pattern_resolved = re.compile(r"Number of resolved characters:\s*\*?\*?\s*(\d+)")
    pattern_primary_resolved = re.compile(r"Number of primary resolved characters:\s*\*?\*?\s*(\d+)")
    pattern_secondary_resolved = re.compile(r"Number of secondary resolved characters:\s*\*?\*?\s*(\d+)")
    pattern_unresolved = re.compile(r"Number of unresolved characters:\s*\*?\*?\s*(\d+)")
    pattern_mentioned = re.compile(r"Number of characters mentioned in the final chapter:\s*\*?\*?\s*(\d+)")

    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue

        m = pattern_chars.search(line)
        if m:
            metrics["num_characters"] = int(m.group(1))
        m = pattern_primary.search(line)
        if m:
            metrics["num_primary"] = int(m.group(1))
        m = pattern_secondary.search(line)
        if m:
            metrics["num_secondary"] = int(m.group(1))
        m = pattern_extras.search(line)
        if m:
            metrics["num_extras"] = int(m.group(1))
        m = pattern_resolved.search(line)
        if m:
            metrics["num_resolved"] = int(m.group(1))
        m = pattern_primary_resolved.search(line)
        if m:
            metrics["num_primary_resolved"] = int(m.group(1))
        m = pattern_secondary_resolved.search(line)
        if m:
            metrics["num_secondary_resolved"] = int(m.group(1))
        m = pattern_unresolved.search(line)
        if m:
            metrics["num_unresolved"] = int(m.group(1))
        m = pattern_mentioned.search(line)
        if m:
            metrics["num_mentioned"] = int(m.group(1))

        cl_match = classification_pattern.match(line)
        if cl_match:
            name, category = cl_match.groups()
            classification[name] = category.capitalize()
            continue

        res_match = resolution_pattern.match(line)
        if res_match:
            name, mentioned, resolved = res_match.groups()
            resolution[name] = resolved.capitalize()

    return classification, resolution, metrics

def compute_weighted_resolution_accuracy(num_primary, num_secondary, num_primary_resolved, num_secondary_resolved, w_p=2, w_s=1):
    """
    Computes weighted resolution accuracy given:
      - num_primary: total number of primary characters.
      - num_secondary: total number of secondary characters.
      - num_primary_resolved: number of primary characters resolved.
      - num_secondary_resolved: number of secondary characters resolved.
    Weights: w_p for primary and w_s for secondary.
    """
    denominator = w_p * num_primary + w_s * num_secondary
    if denominator == 0:
        return None
    return round((w_p * num_primary_resolved + w_s * num_secondary_resolved) / denominator, 3)

# --- Expected Data Loader (if needed) ---
def load_expected_data(story_id):
    ref_file = os.path.join(ref_base, f"{story_id}_expected.json")
    if os.path.exists(ref_file):
        with open(ref_file, "r", encoding="utf-8") as f:
            return json.load(f)

# --- Main Analysis Workflow ---
def analyze_story(story_id):
    print(f"\nAnalyzing story {story_id}...")

    # Load chapters and ending(s)
    chapters = read_chapters(story_id)
    endings = read_endings(story_id)

    # Combine all chapters into one text (all chapters except the final ending)
    full_story_text = "\n".join([f"Chapter {num}:\n{text}" for num, text in chapters])
    ending_chunks = split_endings(endings)
    analysis_results = []

    # Process each generated ending
    for title, ending_text in ending_chunks:
        print(f"→ Evaluating {title}")
        report = analyze_character_coverage(full_story_text, ending_text)
        analysis_results.append({
            "ending_title": title,
            "analysis_report": report
        })

    # Save aggregated analysis reports as JSON in the json folder.
    json_output_file = os.path.join(json_folder, f"{story_id}_character_coverage_analysis.json")
    with open(json_output_file, 'w', encoding='utf-8') as f:
        json.dump(analysis_results, f, indent=2)
    print(f"✅ Saved character coverage analysis to {json_output_file}")

    # Process metrics for each analysis report entry.
    metrics_data = []
    for entry in analysis_results:
        report = entry.get("analysis_report", "")
        ending_title = entry.get("ending_title", "Unknown Ending")
        classification, resolution, raw_metrics = parse_analysis_output(report)
        
        # Compute simple resolution accuracy (for primary + secondary characters)
        num_primary = raw_metrics.get("num_primary", 0)
        num_secondary = raw_metrics.get("num_secondary", 0)
        num_resolved = raw_metrics.get("num_resolved", 0)
        simple_total = num_primary + num_secondary
        simple_accuracy = round(num_resolved / simple_total, 3) if simple_total != 0 else None

        # Compute weighted resolution accuracy
        num_primary_resolved = raw_metrics.get("num_primary_resolved", 0)
        num_secondary_resolved = raw_metrics.get("num_secondary_resolved", 0)
        weighted_accuracy = compute_weighted_resolution_accuracy(num_primary, num_secondary,
                                                                 num_primary_resolved, num_secondary_resolved)
        metrics_entry = {
            "ending_title": ending_title,
            "num_characters": raw_metrics.get("num_characters"),
            "num_primary": num_primary,
            "num_secondary": num_secondary,
            "num_extras": raw_metrics.get("num_extras"),
            "num_resolved": num_resolved,
            "num_primary_resolved": num_primary_resolved,
            "num_secondary_resolved": num_secondary_resolved,
            "num_unresolved": raw_metrics.get("num_unresolved"),
            "num_mentioned": raw_metrics.get("num_mentioned"),
            "simple_resolution_accuracy": simple_accuracy,
            "weighted_resolution_accuracy": weighted_accuracy
        }
        metrics_data.append(metrics_entry)

    # Write metrics to CSV in the csv folder.
    csv_output_file = os.path.join(csv_folder, f"{story_id}_character_coverage_analysis_metrics.csv")
    with open(csv_output_file, "w", newline="", encoding="utf-8") as csvfile:
        fieldnames = [
            "ending_title", "num_characters", "num_primary", "num_secondary",
            "num_extras", "num_resolved", "num_primary_resolved", "num_secondary_resolved",
            "num_unresolved", "num_mentioned", "simple_resolution_accuracy", "weighted_resolution_accuracy"
        ]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for row in metrics_data:
            writer.writerow(row)
    print(f"✅ Saved metrics CSV to {csv_output_file}")

# --- Batch Run ---
if __name__ == "__main__":
    # Detect story ids based on the directory names in sample_stories
    story_ids = [folder for folder in os.listdir(sample_base) if os.path.isdir(os.path.join(sample_base, folder))]
    for story_id in story_ids:
        analyze_story(story_id)
    print("All stories analyzed.")
