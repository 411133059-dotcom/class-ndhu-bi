# /// script
# requires-python = ">=3.10"
# dependencies = ["pandas"]
# ///
"""把 data/ 的三個 CSV 整理成 docs/data.js（window.DATA），讓 index.html 雙擊即可載入。"""
import json
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
read = lambda n: pd.read_csv(ROOT / "data" / n, encoding="utf-8-sig")

enr = (read("enrollment.csv")
       .groupby(["semester", "college", "dept", "degree", "gender"], as_index=False)["count"].sum())
leave = (read("leave.csv")
         .groupby(["semester", "college", "dept", "degree", "gender", "reason"], as_index=False)
         [["new_leave", "on_leave_end"]].sum())
mp = read("dept_mapping.csv").fillna("")

data = {
    "semesters": sorted(enr["semester"].unique()),
    # 欄位順序見 enrollmentCols / leaveCols；每列是一個陣列以縮小檔案
    "enrollmentCols": ["semester", "college", "dept", "degree", "gender", "count"],
    "enrollment": enr.values.tolist(),
    "leaveCols": ["semester", "college", "dept", "degree", "gender", "reason", "new_leave", "on_leave_end"],
    "leave": leave.values.tolist(),
    "depts": [{"dept": r.dept, "college": r.college,
               "aliases": [a for a in r.aliases.split(";") if a]} for r in mp.itertuples()],
}
out = ROOT / "docs" / "data.js"
out.write_text("window.DATA = " + json.dumps(data, ensure_ascii=False, separators=(",", ":"), default=int) + ";\n",
               encoding="utf-8")

e114 = enr[enr.semester == "114-1"]["count"].sum()
print(f"enrollment rows {len(enr)}, leave rows {len(leave)}, depts {len(mp)}")
print(f"114-1 在學人數合計 {e114}", "OK" if e114 == 10035 else "MISMATCH")
print(f"{out}: {out.stat().st_size/1024:.1f} KB")
