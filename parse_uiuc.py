#!/usr/bin/env python3
"""Parse the UIUC propeller database (vols 1-2 with geometry) into a learning table.

Rows = (prop, RPM) static measurements joined with the prop's geometry, resampled onto
a fixed radial grid. Output: data/uiuc_static.parquet (+ csv) and data/props.json.
"""

import json
import re
from pathlib import Path

import numpy as np
import pandas as pd

root = Path(__file__).resolve().parent
db = root / "data" / "UIUC-propDB"
R_GRID = np.linspace(0.2, 0.95, 8)  # r/R stations used as features


def parse_geom(path: Path):
    rows = []
    for line in path.read_text().splitlines()[1:]:
        p = line.split()
        if len(p) >= 3:
            try:
                rows.append([float(p[0]), float(p[1]), float(p[2])])
            except ValueError:
                pass
    a = np.array(rows)
    if len(a) < 4:
        return None
    r, c, b = a[:, 0], a[:, 1], a[:, 2]
    return {"c_R": np.interp(R_GRID, r, c).tolist(), "beta_deg": np.interp(R_GRID, r, b).tolist(),
            "r_min": float(r.min()), "r_max": float(r.max())}


def parse_static(path: Path):
    rows = []
    for line in path.read_text().splitlines()[1:]:
        p = line.split()
        if len(p) >= 3:
            try:
                rows.append([float(p[0]), float(p[1]), float(p[2])])
            except ValueError:
                pass
    return np.array(rows) if rows else None


def prop_id_and_diam(name: str):
    """'apcsf_9x4.7_geom' -> ('apcsf_9x4.7', 9.0 in). Names like 'ef_130x70' mean 13.0x7.0."""
    m = re.match(r"([a-z0-9]+)_([0-9.]+)x([0-9.]+)", name)
    if not m:
        return None, None
    fam, d, p = m.group(1), m.group(2), m.group(3)
    D = float(d)
    P = float(p)
    # volume-2 names encode tenths without a dot: 130x70 = 13.0x7.0, 96x70 = 9.6x7.0
    if "." not in d and (len(d) >= 3 or D > 24):
        D = float(d) / 10.0
        P = float(p) / 10.0 if "." not in p else P
    return f"{fam}_{d}x{p}", (D, P)


def main():
    props = {}
    for vol in ("volume-1", "volume-2"):
        for g in sorted((db / vol / "data").glob("*_geom.txt")):
            pid, dp = prop_id_and_diam(g.stem)
            geom = parse_geom(g)
            if pid and geom and dp:
                props[pid] = {"vol": vol, "diam_in": dp[0], "pitch_in": dp[1], **geom, "static_files": []}
    for vol in ("volume-1", "volume-2"):
        for s in sorted((db / vol / "data").glob("*static*.txt")):
            pid, _ = prop_id_and_diam(s.stem)
            if pid in props:
                props[pid]["static_files"].append(str(s.relative_to(db)))
    rows = []
    for pid, p in props.items():
        for sf in p["static_files"]:
            a = parse_static(db / sf)
            if a is None:
                continue
            for rpm, ct, cp in a:
                if ct <= 0 or cp <= 0 or rpm <= 0:
                    continue
                rows.append({"prop": pid, "vol": p["vol"], "diam_in": p["diam_in"], "pitch_in": p["pitch_in"],
                             "rpm": rpm, "CT": ct, "CP": cp,
                             **{f"c{i}": v for i, v in enumerate(p["c_R"])},
                             **{f"b{i}": v for i, v in enumerate(p["beta_deg"])}})
    df = pd.DataFrame(rows)
    df["D_m"] = df["diam_in"] * 0.0254
    df["n"] = df["rpm"] / 60.0
    rho = 1.225
    df["thrust_N"] = df["CT"] * rho * df["n"] ** 2 * df["D_m"] ** 4
    df["power_W"] = df["CP"] * rho * df["n"] ** 3 * df["D_m"] ** 5
    df["g_per_W"] = df["thrust_N"] / 9.81 * 1000 / df["power_W"]
    df["FM"] = df["CT"] ** 1.5 / (np.sqrt(2) * df["CP"])  # static figure of merit
    df["tip_speed"] = np.pi * df["D_m"] * df["n"]
    out = root / "data" / "uiuc_static.csv"
    df.to_csv(out, index=False)
    (root / "data" / "props.json").write_text(json.dumps(props, indent=1))
    print(f"props with geometry: {len(props)}; static rows: {len(df)}; "
          f"diam range {df.diam_in.min()}-{df.diam_in.max()} in; rpm {df.rpm.min():.0f}-{df.rpm.max():.0f}")
    print(df[["prop", "rpm", "CT", "CP", "thrust_N", "power_W", "g_per_W", "FM"]].describe().round(3).to_string())
    best = df.sort_values("g_per_W", ascending=False).drop_duplicates("prop").head(8)
    print("\nBest measured thrust-per-watt props (static):")
    print(best[["prop", "diam_in", "pitch_in", "rpm", "thrust_N", "power_W", "g_per_W", "FM"]].round(3).to_string())


if __name__ == "__main__":
    main()
