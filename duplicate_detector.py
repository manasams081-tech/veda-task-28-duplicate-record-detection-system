"""
Duplicate Record Detection Engine
Task 28 - VEDA Technology

Uses only Python, Pandas, and Python's standard-library difflib for fuzzy matching.
"""
from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations
import re
from difflib import SequenceMatcher
from pathlib import Path
from typing import Iterable

import pandas as pd


DEFAULT_FIELDS = ["name", "email", "phone", "city"]
TEXT_FIELDS = {"name", "email", "phone", "city", "address", "company", "product", "description"}


def normalize_value(value) -> str:
    """Normalize text for stable comparison."""
    if pd.isna(value):
        return ""
    text = str(value).strip().lower()
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"[^\w\s@.+-]", "", text)
    return text


def normalize_phone(value) -> str:
    if pd.isna(value):
        return ""
    return re.sub(r"\D", "", str(value))


def similarity(a: str, b: str) -> float:
    if not a and not b:
        return 1.0
    if not a or not b:
        return 0.0
    return SequenceMatcher(None, a, b).ratio()


def field_similarity(field: str, a, b) -> float:
    if field == "phone":
        return similarity(normalize_phone(a), normalize_phone(b))
    return similarity(normalize_value(a), normalize_value(b))


def prepare_dataframe(df: pd.DataFrame, fields: list[str]) -> pd.DataFrame:
    """Add normalized helper columns without modifying the original columns."""
    work = df.copy()
    for field in fields:
        if field in work.columns:
            if field == "phone":
                work[f"__norm_{field}"] = work[field].map(normalize_phone)
            else:
                work[f"__norm_{field}"] = work[field].map(normalize_value)
    return work


def detect_exact_duplicates(df: pd.DataFrame, fields: list[str]) -> pd.DataFrame:
    """Return exact duplicate pairs based on the selected normalized fields."""
    valid = [f for f in fields if f in df.columns]
    if not valid:
        return pd.DataFrame(columns=["row_a", "row_b", "match_fields", "match_type"])

    work = prepare_dataframe(df, valid)
    norm_cols = [f"__norm_{f}" for f in valid]

    # Empty values are ignored for matching; at least one field must contain data.
    key = work[norm_cols].fillna("").agg("|".join, axis=1)
    groups = {}
    for idx, k in enumerate(key):
        if k.replace("|", ""):
            groups.setdefault(k, []).append(idx)

    rows = []
    for indices in groups.values():
        if len(indices) > 1:
            for a, b in combinations(indices, 2):
                matched = [f for f in valid if work.loc[a, f"__norm_{f}"] == work.loc[b, f"__norm_{f}"]
                           and work.loc[a, f"__norm_{f}"] != ""]
                rows.append({
                    "row_a": a + 1,
                    "row_b": b + 1,
                    "match_fields": ", ".join(matched),
                    "match_type": "Exact",
                })
    return pd.DataFrame(rows)


def _pair_score(row_a, row_b, fields: list[str]) -> tuple[float, dict[str, float]]:
    scores = {}
    for field in fields:
        if field in row_a.index and field in row_b.index:
            scores[field] = field_similarity(field, row_a[field], row_b[field])
    usable = [v for k, v in scores.items() if v > 0]
    if not usable:
        return 0.0, scores

    # Slightly prioritize identity-like fields when present.
    weights = {"email": 1.25, "phone": 1.25, "name": 1.10}
    total = 0.0
    weight_sum = 0.0
    for field, score in scores.items():
        if score == 0:
            continue
        w = weights.get(field, 1.0)
        total += score * w
        weight_sum += w
    return (total / weight_sum if weight_sum else 0.0), scores


def detect_potential_duplicates(
    df: pd.DataFrame,
    fields: list[str],
    threshold: float = 0.82,
    max_rows: int = 1500,
) -> pd.DataFrame:
    """Find near duplicates with difflib SequenceMatcher.

    A blocking key reduces comparisons for larger files while still allowing
    common name/email/phone variations to meet in the same candidate group.
    """
    valid = [f for f in fields if f in df.columns]
    if not valid:
        return pd.DataFrame(columns=["row_a", "row_b", "score", "match_fields", "match_type"])

    if len(df) > max_rows:
        raise ValueError(
            f"Fuzzy matching is limited to {max_rows:,} rows for a responsive local web app. "
            "Use the cleaned/exact report for larger files or upload a smaller batch."
        )

    work = prepare_dataframe(df, valid)
    exact = detect_exact_duplicates(df, valid)
    exact_pairs = {(int(r.row_a), int(r.row_b)) for r in exact.itertuples()} if not exact.empty else set()

    # Candidate blocking: share first character of normalized name, email local-part,
    # phone suffix, or city. This avoids comparing every unrelated row.
    blocks = {}
    for i, row in work.iterrows():
        keys = set()
        name = row.get("__norm_name", "")
        email = row.get("__norm_email", "")
        phone = row.get("__norm_phone", "")
        city = row.get("__norm_city", "")
        if name:
            keys.add("n:" + name[:2])
        if email:
            keys.add("e:" + email[:3])
        if phone:
            keys.add("p:" + phone[-4:])
        if city:
            keys.add("c:" + city[:3])
        if not keys:
            keys.add("row:" + str(i))
        for key in keys:
            blocks.setdefault(key, set()).add(i)

    candidates = set()
    for indices in blocks.values():
        if len(indices) <= 1:
            continue
        candidates.update(combinations(sorted(indices), 2))

    rows = []
    for a, b in sorted(candidates):
        pair = (a + 1, b + 1)
        if pair in exact_pairs:
            continue
        score, scores = _pair_score(df.iloc[a], df.iloc[b], valid)
        if score >= threshold:
            matched = sorted(
                [f for f, s in scores.items() if s >= 0.78],
                key=lambda f: scores[f],
                reverse=True,
            )
            rows.append({
                "row_a": a + 1,
                "row_b": b + 1,
                "score": round(score * 100, 1),
                "match_fields": ", ".join(matched[:4]) or "combined similarity",
                "match_type": "Potential",
            })

    result = pd.DataFrame(rows)
    if not result.empty:
        result = result.sort_values(["score", "row_a", "row_b"], ascending=[False, True, True])
    return result


def build_cleaned_dataset(df: pd.DataFrame, exact_pairs: pd.DataFrame) -> pd.DataFrame:
    """Keep the first row from each exact duplicate group and preserve potential matches."""
    if exact_pairs.empty:
        return df.copy()

    # Union-find makes exact duplicate groups transitive (A=B and B=C).
    parent = list(range(len(df)))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a, b):
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[rb] = ra

    for r in exact_pairs.itertuples():
        union(int(r.row_a) - 1, int(r.row_b) - 1)

    keep = []
    seen_roots = set()
    for i in range(len(df)):
        root = find(i)
        if root not in seen_roots:
            seen_roots.add(root)
            keep.append(i)

    return df.iloc[keep].copy().reset_index(drop=True)


def analyze_dataframe(df: pd.DataFrame, fields: list[str], threshold: float = 0.82) -> dict:
    fields = [f for f in fields if f in df.columns]
    if len(fields) < 1:
        raise ValueError("Select at least one matching field that exists in the dataset.")

    exact = detect_exact_duplicates(df, fields)
    potential = detect_potential_duplicates(df, fields, threshold=threshold)
    cleaned = build_cleaned_dataset(df, exact)

    return {
        "exact": exact,
        "potential": potential,
        "cleaned": cleaned,
        "fields": fields,
        "threshold": threshold,
        "rows": len(df),
        "columns": list(df.columns),
        "exact_pair_count": len(exact),
        "potential_pair_count": len(potential),
        "removed_exact_rows": len(df) - len(cleaned),
    }


def save_outputs(result: dict, output_dir: str | Path) -> dict[str, str]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    exact_path = output / "exact_duplicate_report.csv"
    potential_path = output / "potential_duplicate_report.csv"
    cleaned_path = output / "cleaned_dataset.csv"

    result["exact"].to_csv(exact_path, index=False)
    result["potential"].to_csv(potential_path, index=False)
    result["cleaned"].to_csv(cleaned_path, index=False)

    return {
        "exact": exact_path.name,
        "potential": potential_path.name,
        "cleaned": cleaned_path.name,
    }
