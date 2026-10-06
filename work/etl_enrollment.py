# /// script
# requires-python = ">=3.10"
# dependencies = ["pandas", "xlrd"]
# ///
"""把 114-1 在學人數統計表 (.xls) 轉成 college, dept_raw, program_raw, gender, count 的長表。"""
import re
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
SRC = next((ROOT / "東華大學統計資料" / "在學人數統計表").glob("114-1*.xls"))
OUT = ROOT / "work" / "enrollment_114-1.csv"

# 區段標題 -> program_raw（「碩專班」底下就是碩士在職專班）
SECTIONS = {"博士班": "博士班", "碩士班": "碩士班", "碩專班": "碩士在職專班", "學士班": "學士班"}

def clean(v):
    return None if pd.isna(v) else re.sub(r"\s+", "", str(v)) or None

def num(v):
    return 0 if pd.isna(v) else int(v)

# header=None：前幾列是表頭，資料從欄 0..6 讀取
# 欄：0 學制別, 1 學院, 2 系所, 3 分組, 4 總計合計, 5 總計女, 6 總計男
raw = pd.read_excel(SRC, sheet_name=0, header=None)

rows, program, college, dept = [], None, None, None
for _, r in raw.iloc[3:].iterrows():
    c0 = clean(r[0])
    if c0 and c0.startswith("備註"):
        break
    if c0 and c0.startswith("總計"):
        continue
    if c0 and "合計" in c0:                      # 例如「博士班 合計1」：新區段，不是資料列
        program = SECTIONS[c0.split("合計")[0]]
        college = dept = None
        continue
    # 合併儲存格：只有範圍第一格有值，其餘為空 -> 往下沿用
    if clean(r[1]):
        college, dept = clean(r[1]), None
    if clean(r[2]):
        dept = clean(r[2])
    # 報表的合併範圍有誤：博士班「材料科學與工程學系」的合併儲存格多罩到一列，
    # 該列分組為「應用物理博士班…」，實際屬於物理學系
    row_dept = dept
    if clean(r[3]) and clean(r[3]).startswith("應用物理") and dept != "物理學系":
        row_dept = dept = "物理學系"
    if program is None or dept is None or pd.isna(r[5]) and pd.isna(r[6]) and pd.isna(r[4]):
        continue
    for gender, col in (("女", 5), ("男", 6)):
        rows.append((re.sub(r"[（(].*?[)）]", "", college).strip(), row_dept, program, gender, num(r[col])))

df = (pd.DataFrame(rows, columns=["college", "dept_raw", "program_raw", "gender", "count"])
        .groupby(["college", "dept_raw", "program_raw", "gender"], sort=False, as_index=False)["count"].sum())
df.to_csv(OUT, index=False, encoding="utf-8-sig")
print(f"wrote {OUT} ({len(df)} rows, total {df['count'].sum()})")
