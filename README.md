# physics_design

Designing printable parts from measured physics rather than formulas. Reference build 1: a 10-inch propeller for 5,000 RPM, at least 3.0 N static thrust, maximising thrust per watt.

- Data: UIUC Propeller Data Site, volumes 1–2. 1,937 static wind-tunnel rows across 110 propellers with chord and twist geometry.
- Model: bootstrap ensemble (6 extra-trees, 4 MLPs) mapping geometry, RPM and diameter to thrust and power coefficients. Ensemble disagreement is used as uncertainty.
- Held-out accuracy (GroupKFold by propeller): R² 0.74 (CT), 0.81 (CP); mean relative error 9.5% and 13.9%.
- Design: search over geometry against the ensemble; output STL in `out/`.

See `RESULT.md` for the full write-up, `DATASETS.md` for verified public datasets, and `PROBLEMS.md` for open issues.
