# Verified public datasets of MEASURED physics for printable-part design (2026-09-03)

Verified against repository APIs (Zenodo, DataCite, GitHub, Mendeley, UIUC).
Sizes/licences as reported by metadata. Gaps are gaps, not guesses.

## Propellers / fans
- UIUC Propeller Data Site — 90.9 MB zip. Vol 1 ~140 props 7–19 in; Vol 2 ~70
  props 2.5–9 in INCLUDING four 3D-printed designs (DA4002/4022/4052, NR640 in
  2/3/4-blade variants — proof that printed props were wind-tunnel tested);
  Vol 3: 40 Aero-Naut folding; Vol 4: 17 APC 12–21 in. Static (RPM, CT, CP)
  and advance-ratio (J, CT, CP, η) sweeps + geometry (r/R, c/R, β). No formal
  licence; cite Brandt & Selig 2011 / Deters 2014. Kaggle mirror:
  heitornunes/uiuc-propeller-database. USED IN REFERENCE BUILD 1.
- APC "performance data": COMPUTED (vortex theory), not measured — prior only.
- Tyto Robotics DB: 1,518 motor/prop systems, 174,811 samples; browse-only,
  ToS-restricted, provenance unverifiable.
- No measured small-fan/blower dataset found.

## Airfoils / wings
- UIUC LSAT Vols 1–5 (~120 airfoils, Re 30k–500k, .LFT/.DRG polars, free with
  attribution) + UIUC coordinate database. Mendeley yn4hxc8m8y.1 (S1210
  0–360°, CC-BY). Zenodo 20353482 (NACA 4412 + vortex generators) currently
  has NO files. NASA airfoil self-noise (UCI 291; 1,503 rows, CC-BY).
- Home-test weakness: box-fan flow is turbulent; lift resolvable, drag is
  noise-level; glide-ratio drop with phone video is the honest proxy.

## 3D-printed lattices / shells — BEST FIT
- BU self-driving lab shells (Snapp et al., Nat. Commun. 2024): 25,387 FDM
  compression experiments (13,250 valid) on generalized cylindrical shells,
  vase mode, 7 filaments (PLA, PETG, nylon, 3 TPUs, TPE), Instron 5 kN.
  Processed release github.com/samsilverman/nonlinear-deformation-design
  (MIT): 12,705 samples — parameters.csv (12 design params + material, 2 MB),
  forces.csv (100-point F–d curves, 9.7 MB), displacements.csv. Raw at
  hdl.handle.net/2144/46687 (unverified).
- Mendeley pbj7zcv55y.2 (30 PLA-CF gyroid tapered tubes, F–d + STLs, CC-BY);
  Mendeley dbzdkz95f8.1 (PLA/TPU cellular compression+bending, CC-BY); Dryad
  pk0p2ngw8 (TPU shell buckling, 463 MB, CC0). Deep-DRAM/spinodoid: no open
  experimental data (FEA-dominated).
- Home test: bathroom scale + ruler/phone camera (0–1.5 kN) or drop test with
  phone accelerometer.

## FDM process / strength (use as the "printer prior")
- Mendeley zd6td6svd6.2 (Jul 2026): 500 runs, 10 filaments, 15 infill
  patterns → peak stress, strain, modulus, hardness, roughness; CC-BY (new,
  unreplicated — check for synthetic filling). Zenodo 21930215: PETG, 327 UTS
  values, X/Y/Z orientation, CC-BY. Zenodo 21939238: PLA/ABS dogbones, 35
  settings, 3.88 GB raw, CC-BY. Mendeley phchsd6g87.1 (Sci Data 2024): 102 PLA
  D638 specimens with embedded defects/under-extrusion, full curves, CC-BY.
  Mendeley 8jxw5533py.2: 21 PLA specimens in 7 orientations. Kaggle
  afumetto/3dprinter: 50 rows — too small. CNC Kitchen: no bulk data.
- Small, single-printer, mutually inconsistent — a prior inside other
  problems, not a problem by itself.

## Vibration / isolation
- Fault datasets (MAFAULDA 13 GB; Fraunhofer Fordatis 151.2 unbalance with a
  3D-printed holder, CC-BY; CWRU; NASA IMS) teach imbalance physics, not
  isolator design. Design-relevant but small: Mendeley 2wdk4m5n97 (measured
  FRFs of Al substructures joined by a 3D-printed TPU insert, HDF5 + STL,
  CC-BY); PLA/Al cantilever modal spectra; Zenodo 21476609 (Prusa bed sine
  sweep 60–300 Hz, CC-BY). No printed-isolator transmissibility corpus; PX4
  public logs hit-or-miss. Home test easy (phone accelerometer); data thin.

## Acoustics
- Zenodo 21866746: 32 perforated-plate + TPMS-core configs, absorption/
  reflection/impedance 50–1,600 Hz, STLs INCLUDED, 68.7 MB, CC-BY. Zenodo
  19367655: 144 ASA concentric-tube absorber spectra, CC-BY. Zenodo 17205964:
  octet-truss absorption, CC-BY. Zenodo 20641998: 134 AM surfaces, absorption
  + TL, 714 MB, CC-BY. No muffler/Helmholtz/whistle datasets.
- Phone mic can't replicate ISO 10534, but a resonator's peak frequency and a
  small-fan muffler's insertion loss are measurable to ~±10%.

## Fluids / other — weak
Zenodo 19382503 (drag of 9 printed morphotypes at low Re, CC-BY); trivial pump
set; Loughborough overlapping-propeller noise (CC-BY-NC). No Tesla-valve,
water-rocket, small-turbine, or fan P–Q measured data.

## Ranked shortlist (agent's, adopted)
1. Energy-absorbing printed shell — BU 12,705 F–d curves. Learn params +
   material → F–d curve / plateau force / efficiency. Print vase-mode TPU/PLA
   shells. Measure with bathroom scale + ruler. Pass: plateau within 20% of
   prediction, efficiency beats best of 5 random shells.
2. Small printed propeller — UIUC. DONE as reference build 1 (10 in); a 5–6 in
   PLA variant at 3–6 krpm is the cheaper physical test. Pass: thrust and g/W
   within 15% of prediction, g/W ≥ matched APC.
3. Tuned printed absorber/resonator — Zenodo 21866746 + 19367655. Pass: peak
   frequency within 5% on phone-mic FFT.
4. Load-bearing bracket with FDM prior — Mendeley 500-run + PETG sets. Pass:
   failure load within 20%.
5. TPU isolator — thinnest data; phone-accelerometer test. Pass: resonance
   within 15%, >10 dB attenuation above √2·f_n.
