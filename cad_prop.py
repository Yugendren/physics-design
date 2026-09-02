#!/usr/bin/env python3
"""Turn the evolved chord/twist design into a printable two-blade propeller STL.

Fixed choices (not searched): NACA 4412-like section, quarter-chord pitch axis,
hub Ø16 x 8 mm with a Ø5.0 mm bore. Printability rules for a Bambu-class FDM
printer: minimum section thickness 1.2 mm, trailing-edge thickness 0.6 mm,
diameter ≤ 254 mm (fits a 256 mm bed along an axis), flat print orientation.
Output: out/prop_<D>in.stl and out/cad_report.json
"""

import json
from pathlib import Path

import numpy as np
import trimesh

root = Path(__file__).resolve().parent
out = root / "out"
MIN_THICK_MM, TE_THICK_MM = 1.2, 0.6
HUB_R, HUB_H, BORE_D = 8.0, 8.0, 5.0
N_SEC_PTS = 60


def naca4(m=0.04, p=0.4, t=0.12, n=N_SEC_PTS, te_gap=0.0):
    """Closed NACA 4-digit section, x from 0..1, returns (x, y) upper then lower."""
    beta = np.linspace(0, np.pi, n // 2)
    x = 0.5 * (1 - np.cos(beta))
    yt = 5 * t * (0.2969 * np.sqrt(x) - 0.1260 * x - 0.3516 * x ** 2 + 0.2843 * x ** 3 - 0.1036 * x ** 4)
    yt += te_gap * x  # open the trailing edge slightly for printability
    yc = np.where(x < p, m / p ** 2 * (2 * p * x - x ** 2), m / (1 - p) ** 2 * ((1 - 2 * p) + 2 * p * x - x ** 2))
    dyc = np.where(x < p, 2 * m / p ** 2 * (p - x), 2 * m / (1 - p) ** 2 * (p - x))
    th = np.arctan(dyc)
    xu, yu = x - yt * np.sin(th), yc + yt * np.cos(th)
    xl, yl = x + yt * np.sin(th), yc - yt * np.cos(th)
    xs = np.concatenate([xu[::-1], xl[1:]])
    ys = np.concatenate([yu[::-1], yl[1:]])
    return xs, ys


def blade_mesh(r_R, c_R, beta_deg, D_mm, n_span=40):
    R = D_mm / 2.0
    rs = np.linspace(HUB_R * 0.85, R, n_span)
    c = np.interp(rs / R, r_R, c_R) * R
    b = np.radians(np.interp(rs / R, r_R, beta_deg))
    # taper the last 4% of span to a rounded tip
    tip = rs > 0.96 * R
    c[tip] *= np.clip(1 - (rs[tip] - 0.96 * R) / (0.04 * R), 0.15, 1.0)
    sections = []
    for ri, ci, bi in zip(rs, c, b):
        t_ratio = max(0.12, MIN_THICK_MM / max(ci, 1e-6))  # enforce min thickness
        te_gap = TE_THICK_MM / max(ci, 1e-6)
        xs, ys = naca4(t=min(t_ratio, 0.35), te_gap=te_gap)
        # pitch axis at quarter chord; chordwise along Y, thickness along Z, span along X
        xy = np.stack([(xs - 0.25) * ci, ys * ci], axis=1)
        rot = np.array([[np.cos(bi), -np.sin(bi)], [np.sin(bi), np.cos(bi)]])
        yz = xy @ rot.T
        sections.append(np.column_stack([np.full(len(yz), ri), yz[:, 0], yz[:, 1]]))
    V = np.vstack(sections)
    m = len(sections[0])
    F = []
    for s in range(n_span - 1):
        a, bidx = s * m, (s + 1) * m
        for k in range(m):
            k2 = (k + 1) % m
            F.append([a + k, bidx + k, bidx + k2]); F.append([a + k, bidx + k2, a + k2])
    # caps
    for base_idx, flip in ((0, False), ((n_span - 1) * m, True)):
        for k in range(1, m - 1):
            tri = [base_idx, base_idx + k, base_idx + k + 1]
            F.append(tri[::-1] if flip else tri)
    mesh = trimesh.Trimesh(V, np.array(F), process=True)
    trimesh.repair.fix_normals(mesh)
    return mesh


def main():
    design = json.loads((out / "design.json").read_text())
    D_in = design["operating_point"]["diam_in"]
    D_mm = D_in * 25.4
    assert D_mm <= 254.5, "diameter exceeds a 256 mm bed"
    b1 = blade_mesh(np.array(design["r_R"]), np.array(design["c_R"]), np.array(design["beta_deg"]), D_mm)
    b2 = b1.copy(); b2.apply_transform(trimesh.transformations.rotation_matrix(np.pi, [0, 0, 1]))
    hub = trimesh.creation.cylinder(radius=HUB_R, height=HUB_H, sections=96)
    bore = trimesh.creation.cylinder(radius=BORE_D / 2, height=HUB_H * 3, sections=64)
    body = trimesh.boolean.union([hub, b1, b2], engine="manifold")
    prop = trimesh.boolean.difference([body, bore], engine="manifold")
    path = out / f"prop_{D_in:g}in_evolved.stl"
    prop.export(path)
    vol_cm3 = prop.volume / 1000.0
    rep = {"stl": str(path), "diameter_mm": D_mm, "watertight": bool(prop.is_watertight),
           "faces": int(len(prop.faces)), "volume_cm3": round(vol_cm3, 2), "mass_g_PLA": round(vol_cm3 * 1.24, 1),
           "bbox_mm": [round(float(x), 1) for x in prop.extents],
           "print_rules": {"min_section_thickness_mm": MIN_THICK_MM, "trailing_edge_mm": TE_THICK_MM,
                           "hub": f"Ø{2*HUB_R} x {HUB_H} mm, bore Ø{BORE_D} mm", "orientation": "flat on bed, blades in XY"},
           "fixed_choices": "NACA 4412-like section, quarter-chord pitch axis, 2 blades — not searched",
           "safety": "PLA at 5000 RPM / 254 mm: test behind a shield, ramp RPM up slowly, inspect for cracks; "
                     "this is a research artifact, not a flight-rated part"}
    (out / "cad_report.json").write_text(json.dumps(rep, indent=2))
    print(json.dumps(rep, indent=1))


if __name__ == "__main__":
    main()
