# Data Mapping: Factory Comparison View with Investment Timeline

## Source Files

| File | Location | Size | Records |
|------|----------|------|---------|
| Utilization Report | `source_data/2025Q4_Quarterly_All_Display_Fab_Utilization Report_RevA copy.xlsm` | 8.3 MB | 28,218 rows (StaticDB sheet) |
| CapacityData Report | `source_data/2025Q4_QOLED_SupDem_CapSpendReport_CapacityData_RevA[1] copy.xlsm` | 7.0 MB | 35 sheets |
| SQLite Database | `displayintel.db` | ~14 MB | 58,635+ records across 12 tables |

---

## Available Columns by Data Source

### 1. `factories` table (172 records)

| Column | Type | Example | Maps To |
|--------|------|---------|---------|
| `factory_id` | TEXT PK | `AUO_FVO_LTPS` | Unique factory identifier |
| `manufacturer` | TEXT | `BOE`, `LGD`, `SDC` | Company name |
| `factory_name` | TEXT | `B16`, `P10`, `FVO` | Factory code |
| `location` | TEXT | `Kunshan`, `Paju` | City |
| `region` | TEXT | `China`, `S Korea` | Country/region (for depreciation) |
| `technology` | TEXT | `LCD`, `OLED` | Frontplane technology |
| `backplane` | TEXT | `LTPS`, `LTPO`, `a-Si`, `Oxide` | Backplane technology |
| `generation` | TEXT | `G6`, `G8.5` | Glass generation |
| `substrate` | TEXT | | Substrate spec |
| `application_category` | TEXT | `Mobile/IT`, `TV` | Target application |
| `eqpt_po_year` | INTEGER | `2023` | Equipment PO year |
| `install_date` | TEXT | `2024-06-01` | Install date |
| `mp_ramp_date` | TEXT | `2016-10-01` | **First MP/ramp date** |
| `probability` | TEXT | `A`, `B`, `C` | A=Confirmed, B=Probable, C=Possible |
| `status` | TEXT | `operating`, `planned` | Current status |

### 2. `utilization` table (16,420 records, Q1 2019 - Q4 2029)

| Column | Type | Example | Maps To |
|--------|------|---------|---------|
| `factory_id` | TEXT FK | `BOE_B16_LTPO` | Links to factories |
| `date` | TEXT | `2024-03-01` | Monthly timestamp |
| `year` / `quarter` / `month` | INT | `2024` / `1` / `3` | Time breakdowns |
| `capacity_ksheets` | REAL | `120.0` | **Current capacity (k sheets/mo)** |
| `actual_input_ksheets` | REAL | `96.0` | Actual production input |
| `utilization_pct` | REAL | `80.0` | **Utilization %** |
| `capacity_sqm_k` | REAL | `180.5` | Area-based capacity (1000 m²/mo) |
| `actual_input_sqm_k` | REAL | `144.4` | Area-based actual input |
| `is_projection` | INT | `0` or `1` | 0=historical, 1=forecast |

### 3. `equipment_orders` table (3,548 records)

| Column | Type | Example | Maps To |
|--------|------|---------|---------|
| `po_year` | INT | `2023` | **Investment year** |
| `po_quarter` | TEXT | `Q2` | PO quarter |
| `manufacturer` | TEXT | `SDC` | Company |
| `factory` / `factory_id` | TEXT | `A6` | Factory |
| `equipment_type` | TEXT | `CVD`, `Lithography` | Equipment class |
| `tool_category` | TEXT | `Evaporation`, `Etch` | Tool subcategory |
| `vendor` | TEXT | `AMAT`, `ASML` | Equipment vendor |
| `units` | INT | `3` | Number of tools |
| `amount_usd` | REAL | `360000000` | **Investment amount (USD)** |
| `is_projection` | INT | `0` or `1` | Historical vs projected |

### 4. StaticDB sheet (Utilization Report Excel, 28,218 rows)

| Col | Header | Maps To |
|-----|--------|---------|
| B | Year | Time period |
| C | Q | Quarter |
| F | Region | `China`, `Taiwan`, `S Korea`, `Japan` |
| G | Manufacturer | Company |
| H | Factory1 | Factory code |
| I | Factory2 (Location) | City/location |
| J | Phase | **Phase number (1, 2, 3...)** — capacity increment ID |
| K | Backplane | `LTPS`, `a-Si`, `LTPO`, `Oxide` |
| L | Frontplane | `LCD`, `OLED` |
| M | TFT Gen1 | Glass generation |
| T | Eqpt PO | Equipment PO year |
| U | Install | **Install date per phase** |
| V | MP Ramp | **Mass production ramp date per phase** |
| W | End | End of production |
| X | Probability | `A`, `B`, `C` |
| Y | Max Input (k sheets/month) | Max capacity |
| Z | Capacity (k Sheet/Month) | **Capacity per phase increment** |
| AA | Actual Input (k Sheet/Month) | Actual utilization |
| AD | Utilization % | Utilization rate |

---

## How to Build the Investment Timeline Dropdown

### Data joins

```
factories (base — one row per factory/phase)
  ├── equipment_orders  (JOIN on factory_id → investment amounts by year)
  ├── utilization       (JOIN on factory_id → monthly capacity & util%)
  └── StaticDB Excel    (backup source — has phase-level detail)
```

### Building increment rows

Each factory can have multiple **phases**. The StaticDB sheet has one row per factory+phase+quarter, with:
- `Phase` column = increment number (1, 2, 3...)
- `Install` column = when that phase's equipment was installed
- `MP Ramp` column = when that phase started mass production
- `Capacity (k Sheet/Month)` = capacity added by that phase

**Query to build timeline:**

```sql
-- Capacity increments by factory (from utilization table)
SELECT
    f.manufacturer,
    f.factory_name,
    f.region,
    f.technology,
    f.backplane,
    f.generation,
    f.mp_ramp_date        AS first_mp_date,
    f.install_date        AS install_date,
    f.eqpt_po_year        AS po_year,
    u.capacity_ksheets    AS current_capacity,
    u.utilization_pct     AS utilization
FROM factories f
JOIN utilization u ON u.factory_id = f.factory_id
WHERE u.date = (SELECT MAX(date) FROM utilization WHERE is_projection = 0)
ORDER BY f.manufacturer, f.factory_name;

-- Investment by factory (aggregate from equipment_orders)
SELECT
    factory_id,
    po_year,
    SUM(amount_usd) AS total_investment_usd,
    COUNT(*) AS order_count,
    GROUP_CONCAT(DISTINCT equipment_type) AS equipment_types
FROM equipment_orders
GROUP BY factory_id, po_year
ORDER BY factory_id, po_year;
```

### Dropdown structure

```
Factory: BOE B16 (Chongqing, China)
├── Phase 1 — Install: 2023 | MP Ramp: Q3 2023 | 30k sheets/mo | $320M equipment
├── Phase 2 — Install: 2024 | MP Ramp: Q1 2025 | +30k sheets/mo | $280M equipment
└── Phase 3 — Install: 2026 | MP Ramp: Q3 2026 | +30k sheets/mo | $250M (projected)
    Total: 90k sheets/mo | $850M cumulative investment
```

---

## Missing Data

| Data Point | Status | Workaround |
|------------|--------|------------|
| Per-phase investment amount | Not directly linked | Aggregate `equipment_orders.amount_usd` by `factory_id` + `po_year`, align with phase install dates |
| Total fab construction cost | Not tracked | Only equipment spend available; building/infra costs excluded |
| OCR/DITO process capacity | Not in DB | Only backplane + frontplane tracked |
| LTPO vs LTPS % split within factory | Partial | Backplane column shows type, but no % breakdown when mixed |
| Factory-level profitability | Not available | `financials` table exists but is empty (0 records); shipments not linked to factories |
| Depreciation schedules | Not stored | Region is available: use 5yr Korea, 7yr China rule externally |
| Yield data by factory | Schema exists but empty | `yields` table has 0 records |

---

## Recommended Structure for Side-by-Side Comparison Cards

```
┌─────────────────────────────────────┐  ┌─────────────────────────────────────┐
│  BOE B16                            │  │  SDC A6                             │
│  Chongqing, China | OLED | LTPO     │  │  Asan, S Korea | OLED | LTPO        │
│  Generation: G8.5 | Application: TV │  │  Generation: G6 | Application: Mobile│
├─────────────────────────────────────┤  ├─────────────────────────────────────┤
│  Current Capacity: 90k sheets/mo    │  │  Current Capacity: 180k sheets/mo   │
│  Utilization: 78%                   │  │  Utilization: 92%                   │
│  Status: Operating (Prob A)         │  │  Status: Operating (Prob A)         │
├─────────────────────────────────────┤  ├─────────────────────────────────────┤
│  ▼ Investment Timeline              │  │  ▼ Investment Timeline              │
│  ┌──────────────────────────────┐   │  │  ┌──────────────────────────────┐   │
│  │ 2023  Install → MP Q3 2023  │   │  │  │ 2020  Install → MP Q1 2021  │   │
│  │ 30k/mo  |  $320M equipment  │   │  │  │ 60k/mo  |  $360M equipment  │   │
│  ├──────────────────────────────┤   │  │  ├──────────────────────────────┤   │
│  │ 2024  Install → MP Q1 2025  │   │  │  │ 2022  Install → MP Q3 2022  │   │
│  │ +30k/mo |  $280M equipment  │   │  │  │ +60k/mo |  $340M equipment  │   │
│  ├──────────────────────────────┤   │  │  ├──────────────────────────────┤   │
│  │ 2026  Install → MP Q3 2026  │   │  │  │ 2024  Install → MP Q1 2025  │   │
│  │ +30k/mo |  $250M (proj)     │   │  │  │ +60k/mo |  $300M (proj)     │   │
│  └──────────────────────────────┘   │  │  └──────────────────────────────┘   │
│  Cumulative: $850M                  │  │  Cumulative: $1.0B                  │
├─────────────────────────────────────┤  ├─────────────────────────────────────┤
│  ▼ Utilization Trend (sparkline)    │  │  ▼ Utilization Trend (sparkline)    │
│  ████████████▓▓▓▓░░░░               │  │  ████████████████████▓▓░░           │
│  2019──────────────────2026         │  │  2019──────────────────2026         │
│  Depreciation: 7yr (China)          │  │  Depreciation: 5yr (S Korea)        │
└─────────────────────────────────────┘  └─────────────────────────────────────┘
```

### Card sections (top to bottom):
1. **Header**: Factory name, location, technology, backplane, generation, application
2. **Key metrics**: Current capacity, utilization %, status/probability
3. **Investment timeline** (expandable): One row per phase — install date, MP ramp, capacity added, equipment spend
4. **Utilization sparkline** (expandable): Quarterly trend line (historical + projected)
5. **Footer**: Depreciation rule, cumulative investment

### Data source for each section:
- Header → `factories` table
- Key metrics → `utilization` table (latest non-projected month)
- Timeline → `equipment_orders` grouped by `po_year` + `factories.install_date` / `mp_ramp_date`
- Sparkline → `utilization` table (full time series)
- Depreciation → derived from `factories.region` (5yr Korea, 7yr China)
