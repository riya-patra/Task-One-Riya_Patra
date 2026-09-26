import pandas as pd

# ---- CONFIG (edit these once you have the actual file) ----
INPUT_FILE = "raw/Dataset for Data Analytics.xlsx"   # your uploaded file
OUTPUT_FILE = "cleaned_dataset.xlsx"
UNIQUE_ID_COL = "OrderID"                              # the true unique identifier column
DATE_COLS = ["Date"]                                   # columns that should be dates
TEXT_COLS_TO_STANDARDIZE = ["ShippingAddress", "PaymentMethod", "OrderStatus", "ReferralSource"]

change_log = []  # each entry: {ChangeID, Description, Impact, Status}


def log_change(change_id, description, impact, status="Resolved"):
    change_log.append(
        {"Change ID": change_id, "Description": description,
         "Impact": impact, "Status": status}
    )


# ---- STEP 1: Load ----
df = pd.read_excel(INPUT_FILE)
print(f"Loaded {len(df)} rows, {len(df.columns)} columns")
print(df.info())

# ---- STEP 2: Missing values ----
missing_before = df.isna().sum()
print("\nMissing values per column:\n", missing_before[missing_before > 0])

for col in df.select_dtypes(include="number").columns:
    n_missing = df[col].isna().sum()
    if n_missing > 0:
        median_val = df[col].median()
        df[col] = df[col].fillna(median_val)
        log_change(f"CR{len(change_log)+1:03d}",
                   f"Imputed '{col}' using Median ({median_val})",
                   f"Preserved {n_missing} records")

for col in df.select_dtypes(include="object").columns:
    n_missing = df[col].isna().sum()
    if n_missing > 0 and col not in DATE_COLS:
        mode_val = df[col].mode(dropna=True)
        mode_val = mode_val[0] if not mode_val.empty else "Unknown"
        df[col] = df[col].fillna(mode_val)
        log_change(f"CR{len(change_log)+1:03d}",
                   f"Imputed '{col}' using Mode ('{mode_val}')",
                   f"Preserved {n_missing} records")

# ---- STEP 3: Duplicates (based on true unique ID, not full-row match) ----
if UNIQUE_ID_COL in df.columns:
    dupe_mask = df.duplicated(subset=[UNIQUE_ID_COL], keep="first")
    n_dupes = dupe_mask.sum()
    if n_dupes > 0:
        df = df[~dupe_mask]
        log_change(f"CR{len(change_log)+1:03d}",
                   f"Removed duplicate rows on '{UNIQUE_ID_COL}'",
                   f"Removed {n_dupes} duplicate records")

# ---- STEP 4: Standardize formats ----
for col in TEXT_COLS_TO_STANDARDIZE:
    if col in df.columns:
        df[col] = df[col].astype(str).str.strip().str.title()
        log_change(f"CR{len(change_log)+1:03d}",
                   f"Standardized casing/whitespace in '{col}'",
                   "Consistent text formatting across column")

for col in DATE_COLS:
    if col in df.columns:
        df[col] = pd.to_datetime(df[col], errors="coerce").dt.strftime("%Y-%m-%d")
        log_change(f"CR{len(change_log)+1:03d}",
                   f"Standardized '{col}' to ISO 8601 (YYYY-MM-DD)",
                   "Consistent date format across column")

for col in df.select_dtypes(include="number").columns:
    df[col] = df[col].round(2)

# ---- STEP 5: Verification gate ----
dupe_check = df.duplicated(subset=[UNIQUE_ID_COL]).sum() if UNIQUE_ID_COL in df.columns else "N/A"
bad_dates = 0
for col in DATE_COLS:
    if col in df.columns:
        bad_dates += df[col].isna().sum()

print(f"\nVerification -> duplicate IDs: {dupe_check}, bad dates: {bad_dates}")
assert dupe_check == 0, "Duplicate IDs remain - investigate before submitting"
assert bad_dates == 0, "Unparseable dates remain - investigate before submitting"

# ---- STEP 6: Save cleaned data + change log ----
df.to_excel(OUTPUT_FILE, index=False)
log_df = pd.DataFrame(change_log)
log_df.to_excel("change_log.xlsx", index=False)
print(f"\nSaved: {OUTPUT_FILE}, change_log.xlsx")
print(log_df) 