
---

## 📁 Folder & File Descriptions



### `Endings/`
Houses the **generated endings**:
- Subfolders for each LLM (`Claude_3.5/`, `Gemini_2.5pro/`, `gpt_4o/`).
- Each batch (e.g., `Batch_1/`) contains `.txt` files.
- Each `.txt` file corresponds to a `story_id` and includes 5 generated endings.

---

### `sample_stories/`
Contains the **input stories**:
- Organized by batches (e.g., `Batch_1` &&  `Batch_2/`).
- Each subfolder is named after a `story_id` and contains its respective chapters.

---

### `Character_coverage/`
Contains all analysis-related resources:
- `csv/` : Evaluation metrics for each LLM (Gemini_2.5pro, GPT-4o, etc.), organized by batches.
- `json/` : (Optional) For structured data storage related to character analysis.
- `Plots/` : Stores generated visualizations (e.g., weighted accuracy comparisons).
- **Python Scripts**:
  - `character_coverage.py` : Computes character resolution metrics.
  - `plot.py` / `plot_batch2.py` : Generates visual comparison plots.
  - `story_ending_generation.py` : Automates story ending generation using LLM APIs.
  - `weighted_accuracy_comparison.png` : Example output plot comparing LLM performance.
- **CSV Files**: Contain character resolution metrics for each story's endings.
- **Plots**: Bar charts comparing LLM performance based on weighted resolution accuracy.

---




