# Model and interpretation

## Matched services and lifecycle abatement

All compared portfolios deliver 300,000 t/y chemical methanol and 5,000,000 GJ/y useful shaft work under the central service assumptions. Conventional methanol and heavy fuel oil complete unmet services. The complete conventional-supply baseline includes source emissions and conventional service production/use. Lifecycle abatement is baseline emissions minus portfolio emissions, including source handling, utilities, conversion, delivery and eventual product-carbon releases.

The additional mitigation from admitting utilisation is

\[
\Delta A = A^*_{\mathrm{all\ routes}} - A^*_{\mathrm{storage\ only}}.
\]

Each portfolio is independently optimised under the same resource and service conditions. The storage-only feasible set is nested inside the all-route set. Thus the increment is non-negative within solver tolerance; a strictly positive increment and its sensitivity are the substantive comparisons. A source-tonne denominator always refers to the declared fixed source cohort unless explicitly labelled as a routed-tonne metric.

## Implementation

`paper/model/engineering.py` supplies declared source-conditioning, compression, methanol synthesis, hydrogen and utility packages. Compression uses CoolProp real-fluid properties with explicit CO₂/N₂ surrogate mixtures. The module also supplies capital annualisation and monetary transformations. These are reference engineering packages, not site-specific impurity-removal designs or observed plant accounts.

`paper/model/allocation.py` constructs the LP from those modules. Route variables represent kt raw source CO₂/y; the qualified-hydrogen variable represents ktH₂/y. Internal power is GWh/y, climate objectives are ktCO₂e/y, and financial objectives are MUSD/y. The `metrics` function exports tonnes, MWh and USD, and reconstructs conventional backfills, carbon closure and financial identities.

The primary optimisation uses SciPy `linprog(method='highs')` with primal and dual feasibility tolerances of 1e-8. A second LP minimises resource expense while retaining the primary optimum within `1e-8 * max(1, abs(primary optimum))` in the relevant internal objective units. This is the archived lexicographic procedure. Allocation vectors or duals may differ across platforms on an optimal face even when objective values agree.

## Resources and objectives

The physical domain contains source access, storage access, electricity, hydrogen, methanol reference capacity, product services and declared qualification limits. The mitigation experiment adds an additional-resource-spending ceiling relative to complete conventional service supply. Its storage-only control disables every non-storage route and independently reruns the optimisation.

The generic policy experiment instead minimises private expense with declared support and a public fiscal ceiling. Unless explicitly requested in another experiment, it does not also impose the mitigation experiment's resource-spending ceiling. Support received by the provider, support retained upstream, actual public payment and unused fiscal authorisation remain separate accounts. Hydrogen-support rates are in USD/t eligible H₂ internally; other generic support rates are in USD/t eligible CO₂-feed equivalent.

Regional statutory fields and qualification gates are retained for historical controls. They are scenario assumptions; they do not establish actual project eligibility or current legal compliance. The publication examples use explicitly labelled generic mechanisms.

## Scenario distinctions

ARA, UK, US and CN have source cohorts of 2.5, 2.0, 2.0 and 0.4 MtCO₂/y. The central cross-region controls use 1.2 TWh/y electricity access, 100 kt/y methanol capacity, 57.566136363636375 USD/t fixed source CO₂ additional resource budget, and a common electricity price of 69.07936363636365 USD/MWh. Regional engineering and hydrogen references remain differentiated.

Figure 1 uses the ARA regional electricity price, 70.64842559228472 USD/MWh, and an electricity inventory of 0.0186 tCO₂e/MWh. Its physical balances do not depend on the displaced methanol production inventory. Its route-abatement and frontier panels use the 0.85 tCO₂e/t methanol gas-based production reference. The high-coal production reference used in later comparisons is 4.81 tCO₂e/t methanol. Delivery and eventual product-carbon terms are accounted for separately and must not be added to the input production inventory twice. These inventories are numerical comparison anchors, not observed regional supply mixes.

## Scope boundaries

The annualised new-route investment boundary is 2030; monetary values use September 2026 USD. Infrastructure-delay calculations compare prescribed annual connection states and production cohorts. They do not determine endogenous construction schedules, sunk-investment adaptation or hourly electricity procurement. Geological retention endpoints are published summary evidence and are independent of the annual allocation coefficients. No original retention Monte Carlo draws are included or regenerated.

The selected route set contains geological storage and methanol fuel/chemical uses. Direct electrification, electricity use elsewhere, other carbon products and wider welfare optimisation lie outside that route set. Results describe emissions avoidance for the specified fossil industrial sources; atmospheric removal requires a different source and retention account.
