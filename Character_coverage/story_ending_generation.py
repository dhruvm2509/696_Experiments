import os

import google.generativeai as genai

# Configure the API key
genai.configure(api_key="API_Key")

# Initialize the Gemini 2.5 Pro model
model = genai.GenerativeModel('gemini-2.5-pro-exp-03-25')

def generate_gemini_ending(prompt):
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        print(f"Error generating ending: {e}")
        return "Error: Could not generate ending."

# Paths
base_dir = "sample_stories/Batch_2"
output_base = "Endings/Gemini_2.5pro/Batch_2"

story_ids = [d for d in os.listdir(base_dir) if os.path.isdir(os.path.join(base_dir, d))]

for story_id in story_ids:
    story_path = os.path.join(base_dir, story_id, f"{story_id}-chapters")
    
    chapters = sorted([f for f in os.listdir(story_path) if f.endswith('.txt')], key=lambda x: int(x.replace('.txt', '')))
    story_text = ""
    for chapter_file in chapters:
        with open(os.path.join(story_path, chapter_file), 'r', encoding='utf-8') as f:
            story_text += f.read() + "\n\n"
    
    prompt = (
        f"Here is a story:\n\n{story_text}\n\n"
        "Now, continue and generate the last chapter which serves as a suitable ending to the given story plot. "
        "The ending should be 500-1000 words long and should naturally fit within the story's themes and tone.\n\n"
    )
    
    # Ensure output directory exists
    os.makedirs(output_base, exist_ok=True)
    output_file = os.path.join(output_base, f"{story_id}.txt")
    
    with open(output_file, 'w', encoding='utf-8') as f:
        for i in range(1, 6):
            ending = generate_gemini_ending(prompt)
            f.write(f"--- Ending {i} ---\n\n")
            f.write(ending + "\n\n")
            f.write("="*50 + "\n\n")  # Separator between endings

print("All story endings generated and saved.")