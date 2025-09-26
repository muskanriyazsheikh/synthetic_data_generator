# synth.py
import os
import pandas as pd
import matplotlib.pyplot as plt
from sdv.metadata.single_table import SingleTableMetadata
from sdv.single_table import CTGANSynthesizer
from db_connection import get_connection
import warnings
warnings.filterwarnings("ignore")

def save_upload_metadata(filename):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO uploads (filename) VALUES (%s)", (filename,))
    conn.commit()
    cursor.close()
    conn.close()

def plot_real_vs_synthetic_single(real_df, synthetic_df, numeric_columns, out_path="plots/real_vs_synthetic_overall.png"):
    os.makedirs("plots", exist_ok=True)

    real_means = real_df[numeric_columns].mean()
    synthetic_means = synthetic_df[numeric_columns].mean()

    compare_df = pd.DataFrame({
        'Real': real_means,
        'Synthetic': synthetic_means
    })

    ax = compare_df.plot(kind='bar', figsize=(10,6))
    ax.set_title("Real vs Synthetic (Mean)")
    ax.set_ylabel("Mean Value")
    plt.tight_layout()
    plt.savefig(out_path)
    plt.close()
    return out_path

def generate_synthetic_from_csv(csv_path, n_rows=1000, epochs=100):
    """
    Trains a CTGAN on a CSV and returns the synthetic dataframe.
    WARNING: Training CTGAN can be heavy/time-consuming depending on dataset and epochs.
    """
    df = pd.read_csv(csv_path)
    # Basic defensive cleaning: drop all-nulls, small check
    df = df.dropna(how='all')
    if df.shape[0] < 2:
        raise ValueError("Dataset too small to train model")

    metadata = SingleTableMetadata()
    metadata.detect_from_dataframe(df)

    # Find categorical columns heuristically and update
    for col in df.columns:
        if df[col].dtype == object or df[col].nunique() < 10:
            try:
                metadata.update_column(col, sdtype='categorical')
            except Exception:
                pass

    synthesizer = CTGANSynthesizer(metadata=metadata, epochs=epochs)
    synthesizer.fit(df)

    synthetic = synthesizer.sample(n_rows)
    # Save synthetic to CSV
    os.makedirs("data/synthetic", exist_ok=True)
    name = os.path.splitext(os.path.basename(csv_path))[0]
    out_csv = f"data/synthetic/{name}_synthetic_{n_rows}.csv"
    synthetic.to_csv(out_csv, index=False)
    return synthetic, out_csv, df

def save_synthetic_to_mysql(synthetic_df):
    conn = get_connection()
    cursor = conn.cursor()

    # This function assumes synthetic_df columns match the synthetic_dataset table order.
    # You might want to adapt per your real dataset.
    sql = """INSERT INTO synthetic_dataset
    (pregnancies, glucose, blood_pressure, skin_thickness, insulin, bmi, diabetes_pedigree_function, age, outcome)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)"""
    rows = []
    # If synthetic_df has different column naming, attempt to align:
    for _, r in synthetic_df.iterrows():
        try:
            row = (
                float(r.get('Pregnancies', r.get('pregnancies', 0))),
                float(r.get('Glucose', r.get('glucose', 0))),
                float(r.get('BloodPressure', r.get('blood_pressure', r.get('Blood_Pressure', 0)))),
                float(r.get('SkinThickness', r.get('skin_thickness', 0))),
                float(r.get('Insulin', r.get('insulin', 0))),
                float(r.get('BMI', r.get('bmi', 0))),
                float(r.get('DiabetesPedigreeFunction', r.get('diabetes_pedigree_function', 0))),
                float(r.get('Age', r.get('age', 0))),
                str(r.get('Outcome', r.get('outcome', '')))
            )
        except Exception:
            # fallback: create a row of zeros/empty if something not parseable
            row = (0,0,0,0,0,0,0,0,'')
        rows.append(row)

    if rows:
        cursor.executemany(sql, rows)
        conn.commit()

    cursor.close()
    conn.close()
    return len(rows)
