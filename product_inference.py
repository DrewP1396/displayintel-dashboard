"""
Product inference for OLED shipments data.

Infers product names from brand + size_inches + application + panel_maker
when the model column is empty. Designed for ~38K OLED-only shipment rows.
"""

import pandas as pd
from typing import Tuple, List, Optional


# ---------------------------------------------------------------------------
# PRODUCT_RULES: (brand, application) → list of (min_size, max_size, product_name)
# Size ranges in inches (inclusive on both ends).
# ---------------------------------------------------------------------------

PRODUCT_RULES: dict[tuple[str, str], list[tuple[float, float, str]]] = {
    # ----- Apple iPhone -----
    ("Apple", "Smartphone"): [
        (4.0, 4.9, "iPhone SE"),
        (5.0, 5.49, "iPhone mini"),
        (5.5, 6.19, "iPhone (standard)"),
        (6.06, 6.19, "iPhone Pro"),          # overlaps with standard
        (6.6, 6.75, "iPhone Plus"),
        (6.65, 6.9, "iPhone Pro Max"),        # overlaps with Plus at 6.7
    ],
    # ----- Samsung Galaxy -----
    ("Samsung", "Smartphone"): [
        (6.0, 6.29, "Galaxy S (standard)"),
        (6.5, 6.69, "Galaxy S+"),
        (6.7, 6.9, "Galaxy S Ultra"),
        (6.7, 6.7, "Galaxy Z Flip"),          # overlaps with Ultra at 6.7
    ],
    # ----- Apple iPad -----
    ("Apple", "Tablet"): [
        (7.5, 8.39, "iPad mini"),
        (10.5, 11.09, "iPad Air"),
        (11.0, 11.1, "iPad Pro 11\""),        # overlaps with Air at 11.0-11.09
        (12.5, 13.0, "iPad Pro 12.9\""),
    ],
    # ----- Huawei MatePad -----
    ("Huawei", "Tablet"): [
        (10.0, 10.9, "MatePad (standard)"),
        (11.0, 12.0, "MatePad Pro"),
        (12.1, 12.9, "MatePad Pro 12.6\""),
    ],
    # ----- Apple MacBook -----
    ("Apple", "Notebook"): [
        (13.0, 13.69, "MacBook Air 13\""),
        (13.7, 14.5, "MacBook Pro 14\""),
        (15.5, 16.5, "MacBook Pro 16\""),
    ],
}

# ---------------------------------------------------------------------------
# SUPPLIER_CUSTOMERS: panel_maker → known customer brands
# ---------------------------------------------------------------------------

SUPPLIER_CUSTOMERS: dict[str, list[str]] = {
    "SDC": ["Samsung", "Apple", "Oppo", "Vivo", "Xiaomi", "ASUS", "HP", "Dell", "Lenovo", "Acer"],
    "LGD": ["Apple", "LGE"],
    "BOE": ["Huawei", "Honor", "Apple", "Oppo", "Vivo", "Xiaomi"],
    "Visionox": ["Honor", "Huawei", "Xiaomi", "Vivo", "Oppo"],
    "Tianma": ["Huawei", "Xiaomi", "Honor", "Apple", "Oppo"],
    "EDO": ["Samsung", "Oppo", "Vivo", "Xiaomi"],
    "China Star": ["Xiaomi", "Huawei"],
    "AUO": ["ASUS"],
    "Truly": ["Huawei", "Oppo"],
    "JDI": ["SONY"],
}

# Reverse lookup: brand → set of known suppliers
_BRAND_SUPPLIERS: dict[str, set[str]] = {}
for _maker, _brands in SUPPLIER_CUSTOMERS.items():
    for _b in _brands:
        _BRAND_SUPPLIERS.setdefault(_b, set()).add(_maker)

# ---------------------------------------------------------------------------
# Supplier disambiguation hints for overlapping size ranges.
# Key: product_name → set of panel_makers that strongly indicate this product.
# ---------------------------------------------------------------------------

_SUPPLIER_HINTS: dict[str, set[str]] = {
    "iPhone Pro": {"LGD"},
    "iPhone Pro Max": {"LGD"},
    "iPad Pro 11\"": {"SDC"},
    "iPad Air": {"LGD"},
    "Galaxy S Ultra": {"SDC"},
}


def _supplier_is_known_pair(brand: str, panel_maker: str) -> bool:
    """Check whether panel_maker is a known supplier for brand."""
    known = _BRAND_SUPPLIERS.get(brand)
    if known is None:
        return False
    return panel_maker in known


def infer_product(
    row: dict,
) -> Tuple[str, str, List[str]]:
    """Infer product name from a shipment row.

    Parameters
    ----------
    row : dict-like
        Must contain keys: brand, application, size_inches, panel_maker.

    Returns
    -------
    (product_name, confidence, alternatives)
        confidence is "high", "medium", or "low".
        alternatives lists other plausible products (empty if unambiguous).
    """
    brand = str(row.get("brand", "") or "").strip()
    application = str(row.get("application", "") or "").strip()
    panel_maker = str(row.get("panel_maker", "") or "").strip()

    try:
        size = float(row.get("size_inches", 0) or 0)
    except (ValueError, TypeError):
        size = 0.0

    # ---- Step 1: look up rules for (brand, application) ----
    rules = PRODUCT_RULES.get((brand, application))
    if rules is None:
        # No rules → generic fallback
        generic = f"{brand} {application}" if brand and application else "Unknown"
        return (generic, "low", [])

    # ---- Step 2: find all matching size ranges ----
    matches: list[str] = []
    for lo, hi, product in rules:
        if lo <= size <= hi:
            matches.append(product)

    if not matches:
        generic = f"{brand} {application}"
        return (generic, "low", [])

    # ---- Step 3: single match → straightforward ----
    if len(matches) == 1:
        product = matches[0]
        known = _supplier_is_known_pair(brand, panel_maker)
        confidence = "high" if known else "medium"
        return (product, confidence, [])

    # ---- Step 4: multiple matches → use supplier hints to disambiguate ----
    hinted: list[str] = []
    others: list[str] = []
    for product in matches:
        hint_makers = _SUPPLIER_HINTS.get(product)
        if hint_makers and panel_maker in hint_makers:
            hinted.append(product)
        else:
            others.append(product)

    if len(hinted) == 1:
        # Supplier hint narrows it to one product
        best = hinted[0]
        alternatives = [p for p in matches if p != best]
        return (best, "high", alternatives)

    # Check if supplier hints rule out some candidates (supplier is known
    # but NOT in the hint set for certain products → those are unlikely).
    # If exactly one candidate survives, that's a high-confidence pick.
    if not hinted:
        unhinted = []
        for product in matches:
            hint_makers = _SUPPLIER_HINTS.get(product)
            if hint_makers and panel_maker not in hint_makers:
                # This product is hinted for OTHER suppliers → unlikely
                continue
            unhinted.append(product)
        if len(unhinted) == 1:
            best = unhinted[0]
            known = _supplier_is_known_pair(brand, panel_maker)
            alternatives = [p for p in matches if p != best]
            return (best, "high" if known else "medium", alternatives)

    # No decisive hint — pick the first non-Pro variant as default,
    # or just the first match if all are "Pro" variants.
    non_pro = [p for p in matches if "Pro" not in p]
    if non_pro:
        best = non_pro[0]
    else:
        best = matches[0]
    alternatives = [p for p in matches if p != best]
    return (best, "medium", alternatives)


def enrich_shipments(df: pd.DataFrame) -> pd.DataFrame:
    """Add inferred_product and inference_confidence columns to a shipments DataFrame.

    Parameters
    ----------
    df : pd.DataFrame
        Shipments data with columns: brand, application, size_inches, panel_maker.

    Returns
    -------
    pd.DataFrame
        Copy of the input with two new columns added.
    """
    results = df.apply(
        lambda r: infer_product(r),
        axis=1,
        result_type="expand",
    )
    out = df.copy()
    out["inferred_product"] = results[0]
    out["inference_confidence"] = results[1]
    return out


# ---------------------------------------------------------------------------
# Smoke tests — run with: python3 product_inference.py
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    tests = [
        {
            "brand": "Apple", "application": "Smartphone",
            "size_inches": 6.12, "panel_maker": "SDC",
            "expect": ("iPhone (standard)", "high"),
        },
        {
            "brand": "Samsung", "application": "Smartphone",
            "size_inches": 6.8, "panel_maker": "SDC",
            "expect": ("Galaxy S Ultra", "high"),
        },
        {
            "brand": "Apple", "application": "Tablet",
            "size_inches": 12.9, "panel_maker": "SDC",
            "expect": ("iPad Pro 12.9\"", "high"),
        },
        {
            "brand": "Apple", "application": "Notebook",
            "size_inches": 14.2, "panel_maker": "LGD",
            "expect": ("MacBook Pro 14\"", "high"),
        },
        {
            "brand": "Huawei", "application": "Tablet",
            "size_inches": 12.6, "panel_maker": "BOE",
            "expect": ("MatePad Pro 12.6\"", "high"),
        },
        {
            "brand": "UnknownBrand", "application": "Smartphone",
            "size_inches": 6.5, "panel_maker": "BOE",
            "expect": ("UnknownBrand Smartphone", "low"),
        },
        # Ambiguity tests
        {
            "brand": "Apple", "application": "Smartphone",
            "size_inches": 6.12, "panel_maker": "LGD",
            "expect": ("iPhone Pro", "high"),
        },
        {
            "brand": "Apple", "application": "Tablet",
            "size_inches": 11.05, "panel_maker": "SDC",
            "expect": ("iPad Pro 11\"", "high"),
        },
        {
            "brand": "Apple", "application": "Tablet",
            "size_inches": 11.05, "panel_maker": "LGD",
            "expect": ("iPad Air", "high"),
        },
    ]

    print("Product Inference Smoke Tests")
    print("=" * 70)

    passed = 0
    failed = 0

    for t in tests:
        expected_product, expected_conf = t["expect"]
        row = {k: v for k, v in t.items() if k != "expect"}
        product, confidence, alternatives = infer_product(row)

        ok = product == expected_product and confidence == expected_conf
        status = "PASS" if ok else "FAIL"
        if ok:
            passed += 1
        else:
            failed += 1

        alt_str = f"  alt={alternatives}" if alternatives else ""
        print(f"  [{status}] {row['brand']:>12} | {row['application']:<12} | "
              f"{row['size_inches']:>5}\" | {row['panel_maker']:<8} "
              f"→ {product} ({confidence}){alt_str}")
        if not ok:
            print(f"         expected: {expected_product} ({expected_conf})")

    print("-" * 70)
    print(f"  {passed} passed, {failed} failed, {passed + failed} total")

    # Quick enrich_shipments test
    print("\nenrich_shipments() test:")
    sample = pd.DataFrame([
        {"brand": "Apple", "application": "Smartphone", "size_inches": 6.12,
         "panel_maker": "SDC", "units_k": 100, "revenue_m": 50},
        {"brand": "Samsung", "application": "Smartphone", "size_inches": 6.8,
         "panel_maker": "SDC", "units_k": 80, "revenue_m": 40},
    ])
    enriched = enrich_shipments(sample)
    print(enriched[["brand", "size_inches", "inferred_product", "inference_confidence"]].to_string(index=False))
