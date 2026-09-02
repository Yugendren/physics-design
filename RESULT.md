# Reference build 1 — propeller designed from measured physics, no hand engineering (2026-09-03)

## The problem (a real bottleneck)
Endurance for small drones and slow-flying planes is limited by thrust per watt.
Off-the-shelf props are compromises across many motors and speeds. Problem as
numbers: **10-inch diameter, 5,000 RPM, at least 3.0 N (≈306 g) static thrust,
maximize grams of thrust per watt**, printable on a Bambu-class FDM printer.

## How the physics was obtained (from data, not formulas)
- Dataset: UIUC Propeller Data Site, volumes 1–2 — wind-tunnel measurements of
  115 real propellers with chord/twist geometry: 2,121 static (RPM → thrust
  coefficient CT, power coefficient CP) points. Regime used for learning:
  4–20 in, 1,500–12,000 RPM → 1,937 rows, 110 props.
- Model: bootstrap ensemble (6 extra-trees + 4 MLPs) mapping
  [chord at 8 stations, twist at 8 stations, log RPM, log diameter] → log CT,
  log CP. Ensemble disagreement = uncertainty.
- Honest accuracy on HELD-OUT propellers (GroupKFold by prop): R² 0.74 (CT),
  0.81 (CP); mean relative error 9.5% (CT), 13.9% (CP).

## How the design was created (search, NASA-antenna style)
(μ+λ) evolution strategy: population 96, 200 generations, initial population =
measured props, Gaussian mutation, bounds = 3rd–97th percentile of measured
geometry. Objective = lower-confidence-bound of thrust-per-watt (CT lower
bound, CP upper bound), with a thrust floor (≥ 3 N), a smoothness term
(printable, sane blades), and a data-hull penalty (stay near measured physics
so the search cannot exploit model ignorance). Runtime 22 s on the Mac.

## The design (out/design.json)
| r/R | 0.20 | 0.31 | 0.41 | 0.52 | 0.63 | 0.74 | 0.84 | 0.95 |
|---|---|---|---|---|---|---|---|---|
| chord c/R | 0.191 | 0.198 | 0.200 | 0.201 | 0.198 | 0.184 | 0.149 | 0.109 |
| twist β (°) | 24.0 | 21.3 | 18.4 | 15.8 | 12.8 | 10.2 | 8.1 | 5.9 |

Character: a wide, nearly constant chord plateau over the inner two-thirds,
smooth taper to the tip, and lower pitch than the measured baselines (24° root
vs 26–38°) — a low-disc-loading, low-pitch efficiency prop. The model found it
without being told any of that.

Predicted at 10 in / 5,000 RPM: CT 0.095, CP 0.035 → **3.37 N thrust, 26.5 W,
12.97 g/W** (lower bound 11.5 g/W); ensemble log-std 0.04 (CT), 0.08 (CP);
hull distance 2.27 (inside the data cloud).

## Scorecard — did it beat what humans already made?
Every measured propeller was evaluated under the same model at the same
operating point. Best known: gwsdd_10x6 at 12.52 g/W mean (12.0 lower bound);
gwsdd_11x7 at 12.42. The evolved design predicts **12.97 g/W mean (+3.6% over
the best measured geometry) but 11.5 g/W lower bound (−4% vs the best known
lower bound)**. The search's composite objective is higher (9.17 vs 8.63) only
because of the smoothness/hull terms.

Honest reading: **the predicted gain is inside the model's own ~10% error.
This design is a credible candidate, not a demonstrated improvement.** The
physical test decides. Best measured 9-inch props at this RPM reach 13.2–14.5
g/W (at 9 in, i.e., lower tip speed), so the absolute level is plausible.

## The CAD (out/prop_10in_evolved.stl)
Two-blade prop, 254.0 mm diameter, watertight, 10,208 faces, 15.1 cm³, ≈18.8 g
in PLA. Hub Ø16 × 8 mm, bore Ø5.0 mm. Printability rules enforced: min section
thickness 1.2 mm, trailing edge 0.6 mm, flat on bed. Fixed (not searched):
NACA-4412-like section, quarter-chord pitch axis, 2 blades.
Also produced: cad_report.json, design_vs_baselines.png.

## Test protocol (home, ~$40)
Brushless motor (≈ 900–1100 KV on 3S) + ESC + tachometer or ESC RPM telemetry,
kitchen scale thrust stand, USB/inline wattmeter. Measure thrust and electrical
power at 5,000 RPM (ramp up slowly, shield, inspect blades). Compare against a
stock GWS 10x6 / APC 10x4.7 on the same rig. Pass = measured g/W within 10% of
prediction (physics learned correctly); win = beats the stock prop on the same
motor by >5%. Note electrical power includes motor/ESC losses — compare props
on the same motor, not against the wind-tunnel shaft-power numbers.

## What this exercise showed
1. The loop "measured data → learned physics → search → printable CAD" runs
   end to end in under a minute for a real aerodynamic problem.
2. The search found a coherent, smooth, physically plausible design without any
   aerodynamic formula — but only after a bug in the smoothness term was
   fixed; the first run produced a zig-zag twist that the model happily rated
   well. Lesson: the regularizers and the hull penalty ARE the safety system.
3. With ~2k measurements and ~10% model error, learned physics is good enough
   to propose and rank designs, not to prove them. The printer + scale is the
   proof, and every test result is new training data.

## Reproduce
    .venv/bin/python parse_uiuc.py && .venv/bin/python design_prop.py && .venv/bin/python cad_prop.py
