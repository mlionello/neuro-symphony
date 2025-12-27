import pandas as pd

KEY = ["userid", "expid", "track_number"]

df_newgpt = pd.read_csv('/home/matteo/Downloads/music_context_code_cleaned/final.csv')
df_oldlegacy = pd.read_csv('/home/matteo/Downloads/music_context_code_cleaned/originalcode_mat.csv')

# find rows only in A, only in B, and in both
diff = df_newgpt.merge(df_oldlegacy, on=KEY, how="outer", indicator=True)

only_in_a = diff[diff["_merge"] == "left_only"]
only_in_b = diff[diff["_merge"] == "right_only"]
in_both   = diff[diff["_merge"] == "both"]

print("only_in_a:", len(only_in_a))
print("only_in_b:", len(only_in_b))
print("in_both:", len(in_both))


only_in_a_by_user = only_in_a.groupby("userid").size().sort_values(ascending=False)
only_in_b_by_user = only_in_b.groupby("userid").size().sort_values(ascending=False)

users_a = set(df_newgpt["userid"].dropna().unique())
users_b = set(df_oldlegacy["userid"].dropna().unique())



print("Users only in df_newgpt:", len(users_a - users_b))
print("Users only in df_oldlegacy:", len(users_b - users_a))


USER = "c1302c7457c579f3"

cols = [
    "description_score_mvt_valence",
    "aggregated_condition_injected",
    "track_q2_1",
    "track_q2_2",
]

# Keep only columns that exist (in case one CSV is missing something)
cols_new = [c for c in cols if c in df_newgpt.columns]
cols_old = [c for c in cols if c in df_oldlegacy.columns]

a = df_newgpt.loc[df_newgpt["userid"].astype(str) == USER, KEY + cols_new].copy()
b = df_oldlegacy.loc[df_oldlegacy["userid"].astype(str) == USER, KEY + cols_old].copy()

a = a.sort_values(KEY)
b = b.sort_values(KEY)

# Outer merge to show rows missing on either side too
cmp = a.merge(b, on=KEY, how="outer", suffixes=("_new", "_old"), indicator=True)

# Compute per-column diff flags where both sides exist
for c in cols:
    c_new, c_old = f"{c}_new", f"{c}_old"
    if c_new in cmp.columns and c_old in cmp.columns:
        cmp[f"{c}_diff"] = cmp[c_new].astype(str) != cmp[c_old].astype(str)

# Show everything for that user
pd.set_option("display.max_rows", 500)
pd.set_option("display.max_columns", 200)
print(cmp)
