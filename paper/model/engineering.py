"""V4.4 native-USD engineering modules, preserving the source-period raw currencies.

These are declared prospective process/utility packages. They do not reconstruct
the four sites' operating accounts, impurity-removal designs or signed supplies.
"""
from __future__ import annotations
from dataclasses import dataclass, asdict
from functools import lru_cache
from pathlib import Path
import json
import math
import numpy as np
import CoolProp
import CoolProp.CoolProp as CP
from scipy.optimize import brentq

HERE=Path(__file__).resolve().parent
ALPHA=1.4
BETA=.1917
MCO2=.0440098
MN2=.02801348
MONEY=json.loads((HERE/'MONEY_LOOKUP.json').read_text())
USD_PER_EUR=MONEY['USD_per_EUR_target']

def eur2026(value):
    """Convert an already harmonized EUR2026-09 assumption to USD2026-09."""
    return value*USD_PER_EUR

def money(value,currency='EUR',period='2020'):
    return value/MONEY['fx'][currency+'@'+period]*MONEY['target_HICP']/MONEY['indices'][period]*USD_PER_EUR

def crf(r,n):
    return r*(1+r)**n/((1+r)**n-1) if r else 1/n

@dataclass(frozen=True)
class Engineering:
    real_discount:float=.08
    reference_hours:float=8000.
    intercooler_K:float=313.15
    eta_isentropic:float=.80
    eta_motor:float=.95
    stage_max_ratio:float=2.
    interstage_pressure_loss:float=.01
    chiller_evaporating_K:float=273.15
    chiller_condensing_K:float=313.15
    chiller_eta_isentropic:float=.75
    installation_factor:float=3.
    equipment_cost_multiplier:float=1.
    synthesis_cost_multiplier:float=1.
    electrolyser_cost_multiplier:float=1.
    osbl_fraction:float=.10
    water_USD2026_per_m3:float=eur2026(2.)
    grid_connection_USD2026_per_kW:float=eur2026(100.)
    h2_kWh_kg:float=54.5
    hydrogen_package:str='complete80bar'
    capture_heat_mode:str='electric'
    capture_cost_multiplier:float=1.
    capture_heat_multiplier:float=1.
    UK_additional_CO2_fan_fraction:float=0.
    boiler_nonpower_vom_fraction:float=0.
    dryer_electricity_MWh_tCO2:float=.004
    storage_nonenergy_GHG_tCO2e_t:float=.007
    utilization_nonenergy_GHG_tCO2e_t:float=.002
    capture_retained_fraction:float=.55
    storage_cost_multiplier:float=1.
    collection_tariff_multiplier:float=1.
    purity_recovery_high:float=.96
    qualification_cost_USD2026_per_t:float=eur2026(10.)
    qualification_energy_MWh_per_t:float=.02
    preserve_native_pressure:bool=True
    cn_low_inlet_Pa:float=28200.
    cn_full_pilot_cost:bool=False
    cn_pilot_life:float=25.
    cn_pilot_capex_multiplier:float=1.
    h2_local_epc:bool=False

def _props_state(y):
    if y>=.999999:
        return CP.AbstractState('HEOS','CarbonDioxide')
    state=CP.AbstractState('HEOS','CarbonDioxide&Nitrogen')
    state.set_mole_fractions([y,1-y])
    return state

def compression(pin,pout,tin,y,opt=Engineering()):
    physical=Engineering(intercooler_K=opt.intercooler_K,eta_isentropic=opt.eta_isentropic,
                         eta_motor=opt.eta_motor,stage_max_ratio=opt.stage_max_ratio,
                         interstage_pressure_loss=opt.interstage_pressure_loss)
    return _compression(pin,pout,tin,y,physical)

@lru_cache(maxsize=1024)
def _compression(pin,pout,tin,y,opt):
    """Staged real-fluid compression. N2 is an explicit impurity surrogate.

    Enthalpy and entropy are EOS functions. PT roots avoid assuming an available
    mixture PS-flash routine. Pure/binary mixture estimates are not site designs.
    Cooling power is split into process heat rejection and electric fan demand.
    """
    if not 0<y<=1:raise ValueError('Invalid CO2 molar fraction')
    state=_props_state(y)
    mass_ratio=(y*MCO2+(1-y)*MN2)/(y*MCO2)
    def hs(p,t):
        state.update(CP.PT_INPUTS,float(p),float(t))
        return state.hmass(),state.smass(),int(state.phase())
    t0=min(tin,opt.intercooler_K)
    h_native=hs(pin,tin)[0]
    h_pre=hs(pin,t0)[0]
    q_pre=max(0.,h_native-h_pre)*mass_ratio/3.6e6
    stages=[]
    if pout>pin*(1+1e-10):
        # Each compressor also replaces its downstream cooler pressure loss.
        n=math.ceil(math.log(pout/pin)/math.log(opt.stage_max_ratio*(1-opt.interstage_pressure_loss)))
        p=pin
        for j in range(n):
            p_after=pin*(pout/pin)**((j+1)/n)
            p_hot=p_after/(1-opt.interstage_pressure_loss)
            t_start=t0 if j==0 else opt.intercooler_K
            h1,s1,phase=hs(p,t_start)
            density_in=state.rhomass()
            def f(t):return hs(p_hot,t)[1]-s1
            lo=t_start
            hi=t_start+700.
            ts=brentq(f,lo,hi,xtol=1e-7)
            h2s=hs(p_hot,ts)[0]
            if h2s<h1-1e-5:raise ArithmeticError('Negative isentropic work')
            eta=.75 if phase in (int(CP.iphase_liquid),int(CP.iphase_supercritical_liquid)) else opt.eta_isentropic
            dh=(h2s-h1)/eta
            h2=h1+dh
            thot=brentq(lambda t:hs(p_hot,t)[0]-h2,lo,hi,xtol=1e-7)
            hcooled=hs(p_after,opt.intercooler_K)[0]
            work_shaft=dh*mass_ratio/3.6e6
            q_cool=max(0.,h2-hcooled)*mass_ratio/3.6e6
            stages.append(dict(stage=j+1,p_in_Pa=p,p_hot_Pa=p_hot,p_after_cooler_Pa=p_after,
                               T_in_K=t_start,T_isentropic_K=ts,T_hot_K=thot,
                               shaft_MWh_tCO2=work_shaft,electric_MWh_tCO2=work_shaft/opt.eta_motor,
                               inlet_density_kg_m3=density_in,
                               rejected_heat_MWhth_tCO2=q_cool,inlet_phase=phase,
                               device='pump' if phase in (int(CP.iphase_liquid),int(CP.iphase_supercritical_liquid)) else 'compressor'))
            p=p_after
        terminal_T=opt.intercooler_K
    else:
        # Pressure reduction has no expander credit. Energy conservation across
        # throttling is retained; the delivered temperature is subsequently set.
        p=pout
        h_before=h_pre
        terminal_T=brentq(lambda t:hs(pout,t)[0]-h_before,220.,tin+300.,xtol=1e-7) if pout<pin*(1-1e-9) else t0
    e=sum(s['electric_MWh_tCO2'] for s in stages)
    q=q_pre+sum(s['rejected_heat_MWhth_tCO2'] for s in stages)
    return dict(pin_Pa=pin,pout_Pa=pout,y_CO2=y,mass_mixture_per_mass_CO2=mass_ratio,
                shaft_MWh_tCO2=sum(s['shaft_MWh_tCO2'] for s in stages),electric_MWh_tCO2=e,
                cooling_heat_MWhth_tCO2=q,pre_cooling_MWhth_tCO2=q_pre,terminal_T_K=terminal_T,stages=stages,
                electricity_fans_MWh_tCO2=.009*q,
                surrogate='pureCO2' if y>=.999999 else 'drybinaryCO2_N2; other dry noncondensables represented byN2')

def refrigeration(opt=Engineering()):
    physical=Engineering(chiller_evaporating_K=opt.chiller_evaporating_K,
                         chiller_condensing_K=opt.chiller_condensing_K,
                         chiller_eta_isentropic=opt.chiller_eta_isentropic,eta_motor=opt.eta_motor)
    return _refrigeration(physical)

@lru_cache(maxsize=128)
def _refrigeration(opt):
    """R717 utility cycle: 5K superheat/subcool, 0C evaporation, 40C condensation."""
    fluid='Ammonia'
    pe=CP.PropsSI('P','T',opt.chiller_evaporating_K,'Q',1,fluid)
    pc=CP.PropsSI('P','T',opt.chiller_condensing_K,'Q',0,fluid)
    h1=CP.PropsSI('H','P',pe,'T',opt.chiller_evaporating_K+5,fluid)
    s1=CP.PropsSI('S','P',pe,'T',opt.chiller_evaporating_K+5,fluid)
    h2s=CP.PropsSI('H','P',pc,'S',s1,fluid)
    h2=h1+(h2s-h1)/opt.chiller_eta_isentropic
    h3=CP.PropsSI('H','P',pc,'T',opt.chiller_condensing_K-5,fluid)
    q=h1-h3
    w=h2-h1
    assert q>0 and w>0
    return dict(refrigerant='R717',P_evap_Pa=pe,P_cond_Pa=pc,
                q_evap_J_kg=q,w_shaft_J_kg=w,w_electric_J_kg=w/opt.eta_motor,
                COP_electric=q/(w/opt.eta_motor),q_cond_per_q_evap=(h2-h3)/q,
                eta_isentropic=opt.chiller_eta_isentropic,eta_motor=opt.eta_motor,
                superheat_K=5,subcool_K=5,
                status='declared utility cycle, not measured four-site refrigeration performance')

CORRELATIONS={
    'pump':(15430.,60.,.6,9.,1800.),
    'centrifugal':(1261682.,1000.,.9,2.,4000.),
    'reciprocating':(168224.,100.,.8,1.,10000.),
    'shell_tube':(65421.,100.,.7,20.,2000.),
    'dry_cooler':(65421.,100.,.4,10.,10000.),
}

def equipment_cost(kind,size,opt=Engineering()):
    """Purchased CEPCI1000 -> CEPCI2023=797.9 -> USD2026-09, then installed.

    Installation factor is an author scenario (2–4 sensitivity), not a recovered
    numerical EDF factor from the original paper. Minimum size is costed at the
    smallest published range; parallel units stay within the upper range.
    """
    if size<=1e-12:return dict(capital=0.,units=0,effective_unit_size=0.,floor=False)
    c0,x0,exponent,lower,upper=CORRELATIONS[kind]
    units=math.ceil(size/upper)
    x=max(lower,size/units)
    bare=c0*(x/x0)**exponent*units
    capital=money(bare*.7979,'EUR','2023')*opt.installation_factor*opt.equipment_cost_multiplier
    return dict(capital=capital,units=units,effective_unit_size=x,floor=size/units<lower,
                raw_bare_EUR_CEPCI1000=bare,correlation=kind,range=[lower,upper])

def annual_component(capital,fom,life,denom,opt=Engineering()):
    return (crf(opt.real_discount,life)+fom)*capital/denom

def pressure_capital(profile,flow_tph,opt=Engineering()):
    parts=[]
    for s in profile['stages']:
        size=s['shaft_MWh_tCO2']*flow_tph*1000
        if s['device']=='pump':
            volume=flow_tph*1000*profile['mass_mixture_per_mass_CO2']/s['inlet_density_kg_m3']
            part=equipment_cost('pump',volume,opt)
            part['volume_m3_h']=volume
        else:
            part=equipment_cost('reciprocating' if size<1000 else 'centrifugal',size,opt)
        part.update(stage=s['stage'],shaft_kW=size,device=s['device'])
        parts.append(part)
    return sum(p['capital'] for p in parts),parts

def cooling_capital(heat_MW,opt=Engineering()):
    # Primary correlation U=.5kW/(m2K), declared15K driving difference.
    return equipment_cost('dry_cooler',heat_MW*1000/(.5*15),opt)

def cold_module(q_MWhth_per_t,flow_tph,opt=Engineering()):
    cycle=refrigeration(opt)
    q=max(0.,q_MWhth_per_t)
    if q<1e-12:return dict(electricity=0.,nonpower=0.,capital=0.,heat=0.,cycle=cycle)
    load_MW=q*flow_tph
    shaft_MW=load_MW*cycle['w_shaft_J_kg']/cycle['q_evap_J_kg']
    comp=equipment_cost('reciprocating',shaft_MW*1000,opt)
    # A5K minimum approach throughout is a conservative reference sizing rule.
    evap=equipment_cost('shell_tube',load_MW*1000/(.3*5),opt)
    cond=cooling_capital(load_MW*cycle['q_cond_per_q_evap'],opt)
    cap=comp['capital']+evap['capital']+cond['capital']
    annual=(crf(opt.real_discount,25)*cap+.05*comp['capital']+.03*(evap['capital']+cond['capital']))
    e=q/cycle['COP_electric']+.009*q*cycle['q_cond_per_q_evap']
    return dict(electricity=e,nonpower=annual/(flow_tph*opt.reference_hours),capital=cap,heat=q,
                compressor=comp,evaporator=evap,condenser=cond,cycle=cycle)

def co2_route(pin,tin,y,pout,flow_tph,drying,final_K,opt=Engineering(),fan_extra_fraction=1.):
    profile=compression(pin,pout,tin,y,opt)
    state=_props_state(y)
    def h(t):
        state.update(CP.PT_INPUTS,pout,t)
        return state.hmass()
    q_cold=max(0.,h(profile['terminal_T_K'])-h(final_K))*profile['mass_mixture_per_mass_CO2']/3.6e6 if final_K<profile['terminal_T_K'] else 0.
    cold=cold_module(q_cold,flow_tph,opt)
    cap_comp,comp_parts=pressure_capital(profile,flow_tph,opt)
    cool=cooling_capital(profile['cooling_heat_MWhth_tCO2']*flow_tph,opt)
    # Independent adsorption-drying module from Pedersen2025, 50tCO2/h.
    # Linear modular reference, not a claimed scale economy or Yulin quotation.
    cap_dry=money(1489000.,'EUR','2023')*flow_tph/50 if drying else 0.
    dry_annual_OM=money(77000.,'EUR','2023')*flow_tph/50 if drying else 0.
    e_dry=opt.dryer_electricity_MWh_tCO2 if drying else 0.
    # UK source auxiliary already includes compressor-cooling fans.
    # Shared-fan reference0 and upper addition1 are declared alternatives.
    # New 5C refrigeration fans remain in cold, outside original110bar40C.
    e_profile_fan=fan_extra_fraction*profile['electricity_fans_MWh_tCO2']
    grid_kW=(profile['electric_MWh_tCO2']+cold['electricity']+e_profile_fan+e_dry)*flow_tph*1000
    cap_grid=grid_kW*opt.grid_connection_USD2026_per_kW
    cap=(cap_comp+cool['capital']+cap_dry+cold['capital']+cap_grid)
    annual=(crf(opt.real_discount,25)*(cap_comp+cool['capital']+cap_dry+cap_grid)
            +.05*cap_comp+.03*cool['capital']+dry_annual_OM+.01*cap_grid)
    nonpower=annual/(flow_tph*opt.reference_hours)+cold['nonpower']
    return dict(electricity=profile['electric_MWh_tCO2']+e_profile_fan+e_dry+cold['electricity'],
                nonpower=nonpower,capital=cap,compression=profile,compressor_cost_parts=comp_parts,
                drycooler=cool,dryer_capital=cap_dry,dryer_electricity=e_dry,cold=cold,
                additional_compression_fan_electricity=e_profile_fan,fan_extra_fraction=fan_extra_fraction,
                grid_connection_capital=cap_grid,feed_temperature_K=final_K,
                status='explicit reference sizing, with binary impurity/utility assumptions')

@lru_cache(maxsize=256)
def methanol_module(opt=Engineering()):
    hours=opt.reference_hours
    meoh=100000.
    rate=meoh/8000.  # Fixed reference installed throughput, hours vary utilization.
    denom=rate*hours
    cap_s=money(93e6)*opt.synthesis_cost_multiplier
    fom_s=money(2.7e6)*opt.synthesis_cost_multiplier
    c_s=(crf(opt.real_discount,30)*cap_s+fom_s)/denom
    # Full package includes the catalogue40EUR/kW compressor capital exactly once.
    cap_h_per_kW=money(989.5694620642815,'EUR','2025')*opt.electrolyser_cost_multiplier
    stack=money(147.09490364018396,'EUR','2025')*opt.electrolyser_cost_multiplier
    times=np.arange(73000/hours,25.,73000/hours)
    pv_stack=sum(stack/(1+opt.real_discount)**float(t) for t in times)
    kwh=opt.h2_kWh_kg
    c_h_kg=((cap_h_per_kW+pv_stack)*crf(opt.real_discount,25)+.045*cap_h_per_kW)/(hours/kwh)
    if opt.h2_local_epc:
        K=money(168802319.19,'CNY','2025-09')*opt.electrolyser_cost_multiplier
        # Full EPC/nominal throughput alternative. Stack replacements are not
        # separately priced in the award, so add the same reference replacement
        # charge as an explicit lifecycle extension, rather than silently omit it.
        kg_y=12000*8000*.0899*hours/8000
        Kperkg=K*(crf(opt.real_discount,25)+.04)/kg_y
        stack_perkg=pv_stack*crf(opt.real_discount,25)/(hours/kwh)
        c_h_kg=Kperkg+stack_perkg
    e_h=kwh*1000/1000  # MWh/tH2 has same numerical value as kWh/kg.
    booster=0.
    if opt.hydrogen_package=='30bar_plus_booster':
        booster=(8.314462618*303.15/.00201588/3.6e6/.75*math.log(70/30))/1000
        # Formula above is MWh/kgH2. Report per tonne below.
    elif opt.hydrogen_package!='complete80bar':raise ValueError('Invalid H2 package')
    # H2 source at30C/80bar after complete BoP; both are declared package endpoints.
    hhot=CP.PropsSI('H','P',8e6,'T',303.15,'Hydrogen')
    hcold=CP.PropsSI('H','P',7e6,'T',278.15,'Hydrogen')
    q_h=max(0.,hhot-hcold)*BETA/3.6e6  # tH2/tMeOH *J/kg ->MWh/tMeOH.
    cold=cold_module(q_h,rate,opt)
    e_steam=.58/.99+.58*.005
    cap_steam=money(.1e6,'EUR','2025')*(rate*.58)
    fom_steam=money(1237.,'EUR','2025')*(rate*.58)
    # DEA gross VOM includes auxiliary electricity at an undisclosed tariff.
    # Price physical auxiliary power once. Nonenergy remainder is unidentified:
    # reference0 and bounded0..gross.58, not a fabricated exact subtraction.
    vom_steam=money(.58,'EUR','2025')*.58*opt.boiler_nonpower_vom_fraction
    c_steam=(crf(opt.real_discount,25)*cap_steam+fom_steam)/denom+vom_steam
    # Required process heat rejection from DEA's20% low-grade heat fraction.
    # DEA0.1 includes BOTH pumps and process cooling-system electricity.
    q_process=.20*(BETA*33.333+.1+.58)
    cool=cooling_capital(q_process*rate,opt)
    c_cool=annual_component(cool['capital'],.03,25,denom,opt)
    # Ancillary scope allowance excludes all explicitly sized utilities, so it
    # cannot re-add those capitals. It is an author scenario, not field evidence.
    cap_other=opt.osbl_fraction*cap_s
    c_other=annual_component(cap_other,.02,25,denom,opt)
    water_per_t=BETA*e_h*.18997692307692307  # DEA189.977kg water/MWh ->m3/MWh.
    c_water=water_per_t*opt.water_USD2026_per_m3
    c_waste=.55*money(.2,'EUR','2023')
    process_fan=0. # Already inside DEA0.1, no duplicate process fan addition.
    e_total=BETA*e_h+.1+e_steam+cold['electricity']+BETA*1000*booster
    # Separate site HV/grid connection is excluded from DEA electrolyser CAPEX.
    cap_grid=e_total*rate*1000*opt.grid_connection_USD2026_per_kW
    c_grid=annual_component(cap_grid,.01,25,denom,opt)
    components=dict(synthesis=c_s,electrolysis=BETA*1000*c_h_kg,steam=c_steam,
                    hydrogen_cooling=cold['nonpower'],process_cooling=c_cool,
                    other_OSBL=c_other,water=c_water,wastewater=c_waste,grid_connection=c_grid)
    return dict(alpha=ALPHA,beta=BETA,electricity_MWh_tMeOH=e_total,hydrogen_kWh_kg=kwh,
                process_cooling_fan_MWh_tMeOH=process_fan,
                synthesis_auxiliary_scope='DEA0.1MWh/t includes process pumping andcooling; feedconditioningoutside declaredinlet isseparate',
                boiler_nonenergy_VOM_scope='unknownresidual fraction0..1 ofgross.58EUR2025/MWhheat, withphysicalauxelectricitypricedonce',
                hydrogen_quote_scope_exception='grossVATinclusiveH2EPCanalogy; notmatchednetVATscope' if opt.h2_local_epc else None,
                hydrogen_booster_MWh_tMeOH=BETA*1000*booster,steam_electricity_MWh_tMeOH=e_steam,
                water_m3_tMeOH=water_per_t,nonpower_USD_tMeOH=sum(components.values()),
                nonpower_components=components,hydrogen_nonpower_USD_kg=c_h_kg,hydrogen_cold=cold,
                reference_tph=rate,reference_output_t_y=denom,reference_installed_nameplate_t_y=100000.,
                synthesis_capital_USD2026=cap_s,ancillary_capital_USD2026=cap_other,
                process_cooling_capital=cool,grid_connection_capital=cap_grid,
                fixed_reference_hours=opt.reference_hours,stack_replacement_years=times.tolist(),
                uniform_exclusions=['land','VAT/taxes','owner corporate cost','construction finance','districtheat export','longdistance methanol delivery'],
                uncertainty='OSBL,waterprice,installationfactor and gridconnection are explicit bounded reference assumptions, not observed site quotations')

def separator(region,opt=Engineering()):
    if region not in ['ARA','UK']:
        return dict(electricity=0.,nonpower=0.,capital_specific=0.,heat=0.,
                    status='Native separated process gas decision inlet. Historical upstream separation is held fixed, not asserted free.')
    cap=money(2.3e6)*opt.capture_retained_fraction*opt.capture_cost_multiplier
    c=(crf(opt.real_discount,25)+.03)*cap/opt.reference_hours+money(2.5)*opt.capture_cost_multiplier
    e_aux=.025 if region=='ARA' else 23.5/289
    q=(.72 if region=='ARA' else .75)*opt.capture_heat_multiplier
    heat_e=q/.99+q*.005
    if region=='UK' and opt.capture_heat_mode=='integrated':
        # Fixed gas-generation/output-service alternative: replace lost net
        # output instead of adding electric steam. Rounded106MW reference is
        # separated from the report26.5MW compressor exactly once.
        heat_e=(106-26.5-23.5)/289*opt.capture_heat_multiplier
        c_heat=money(.10e6,'EUR','2025')*q*(crf(opt.real_discount,25)+.01)/opt.reference_hours
    else:
        c_heat=(money(.10e6,'EUR','2025')*q*crf(opt.real_discount,25)+money(1237.,'EUR','2025')*q)/opt.reference_hours+money(.58,'EUR','2025')*q*opt.boiler_nonpower_vom_fraction
    # IEAGHG UK auxiliary already includes additional cooling-tower fans.
    # DEA ARA auxiliary boundary excludes the induced-draft tower allowance.
    e_fan=.009*q if region=='ARA' else 0.
    grid_cost=(e_aux+heat_e+e_fan)*1000*opt.grid_connection_USD2026_per_kW*(crf(opt.real_discount,25)+.01)/opt.reference_hours
    return dict(electricity=e_aux+heat_e+e_fan,nonpower=c+c_heat+grid_cost,
                capital_specific=cap,heat=q,capture_auxiliary=e_aux,heat_electric_equivalent=heat_e,
                cooling_fan=e_fan,status='DEA scope-adjusted generic separator cost; UK matchedIEAGHG energy analogy, not site measurement')

@lru_cache(maxsize=128)
def storage_reference(kind,opt=Engineering()):
    """DEA1Mt onshore cost scope, offshore analogue is an independent option.

    Published capital entries are per total30Mt lifetime capacity, not annual
    tonnes. FOM entries are annual throughput averages. They are treated as
    nominal reference annual costs. Closure/monitoring future sums are discounted.
    """
    if kind=='onshore':
        cap_per_lifetime_t=2.6729514661371327
        pre=.7837977983409637
        decommission=.4562105133933302
        monitoring=1.6077903555712079
        fom=3.396457126144176
        vom=1.4819807602477608
    elif kind=='offshore':
        cap_per_lifetime_t=4.9841501022707435
        pre=.40194758889280197
        decommission=.8159536054523879
        monitoring=2.4116855333568115
        fom=5.808142659500988
        vom=9.035781798310188
    else:raise ValueError(kind)
    K=money((cap_per_lifetime_t+pre)*30e6)
    K+=money((decommission+monitoring)*30e6)/(1+opt.real_discount)**30
    annual=K*crf(opt.real_discount,30)+money(fom+vom)*1e6
    return dict(nonpower=annual/1e6*opt.storage_cost_multiplier,electricity=50/3600,
                lifetime_capacity_t=30e6,annual_reference_t=1e6,life=30.,kind=kind,
                scope='DEA cold-liquid tanker receiving/tanks/heating/localpipeline/injection cost kernel. Reuse at150bar40C is a bounded author service-cost analogy, NOT an exactly compatible inlet package or actualfour-site tariff.',
                PV_capital_USD2026=K)

def region_sources(region,opt=Engineering()):
    if region=='ARA':return [dict(name='portfolio',Q=2500000.,pin=300000.,Tin=313.15,y=.9995,dry=True,separate=True,storageP=15e6,quality=True)]
    if region=='UK':return [dict(name='NGCC',Q=2000000.,pin=160000.,Tin=313.15,y=.9995,dry=True,separate=True,storageP=15e6,quality=True)]
    if region=='US':return [dict(name='ammonia',Q=2000000.,pin=101325.,Tin=313.15,y=.9995,dry=True,separate=False,storageP=15e6,quality=True)]
    if region=='CN':return [
        dict(name='EG_high',Q=100000.,pin=8.201325e6,Tin=373.15,y=.9894,dry=False,separate=False,storageP=27.101325e6,quality=True),
        dict(name='EG_low',Q=300000.,pin=opt.cn_low_inlet_Pa,Tin=290.52,y=.7778/(1-.0173),dry=True,separate=False,storageP=27.101325e6,quality=False)]
    raise ValueError(region)

def source_modules(region,opt=Engineering()):
    sep=separator(region,opt)
    store=storage_reference('onshore',opt)
    rows=[]
    for src in region_sources(region,opt):
        sflow=src['Q']/8000.
        # Common T&S receiving interface is150bar. The receiving service owns
        # any injection booster beyond that interface, so its power/capital is
        # never charged a second time in the external preparation package.
        fan_fraction=opt.UK_additional_CO2_fan_fraction if region=='UK' else 1.
        sr=co2_route(src['pin'],src['Tin'],src['y'],15e6,sflow,src['dry'],opt.intercooler_K,opt,fan_fraction)
        receiving=dict(store)
        if src['storageP']>15e6:
            boost=compression(15e6,src['storageP'],opt.intercooler_K,src['y'],opt)
            receiving['injection_booster_reference']=boost
            receiving['electricity']=max(store['electricity'],boost['electric_MWh_tCO2']+boost['electricity_fans_MWh_tCO2']+.003)
            receiving['scope_condition']='Receiving fee assumed to cover injection booster rating. Power is at least real-fluid boost plus0.003MWh/t nonpressure service. Fee is a scenario, not verified site contract.'
        # Storage service is a declared shared receiving/injection reference.
        # Collection and offshore distance costs are explicit external parameters,
        # not inferred from the receiving-facility catalogue.
        ts=eur2026({'ARA':20.,'UK':25.,'US':15.,'CN':5.}[region])*opt.collection_tariff_multiplier
        s_nonpower=sep['nonpower']+sr['nonpower']+receiving['nonpower']+ts
        if region=='CN' and opt.cn_full_pilot_cost:
            K=money(499e6,'CNY','2026-09')*opt.cn_pilot_capex_multiplier
            # Mutually exclusive all-pilot capital/FOM replaces pressure,drying,
            # localpipeline/injection/reference extras. Actual energy still used.
            s_nonpower=K*(crf(opt.real_discount,opt.cn_pilot_life)+.04)/400000
        storage=dict(electricity=sep['electricity']+sr['electricity']+receiving['electricity'],
                     nonpower=s_nonpower,nonenergy_ghg=opt.storage_nonenergy_GHG_tCO2e_t,modules=dict(separator=sep,pressure=sr,receiving=receiving,collection_tariff=ts),
                     cost_basis='generic_modular' if not(region=='CN' and opt.cn_full_pilot_cost) else 'independent_full_pilot_budget_analogy')
        util=None
        if src['quality']:
            recovery=opt.purity_recovery_high if region=='CN' else .998
            # Qualification is an explicit black-box conditional module. A cost
            # and carbon-recovery allowance does not prove catalyst acceptance.
            # Native pressure retention is a scenario, independently switched off.
            pqual=src['pin'] if opt.preserve_native_pressure else 101325.
            uflow=min(src['Q']*recovery,ALPHA*100000)/8000
            ur=co2_route(pqual,src['Tin'],.999999,10e6,uflow,src['dry'],278.15,opt,fan_fraction)
            qa_e=opt.qualification_energy_MWh_per_t
            qa_c=opt.qualification_cost_USD2026_per_t
            util=dict(recovery=recovery,electricity_per_raw_t=sep['electricity']+qa_e+recovery*ur['electricity'],
                      nonpower_per_raw_t=sep['nonpower']+qa_c+recovery*ur['nonpower'],
                      nonenergy_ghg_per_raw_t=opt.utilization_nonenergy_GHG_tCO2e_t,
                      modules=dict(separator=sep,qualification=dict(energy=qa_e,nonpower=qa_c,recovery=recovery,
                                  scope='conditional delivered quality at declared pressure, feed-spec acceptance assumed, not an engineering purification design'),pressure=ur))
        rows.append(dict(source=src,storage=storage,utilization=util))
    return rows

def runtime():
    return {'CoolProp':CoolProp.__version__,'CoolProp_revision':CoolProp.__gitrevision__,
            'numpy':np.__version__,'EOS':'HEOS SpanWagner pureCO2 and availableCO2/N2binarymodel',
            'mixture_scope':'binary drysurrogate, no assertion of measured mixture composition or injectivity'}
