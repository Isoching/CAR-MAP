"""Deterministic supplementary controls on the unchanged allocation kernel."""
from pathlib import Path
from dataclasses import replace, asdict
import csv, json, sys, hashlib
import numpy as np

P=Path(__file__).resolve().parent
BASE=P.parent
sys.path.insert(0,str(BASE/'model'))
from allocation import Scenario, build, solve, metrics
from engineering import Engineering, ALPHA, BETA

import argparse
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--output',type=Path,default=BASE/'reproduced/controls')
args=parser.parse_args()
O=args.output.resolve();O.mkdir(parents=True,exist_ok=True)
REGIONS=['ARA','UK','US','CN']
PRICE=69.07936363636365
SOLVES=[]
def clean(x):
    if isinstance(x,np.ndarray):return x.tolist()
    if isinstance(x,np.generic):return x.item()
    if isinstance(x,dict):return {k:clean(v) for k,v in x.items()}
    if isinstance(x,(tuple,list)):return [clean(v) for v in x]
    return x
def save(name,x): (O/name).write_text(json.dumps(clean(x),indent=2,ensure_ascii=False,allow_nan=False))
def csvsave(name,rows):
    with (O/name).open('w',newline='',encoding='utf-8-sig') as h:
        w=csv.DictWriter(h,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
def paired(region,sc,label):
    p=build(region,sc)
    budget=p['baseline_resource_MUSD']+sc.budget_per_source_t*p['fixed_source_t']/1e6
    records=[]
    for storage in [False,True]:
        r=solve(p,'ghg',budget_MUSD=budget,storage_only=storage)
        m=metrics(p,r)
        assert m['feasible'],(label,m)
        records.append(m)
        SOLVES.append(dict(label=label,storage_only=storage,region=region,scenario=asdict(sc),metrics=m))
    a,s=records
    gain=a['abatement_tCO2e']-s['abatement_tCO2e']
    assert gain>=-.05,(label,gain)
    return dict(region=region,inventory=sc.conventional_meoh_production_GHG,
        electricity_CI_g_kWh=p['electricity_GHG']*1000,
        power_MWh_per_source_t=sc.power_GWh*1000/p['fixed_source_t'],
        synthesis_cost_multiplier=sc.engineering.synthesis_cost_multiplier,
        hydrogen_share=sc.hydrogen_share,
        extra_abatement_kg_per_source_t=1000*gain/p['fixed_source_t'],
        relative_gain_pct=100*gain/s['abatement_tCO2e'] if s['abatement_tCO2e']>0 else None,
        capture_pct=100*a['captured_raw_CO2_t']/p['fixed_source_t'],
        utilization_pct=100*(a['captured_raw_CO2_t']-a['stored_CO2_t'])/p['fixed_source_t'],
        electricity_MWh=a['electricity_MWh'],hydrogen_t=a['hydrogen_t'],
        abatement_tCO2e=a['abatement_tCO2e'],storage_only_abatement_tCO2e=s['abatement_tCO2e'])

central=[]
for region in REGIONS:
    for inv in [.85,2.6,3.8,4.54,4.81,5.06]:
        central.append(paired(region,Scenario(electricity_price=PRICE,conventional_meoh_production_GHG=inv),f'central_{region}_{inv}'))
csvsave('CENTRAL_LITERATURE_CONTROLS.csv',central)
print('Central literature controls',len(central),flush=True)

normal=[]
for region in REGIONS:
    q=build(region,Scenario())['fixed_source_t']
    for power in [.48,.6,3.]:
        for inv in [.85,3.8,4.81]:
            normal.append(paired(region,Scenario(electricity_price=PRICE,power_GWh=power*q/1000,
                conventional_meoh_production_GHG=inv),f'normalised_{region}_{power}_{inv}'))
csvsave('NORMALISED_ELECTRICITY.csv',normal)
print('Normalised electricity',len(normal),flush=True)

joint=[]
for region in REGIONS:
    for inv in [.584,.627,.85,2.6,3.2,3.8,4.54,4.65,4.81,5.06]:
        for ef in [.01,.017652631578947368,.0186,.05,.1,.2]:
            for cm in [.8,1.,1.2]:
                sc=Scenario(electricity_price=PRICE,electricity_GHG=ef,
                    conventional_meoh_production_GHG=inv,
                    engineering=Engineering(synthesis_cost_multiplier=cm))
                joint.append(paired(region,sc,f'joint_{region}_{inv}_{ef}_{cm}'))
csvsave('JOINT_INVENTORY_ELECTRICITY_COST.csv',joint)
print('Joint controls',len(joint),flush=True)

h2=[]
for region in REGIONS:
    for share in [.5,.75,1.]:
        for inv in [.85,3.8,4.81]:
            h2.append(paired(region,Scenario(electricity_price=PRICE,hydrogen_share=share,
                conventional_meoh_production_GHG=inv),f'hydrogen_{region}_{share}_{inv}'))
csvsave('HYDROGEN_ACCESS.csv',h2)

# Extend the plotted inventory scan without discarding any original nodes.
extension=[]
for region in REGIONS:
    for inv in [4.85,4.9,4.95,5.,5.06,5.1,5.2]:
        extension.append(paired(region,Scenario(electricity_price=PRICE,
            conventional_meoh_production_GHG=inv),f'extension_{region}_{inv}'))
csvsave('INVENTORY_EXTENSION.csv',extension)

# Calibrate each generic support object to the cheapest eligible route's
# annualised entry expense. Premiums avoid the zero-margin tie at exact entry.
policy=[]
for target in ['storage','utilization','hydrogen','fuel']:
    s0=Scenario(policy='mechanism',electricity_price=PRICE,payment_target=target)
    p0=build('ARA',s0)
    rec={r['variable']:r for r in p0['coefficient_records']} if 'coefficient_records' in p0 else None
    candidates=[]
    for j,name in enumerate(p0['names']):
        if name=='qualified_H2':continue
        route=name.split('::')[1]
        allowed=(route=='storage' if target=='storage' else route=='chemical' if target in ['utilization','hydrogen'] else route=='fuel')
        if not allowed:continue
        cost=p0['vectors']['gross_increment'][j]*1000
        eligible=1. if target=='storage' else p0['vectors']['methanol'][j]*ALPHA
        if target=='hydrogen':cost+=p0['vectors']['hydrogen'][j]*s0.certification_cost_per_tH2
        if eligible>0:candidates.append(cost/eligible)
    entry=min(candidates)
    for premium in [.001,.01,.05]:
        rate=entry*(1+premium)
        native_rate=rate*ALPHA/BETA if target=='hydrogen' else rate
        sc=replace(s0,payment_rate=native_rate,fiscal_budget_per_source_t=20.)
        p=build('ARA',sc);r=solve(p,'private');m=metrics(p,r)
        assert m['feasible']
        actual=m['public_fiscal_USD']/p['fixed_source_t']
        assert abs(actual-20)<.001,(target,actual)
        SOLVES.append(dict(label=f'calibrated_{target}_{premium}',region='ARA',scenario=asdict(sc),metrics=m))
        policy.append(dict(target=target,premium_fraction=premium,entry_USD_per_feed_equivalent=entry,
            support_USD_per_feed_equivalent=rate,native_support_USD_per_tH2=native_rate if target=='hydrogen' else None,
            actual_public_USD_per_source_t=actual,
            abatement_kg_per_source_t=m['abatement_tCO2e']/p['fixed_source_t']*1000,
            resource_USD_per_source_t=(m['resource_expense_USD']-m['baseline_resource_USD'])/p['fixed_source_t'],
            private_change_USD_per_source_t=(m['private_expense_USD']-m['baseline_resource_USD'])/p['fixed_source_t'],
            electricity_GWh=m['electricity_MWh']/1000,hydrogen_t=m['hydrogen_t']))
csvsave('ENTRY_CALIBRATED_SUPPORT.csv',policy)
save('FULL_CONTROL_SOLUTIONS.json',SOLVES)
summary={'central':central,'normalised':normal,'policy_1pct':[r for r in policy if r['premium_fraction']==.01],
    'joint_grid':{'regions':4,'production_inventories':10,'electricity_inventories':6,'synthesis_cost_factors':3,'paired_scenarios':len(joint)},
    'number_of_solutions':len(SOLVES),
    'max_carbon_residual_t':max(abs(r['metrics']['carbon_balance_residual_t']) for r in SOLVES),
    'max_financial_residual_USD':max(abs(r['metrics']['finance_ledger_residual_USD']) for r in SOLVES),
    'max_scaled_primal_residual':max(r['metrics']['solver_primal_residual'] for r in SOLVES),
    'frozen_model_hashes':{str(f.relative_to(BASE)):hashlib.sha256(f.read_bytes()).hexdigest() for f in (BASE/'model').glob('*.py')}}
save('SUMMARY.json',summary)
print(json.dumps(clean(summary['policy_1pct']),indent=2),flush=True)
print('Complete',len(SOLVES),'solutions',flush=True)
