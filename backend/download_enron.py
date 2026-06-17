import kagglehub
from kagglehub import KaggleDatasetAdapter
import pandas as pd

# Path to the file in the dataset
file_path = "emails.csv"

print("Downloading Enron email dataset...")
try:
    # Load the latest version
    df = kagglehub.load_dataset(
      KaggleDatasetAdapter.PANDAS,
      "wcukierski/enron-email-dataset",
      file_path,
    )

    print("Successfully loaded dataset.")
    print("First 5 records:")
    print(df.head())
    
    # Save a small subset for SentinelX seeding
    subset = df.head(100)
    subset.to_csv("backend/enron_subset.csv", index=False)
    print("Saved a 100-record subset to backend/enron_subset.csv")

except Exception as e:
    print(f"Error downloading dataset: {e}")
    print("This might be due to missing Kaggle credentials (~/.kaggle/kaggle.json).")
