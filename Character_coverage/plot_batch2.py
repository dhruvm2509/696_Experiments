import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

def collect_and_aggregate_batch(batch_paths):
    aggregated_data = []

    for llm_name, batch_path in batch_paths.items():
        for fname in os.listdir(batch_path):
            if fname.lower().endswith(".csv"):
                csv_path = os.path.join(batch_path, fname)
                try:
                    df = pd.read_csv(csv_path)
                except Exception as e:
                    print(f"Error reading {csv_path}: {e}")
                    continue

                if "weighted_resolution_accuracy" not in df.columns:
                    print(f"Skipping {csv_path}: missing needed columns.")
                    continue

                mean_weighted_accuracy_5 = df.head(5)["weighted_resolution_accuracy"].mean()
                story_name = fname.split("_")[0]

                aggregated_data.append({
                    "story_name": story_name,
                    "llm_name": llm_name,
                    "mean_weighted_accuracy_5": mean_weighted_accuracy_5
                })
    return pd.DataFrame(aggregated_data)

def plot_llm_individual(df_agg, llm_name):
    df_llm = df_agg[df_agg['llm_name'] == llm_name].sort_values(by="story_name")
    plt.figure(figsize=(10,6))
    sns.barplot(data=df_llm, x="story_name", y="mean_weighted_accuracy_5", palette="Blues_d")
    plt.title(f"{llm_name} - Mean Weighted Accuracy (Top 5 Endings)")
    plt.xlabel("Story ID")
    plt.ylabel("Mean Weighted Accuracy")
    plt.xticks(rotation=45, ha="right")
    plt.ylim(0,1)
    plt.tight_layout()
    plt.show()

def plot_comparison(df_agg):
    df_sorted = df_agg.sort_values(by="story_name")
    plt.figure(figsize=(12,8))
    sns.barplot(data=df_sorted, x="story_name", y="mean_weighted_accuracy_5", hue="llm_name")
    plt.title("LLM Comparison: Mean Weighted Accuracy (Top 5 Endings)")
    plt.xlabel("Story ID")
    plt.ylabel("Mean Weighted Accuracy")
    plt.xticks(rotation=45, ha="right")
    plt.ylim(0,1)
    plt.legend(title="LLM")
    plt.tight_layout()
    plt.show()

def main():
    batch_paths = {
        "Gemini_2.5pro": r"csv\\Gemini_2.5pro\\Batch_2",
        "gpt_4o": r"csv\\gpt_4o\\batch_2"
    }

    df_agg = collect_and_aggregate_batch(batch_paths)
    if df_agg.empty:
        print("No data found.")
        return

    # Plot for each LLM
    plot_llm_individual(df_agg, "Gemini_2.5pro")
    plot_llm_individual(df_agg, "gpt_4o")

    # Plot comparison
    plot_comparison(df_agg)

if __name__ == "__main__":
    main()
