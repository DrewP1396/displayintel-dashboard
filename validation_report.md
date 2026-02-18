# Capacity Validation Report — Phase Family Logic

> **Source:** ScenarioByFab (2025Q4)  
> **Generated:** 2026-02-18 14:01

---

## 1. Methodology

### The Phase Family Approach

Traditional capacity tracking sums every phase row in the fab database. However, many phases represent **reconfiguration of the same physical capacity** rather than incremental additions. For example, when a production line upgrades from LTPS to LTPO backplane, a new phase row is added (e.g., Phase 1 → Phase 1O), but the underlying equipment is the same.

**Phase families** group related phases that share the same physical capacity:

- Phases are grouped by their numeric base (e.g., 1, 1F, 1O, 1OF all belong to Family 1)
- Within each family, only the **latest configuration** (by MP ramp date) counts toward total capacity
- The result: `total_capacity` = sum of latest-phase TFT max input across all families
- The old method: `old_sum` = sum of TFT max input across ALL phase rows (double/triple-counting)

This approach eliminates systematic over-counting that occurs when capacity is reconfigured across technology transitions (LTPS → LTPO, Rigid → Flexible → Foldable).

---

## 2. Summary — All Factories

| # | Manufacturer | Factory | Families | Correct Total (K) | Old Sum (K) | Difference (K) | % Over-counted |
|---|-------------|---------|----------|-------------------|-------------|-----------------|----------------|
| 1 | AUO | L3D | 1 | — | — | — | — |
| 2 | AUO | L4B | 1 | 7 | 7 | — | 0% |
| 3 | BOE | B11 | 3 | 30 | 75 | 45 | 150% |
| 4 | BOE | B12 | 3 | 21 | 105 | 84 | 400% |
| 5 | BOE | B16 | 2 | 15 | 30 | 15 | 100% |
| 6 | BOE | B5 R&D | 1 | — | — | — | — |
| 7 | BOE | B6 | 1 | 4 | 4 | — | 0% |
| 8 | BOE | B7 | 3 | 32 | 65 | 33 | 103% |
| 9 | BOE | TBD | 1 | — | — | — | — |
| 10 | China Star | t2 | 2 | — | — | — | — |
| 11 | China Star | t3 R&D | 1 | — | — | — | — |
| 12 | China Star | t4 | 3 | 35 | 65 | 30 | 86% |
| 13 | China Star | t5 | 2 | 30 | 50 | 20 | 67% |
| 14 | China Star | t8 | 1 | 9.2 | 22.5 | 13.3 | 145% |
| 15 | EDO | Fab1 | 2 | 15 | 15 | — | 0% |
| 16 | EDO | Fab2 | 3 | 19 | 64 | 45 | 237% |
| 17 | JDI | Ishikawa | 1 | 3 | 3 | — | 0% |
| 18 | JDI | J1 | 2 | 4 | 4 | — | 0% |
| 19 | JOLED | D2 | 1 | 4 | 20 | 16 | 400% |
| 20 | JOLED | OLED G4.5 | 1 | 4 | 4 | — | 0% |
| 21 | LGD | AP2/E2 | 3 | 32 | 32 | — | 0% |
| 22 | LGD | AP3/E5 | 2 | 12.5 | 27.5 | 15 | 120% |
| 23 | LGD | AP4/E6 | 3 | 30 | 75 | 45 | 150% |
| 24 | LGD | AP5/E7 | 2 | 5 | 15 | 10 | 200% |
| 25 | LGD | GP3 | 4 | 100 | 100 | — | 0% |
| 26 | LGD | P10 IT | 1 | 7.5 | 15 | 7.5 | 100% |
| 27 | LGD | P7 | 1 | 50 | 50 | — | 0% |
| 28 | LGD | P8/E3 | 1 | 5 | 5 | — | 0% |
| 29 | LGD | P8/E4 | 2 | 55 | 55 | — | 0% |
| 30 | LGD | P8/E4 Inkjet | 1 | — | — | — | — |
| 31 | Royole | R1 | 1 | 7 | 7 | — | 0% |
| 32 | SDC | A1 | 2 | 55 | 55 | — | 0% |
| 33 | SDC | A2 | 4 | 189 | 199 | 10 | 5% |
| 34 | SDC | A2_E (V1) | 1 | 11 | 22 | 11 | 100% |
| 35 | SDC | A3 | 9 | 135 | 285 | 150 | 111% |
| 36 | SDC | A4 (L7-1) | 2 | 30 | 75 | 45 | 150% |
| 37 | SDC | A4 (L7-2) | 3 | 30 | 40 | 10 | 33% |
| 38 | SDC | A5 | 1 | — | — | — | — |
| 39 | SDC | A6 | 2 | 15 | 22.5 | 7.5 | 50% |
| 40 | SDC | Q1 | 1 | 30 | 30 | — | 0% |
| 41 | SDC | Q2 | 1 | 30 | 30 | — | 0% |
| 42 | Sharp | OLED G4.5 | 1 | 12 | 12 | — | 0% |
| 43 | Sony | OLED G3.5 | 1 | 10 | 10 | — | 0% |
| 44 | Tianma | TM15 | 2 | 8 | 8 | — | 0% |
| 45 | Tianma | TM17 | 2 | 22.5 | 37.5 | 15 | 67% |
| 46 | Tianma | TM18 | 3 | 22.5 | 70 | 47.5 | 211% |
| 47 | Truly | Huizhoi B | 1 | 15 | 15 | — | 0% |
| 48 | Visionox | V1 | 3 | 15 | 15 | — | 0% |
| 49 | Visionox | V2 | 2 | 19 | 34 | 15 | 79% |
| 50 | Visionox | V3 | 3 | 37.5 | 67.5 | 30 | 80% |
| 51 | Visionox | V5 | 2 | 15 | 22.5 | 7.5 | 50% |
| | **TOTAL** | | | **1,237.7** | **1,965** | **727.3** | **59%** |

---

## 3. Focus Factory Deep-Dive

The following factories are analyzed in detail due to their strategic importance, high capacity, or significant over-counting ratios.

### BOE B11

**Region:** China · **Location:** Mianyang · **TFT Gen:** G6 · **OLED Gen:** 1/2 G6

| Metric | Value |
|--------|-------|
| Correct Total | **30K** |
| Old Sum | 75K |
| Over-count | 45K (2.5x) |
| Phase Rows | 6 |
| Phase Families | 3 |

**Family Breakdown:**

| Family | Members | Latest | Backplane | TFT Max (K) | Substrate | Status |
|--------|---------|--------|-----------|-------------|-----------|--------|
| 1 | 1, 1O | **1O** | LTPO | 10K | Flexible | MP |
| 2 | 2, 2O | **2O** | LTPO | 10K | Flexible | MP |
| 3 | 3, 3O | **3O** | LTPO | 10K | Flexible | MP |

**Technology Mix:**

| LTPS | LTPO | Rigid | Flex/Fold | Glass | TFE |
|------|------|-------|-----------|-------|-----|
| — | 30K | — | 30K | — | 30K |

---

### BOE B12

**Region:** China · **Location:** Chongqing · **TFT Gen:** G6 · **OLED Gen:** 1/2 G6

| Metric | Value |
|--------|-------|
| Correct Total | **21K** |
| Old Sum | 105K |
| Over-count | 84K (5.0x) |
| Phase Rows | 9 |
| Phase Families | 3 |

**Family Breakdown:**

| Family | Members | Latest | Backplane | TFT Max (K) | Substrate | Status |
|--------|---------|--------|-----------|-------------|-----------|--------|
| 1 | 1, 1O | **1O** | LTPO | 15K | Flexible | MP |
| 2 | 2, 2F, 2O, 2OF | **2OF** | LTPO | 6K | Foldable | MP |
| 3 | 3, 3F, 3OF | **3OF** | LTPO | — | Foldable | MP |

**Technology Mix:**

| LTPS | LTPO | Rigid | Flex/Fold | Glass | TFE |
|------|------|-------|-----------|-------|-----|
| — | 21K | — | 15K | — | 21K |

---

### BOE B7

**Region:** China · **Location:** Chengdu · **TFT Gen:** G6 · **OLED Gen:** 1/2 G6

| Metric | Value |
|--------|-------|
| Correct Total | **32K** |
| Old Sum | 65K |
| Over-count | 33K (2.0x) |
| Phase Rows | 6 |
| Phase Families | 3 |

**Family Breakdown:**

| Family | Members | Latest | Backplane | TFT Max (K) | Substrate | Status |
|--------|---------|--------|-----------|-------------|-----------|--------|
| 1 | 1, 1O | **1O** | LTPO | 5K | Flexible | MP |
| 2 | 2, 2F, 2O | **2O** | LTPO | 12K | Flexible | MP |
| 3 | 3 | **3** | LTPS | 15K | Flexible | MP |

**Technology Mix:**

| LTPS | LTPO | Rigid | Flex/Fold | Glass | TFE |
|------|------|-------|-----------|-------|-----|
| 15K | 17K | — | 32K | — | 32K |

---

### SDC A3

**Region:** S Korea · **Location:** Tangjeong · **TFT Gen:** G6 · **OLED Gen:** 1/2 G6

| Metric | Value |
|--------|-------|
| Correct Total | **135K** |
| Old Sum | 285K |
| Over-count | 150K (2.1x) |
| Phase Rows | 19 |
| Phase Families | 9 |

**Family Breakdown:**

| Family | Members | Latest | Backplane | TFT Max (K) | Substrate | Status |
|--------|---------|--------|-----------|-------------|-----------|--------|
| 1 | 1, 1F, 1O, 1O | **1O** | LTPO | 15K | Hybrid | MP |
| 2 | 2, 2O, 2OF | **2OF** | LTPO | 15K | Foldable | MP |
| 3 | 3, 3O | **3O** | LTPO | 15K | Flexible | MP |
| 4 | 4, 4O | **4O** | LTPO | 15K | Flexible | MP |
| 5 | 5, 5O | **5O** | LTPO | 15K | Flexible | MP |
| 6 | 6, 6O, 6OF | **6OF** | LTPO | 15K | Flexible | MP |
| 7 | 7 | **7** | LTPS | 15K | Flexible | MP |
| 8 | 8 | **8** | LTPS | 15K | Flexible | MP |
| 9 | 9 | **9** | LTPS | 15K | Flexible | MP |

**Technology Mix:**

| LTPS | LTPO | Rigid | Flex/Fold | Glass | TFE |
|------|------|-------|-----------|-------|-----|
| 45K | 90K | — | 105K | — | 135K |

---

### SDC A2

**Region:** S Korea · **Location:** Tangjeong · **TFT Gen:** G5.5 · **OLED Gen:** 1/4 G5.5

| Metric | Value |
|--------|-------|
| Correct Total | **189K** |
| Old Sum | 199K |
| Over-count | 10K (1.1x) |
| Phase Rows | 5 |
| Phase Families | 4 |

**Family Breakdown:**

| Family | Members | Latest | Backplane | TFT Max (K) | Substrate | Status |
|--------|---------|--------|-----------|-------------|-----------|--------|
| 1 | 1 | **1** | LTPS | 155K | Rigid | MP |
| 2 | 2, 2 | **2** | LTPS | 10K | Flexible | MP |
| 3 | 3 | **3** | LTPS | 10K | Rigid | MP |
| 4 | 4 | **4** | LTPS | 14K | Rigid | MP |

**Technology Mix:**

| LTPS | LTPO | Rigid | Flex/Fold | Glass | TFE |
|------|------|-------|-----------|-------|-----|
| 189K | — | 179K | 10K | 169K | 20K |

---

### SDC A4 (L7-1)

**Region:** S Korea · **Location:** Tangjeong · **TFT Gen:** G6 · **OLED Gen:** 1/2 G6

| Metric | Value |
|--------|-------|
| Correct Total | **30K** |
| Old Sum | 75K |
| Over-count | 45K (2.5x) |
| Phase Rows | 5 |
| Phase Families | 2 |

**Family Breakdown:**

| Family | Members | Latest | Backplane | TFT Max (K) | Substrate | Status |
|--------|---------|--------|-----------|-------------|-----------|--------|
| 1 | 1, 1O, 1OF | **1OF** | LTPO | 15K | Foldable | MP |
| 2 | 2, 2OF | **2OF** | LTPO | 15K | Foldable | MP |

**Technology Mix:**

| LTPS | LTPO | Rigid | Flex/Fold | Glass | TFE |
|------|------|-------|-----------|-------|-----|
| — | 30K | — | — | — | 30K |

---

### LGD AP3/E5

**Region:** S Korea · **Location:** Gumi · **TFT Gen:** G6 · **OLED Gen:** 1/2 G6

| Metric | Value |
|--------|-------|
| Correct Total | **12.5K** |
| Old Sum | 27.5K |
| Over-count | 15K (2.2x) |
| Phase Rows | 4 |
| Phase Families | 2 |

**Family Breakdown:**

| Family | Members | Latest | Backplane | TFT Max (K) | Substrate | Status |
|--------|---------|--------|-----------|-------------|-----------|--------|
| 1 | 1 | **1** | LTPS | 7.5K | Flexible | MP |
| 2 | 2, 2F, 2O | **2O** | LTPO | 5K | Flexible | MP |

**Technology Mix:**

| LTPS | LTPO | Rigid | Flex/Fold | Glass | TFE |
|------|------|-------|-----------|-------|-----|
| 7.5K | 5K | — | 12.5K | — | 12.5K |

---

### LGD AP4/E6

**Region:** S Korea · **Location:** Paju · **TFT Gen:** G6 · **OLED Gen:** 1/2 G6

| Metric | Value |
|--------|-------|
| Correct Total | **30K** |
| Old Sum | 75K |
| Over-count | 45K (2.5x) |
| Phase Rows | 6 |
| Phase Families | 3 |

**Family Breakdown:**

| Family | Members | Latest | Backplane | TFT Max (K) | Substrate | Status |
|--------|---------|--------|-----------|-------------|-----------|--------|
| 1 | 1, 1O | **1O** | LTPO | 5K | Flexible | MP |
| 2 | 2, 2O, 2OF | **2OF** | LTPO | 15K | Foldable | MP |
| 3 | 3 | **3** | LTPO | 10K | Flexible | MP |

**Technology Mix:**

| LTPS | LTPO | Rigid | Flex/Fold | Glass | TFE |
|------|------|-------|-----------|-------|-----|
| — | 30K | — | 15K | — | 30K |

---

### China Star t4

**Region:** China · **Location:** Wuhan · **TFT Gen:** G6 · **OLED Gen:** 1/2 G6

| Metric | Value |
|--------|-------|
| Correct Total | **35K** |
| Old Sum | 65K |
| Over-count | 30K (1.9x) |
| Phase Rows | 5 |
| Phase Families | 3 |

**Family Breakdown:**

| Family | Members | Latest | Backplane | TFT Max (K) | Substrate | Status |
|--------|---------|--------|-----------|-------------|-----------|--------|
| 1 | 1 | **1** | LTPS | 15K | Flexible | MP |
| 2 | 2, 2OF | **2OF** | LTPO | 10K | Foldable | MP |
| 3 | 3, 3O | **3O** | LTPO | 10K | Flexible | MP |

**Technology Mix:**

| LTPS | LTPO | Rigid | Flex/Fold | Glass | TFE |
|------|------|-------|-----------|-------|-----|
| 15K | 20K | — | 25K | — | 35K |

---

### China Star t5

**Region:** China · **Location:** Wuhan · **TFT Gen:** G6 · **OLED Gen:** 1/2 G6

| Metric | Value |
|--------|-------|
| Correct Total | **30K** |
| Old Sum | 50K |
| Over-count | 20K (1.7x) |
| Phase Rows | 4 |
| Phase Families | 2 |

**Family Breakdown:**

| Family | Members | Latest | Backplane | TFT Max (K) | Substrate | Status |
|--------|---------|--------|-----------|-------------|-----------|--------|
| 1 | 1_1, 1_2, 1 | **1** | LTPO | 15K | Flexible | MP |
| 2 | 2 | **2** | LTPO | 15K | Flexible | MP |

**Technology Mix:**

| LTPS | LTPO | Rigid | Flex/Fold | Glass | TFE |
|------|------|-------|-----------|-------|-----|
| — | 30K | — | 30K | — | 30K |

---

## 4. Flags & Alerts

### 4.1 High-Capacity G6 Factories (Total > 200K)

Factories with G6 TFT generation and total corrected capacity exceeding 200K sheets/month.

> No G6 factories exceed 200K total capacity.


### 4.2 Extreme Over-Count Ratio (Old Sum / Total > 3x)

Factories where naive summation over-counts capacity by more than 3x, indicating extensive phase reconfiguration history.

| Manufacturer | Factory | Total (K) | Old Sum (K) | Ratio | Families | Phases |
|-------------|---------|-----------|-------------|-------|----------|--------|
| BOE | B12 | 21 | 105 | 5.0x | 3 | 9 |
| JOLED | D2 | 4 | 20 | 5.0x | 1 | 2 |
| EDO | Fab2 | 19 | 64 | 3.4x | 3 | 9 |
| Tianma | TM18 | 22.5 | 70 | 3.1x | 3 | 7 |

---

## 5. Technology Breakdown — All Factories

Aggregate capacity by technology type across all 51 factories (using corrected totals).

| Manufacturer | Factory | Total (K) | LTPS (K) | LTPO (K) | Rigid (K) | Flex/Fold (K) | Glass (K) | TFE (K) |
|-------------|---------|-----------|----------|----------|-----------|---------------|-----------|---------|
| AUO | L3D | — | — | — | — | — | — | — |
| AUO | L4B | 7 | 7 | — | 7 | — | 7 | — |
| BOE | B11 | 30 | — | 30 | — | 30 | — | 30 |
| BOE | B12 | 21 | — | 21 | — | 15 | — | 21 |
| BOE | B16 | 15 | — | 15 | — | 15 | — | 15 |
| BOE | B5 R&D | — | — | — | — | — | — | — |
| BOE | B6 | 4 | 4 | — | 4 | — | 4 | — |
| BOE | B7 | 32 | 15 | 17 | — | 32 | — | 32 |
| BOE | TBD | — | — | — | — | — | — | — |
| China Star | t2 | — | — | — | — | — | — | — |
| China Star | t3 R&D | — | — | — | — | — | — | — |
| China Star | t4 | 35 | 15 | 20 | — | 25 | — | 35 |
| China Star | t5 | 30 | — | 30 | — | 30 | — | 30 |
| China Star | t8 | 9.2 | 9.2 | — | — | — | — | 9.2 |
| EDO | Fab1 | 15 | 15 | — | 15 | — | 15 | — |
| EDO | Fab2 | 19 | 19 | — | 15 | — | 15 | 4 |
| JDI | Ishikawa | 3 | 3 | — | — | — | — | 3 |
| JDI | J1 | 4 | — | 4 | — | 4 | — | 4 |
| JOLED | D2 | 4 | 4 | — | 4 | — | — | 4 |
| JOLED | OLED G4.5 | 4 | 4 | — | 4 | — | 4 | — |
| LGD | AP2/E2 | 32 | 20 | 12 | — | 32 | — | 32 |
| LGD | AP3/E5 | 12.5 | 7.5 | 5 | — | 12.5 | — | 12.5 |
| LGD | AP4/E6 | 30 | — | 30 | — | 15 | — | 30 |
| LGD | AP5/E7 | 5 | — | 5 | — | 5 | — | 5 |
| LGD | GP3 | 100 | — | — | 100 | — | 100 | — |
| LGD | P10 IT | 7.5 | — | — | — | — | — | 7.5 |
| LGD | P7 | 50 | — | — | 50 | — | 50 | — |
| LGD | P8/E3 | 5 | — | — | 5 | — | 5 | — |
| LGD | P8/E4 | 55 | — | — | 55 | — | 55 | — |
| LGD | P8/E4 Inkjet | — | — | — | — | — | — | — |
| Royole | R1 | 7 | — | — | — | — | — | 7 |
| SDC | A1 | 55 | 55 | — | 50 | 5 | 50 | 5 |
| SDC | A2 | 189 | 189 | — | 179 | 10 | 169 | 20 |
| SDC | A2_E (V1) | 11 | 11 | — | — | 11 | — | 11 |
| SDC | A3 | 135 | 45 | 90 | — | 105 | — | 135 |
| SDC | A4 (L7-1) | 30 | — | 30 | — | — | — | 30 |
| SDC | A4 (L7-2) | 30 | — | 30 | — | 10 | — | 30 |
| SDC | A5 | — | — | — | — | — | — | — |
| SDC | A6 | 15 | 7.5 | — | — | — | — | 15 |
| SDC | Q1 | 30 | — | — | 30 | — | 30 | — |
| SDC | Q2 | 30 | — | — | 30 | — | 30 | — |
| Sharp | OLED G4.5 | 12 | 12 | — | — | 12 | — | 12 |
| Sony | OLED G3.5 | 10 | 10 | — | 10 | — | 10 | — |
| Tianma | TM15 | 8 | 8 | — | 8 | — | 8 | — |
| Tianma | TM17 | 22.5 | 22.5 | — | — | 22.5 | — | 22.5 |
| Tianma | TM18 | 22.5 | — | 22.5 | — | 22.5 | — | 22.5 |
| Truly | Huizhoi B | 15 | 15 | — | 15 | — | 15 | — |
| Visionox | V1 | 15 | 15 | — | 11 | 4 | 11 | 4 |
| Visionox | V2 | 19 | — | 19 | — | 19 | — | 19 |
| Visionox | V3 | 37.5 | — | 37.5 | — | 22.5 | — | 37.5 |
| Visionox | V5 | 15 | — | 15 | — | 7.5 | — | 15 |
| **TOTAL** | | **1,237.7** | **512.7** | **433** | **592** | **466.5** | **578** | **659.7** |

### Technology Share Summary

| Technology | Capacity (K) | Share of Total |
|-----------|-------------|----------------|
| LTPS | 512.7 | 41% |
| LTPO | 433 | 35% |
| Rigid | 592 | 48% |
| Flexible/Foldable | 466.5 | 38% |
| Glass Encapsulation | 578 | 47% |
| TFE Encapsulation | 659.7 | 53% |

---

*Report generated on 2026-02-18 14:01 using phase family methodology.*
