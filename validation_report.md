# Capacity Validation Report -- Phase Family Logic

Generated: 2026-02-18 14:26

## 1. Methodology

Phases sharing a numeric base (e.g., 1, 1O, 1F, 1OF) belong to the same **phase family**.
Within each family, only the **latest MP Ramp configuration** with capacity > 0 counts.
Phases at the same date = capacity split (summed). Sum across families = factory total.

### Terminology

- **Standard Rigid**: Glass substrate + glass seal (no TFE)
- **Thin Profile**: Glass substrate + TFE encapsulation
- **Foldable**: PI/Flexible/Hybrid substrate + TFE encapsulation
- **Effective Capacity**: min(TFT, OLED MG-equiv, OCT) -- bottleneck-limited
- **OLED MG-equiv**: OLED capacity normalized to mother glass sheet size

## 2. Summary Table

| # | Factory | Families | TFT Cap | Effective | Old Sum | Over % | Bottleneck | Std Rigid | Thin Prof | Foldable |
|---|---------|----------|---------|-----------|---------|--------|------------|-----------|-----------|----------|
| 1 | AUO L3D | 1 | 0.0 | 0.0 | 0.0 | 0% | - | 0.0 | 0.0 | 0.0 |
| 2 | AUO L4B | 1 | 7.0 | 7.0 | 7.0 | 0% | - | 7.0 | 0.0 | 0.0 |
| 3 | BOE B11 | 3 | 30.0 | 27.5 | 75.0 | 150% | - | 0.0 | 0.0 | 30.0 |
| 4 | BOE B12 | 3 | 45.0 | 45.0 | 105.0 | 133% | - | 0.0 | 0.0 | 45.0 |
| 5 | BOE B16 | 2 | 15.0 | 15.0 | 30.0 | 100% | - | 0.0 | 0.0 | 15.0 |
| 6 | BOE B5 R&D | 1 | 0.0 | 0.0 | 0.0 | 0% | - | 0.0 | 0.0 | 0.0 |
| 7 | BOE B6 | 1 | 4.0 | 4.0 | 4.0 | 0% | - | 4.0 | 0.0 | 0.0 |
| 8 | BOE B7 | 3 | 32.0 | 32.0 | 65.0 | 103% | - | 0.0 | 0.0 | 32.0 |
| 9 | BOE TBD | 1 | 0.0 | 0.0 | 0.0 | 0% | - | 0.0 | 0.0 | 0.0 |
| 10 | China Star t2 | 2 | 0.0 | 0.0 | 0.0 | 0% | - | 0.0 | 0.0 | 0.0 |
| 11 | China Star t3 R&D | 1 | 0.0 | 0.0 | 0.0 | 0% | - | 0.0 | 0.0 | 0.0 |
| 12 | China Star t4 | 3 | 35.0 | 28.0 | 65.0 | 86% | OCT | 0.0 | 0.0 | 35.0 |
| 13 | China Star t5 | 2 | 30.0 | 30.0 | 50.0 | 67% | - | 0.0 | 0.0 | 30.0 |
| 14 | China Star t8 | 1 | 22.5 | 22.5 | 22.5 | 0% | - | 0.0 | 0.0 | 22.5 |
| 15 | EDO Fab1 | 2 | 15.0 | 15.0 | 15.0 | 0% | - | 15.0 | 0.0 | 0.0 |
| 16 | EDO Fab2 | 3 | 34.0 | 34.0 | 64.0 | 88% | - | 30.0 | 0.0 | 4.0 |
| 17 | JDI Ishikawa | 1 | 3.0 | 3.0 | 3.0 | 0% | - | 0.0 | 0.0 | 3.0 |
| 18 | JDI J1 | 2 | 4.0 | 4.0 | 4.0 | 0% | - | 0.0 | 0.0 | 4.0 |
| 19 | JDI Unknown | 1 | 15.0 | 15.0 | 15.0 | 0% | - | 0.0 | 0.0 | 15.0 |
| 20 | JOLED D2 | 1 | 4.0 | 4.0 | 20.0 | 400% | - | 0.0 | 4.0 | 0.0 |
| 21 | JOLED OLED G4.5 | 1 | 4.0 | 4.0 | 4.0 | 0% | - | 4.0 | 0.0 | 0.0 |
| 22 | LGD AP2/E2 | 3 | 32.0 | 32.0 | 32.0 | 0% | - | 0.0 | 0.0 | 32.0 |
| 23 | LGD AP3/E5 | 2 | 12.5 | 12.5 | 27.5 | 120% | - | 0.0 | 0.0 | 12.5 |
| 24 | LGD AP4/E6 | 3 | 30.0 | 30.0 | 75.0 | 150% | - | 0.0 | 0.0 | 30.0 |
| 25 | LGD AP5/E7 | 2 | 5.0 | 5.0 | 15.0 | 200% | - | 0.0 | 0.0 | 5.0 |
| 26 | LGD GP3 | 4 | 100.0 | 100.0 | 100.0 | 0% | - | 100.0 | 0.0 | 0.0 |
| 27 | LGD P10 IT | 1 | 7.5 | 7.5 | 15.0 | 100% | - | 0.0 | 0.0 | 7.5 |
| 28 | LGD P7 | 1 | 50.0 | 50.0 | 50.0 | 0% | - | 50.0 | 0.0 | 0.0 |
| 29 | LGD P8/E3 | 1 | 5.0 | 5.0 | 5.0 | 0% | - | 5.0 | 0.0 | 0.0 |
| 30 | LGD P8/E4 | 2 | 55.0 | 55.0 | 55.0 | 0% | - | 55.0 | 0.0 | 0.0 |
| 31 | LGD P8/E4 Inkjet | 1 | 0.0 | 0.0 | 0.0 | 0% | - | 0.0 | 0.0 | 0.0 |
| 32 | Royole R1 | 1 | 7.0 | 7.0 | 7.0 | 0% | - | 0.0 | 0.0 | 7.0 |
| 33 | SDC A1 | 2 | 55.0 | 55.0 | 55.0 | 0% | - | 50.0 | 0.0 | 5.0 |
| 34 | SDC A2 | 4 | 189.0 | 189.0 | 199.0 | 5% | - | 169.0 | 10.0 | 10.0 |
| 35 | SDC A2_E (V1) | 1 | 11.0 | 11.0 | 22.0 | 100% | - | 0.0 | 0.0 | 11.0 |
| 36 | SDC A3 | 9 | 135.0 | 90.0 | 285.0 | 111% | OCT | 0.0 | 0.0 | 135.0 |
| 37 | SDC A4 (L7-1) | 2 | 30.0 | 30.0 | 75.0 | 150% | - | 0.0 | 0.0 | 30.0 |
| 38 | SDC A4 (L7-2) | 3 | 30.0 | 30.0 | 40.0 | 33% | - | 0.0 | 0.0 | 30.0 |
| 39 | SDC A5 | 1 | 0.0 | 0.0 | 0.0 | 0% | - | 0.0 | 0.0 | 0.0 |
| 40 | SDC A6 | 2 | 15.0 | 15.0 | 22.5 | 50% | - | 0.0 | 0.0 | 15.0 |
| 41 | SDC Q1 | 1 | 30.0 | 30.0 | 30.0 | 0% | - | 30.0 | 0.0 | 0.0 |
| 42 | SDC Q2 | 1 | 30.0 | 30.0 | 30.0 | 0% | - | 30.0 | 0.0 | 0.0 |
| 43 | Sharp OLED G4.5 | 1 | 12.0 | 12.0 | 12.0 | 0% | - | 0.0 | 0.0 | 12.0 |
| 44 | Sony OLED G3.5 | 1 | 10.0 | 10.0 | 10.0 | 0% | - | 10.0 | 0.0 | 0.0 |
| 45 | Tianma TM15 | 2 | 8.0 | 8.0 | 8.0 | 0% | - | 8.0 | 0.0 | 0.0 |
| 46 | Tianma TM17 | 2 | 22.5 | 22.5 | 37.5 | 67% | - | 0.0 | 0.0 | 22.5 |
| 47 | Tianma TM18 | 3 | 47.5 | 47.5 | 70.0 | 47% | - | 0.0 | 0.0 | 47.5 |
| 48 | Truly Huizhoi B | 1 | 15.0 | 15.0 | 15.0 | 0% | - | 15.0 | 0.0 | 0.0 |
| 49 | Visionox V1 | 3 | 15.0 | 15.0 | 15.0 | 0% | - | 11.0 | 0.0 | 4.0 |
| 50 | Visionox V2 | 2 | 19.0 | 19.0 | 34.0 | 79% | - | 0.0 | 0.0 | 19.0 |
| 51 | Visionox V3 | 3 | 37.5 | 37.5 | 67.5 | 80% | - | 0.0 | 0.0 | 37.5 |
| 52 | Visionox V5 | 2 | 15.0 | 15.0 | 22.5 | 50% | - | 0.0 | 0.0 | 15.0 |

**Industry Total: 1330.0K (correct) vs 1980.0K (old) = 49% over-counted**

## 3. Focus Factory Deep-Dive

### BOE B11

- **TFT Capacity**: 30.0K MG/mo
- **OLED (MG equiv)**: 30.0K
- **OCT**: 27.5K
- **Effective**: 27.5K
- **Old Sum**: 75.0K
- **Families**: 3
- **Standard Rigid**: 0.0K | **Thin Profile**: 0.0K | **Foldable**: 30.0K

| Family | Members | TFT | OLED MG | OCT | Form Factor |
|--------|---------|-----|---------|-----|-------------|
| 1 | 1, 1O | 10.0 | 10.0 | 10.0 | Foldable |
| 2 | 2, 2O | 10.0 | 10.0 | 10.0 | Foldable |
| 3 | 3, 3O | 10.0 | 10.0 | 7.5 | Foldable |

### BOE B12

- **TFT Capacity**: 45.0K MG/mo
- **OLED (MG equiv)**: 45.0K
- **OCT**: 45.0K
- **Effective**: 45.0K
- **Old Sum**: 105.0K
- **Families**: 3
- **Standard Rigid**: 0.0K | **Thin Profile**: 0.0K | **Foldable**: 45.0K

| Family | Members | TFT | OLED MG | OCT | Form Factor |
|--------|---------|-----|---------|-----|-------------|
| 1 | 1, 1O | 15.0 | 15.0 | 15.0 | Foldable |
| 2 | 2, 2F, 2O, 2OF | 15.0 | 15.0 | 15.0 | Foldable |
| 3 | 3, 3F, 3OF | 15.0 | 15.0 | 15.0 | Foldable |

### BOE B7

- **TFT Capacity**: 32.0K MG/mo
- **OLED (MG equiv)**: 32.0K
- **OCT**: 32.0K
- **Effective**: 32.0K
- **Old Sum**: 65.0K
- **Families**: 3
- **Standard Rigid**: 0.0K | **Thin Profile**: 0.0K | **Foldable**: 32.0K

| Family | Members | TFT | OLED MG | OCT | Form Factor |
|--------|---------|-----|---------|-----|-------------|
| 1 | 1, 1O | 5.0 | 5.0 | 5.0 | Foldable |
| 2 | 2, 2O, 2F | 12.0 | 12.0 | 12.0 | Foldable |
| 3 | 3 | 15.0 | 15.0 | 15.0 | Foldable |

### China Star t4

- **TFT Capacity**: 35.0K MG/mo
- **OLED (MG equiv)**: 35.0K
- **OCT**: 28.0K
- **Effective**: 28.0K (limited by OCT)
- **Old Sum**: 65.0K
- **Families**: 3
- **Standard Rigid**: 0.0K | **Thin Profile**: 0.0K | **Foldable**: 35.0K

| Family | Members | TFT | OLED MG | OCT | Form Factor |
|--------|---------|-----|---------|-----|-------------|
| 1 | 1 | 15.0 | 15.0 | 15.0 | Foldable |
| 2 | 2, 2OF | 10.0 | 10.0 | 3.0 | Foldable |
| 3 | 3, 3O | 10.0 | 10.0 | 10.0 | Foldable |

### China Star t5

- **TFT Capacity**: 30.0K MG/mo
- **OLED (MG equiv)**: 30.0K
- **OCT**: 0.0K
- **Effective**: 30.0K
- **Old Sum**: 50.0K
- **Families**: 2
- **Standard Rigid**: 0.0K | **Thin Profile**: 0.0K | **Foldable**: 30.0K

| Family | Members | TFT | OLED MG | OCT | Form Factor |
|--------|---------|-----|---------|-----|-------------|
| 1 | 1, 1_1, 1_2 | 15.0 | 15.0 | 0.0 | Foldable |
| 2 | 2 | 15.0 | 15.0 | 0.0 | Foldable |

### LGD AP3/E5

- **TFT Capacity**: 12.5K MG/mo
- **OLED (MG equiv)**: 12.5K
- **OCT**: 12.5K
- **Effective**: 12.5K
- **Old Sum**: 27.5K
- **Families**: 2
- **Standard Rigid**: 0.0K | **Thin Profile**: 0.0K | **Foldable**: 12.5K

| Family | Members | TFT | OLED MG | OCT | Form Factor |
|--------|---------|-----|---------|-----|-------------|
| 1 | 1 | 7.5 | 7.5 | 7.5 | Foldable |
| 2 | 2, 2F, 2O | 5.0 | 5.0 | 5.0 | Foldable |

### LGD AP4/E6

- **TFT Capacity**: 30.0K MG/mo
- **OLED (MG equiv)**: 30.0K
- **OCT**: 30.0K
- **Effective**: 30.0K
- **Old Sum**: 75.0K
- **Families**: 3
- **Standard Rigid**: 0.0K | **Thin Profile**: 0.0K | **Foldable**: 30.0K

| Family | Members | TFT | OLED MG | OCT | Form Factor |
|--------|---------|-----|---------|-----|-------------|
| 1 | 1, 1O | 5.0 | 5.0 | 5.0 | Foldable |
| 2 | 2, 2O, 2OF | 15.0 | 15.0 | 15.0 | Foldable |
| 3 | 3 | 10.0 | 10.0 | 10.0 | Foldable |

### SDC A2

- **TFT Capacity**: 189.0K MG/mo
- **OLED (MG equiv)**: 189.0K
- **OCT**: 0.0K
- **Effective**: 189.0K
- **Old Sum**: 199.0K
- **Families**: 4
- **Standard Rigid**: 169.0K | **Thin Profile**: 10.0K | **Foldable**: 10.0K

| Family | Members | TFT | OLED MG | OCT | Form Factor |
|--------|---------|-----|---------|-----|-------------|
| 1 | 1 | 155.0 | 155.0 | 0.0 | Standard Rigid |
| 2 | 2, 2 | 10.0 | 10.0 | 0.0 | Foldable |
| 3 | 3 | 10.0 | 10.0 | 0.0 | Thin Profile |
| 4 | 4 | 14.0 | 14.0 | 0.0 | Standard Rigid |

### SDC A3

- **TFT Capacity**: 135.0K MG/mo
- **OLED (MG equiv)**: 135.0K
- **OCT**: 90.0K
- **Effective**: 90.0K (limited by OCT)
- **Old Sum**: 285.0K
- **Families**: 9
- **Standard Rigid**: 0.0K | **Thin Profile**: 0.0K | **Foldable**: 135.0K

| Family | Members | TFT | OLED MG | OCT | Form Factor |
|--------|---------|-----|---------|-----|-------------|
| 1 | 1, 1F, 1O, 1O | 15.0 | 15.0 | 15.0 | Foldable |
| 2 | 2, 2O, 2OF | 15.0 | 15.0 | 15.0 | Foldable |
| 3 | 3, 3O | 15.0 | 15.0 | 15.0 | Foldable |
| 4 | 4, 4O | 15.0 | 15.0 | 15.0 | Foldable |
| 5 | 5, 5O | 15.0 | 15.0 | 15.0 | Foldable |
| 6 | 6, 6O, 6OF | 15.0 | 15.0 | 15.0 | Foldable |
| 7 | 7 | 15.0 | 15.0 | 0.0 | Foldable |
| 8 | 8 | 15.0 | 15.0 | 0.0 | Foldable |
| 9 | 9 | 15.0 | 15.0 | 0.0 | Foldable |

## 4. Process Bottleneck Analysis

Factories where Effective Capacity < TFT Capacity (bottleneck detected):

| Factory | TFT | OLED MG | OCT | Effective | Bottleneck | OCT/TFT Ratio |
|---------|-----|---------|-----|-----------|------------|---------------|
| China Star t4 | 35.0 | 35.0 | 28.0 | 28.0 | OCT | 80% |
| SDC A3 | 135.0 | 135.0 | 90.0 | 90.0 | OCT | 67% |

## 5. Flags

### 5.1 Large G6 factories (>100K)

- SDC A2: 189.0K
- SDC A3: 135.0K

### 5.2 Factories with >3x over-count ratio

- JOLED D2: 20.0K old vs 4.0K correct (5.0x)

## 6. Technology & Form Factor Summary

| Factory | TFT | LTPS | LTPO | Std Rigid | Thin Prof | Foldable | Effective | Bottleneck |
|---------|-----|------|------|-----------|-----------|----------|-----------|------------|
| AUO L3D | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | - |
| AUO L4B | 7.0 | 7.0 | 0.0 | 7.0 | 0.0 | 0.0 | 7.0 | - |
| BOE B11 | 30.0 | 0.0 | 30.0 | 0.0 | 0.0 | 30.0 | 27.5 | - |
| BOE B12 | 45.0 | 15.0 | 30.0 | 0.0 | 0.0 | 45.0 | 45.0 | - |
| BOE B16 | 15.0 | 0.0 | 15.0 | 0.0 | 0.0 | 15.0 | 15.0 | - |
| BOE B5 R&D | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | - |
| BOE B6 | 4.0 | 4.0 | 0.0 | 4.0 | 0.0 | 0.0 | 4.0 | - |
| BOE B7 | 32.0 | 15.0 | 17.0 | 0.0 | 0.0 | 32.0 | 32.0 | - |
| BOE TBD | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | - |
| China Star t2 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | - |
| China Star t3 R&D | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | - |
| China Star t4 | 35.0 | 15.0 | 20.0 | 0.0 | 0.0 | 35.0 | 28.0 | OCT |
| China Star t5 | 30.0 | 0.0 | 30.0 | 0.0 | 0.0 | 30.0 | 30.0 | - |
| China Star t8 | 22.5 | 9.2 | 0.0 | 0.0 | 0.0 | 22.5 | 22.5 | - |
| EDO Fab1 | 15.0 | 15.0 | 0.0 | 15.0 | 0.0 | 0.0 | 15.0 | - |
| EDO Fab2 | 34.0 | 34.0 | 0.0 | 30.0 | 0.0 | 4.0 | 34.0 | - |
| JDI Ishikawa | 3.0 | 3.0 | 0.0 | 0.0 | 0.0 | 3.0 | 3.0 | - |
| JDI J1 | 4.0 | 0.0 | 4.0 | 0.0 | 0.0 | 4.0 | 4.0 | - |
| JDI Unknown | 15.0 | 0.0 | 0.0 | 0.0 | 0.0 | 15.0 | 15.0 | - |
| JOLED D2 | 4.0 | 4.0 | 0.0 | 0.0 | 4.0 | 0.0 | 4.0 | - |
| JOLED OLED G4.5 | 4.0 | 4.0 | 0.0 | 4.0 | 0.0 | 0.0 | 4.0 | - |
| LGD AP2/E2 | 32.0 | 20.0 | 12.0 | 0.0 | 0.0 | 32.0 | 32.0 | - |
| LGD AP3/E5 | 12.5 | 7.5 | 5.0 | 0.0 | 0.0 | 12.5 | 12.5 | - |
| LGD AP4/E6 | 30.0 | 0.0 | 30.0 | 0.0 | 0.0 | 30.0 | 30.0 | - |
| LGD AP5/E7 | 5.0 | 0.0 | 5.0 | 0.0 | 0.0 | 5.0 | 5.0 | - |
| LGD GP3 | 100.0 | 0.0 | 0.0 | 100.0 | 0.0 | 0.0 | 100.0 | - |
| LGD P10 IT | 7.5 | 0.0 | 0.0 | 0.0 | 0.0 | 7.5 | 7.5 | - |
| LGD P7 | 50.0 | 0.0 | 0.0 | 50.0 | 0.0 | 0.0 | 50.0 | - |
| LGD P8/E3 | 5.0 | 0.0 | 0.0 | 5.0 | 0.0 | 0.0 | 5.0 | - |
| LGD P8/E4 | 55.0 | 0.0 | 0.0 | 55.0 | 0.0 | 0.0 | 55.0 | - |
| LGD P8/E4 Inkjet | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | - |
| Royole R1 | 7.0 | 0.0 | 0.0 | 0.0 | 0.0 | 7.0 | 7.0 | - |
| SDC A1 | 55.0 | 55.0 | 0.0 | 50.0 | 0.0 | 5.0 | 55.0 | - |
| SDC A2 | 189.0 | 189.0 | 0.0 | 169.0 | 10.0 | 10.0 | 189.0 | - |
| SDC A2_E (V1) | 11.0 | 11.0 | 0.0 | 0.0 | 0.0 | 11.0 | 11.0 | - |
| SDC A3 | 135.0 | 45.0 | 90.0 | 0.0 | 0.0 | 135.0 | 90.0 | OCT |
| SDC A4 (L7-1) | 30.0 | 0.0 | 30.0 | 0.0 | 0.0 | 30.0 | 30.0 | - |
| SDC A4 (L7-2) | 30.0 | 0.0 | 30.0 | 0.0 | 0.0 | 30.0 | 30.0 | - |
| SDC A5 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | - |
| SDC A6 | 15.0 | 7.5 | 0.0 | 0.0 | 0.0 | 15.0 | 15.0 | - |
| SDC Q1 | 30.0 | 0.0 | 0.0 | 30.0 | 0.0 | 0.0 | 30.0 | - |
| SDC Q2 | 30.0 | 0.0 | 0.0 | 30.0 | 0.0 | 0.0 | 30.0 | - |
| Sharp OLED G4.5 | 12.0 | 12.0 | 0.0 | 0.0 | 0.0 | 12.0 | 12.0 | - |
| Sony OLED G3.5 | 10.0 | 10.0 | 0.0 | 10.0 | 0.0 | 0.0 | 10.0 | - |
| Tianma TM15 | 8.0 | 8.0 | 0.0 | 8.0 | 0.0 | 0.0 | 8.0 | - |
| Tianma TM17 | 22.5 | 22.5 | 0.0 | 0.0 | 0.0 | 22.5 | 22.5 | - |
| Tianma TM18 | 47.5 | 15.0 | 32.5 | 0.0 | 0.0 | 47.5 | 47.5 | - |
| Truly Huizhoi B | 15.0 | 15.0 | 0.0 | 15.0 | 0.0 | 0.0 | 15.0 | - |
| Visionox V1 | 15.0 | 15.0 | 0.0 | 11.0 | 0.0 | 4.0 | 15.0 | - |
| Visionox V2 | 19.0 | 0.0 | 19.0 | 0.0 | 0.0 | 19.0 | 19.0 | - |
| Visionox V3 | 37.5 | 0.0 | 37.5 | 0.0 | 0.0 | 37.5 | 37.5 | - |
| Visionox V5 | 15.0 | 0.0 | 15.0 | 0.0 | 0.0 | 15.0 | 15.0 | - |

**Technology Share**: LTPS 557.7K (42%) | LTPO 452.0K (34%)
**Form Factor Share**: Standard Rigid 593.0K (45%) | Thin Profile 14.0K (1%) | Foldable 723.0K (54%)