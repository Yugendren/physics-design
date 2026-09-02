#!/usr/bin/env python3
"""Learn propeller physics from measured data, then search for a new design.

No aerodynamic formulas are used to create the design. The "physics" is an ensemble
of models trained on UIUC wind-tunnel measurements (geometry + RPM → thrust and power
coefficients). An evolution strategy then searches chord/twist distributions to
maximize a lower-confidence-bound on thrust-per-watt at a fixed operating point,
with a required minimum thrust, a smoothness regularizer (printability), and a
data-hull penalty so the search cannot wander where the models know nothing.

Outputs: out/design.json, out/design_vs_baselines.png, out/surrogate_cv.json
Runtime: seconds to ~1 minute on the Mac (tiny data, small ensemble).
"""

import json
import time
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import ExtraTreesRegressor
from sklearn.model_selection import GroupKFold
from sklearn.neural_network import MLPRegressor
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

root = Path(__file__).resolve().parent
out = root / "out"
out.mkdir(exist_ok=True)
RHO = 1.225

# ---- operating point: the "bottleneck problem" ------------------------------
# Endurance multirotor / slow-flyer: maximize static thrust per watt at a fixed
# 10-inch diameter and 5000 RPM, with at least 3.0 N of thrust (≈306 g).
D_IN, RPM, T_MIN = 10.0, 5000.0, 3.0

C_COLS = [f"c{i}" for i in range(8)]
B_COLS = [f"b{i}" for i in range(8)]
FEATS = C_COLS + B_COLS + ["log_n", "log_D"]


def features(df):
    X = df[C_COLS + B_COLS].to_numpy(dtype=float)
    ln = np.log(df["rpm"].to_numpy(dtype=float) / 60.0)[:, None]
    lD = np.log(df["diam_in"].to_numpy(dtype=float) * 0.0254)[:, None]
    return np.hstack([X, ln, lD])


class Ensemble:
    """Bootstrap ensemble of tree + MLP regressors on log-targets; disagreement = uncertainty."""

    def __init__(self, n_trees=6, n_mlp=4, seed=0):
        self.members = []
        rng = np.random.default_rng(seed)
        for i in range(n_trees):
            self.members.append(("et", ExtraTreesRegressor(n_estimators=300, min_samples_leaf=2,
                                                            max_features=0.7, random_state=int(rng.integers(1e9)))))
        for i in range(n_mlp):
            self.members.append(("mlp", make_pipeline(StandardScaler(), MLPRegressor(
                hidden_layer_sizes=(64, 64), alpha=1e-3, max_iter=3000, random_state=int(rng.integers(1e9))))))
        self.rng = rng

    def fit(self, X, Y):
        n = len(X)
        for kind, m in self.members:
            idx = self.rng.integers(0, n, n)  # bootstrap
            m.fit(X[idx], Y[idx])
        return self

    def predict(self, X):
        P = np.stack([m.predict(X) for _, m in self.members])  # (members, n, 2)
        return P.mean(axis=0), P.std(axis=0)


def cross_validate(df, X, Y):
    """Honest generalization: hold out whole propellers (GroupKFold by prop)."""
    gkf = GroupKFold(n_splits=5)
    preds = np.zeros_like(Y)
    for tr, te in gkf.split(X, Y, groups=df["prop"]):
        e = Ensemble(n_trees=4, n_mlp=2, seed=1).fit(X[tr], Y[tr])
        preds[te], _ = e.predict(X[te])
    r2 = 1 - ((preds - Y) ** 2).sum(axis=0) / ((Y - Y.mean(axis=0)) ** 2).sum(axis=0)
    mape = np.abs(np.exp(preds) - np.exp(Y)).mean(axis=0) / np.exp(Y).mean(axis=0)
    return {"r2_logCT": round(float(r2[0]), 3), "r2_logCP": round(float(r2[1]), 3),
            "relative_error_CT": round(float(mape[0]), 3), "relative_error_CP": round(float(mape[1]), 3)}


def perf_from_coeffs(ct, cp, D_in=D_IN, rpm=RPM):
    D = D_in * 0.0254
    n = rpm / 60.0
    T = ct * RHO * n ** 2 * D ** 4
    P = cp * RHO * n ** 3 * D ** 5
    return T, P, (T / 9.81 * 1000.0) / P


def main():
    t0 = time.time()
    df = pd.read_csv(root / "data" / "uiuc_static.csv")
    # keep the regime that resembles the target so the models learn relevant physics
    df = df[(df.diam_in >= 4) & (df.diam_in <= 20) & (df.rpm >= 1500) & (df.rpm <= 12000)].reset_index(drop=True)
    X = features(df)
    Y = np.log(df[["CT", "CP"]].to_numpy(dtype=float))
    cv = cross_validate(df, X, Y)
    print("surrogate CV (held-out props):", cv)
    ens = Ensemble().fit(X, Y)

    # geometry bounds and data hull from the training props
    G = df.drop_duplicates("prop")[C_COLS + B_COLS].to_numpy(dtype=float)
    lo, hi = np.percentile(G, 3, axis=0), np.percentile(G, 97, axis=0)
    g_mean, g_std = G.mean(axis=0), G.std(axis=0) + 1e-9
    Gz = (G - g_mean) / g_std

    def hull_distance(g):
        z = (g - g_mean) / g_std
        d = np.sqrt(((Gz[None, :, :] - z[:, None, :]) ** 2).sum(axis=2)).min(axis=1)
        return d  # standardized distance to nearest measured prop

    log_n, log_D = np.log(RPM / 60.0), np.log(D_IN * 0.0254)

    def evaluate(g):
        """g: (pop, 16) chord/twist. Returns objective (higher better) and details."""
        Xg = np.hstack([g, np.full((len(g), 1), log_n), np.full((len(g), 1), log_D)])
        mu, sd = ens.predict(Xg)
        ct_lo = np.exp(mu[:, 0] - 1.0 * sd[:, 0])  # lower confidence bound on thrust
        cp_hi = np.exp(mu[:, 1] + 1.0 * sd[:, 1])  # upper bound on power
        T, P, gpw = perf_from_coeffs(ct_lo, cp_hi)
        # smoothness (printable, sane blades): penalize second differences
        c2 = np.abs(np.diff(g[:, :8], n=2, axis=1)).sum(axis=1)
        b2 = np.abs(np.diff(g[:, 8:], n=2, axis=1)).sum(axis=1)
        hull = hull_distance(g)
        obj = gpw.copy()
        obj -= 40.0 * np.maximum(0.0, T_MIN - T)          # thrust floor
        obj -= 30.0 * c2 + 0.5 * b2                       # jaggedness (chord in c/R, twist in degrees)
        obj -= 4.0 * np.maximum(0.0, hull - 2.5) ** 2     # stay near measured physics
        return obj, {"T": T, "P": P, "gpw": gpw, "ct_lo": ct_lo, "cp_hi": cp_hi, "hull": hull, "mu": mu, "sd": sd}

    # ---- evolution strategy (mu + lambda, Gaussian mutation with adaptive step) ----
    rng = np.random.default_rng(0)
    pop = 96
    # start from measured props (data-grounded initial population)
    parents = G[rng.integers(0, len(G), pop)].copy()
    sigma = 0.15 * (hi - lo)
    best_hist = []
    for gen in range(200):
        kids = parents + rng.normal(0, 1, parents.shape) * sigma
        kids = np.clip(kids, lo, hi)
        allg = np.vstack([parents, kids])
        obj, det = evaluate(allg)
        order = np.argsort(-obj)
        parents = allg[order[:pop]]
        best_hist.append(float(obj[order[0]]))
        if gen % 50 == 0:
            sigma *= 0.7
    obj, det = evaluate(parents)
    i = int(np.argmax(obj))
    best = parents[i]

    # ---- compare with the best MEASURED props at the same operating point -------
    same = df[(df.diam_in.between(9, 11)) & (df.rpm.between(4000, 6000))]
    base_rows = []
    for pid, grp in same.groupby("prop"):
        r = grp.iloc[(grp.rpm - RPM).abs().argsort().iloc[0]]
        T, P, gpw = perf_from_coeffs(r.CT, r.CP, r.diam_in, r.rpm)
        base_rows.append({"prop": pid, "diam_in": float(r.diam_in), "rpm": float(r.rpm), "measured_CT": float(r.CT),
                          "measured_CP": float(r.CP), "thrust_N": round(T, 3), "power_W": round(P, 2), "g_per_W": round(gpw, 2)})
    base = sorted(base_rows, key=lambda r: -r["g_per_W"])
    # surrogate's opinion of those same props at exactly D_IN, RPM (apples to apples)
    for b in base[:10]:
        g = df[df.prop == b["prop"]].iloc[0][C_COLS + B_COLS].to_numpy(dtype=float)[None, :]
        _, d = evaluate(g)
        b["surrogate_g_per_W_at_target"] = round(float(d["gpw"][0]), 2)

    # the honest scorecard: EVERY measured geometry evaluated at the target point under the
    # same objective (LCB g/W + penalties). The search must beat the best of these.
    allprops = df.drop_duplicates("prop")
    obj_known, det_known = evaluate(allprops[C_COLS + B_COLS].to_numpy(dtype=float))
    order = np.argsort(-obj_known)
    known_best = [{"prop": allprops.iloc[k].prop, "objective": round(float(obj_known[k]), 2),
                   "g_per_W_lower_bound": round(float(det_known["gpw"][k]), 2),
                   "g_per_W_mean": round(float(perf_from_coeffs(np.exp(det_known["mu"][k, 0]), np.exp(det_known["mu"][k, 1]))[2]), 2),
                   "thrust_N_lower": round(float(det_known["T"][k]), 3)} for k in order[:5]]

    T, P, gpw = perf_from_coeffs(np.exp(det["mu"][i, 0]), np.exp(det["mu"][i, 1]))
    design = {
        "operating_point": {"diam_in": D_IN, "rpm": RPM, "thrust_min_N": T_MIN},
        "r_R": np.linspace(0.2, 0.95, 8).round(3).tolist(),
        "c_R": best[:8].round(4).tolist(), "beta_deg": best[8:].round(2).tolist(),
        "predicted": {"CT_mean": round(float(np.exp(det["mu"][i, 0])), 4), "CP_mean": round(float(np.exp(det["mu"][i, 1])), 4),
                      "CT_lower": round(float(det["ct_lo"][i]), 4), "CP_upper": round(float(det["cp_hi"][i]), 4),
                      "thrust_N_mean": round(float(T), 3), "power_W_mean": round(float(P), 2), "g_per_W_mean": round(float(gpw), 2),
                      "g_per_W_lower_bound": round(float(det["gpw"][i]), 2),
                      "ensemble_std_logCT": round(float(det["sd"][i, 0]), 3), "ensemble_std_logCP": round(float(det["sd"][i, 1]), 3),
                      "hull_distance": round(float(det["hull"][i]), 3)},
        "surrogate_cv": cv, "n_training_rows": int(len(df)), "n_training_props": int(df.prop.nunique()),
        "search_objective_of_design": round(float(obj[i]), 2),
        "best_known_geometries_under_same_objective": known_best,
        "beats_best_known_geometry": bool(obj[i] > known_best[0]["objective"]),
        "best_measured_baselines_same_regime": base[:10],
        "search": {"population": pop, "generations": 200, "objective": "lower-confidence-bound g/W with thrust floor, smoothness, hull penalty",
                   "best_objective_history": best_hist[::20]},
        "runtime_s": round(time.time() - t0, 1),
        "caveats": ["Design is optimal under an ensemble learned from ~2k static measurements of ~100 props; "
                    "the lower-confidence-bound objective and hull penalty limit but do not eliminate surrogate exploitation.",
                    "Airfoil section shape is NOT a design variable (fixed in cad_prop.py); only chord and twist are learned/searched.",
                    "Must be validated by a physical thrust/power test (motor + ESC + scale + wattmeter) at 5000 RPM."],
    }
    (out / "design.json").write_text(json.dumps(design, indent=2))
    print(json.dumps({k: design[k] for k in ("c_R", "beta_deg", "predicted")}, indent=1))
    print(f"design objective {design['search_objective_of_design']} vs best known geometry "
          f"{known_best[0]['prop']} {known_best[0]['objective']} → beats known: {design['beats_best_known_geometry']}")
    for k in known_best:
        print("   known:", k)
    print("best measured baselines (9-11 in, 4-6k RPM):")
    for b in base[:4]:
        print("  ", {kk: (round(float(vv), 2) if isinstance(vv, (float, np.floating)) else vv) for kk, vv in b.items()})

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(1, 2, figsize=(11, 4))
    rr = design["r_R"]
    for b in base[:5]:
        g = df[df.prop == b["prop"]].iloc[0]
        ax[0].plot(rr, g[C_COLS].to_numpy(), color="gray", alpha=0.6, label=b["prop"])
        ax[1].plot(rr, g[B_COLS].to_numpy(), color="gray", alpha=0.6)
    ax[0].plot(rr, best[:8], "r-o", label="evolved design"); ax[1].plot(rr, best[8:], "r-o")
    ax[0].set_title("chord c/R vs r/R"); ax[1].set_title("twist beta (deg) vs r/R"); ax[0].legend(fontsize=7)
    fig.savefig(out / "design_vs_baselines.png", dpi=110, bbox_inches="tight")
    print("saved", out / "design.json", out / "design_vs_baselines.png", f"({design['runtime_s']} s)")


if __name__ == "__main__":
    main()
