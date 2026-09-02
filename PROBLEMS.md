# Bottleneck problems a Bambu-class printer can solve — with physics learned, not hand-derived (2026-09-03)

Printer envelope assumed (Bambu X1/P1/A1 class): FDM, 0.4 mm nozzle, ~256 mm
cube, PLA/PETG/ABS/TPU, ±0.1–0.2 mm, min wall ~0.8 mm, anisotropic strength
(layer adhesion ~50–70% of in-plane), no conductors, no metal, heat limit
~60 °C (PLA) / ~100 °C (ABS/ASA). Design method for all: a simulated or
data-learned environment + search/learning (evolution, RL, diffusion), NASA
evolved-antenna style — the model discovers the geometry; humans supply only
the environment, constraints, and the test.

| # | Bottleneck problem | Why current designs are limited | Environment (physics oracle) | Data | Printed part (material) | Home test | Feasibility now |
|---|---|---|---|---|---|---|---|
| 1 | Endurance propeller for small drones/planes — thrust per watt | Off-the-shelf props are compromises across many motors/speeds; small-prop aero is poorly captured by textbook design | Surrogate learned from UIUC wind-tunnel measurements (2,121 static points, 115 props) ± BEMT cross-check | UIUC propDB (real sensor data) | 2-blade prop, PLA/PETG | motor + ESC + kitchen scale + USB wattmeter (~$40) | HIGH — executed here (out/) |
| 2 | FPV vibration isolation mount (jello / gyro noise) | Generic silicone grommets tuned for nobody; TPU lattice shapes designed by guesswork | Linear FEA harmonic response (scikit-fem / JAX-FEM) on voxel lattices; reward = transmissibility in the noise band | Betaflight blackbox logs (public), TPU datasheets | TPU isolator / camera mount | phone or FC accelerometer | HIGH (build next) |
| 3 | Evolved wire antenna FORMER for 5.8 GHz / 915 MHz | Hobby antennas are copies of a few canonical shapes; bent-wire designs outperform but no one searches them | NEC-2 (PyNEC) — exactly the NASA ST5 setup | none needed (simulator) | printed former/jig holding the evolved wire path | NanoVNA SWR ($50), RSSI | HIGH; printed part is the jig, not the radiator |
| 4 | Impact / drop protection insert (phones, drones, shipping) | Foam is one-size; printed lattices designed by trial | Explicit nonlinear FEA is heavy → learn from published lattice compression datasets + a spring-network sim | Zenodo/Mendeley lattice crush tests (to verify) | TPU lattice pad | drop test with phone accelerometer in a box | MEDIUM (sim fidelity) |
| 5 | Minimum-material load bracket / hook (shelves, wall mounts) | Human designs are over-built and ignore layer anisotropy | FEA with anisotropic PLA model learned from FDM tensile datasets | Kaggle/Mendeley FDM strength sets | PLA bracket | weights + luggage scale | HIGH but low novelty |
| 6 | Compliant gripper finger / snap-fit clip with target force | Snap-fits are designed by rule of thumb; break or won't hold | Nonlinear FEA (large deflection) + learned PLA fatigue | FDM datasets | PLA/PETG clip | luggage scale pull test | MEDIUM |
| 7 | Passive acoustic part: fan-noise resonator, quiet duct | Analytic mufflers assume plane waves; printed geometry can be arbitrary | FDTD/BEM acoustic sim (openly available) | phone-mic spectra | PLA resonator/duct | phone microphone spectrum | MEDIUM (sim cost) |
| 8 | Low-Reynolds wing/glider section | Textbook airfoils are poor at low Re; measured polars exist | Surrogate on UIUC low-speed airfoil tests + XFOIL | UIUC LSAT data | PLA wing/fin | fan + scale, or glide test | MEDIUM |

Excluded by the printer envelope: anything conductive (no printed antennas or
circuits), anything hot (heat sinks, engine parts), high-cycle structural
parts in PLA (creep), sub-0.8 mm features.

Selection for the reference build: #1 — the only one with a large REAL sensor
dataset already on disk, a cheap unambiguous test, and a genuine bottleneck
(flight time). #2 follows because its demand is validated (research/08) and
its test instrument is a phone.

## Update after dataset verification (DATASETS.md, 2026-09-03)
- NEW #1 candidate for the next build: **energy-absorbing printed shell** —
  the Boston University self-driving-lab dataset holds 12,705 real FDM
  compression experiments (F–d curves, 7 filaments incl. three TPUs, MIT
  licence, on GitHub). FDM-native, parametric, large: the best learnable
  dataset in the whole survey. Home test = bathroom scale + ruler.
- Propeller (#1 above) confirmed as the right first build; UIUC Vol 2 even
  contains four wind-tunnel-tested 3D-printed props. A 5–6 in variant is the
  cheaper physical test than the 10 in reference.
- Acoustic absorbers gained a real dataset with STLs (Zenodo 21866746) →
  promoted to a strong #3.
- FPV isolator (#2 above) demoted on DATA: no printed-isolator
  transmissibility corpus exists; would rely on FEA + three small FRF sets.
- Impact lattice: Deep-DRAM/spinodoid experimental data is not open; the BU
  shells dataset covers the same physics better.
- Wing/airfoil: data rich (UIUC LSAT) but the home test cannot resolve drag.
