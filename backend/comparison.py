"""Preference-sensitive selection over independently verified outcomes."""

import math

DEFAULT_WEIGHTS = {"coverage": .55, "equity": .35, "cost": .10}


def compare_worlds(worlds: list[dict], weights: dict | None = None,
                   cost_bound: float = 20000) -> dict:
    weights = dict(DEFAULT_WEIGHTS if weights is None else weights)
    if set(weights) != set(DEFAULT_WEIGHTS) or any(
        not isinstance(x, (int, float)) or not math.isfinite(x) or x < 0 or x > 1
        for x in weights.values()
    ) or sum(weights.values()) <= 0:
        raise ValueError("Choose nonnegative preference weights with a positive total.")
    total = sum(weights.values())
    weights = {key: value / total for key, value in weights.items()}
    eligible = [w for w in worlds if w.get("verification", {}).get("valid")]
    metrics = {w["id"]: w["verification"]["metrics"] for w in eligible}
    scores = {}
    for world in eligible:
        m = metrics[world["id"]]
        scores[world["id"]] = round(
            weights["coverage"] * m["on_time_coverage"]
            + weights["equity"] * m["priority_coverage"]
            + weights["cost"] * (1 - min(1., m["cost_cents"] / max(1, cost_bound))), 8)
    def dominates(a: dict, b: dict) -> bool:
        av = (a["on_time_coverage"], a["priority_coverage"], -a["cost_cents"])
        bv = (b["on_time_coverage"], b["priority_coverage"], -b["cost_cents"])
        return all(x >= y for x, y in zip(av, bv)) and any(x > y for x, y in zip(av, bv))
    pareto = [w["id"] for w in eligible if not any(
        dominates(metrics[other["id"]], metrics[w["id"]])
        for other in eligible if other["id"] != w["id"])]
    best = max(scores.values(), default=None)
    tied = [key for key, score in scores.items() if best is not None and abs(score - best) < 1e-7]
    recommended = tied[0] if len(tied) == 1 else None
    if recommended:
        world = next(w for w in eligible if w["id"] == recommended)
        m = metrics[recommended]
        explanation = (f"{world['name']} leads under your current preferences: "
                       f"{m['meals_delivered']} meals delivered, "
                       f"{m['priority_coverage']:.0%} on-time high-need coverage, "
                       f"${m['cost_cents'] / 100:.2f} modeled travel cost.")
    elif tied:
        explanation = "These verified outcomes tie under your preferences. Inspect their routes before choosing."
    else:
        explanation = "No world has passed independent verification. No operational recommendation is eligible."
    return {"recommended_id": recommended, "pareto_ids": pareto,
            "scores": scores, "weights": weights, "tied_ids": tied,
            "eligible_ids": [w["id"] for w in eligible], "explanation": explanation,
            "normalization": {"cost_bound_cents": cost_bound,
                              "coverage": "on_time_meals / total_requested",
                              "equity": "on_time_priority_3_meals / priority_3_requested"}}
