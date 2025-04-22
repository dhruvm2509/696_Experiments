import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

def collect_and_aggregate(root_folder):
    """
    Walks through the `root_folder`, and for each subfolder (LLM),
    reads all CSV files. Each CSV is assumed to represent one story
    with multiple endings in rows.

    We:
      1) Read the CSV.
      2) Take only the first 5 endings (head(5)) from each story.
      3) Compute the mean of `weighted_resolution_accuracy` over these 5 endings.
      4) Store the aggregated row in a DataFrame with columns:
         [story_name, llm_name, mean_weighted_accuracy_5]

    Returns:
        A pandas DataFrame with:
          story_name, llm_name, mean_weighted_accuracy_5
    """
    aggregated_data = []

    # Walk through all subfolders in the root directory
    for dirpath, dirnames, filenames in os.walk(root_folder):
        # The subfolder name is considered the LLM name
        llm_name = os.path.basename(dirpath)

        for fname in filenames:
            if fname.lower().endswith(".csv"):
                csv_path = os.path.join(dirpath, fname)

                # Attempt to read the CSV
                try:
                    df = pd.read_csv(csv_path)
                except Exception as e:
                    print(f"Error reading {csv_path}: {e}")
                    continue

                # Make sure required columns exist
                needed_cols = [
                    "ending_title",
                    "weighted_resolution_accuracy"
                ]
                if not all(col in df.columns for col in needed_cols):
                    print(f"Skipping {csv_path}: missing needed columns.")
                    continue

                # Take only the first 5 endings
                df_top5 = df.head(5)

                # Compute mean of weighted_resolution_accuracy for these 5 endings
                mean_weighted_accuracy_5 = df_top5["weighted_resolution_accuracy"].mean()

                # Infer "story_name" from either the CSV filename or from the data
                # Approach 1: Parse from CSV filename
                # e.g., "23308_character_coverage_analysis_metrics.csv" -> "23308"
                story_name = os.path.splitext(fname)[0]  # drop .csv
                # If your filenames look like "23308_character_coverage_analysis_metrics",
                # you might want to split by underscore:
                # story_name = story_name.split("_")[0]
                
                # Add row to our aggregated list
                aggregated_data.append({
                    "story_name": story_name,
                    "llm_name": llm_name,
                    "mean_weighted_accuracy_5": mean_weighted_accuracy_5
                })

    # Convert list of dicts to a DataFrame
    df_agg = pd.DataFrame(aggregated_data)
    return df_agg

def plot_mean_weighted_accuracy(df_agg):
    """
    Given the aggregated DataFrame, plots a grouped bar chart where:
      - X-axis: Story Name
      - Y-axis: Mean Weighted Accuracy (first 5 endings)
      - Hue: LLM Name
    """
    # Sort stories by name (optional, or you can skip this)
    df_agg_sorted = df_agg.sort_values(by="story_name")

    plt.figure(figsize=(12, 8))
    # Create a grouped barplot
    sns.barplot(
        data=df_agg_sorted,
        x="story_name",
        y="mean_weighted_accuracy_5",
        hue="llm_name"
    )
    plt.title("Comparison of Mean Weighted Accuracy (First 5 Endings) Across LLMs")
    plt.xlabel("Story Name")
    plt.ylabel("Mean Weighted Accuracy (Top 5 Endings)")
    plt.xticks(rotation=45, ha="right")
    plt.legend(title="LLM Name")
    plt.tight_layout()
    plt.show()

def main():
    # 1. Define the path to your parent "csv" folder
    root_folder = r"csv"  # <-- Change this to your real path

    # 2. Collect data and compute the aggregated mean across the first 5 endings
    df_agg = collect_and_aggregate(root_folder)
    if df_agg.empty:
        print("No aggregated data found. Please check your folder structure/CSVs.")
        return

    print(df_agg.head())

    # 3. Plot the grouped bar chart comparing each story across all LLMs
    plot_mean_weighted_accuracy(df_agg)

if __name__ == "__main__":
    main()
