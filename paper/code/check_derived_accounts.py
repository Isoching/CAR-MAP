"""Reconstruct retained-carbon intervals, cohort shortfalls and fiscal identities."""
from pathlib import Path
import argparse,csv,json
ROOT=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--report',type=Path,default=ROOT/'reproduced/derived_accounts.json')
args=parser.parse_args()
def rows(rel):
    with (ROOT/rel).open(encoding='utf-8-sig') as h:return list(csv.DictReader(h))
retention=rows('data/main/Figure3/GEOLOGICAL_ENDPOINTS.csv');retention_error=0
for r in retention:
    for retained,leaked in [('retained_median_pct','leaked_median_pct'),('retained_low_pct','leaked_table_P05_pct'),('retained_high_pct','leaked_table_P95_pct')]:
        retention_error=max(retention_error,abs(float(r[retained])-(100-float(r[leaked]))))
assert retention_error<1e-10
delay=rows('data/main/Figure3/DELAY_SENSITIVITY.csv');shortfall_error=cohort_error=0
for r in delay:
    d=float(r['delay_years']);n=float(r['annual_periods']);a0=float(r['ready_annual_abatement_tCO2e']);aj=float(r['interim_annual_abatement_tCO2e'])
    shortfall_error=max(shortfall_error,abs(float(r['cumulative_shortfall_tCO2e'])-d*(a0-aj)))
    cohort_error=max(cohort_error,abs(float(r['cumulative_cohort_LCA_abatement_tCO2e'])-((n-d)*a0+d*aj)))
assert max(shortfall_error,cohort_error)<0.01
payment=json.loads((ROOT/'data/supplement/policy_accounts/PANEL_B_PAYMENT_CHAIN.json').read_text())
public_error=abs(payment['ceiling']-payment['paid']-payment['unspent'])
recipient_error=abs(payment['paid']-payment['received']-payment['upstream'])
assert max(public_error,recipient_error)<1e-10
matched=rows('data/main/Figure4/panel_c/PANEL_C_DISPLAY.csv');fiscal_error=private_error=0
for r in matched:
    q=float(r['source_cohort_t']);paid=float(r['public_fiscal_USD'])/q
    resource=(float(r['resource_expense_USD'])-float(r['baseline_resource_USD']))/q
    private=(float(r['private_expense_USD'])-float(r['baseline_resource_USD']))/q
    fiscal_error=max(fiscal_error,abs(paid-float(r['actual_public_USD_source_t'])))
    private_error=max(private_error,abs(private-resource+paid))
assert max(fiscal_error,private_error)<1e-7
report=dict(status='PASS',published_retention_scenarios=len(retention),max_retention_reconstruction_error_pct=retention_error,
    cohort_delay_scenarios=len(delay),max_cohort_reconstruction_error_tCO2e=cohort_error,
    max_shortfall_reconstruction_error_tCO2e=shortfall_error,
    authorisation_payment_reconciliation_error_USD_per_source_t=public_error,
    public_recipient_reconciliation_error_USD_per_source_t=recipient_error,
    matched_outlay_coordinates=len(matched),max_actual_payment_error_USD_per_source_t=fiscal_error,
    max_private_resource_fiscal_identity_error_USD_per_source_t=private_error,
    scope='Reconstruction from retained published endpoints and solved annual-state/financial inputs. No new forecasts, optimisation or Monte Carlo samples.')
args.report.parent.mkdir(parents=True,exist_ok=True);args.report.write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
