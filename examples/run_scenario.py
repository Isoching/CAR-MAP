"""Evaluate a declared scenario and its independently reoptimised storage comparator."""
from __future__ import annotations

import argparse
from dataclasses import asdict
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "paper/model"))
from allocation import Scenario, build, metrics, solve


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--region", choices=("ARA", "UK", "US", "CN"), default="ARA")
    parser.add_argument("--inventory", type=float, default=0.85,
                        help="Conventional methanol production emissions, tCO2e/t methanol; gas reference 0.85, high-coal reference 4.81")
    parser.add_argument("--electricity-price", type=float, default=69.07936363636365,
                        help="USD2026-09/MWh; default is the common Figure 2 reference")
    parser.add_argument("--regional-price", action="store_true",
                        help="Use the kernel's regional reference electricity price (ARA: Figure 1 reference)")
    parser.add_argument("--electricity-ci", type=float, default=None,
                        help="Electricity emissions, tCO2e/MWh; omitted uses the regional kernel default")
    parser.add_argument("--power-gwh", type=float, default=1200.0)
    parser.add_argument("--budget", type=float, default=57.566136363636375,
                        help="Additional resource budget in USD/t fixed source CO2, for the mitigation objective")
    parser.add_argument("--objective", choices=("mitigation", "private"), default="mitigation")
    parser.add_argument("--support", choices=("none", "storage", "utilization", "fuel", "hydrogen"), default="none")
    parser.add_argument("--rate", type=float, default=0.0,
                        help="USD/t eligible CO2 feed equivalent, except hydrogen: USD/t eligible H2")
    parser.add_argument("--fiscal-cap", type=float, default=20.0,
                        help="USD/t fixed source CO2, for the private objective")
    parser.add_argument("--passthrough", type=float, default=1.0)
    parser.add_argument("--output", type=Path, default=ROOT / "reproduced/example.json")
    args = parser.parse_args()
    if args.objective == "mitigation" and args.support != "none":
        parser.error("Use --objective private for a support mechanism")
    if args.inventory < 0 or args.power_gwh < 0 or args.budget < 0 or args.rate < 0 or args.fiscal_cap < 0:
        parser.error("Inventory, resource access, budgets and payment rates must be non-negative")
    if args.output.resolve() == ROOT / "paper" or (ROOT / "paper").resolve() in args.output.resolve().parents:
        parser.error("Write new results outside the frozen paper/ tree")
    sc = Scenario(electricity_price=None if args.regional_price else args.electricity_price,
                  electricity_GHG=args.electricity_ci, power_GWh=args.power_gwh,
                  conventional_meoh_production_GHG=args.inventory,
                  budget_per_source_t=args.budget,
                  policy="mechanism" if args.objective == "private" else "neutral",
                  payment_target=args.support, payment_rate=args.rate,
                  hydrogen_credit_passthrough=args.passthrough,
                  fiscal_budget_per_source_t=args.fiscal_cap if args.objective == "private" else None)
    model = build(args.region, sc)
    if args.objective == "mitigation":
        budget = model["baseline_resource_MUSD"] + args.budget * model["fixed_source_t"] / 1e6
        all_routes = metrics(model, solve(model, "ghg", budget_MUSD=budget))
        storage_only = metrics(model, solve(model, "ghg", budget_MUSD=budget, storage_only=True))
        if not all_routes["feasible"] or not storage_only["feasible"]:
            raise RuntimeError("The requested portfolio or comparator is infeasible")
        gain = all_routes["abatement_tCO2e"] - storage_only["abatement_tCO2e"]
        if gain < -0.05:
            raise ArithmeticError("All-route abatement fell below its nested storage comparator")
        result = {"all_routes": all_routes, "storage_only": storage_only,
                  "additional_abatement_tCO2e": gain,
                  "additional_abatement_kg_per_fixed_source_t": 1000 * gain / model["fixed_source_t"]}
    else:
        private = metrics(model, solve(model, "private"))
        if not private["feasible"]:
            raise RuntimeError("The requested private allocation is infeasible")
        result = {"private_optimum": private,
                  "note": "Generic support mechanism with a fiscal cap. The mitigation resource-budget constraint is not imposed in this private decision experiment."}
    payload = {"framework": "CAR-MAP", "region": args.region, "scenario": asdict(sc),
               "effective_electricity_price_USD_MWh": model["electricity_price"],
               "effective_electricity_GHG_tCO2e_MWh": model["electricity_GHG"], **result}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    if args.objective == "mitigation":
        print(f"{args.region}: all-route abatement {all_routes['abatement_tCO2e']:.6f} tCO2e/y; "
              f"storage comparator {storage_only['abatement_tCO2e']:.6f}; increment {gain:.6f}")
    else:
        print(f"{args.region}: private optimum; abatement {private['abatement_tCO2e']:.6f} tCO2e/y; "
              f"actual public outlay USD {private['public_fiscal_USD']:.6f}/y")
    print(f"Saved {args.output}")


if __name__ == "__main__":
    main()
