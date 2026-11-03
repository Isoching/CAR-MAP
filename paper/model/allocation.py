"""V4.4 native-USD annual carbon allocation LP and separately reconciled ledgers.

Flow variables are kt of native-source CO2 per year. Eligible H2 is ktH2/y.
Final-service backfills are eliminated analytically, and reconstructed for audit.
No historical LP arrays are patched or imported.
"""
from __future__ import annotations
from dataclasses import dataclass, asdict
from functools import lru_cache
import json
import math
import numpy as np
from scipy.optimize import linprog
from engineering import Engineering,ALPHA,BETA,source_modules,methanol_module,money,region_sources,HERE,eur2026,USD_PER_EUR

REGIONS=('ARA','UK','US','CN')
ROUTES=('storage','fuel','fuel_qualified','chemical')
TOL=2e-6

@dataclass(frozen=True)
class Scenario:
    engineering:Engineering=Engineering()
    policy:str='neutral'
    electricity_price:float|None=None
    electricity_GHG:float|None=None
    backup_share:float=0.
    network_GHG:float=.0046
    product_delivery_GHG:float=.02
    methanol_fuel_nonCO2:float=.0491
    power_GWh:float=1200.
    hydrogen_share:float=1.
    source_share:float=1.
    storage_share:float=1.
    quality_share:float=1.
    chemical_demand_t:float=300000.
    shaft_service_GJ:float=5e6
    methanol_engine_efficiency:float=.45
    hfo_engine_efficiency:float=.45
    methanol_capacity_t:float=100000.
    conventional_meoh_production_GHG:float=.85
    conventional_meoh_price:float=eur2026(460.22125629126094)
    hfo_price:float=eur2026(511.35695143473436)
    new_product_delivery_cost:float=eur2026(20.)
    certification_cost_per_tH2:float=eur2026(100.)
    hydrogen_qualification_share:float=1.
    certification_ok:bool=True
    regulatory_h2_CI:float=.4
    us_construction_before2028:bool=True
    us_capture_construction_before2033:bool=True
    us_capture_service_year:int=2029
    us_hydrogen_service_year:int=2029
    us_pwa:bool=True
    us_same_h2_facility_45q:bool=False
    credit_realization:float=1.
    hydrogen_credit_passthrough:float=1.
    fiscal_budget_per_source_t:float|None=None
    payment_target:str='none'
    payment_rate:float=0.
    sde_base_rate:float|None=None
    force_fuel_compliance:bool=False
    destination_locked:bool=False
    budget_per_source_t:float=eur2026(50.)
    relative_scale:bool=False
    uk_supported_rate:float|None=None
    uk_generation_CO2_t:float|None=None

def defaults(region,sc):
    prices={'ARA':eur2026(61.36283417216812),'UK':eur2026(102.27139028694688),'US':eur2026(55.39212722805865),
            'CN':(money(127.,'CNY','2020')+money(50.,'CNY','2026-09'))/.95}
    price=prices[region] if sc.electricity_price is None else sc.electricity_price
    wind=.0133 if region in ['ARA','UK'] else .0124
    ef=((1-sc.backup_share)*wind+sc.backup_share*.434)/.95+sc.network_GHG
    if sc.electricity_GHG is not None:ef=sc.electricity_GHG
    h2={'ARA':21900.,'UK':68.8*8760*.8/sc.engineering.h2_kWh_kg,'US':20000.,'CN':8630.4}[region]
    return price,ef,h2

@lru_cache(maxsize=512)
def engineering_bundle(region,engineering):
    return source_modules(region,engineering),methanol_module(engineering)

def build(region,sc=Scenario(),claim_45q=False):
    if region not in REGIONS:raise ValueError(region)
    if claim_45q and not(sc.us_capture_construction_before2033 and 0<=2030-sc.us_capture_service_year<12):
        raise ValueError('45Q claim outside construction/service eligibility window')
    for name in ['hydrogen_share','source_share','storage_share','quality_share','hydrogen_qualification_share','credit_realization','hydrogen_credit_passthrough','backup_share']:
        if not 0<=getattr(sc,name)<=1:raise ValueError(name)
    sources,meoh=engineering_bundle(region,sc.engineering)
    price,ef,h2_nom=defaults(region,sc)
    cohort=sum(s['source']['Q'] for s in sources)
    scale=cohort/2e6 if sc.relative_scale else 1.
    Dm=sc.chemical_demand_t*scale
    Dshaft=sc.shaft_service_GJ*scale
    power_cap=sc.power_GWh*scale
    cap_M=sc.methanol_capacity_t*scale
    etaM=sc.methanol_engine_efficiency;etaH=sc.hfo_engine_efficiency
    base_hfo=Dshaft/(40.5*etaH)
    conv_G=sc.conventional_meoh_production_GHG+1.375+sc.product_delivery_GHG
    base_G=(cohort+base_hfo*3.70985+Dm*conv_G)/1000
    base_C=(base_hfo*sc.hfo_price+Dm*sc.conventional_meoh_price)/1e6
    names=[f'{s["source"]["name"]}::{r}' for s in sources for r in ROUTES]+['qualified_H2']
    n=len(names);index={name:i for i,name in enumerate(names)}
    vecs={name:np.zeros(n) for name in ['power','hydrogen','methanol','chemical','fuel','stored','raw_captured','qualified_fuel_hydrogen','gross_increment','ghg_increment','tax_increment','fiscal','received','supplier_retained','certification_resource','private_increment']}
    bounds=[(0.,None)]*n
    source_masks={}
    records=[]
    for source in sources:
        native=source['source'];sname=native['name'];mask=np.zeros(n)
        for route in ROUTES:
            j=index[f'{sname}::{route}'];mask[j]=1.
            if route=='storage':
                mod=source['storage']
                E=mod['electricity'];C=mod['nonpower']+price*E
                G=ef*E+mod['nonenergy_ghg']-1.
                m=0.;h=0.
                vecs['stored'][j]=1.
            else:
                mod=source['utilization']
                if mod is None:
                    bounds[j]=(0.,0.);E=C=G=m=h=0.
                else:
                    m=mod['recovery']/ALPHA
                    h=BETA*m
                    E=mod['electricity_per_raw_t']+m*meoh['electricity_MWh_tMeOH']
                    C=mod['nonpower_per_raw_t']+m*(meoh['nonpower_USD_tMeOH']+sc.new_product_delivery_cost)+price*E
                    # Fixed source carbon remains emitted after utilization.
                    # Product/byproduct/qualification vents sum to the raw CO2.
                    G=ef*E+mod['nonenergy_ghg_per_raw_t']+sc.product_delivery_GHG*m
                    if route=='chemical':
                        C-=m*sc.conventional_meoh_price
                        G-=m*conv_G
                        vecs['chemical'][j]=m
                    else:
                        # Official TBM fallback accounting reference, not measured
                        # engine inventory. Source CO2 remains inQ-S exactly once.
                        G+=m*sc.methanol_fuel_nonCO2
                        displaced_hfo=m*19.9*etaM/(40.5*etaH)
                        C-=displaced_hfo*sc.hfo_price
                        G-=displaced_hfo*3.70985
                        vecs['fuel'][j]=m
                    if route=='fuel_qualified':vecs['qualified_fuel_hydrogen'][j]=h
                if sc.destination_locked:bounds[j]=(0.,0.)
            vecs['power'][j]=E # GWh per ktCO2 (numerically MWh/t)
            vecs['hydrogen'][j]=h # ktH2 per ktCO2
            vecs['methanol'][j]=m
            vecs['raw_captured'][j]=1.
            vecs['gross_increment'][j]=C/1000 # MUSD per ktCO2
            vecs['ghg_increment'][j]=G # ktCO2e per ktCO2
            records.append(dict(variable=names[j],raw_source=native['name'],route=route,
                                electricity_MWh_per_raw_t=E,hydrogen_t_per_raw_t=h,methanol_t_per_raw_t=m,
                                resource_increment_USD_per_raw_t=C,GHG_increment_tCO2e_per_raw_t=G,
                                scope='raw carbon basis, qualification recovery included; relative to complete-service baseline'))
        source_masks[sname]=mask
    q=index['qualified_H2']
    vecs['certification_resource'][q]=sc.certification_cost_per_tH2/1000
    vecs['gross_increment'][q]=vecs['certification_resource'][q]
    A=[];b=[];cn=[];units=[]
    def add(row,rhs,name,unit):
        A.append(np.asarray(row,dtype=float).copy());b.append(float(rhs));cn.append(name);units.append(unit)
    for source in sources:
        native=source['source'];name=native['name'];mask=source_masks[name]
        add(mask,native['Q']/1000*sc.source_share,'source_access::'+name,'ktCO2/year')
        usemask=mask.copy();usemask[index[f'{name}::storage']]=0
        add(usemask,native['Q']/1000*sc.source_share*sc.quality_share,'qualified_native_gas::'+name,'ktCO2/year')
    add(vecs['stored'],cohort/1000*sc.storage_share,'storage_access','ktCO2/year')
    add(vecs['power'],power_cap,'electricity','GWh/year')
    add(vecs['hydrogen'],h2_nom/1000*sc.hydrogen_share,'hydrogen','ktH2/year')
    add(vecs['methanol'],cap_M/1000,'methanol_reference_capacity','ktMeOH/year')
    add(vecs['chemical'],Dm/1000,'chemical_service','ktMeOH/year')
    # hfo backfill>=0 at fixed delivered shaft service.
    add(vecs['fuel']*19.9*etaM,Dshaft/1000,'shaft_service','TJshaft/year')
    r=np.zeros(n);r[q]=1
    add(r-vecs['hydrogen'],0.,'qualified_H2_is_actually_used','ktH2/year')
    qcap=h2_nom/1000*sc.hydrogen_share*sc.hydrogen_qualification_share if sc.certification_ok else 0.
    add(r,qcap,'qualified_H2_access','ktH2/year')
    add(vecs['qualified_fuel_hydrogen']-r,0.,'qualified_fuel_uses_qualified_hydrogen','ktH2/year')
    # This is an annual resource conservation condition, not proof of hourly
    # matching/additionality. Those are independent declared qualification gates.
    add(r*sc.engineering.h2_kWh_kg-(1-sc.backup_share)*vecs['power'],0.,'annual_renewable_volume_for_qualified_H2','GWh/year')
    baseline_tax=0.
    qualified_flag=(sc.certification_ok and sc.regulatory_h2_CI<=4. and sc.us_construction_before2028
                    and 0<=2030-sc.us_hydrogen_service_year<10)
    if sc.policy=='regional' or sc.force_fuel_compliance:
        if region=='ARA':
            tau=eur2026(81.8171122295575)
            # Separate allowance expenditure from public subsidy outlay.
            baseline_tax=tau*cohort/1e6+tau*.5*3.1631*base_hfo/1e6
            vecs['tax_increment']-=tau/1000*vecs['stored']
            for source in sources:
                name=source['source']['name']
                for route in ['fuel','fuel_qualified']:
                    j=index[f'{name}::{route}'];m=vecs['methanol'][j]
                    hfo=m*19.9*etaM/(40.5*etaH)
                    combustion=(sc.methanol_fuel_nonCO2+(0. if route=='fuel_qualified' else 1.375))*m
                    vecs['tax_increment'][j]+=tau*.5*(combustion-3.1631*hfo)/1000
            # Strict FuelEU2030 annual domain. Qualified20g/MJ is a declared
            # regulatory accounting condition, independent of physical LCA.
            target=85.6904;Ih=3.70985/40.5*1000
            baseline_fueleu=(Ih-target)*Dshaft/etaH/1e6
            row=np.zeros(n)
            for source in sources:
                name=source['source']['name']
                for route in ['fuel','fuel_qualified']:
                    j=index[f'{name}::{route}'];m=vecs['methanol'][j]
                    regCI=20. if route=='fuel_qualified' else 100.4
                    reward=2. if route=='fuel_qualified' else 1.
                    row[j]=((regCI-target*reward)-(Ih-target)*etaM/etaH)*m*19.9/1000
            add(row,-baseline_fueleu,'FuelEU2030_strict_no_pooling','ktCO2e_regulatory/year')
        elif region=='UK':
            tau=eur2026(62.72358018719762)
            baseline_tax=tau*cohort/1e6
            vecs['tax_increment']-=tau/1000*vecs['stored']
        elif region=='US':
            if claim_45q:
                add(-vecs['raw_captured'],-12.5,'45Q_industrial_minimum_capture','ktCO2/year')
                rate=money(17.*(5 if sc.us_pwa else 1),'USD','2026-09')
                v=rate/1000*vecs['stored']*sc.credit_realization
                vecs['fiscal']+=v;vecs['received']+=v
            if qualified_flag and not(claim_45q and sc.us_same_h2_facility_45q):
                ci=sc.regulatory_h2_CI
                base_rate=.656 if ci<.45 else .219 if ci<1.5 else .164 if ci<2.5 else .131
                rate=money(base_rate*(5 if sc.us_pwa else 1)*1000,'USD','2026-09')
                nominal=rate/1000*sc.credit_realization
                vecs['fiscal'][q]+=nominal
                vecs['received'][q]+=nominal*sc.hydrogen_credit_passthrough
                vecs['supplier_retained'][q]+=nominal*(1-sc.hydrogen_credit_passthrough)
    if sc.sde_base_rate is not None and region=='ARA':
        if sc.policy!='regional':raise ValueError('SDE mechanism expects regionalETS control')
        payment=max(0.,sc.sde_base_rate-eur2026(81.8171122295575))
        v=payment/1000*vecs['stored']*sc.credit_realization
        vecs['fiscal']+=v;vecs['received']+=v
    if sc.payment_target!='none':
        if sc.policy!='mechanism':raise ValueError('Matched generic mechanism needs mechanism policy mode')
        v=np.zeros(n)
        if sc.payment_target=='storage':v=vecs['stored'].copy()
        elif sc.payment_target=='capture':v=vecs['raw_captured'].copy()
        elif sc.payment_target=='utilization':v=vecs['methanol']*ALPHA
        elif sc.payment_target=='fuel':v=vecs['fuel']*ALPHA
        elif sc.payment_target=='hydrogen':v[q]=1.
        else:raise ValueError(sc.payment_target)
        v*=sc.payment_rate/1000*sc.credit_realization
        vecs['fiscal']+=v
        share=sc.hydrogen_credit_passthrough if sc.payment_target=='hydrogen' else 1.
        vecs['received']+=v*share;vecs['supplier_retained']+=v*(1-share)
    if sc.fiscal_budget_per_source_t is not None:
        add(vecs['fiscal'],sc.fiscal_budget_per_source_t*cohort/1e6,'public_fiscal_budget','MUSD/year')
    if sc.uk_supported_rate is not None:
        if region!='UK' or sc.uk_generation_CO2_t is None:raise ValueError('UKdesign requires separately declared generationCO2 denominator')
        add(-vecs['stored'],-sc.uk_supported_rate*sc.uk_generation_CO2_t/1000,'UK_supported_storage_export_design','ktCO2/year')
    vecs['private_increment']=vecs['gross_increment']+vecs['tax_increment']-vecs['received']
    p=dict(currency='USD',price_basis='2026-09',region=region,scenario=asdict(sc),names=names,index=index,vectors=vecs,bounds=bounds,
           A=np.asarray(A),b=np.asarray(b),constraint_names=cn,constraint_units=units,
           baseline_GHG_kt=base_G,baseline_resource_MUSD=base_C,baseline_tax_MUSD=baseline_tax,
           baseline_HFO_t=base_hfo,chemical_service_t=Dm,shaft_service_GJ=Dshaft,
           fixed_source_t=cohort,source_masks=source_masks,source_modules=sources,methanol_module=meoh,
           electricity_price=price,electricity_GHG=ef,nominal_H2_t=h2_nom,claim_45q=claim_45q,
           eligibility=dict(regulatory_H2_assumed_qualified=qualified_flag,actual_project_qualification=None,
                            DPA_actual_rate=None,DPA_actual_payment=None,SDE_actual_payment=None,
                            CB_scope='New-route reference, actual project dispatch and full welfare not inferred'))
    return p

def solve(p,objective='private',budget_MUSD=None,extra_equalities=None,storage_only=False):
    v=p['vectors']
    c={'private':v['private_increment'],'ghg':v['ghg_increment'],'resource':v['gross_increment']}[objective]
    A=p['A'].copy();b=p['b'].copy();names=list(p['constraint_names'])
    if budget_MUSD is not None:
        A=np.vstack([A,v['gross_increment']]);b=np.append(b,budget_MUSD-p['baseline_resource_MUSD']);names.append('resource_budget')
    bounds=list(p['bounds'])
    if storage_only:
        for i,name in enumerate(p['names']):
            if not name.endswith('::storage'):bounds[i]=(0.,0.)
    Aeq=beq=None
    if extra_equalities:
        Aeq=np.asarray([r for r,b in extra_equalities]);beq=np.asarray([b for r,b in extra_equalities])
    r=linprog(c,A_ub=A,b_ub=b,A_eq=Aeq,b_eq=beq,bounds=bounds,method='highs',
              options={'primal_feasibility_tolerance':1e-8,'dual_feasibility_tolerance':1e-8})
    if not r.success:return dict(feasible=False,status=int(r.status),message=r.message)
    # Genuine lexicographic refinement, no arbitrary small weighted objective.
    # The first objective and duals remain available for interpretable slopes.
    optimum=float(c@r.x)
    if objective!='resource':
        rhs=optimum+1e-8*max(1.,abs(optimum))
        r2=linprog(v['gross_increment'],A_ub=np.vstack([A,c]),b_ub=np.append(b,rhs),A_eq=Aeq,b_eq=beq,bounds=bounds,method='highs',
                   options={'primal_feasibility_tolerance':1e-8,'dual_feasibility_tolerance':1e-8})
        if r2.success:x=r2.x
        else:x=r.x
    else:x=r.x
    residual=max(0.,float(np.max(A@x-b)),float(np.max(-x)))
    if Aeq is not None:residual=max(residual,float(np.max(np.abs(Aeq@x-beq))))
    if residual>1e-4:raise ArithmeticError('LP residual '+str(residual))
    return dict(feasible=True,x=x,objective=float(c@x),primary_objective=optimum,
                primal_residual_scaled=residual,constraint_names=names,
                slacks=b-A@x,duals=np.array(r.ineqlin.marginals),
                primary_objective_kind=objective,claim_45q=p['claim_45q'])

def metrics(p,r):
    if not r['feasible']:return {k:v for k,v in r.items() if k not in ['x']}
    x=r['x'];v=p['vectors']
    meoh_t=float(v['methanol']@x)*1000
    chem_t=float(v['chemical']@x)*1000
    fuel_t=float(v['fuel']@x)*1000
    etaM=p['scenario']['methanol_engine_efficiency'];etaH=p['scenario']['hfo_engine_efficiency']
    hfo_t=p['baseline_HFO_t']-fuel_t*19.9*etaM/(40.5*etaH)
    back_meoh_t=p['chemical_service_t']-chem_t
    G=p['baseline_GHG_kt']+float(v['ghg_increment']@x)
    C=p['baseline_resource_MUSD']+float(v['gross_increment']@x)
    tax=p['baseline_tax_MUSD']+float(v['tax_increment']@x)
    fiscal=float(v['fiscal']@x);received=float(v['received']@x);retained=float(v['supplier_retained']@x)
    private=C+tax-received
    captured=float(v['raw_captured']@x)*1000
    stored=float(v['stored']@x)*1000
    qa_vent=0.;product_carbon=0.;byproduct_carbon=0.
    for i,name in enumerate(p['names']):
        if name=='qualified_H2' or name.endswith('::storage'):continue
        m=v['methanol'][i]*x[i]*1000
        retained_carbon=m*ALPHA
        qa_vent+=x[i]*1000-retained_carbon
        product_carbon+=m*1.375
        byproduct_carbon+=m*(ALPHA-1.375)
    uncaptured=p['fixed_source_t']-captured
    carbon_residual=p['fixed_source_t']-(uncaptured+stored+qa_vent+product_carbon+byproduct_carbon)
    ledger_residual=private+fiscal-retained-tax-C
    shaft=fuel_t*19.9*etaM+hfo_t*40.5*etaH
    cert_t=x[p['index']['qualified_H2']]*1000
    rows={name:float(value*1000) for name,value in zip(p['names'],x)}
    return dict(feasible=True,currency='USD',price_basis='2026-09',region=p['region'],methanol_t=meoh_t,fuel_methanol_t=fuel_t,chemical_methanol_t=chem_t,
                captured_raw_CO2_t=captured,stored_CO2_t=stored,unallocated_CO2_t=uncaptured,
                qualification_vent_CO2_t=qa_vent,product_eventual_release_CO2_t=product_carbon,byproduct_eventual_release_CO2_t=byproduct_carbon,
                HFO_backfill_t=hfo_t,conventional_methanol_backfill_t=back_meoh_t,
                electricity_MWh=float(v['power']@x)*1000,hydrogen_t=float(v['hydrogen']@x)*1000,
                qualified_H2_t=cert_t,GHG_tCO2e=G*1000,baseline_GHG_tCO2e=p['baseline_GHG_kt']*1000,
                abatement_tCO2e=(p['baseline_GHG_kt']-G)*1000,
                resource_expense_USD=C*1e6,baseline_resource_USD=p['baseline_resource_MUSD']*1e6,
                private_expense_USD=private*1e6,allowance_expense_USD=tax*1e6,
                public_fiscal_USD=fiscal*1e6,private_received_support_USD=received*1e6,supplier_retained_support_USD=retained*1e6,
                carbon_balance_residual_t=carbon_residual,finance_ledger_residual_USD=ledger_residual*1e6,
                shaft_service_residual_GJ=shaft-p['shaft_service_GJ'],chemical_service_residual_t=chem_t+back_meoh_t-p['chemical_service_t'],
                solver_primal_residual=r['primal_residual_scaled'],claim_45q=r['claim_45q'],flows=rows,
                active_constraints=[n for n,s in zip(r['constraint_names'],r['slacks']) if abs(s)<1e-5],
                duals={name:float(value) for name,value in zip(r['constraint_names'],r['duals'])},
                evaluation='conditional prospective simulation, not measured project outcome')

def evaluate(region,sc=Scenario(),objective='private',budget_MUSD=None,extra_equalities=None,storage_only=False):
    q45_live=sc.us_capture_construction_before2033 and 0<=2030-sc.us_capture_service_year<12
    regimes=[False,True] if region=='US' and sc.policy=='regional' and q45_live else [False]
    candidates=[];failures=[]
    for claim in regimes:
        p=build(region,sc,claim)
        r=solve(p,objective,budget_MUSD,extra_equalities,storage_only)
        if r['feasible']:candidates.append((r['objective'],p,r))
        else:failures.append(r)
    if not candidates:return None,dict(feasible=False,region=region,failures=failures)
    _,p,r=min(candidates,key=lambda z:z[0])
    return p,metrics(p,r)

def frontier(region,sc=Scenario(),storage_only=False):
    p=build(region,sc)
    budget=p['baseline_resource_MUSD']+sc.budget_per_source_t*p['fixed_source_t']/1e6
    # Main frontiers always use the common policy-neutral physical domain.
    if sc.policy!='neutral':raise ValueError('Common frontier requires neutral policy domain')
    _,m=evaluate(region,sc,'ghg',budget,storage_only=storage_only)
    if m['feasible']:
        m.update(resource_budget_USD=budget*1e6,budget_slack_USD=budget*1e6-m['resource_expense_USD'],budget_per_source_t=sc.budget_per_source_t)
    return m

def decompose(region,sc=Scenario(policy='regional')):
    p,anchor=evaluate(region,sc)
    if not anchor['feasible']:return dict(anchor=anchor,comparators={})
    x=np.array([anchor['flows'][n]/1000 for n in p['names']])
    budget=anchor['resource_expense_USD']/1e6
    eqM=[(mask,float(mask@x)) for mask in p['source_masks'].values()]
    eqT=[(p['vectors']['raw_captured'],float(p['vectors']['raw_captured']@x))]
    comps={}
    for name,eq in [('M',eqM),('T',eqT),('U',None)]:
        _,m=evaluate(region,sc,'ghg',budget,extra_equalities=eq)
        if not m['feasible']:raise ArithmeticError('Private anchor lost in nested domain')
        comps[name]=m
    gs=[anchor['GHG_tCO2e']]+[comps[n]['GHG_tCO2e'] for n in ['M','T','U']]
    if any(gs[i+1]>gs[i]+.1 for i in range(3)):raise ArithmeticError('Nested-domain monotonicity')
    return dict(anchor=anchor,comparators=comps,decomposition=dict(destination=gs[0]-gs[1],source=gs[1]-gs[2],scale=gs[2]-gs[3],total=gs[0]-gs[3]),
                interpretation='T is structurally unidentifiable with one aggregate source. Nested domains and private-derived budget can produce exact zeros.')
