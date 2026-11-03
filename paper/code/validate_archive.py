"""Validate the frozen source-data attachment with the Python standard library."""
from pathlib import Path
from collections import Counter
import argparse,csv,hashlib,json,math

ROOT=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--report',type=Path,default=ROOT/'reproduced/archive_validation.json')
args=parser.parse_args()
manifest=json.loads((ROOT/'MANIFEST.json').read_text())
errors=[];csv_counts={};json_counts={};checked=0
def strict_constant(value):raise ValueError('Non-standard JSON constant: '+value)
for record in manifest['files']:
    p=ROOT/record['path'];checked+=1
    if not p.is_file():errors.append('Missing file: '+record['path']);continue
    if hashlib.sha256(p.read_bytes()).hexdigest()!=record['sha256']:errors.append('Checksum mismatch: '+record['path'])
    try:
        if p.suffix=='.csv':
            with p.open(encoding='utf-8-sig',newline='') as h:
                reader=csv.reader(h);header=next(reader);n=0
                if len(header)!=len(set(header)):errors.append('Duplicate CSV field: '+record['path'])
                for n,row in enumerate(reader,1):
                    if len(row)!=len(header):errors.append(f'Non-rectangular CSV: {record["path"]}, row {n+1}')
                csv_counts[record['path']]=n
        elif p.suffix=='.json':
            with p.open(encoding='utf-8-sig') as h:value=json.load(h,parse_constant=strict_constant)
            json_counts[record['path']]=len(value) if isinstance(value,(list,dict)) else None
    except Exception as exc:errors.append(record['path']+': '+str(exc))

def readcsv(rel):
    with (ROOT/rel).open(encoding='utf-8-sig',newline='') as h:return list(csv.DictReader(h))
for row in readcsv('DISPLAY_DATA_MAP.csv'):
    if not (ROOT/row['file']).is_file():errors.append('Missing display link: '+row['display']+' -> '+row['file'])
assert_counts={
 'data/evidence/SOURCE_INPUT_LEDGER_USD.csv':209,
 'data/controls/CENTRAL_LITERATURE_CONTROLS.csv':24,
 'data/controls/NORMALISED_ELECTRICITY.csv':36,
 'data/controls/JOINT_INVENTORY_ELECTRICITY_COST.csv':720,
 'data/controls/HYDROGEN_ACCESS.csv':36,
 'data/controls/INVENTORY_EXTENSION.csv':28,
 'data/controls/ENTRY_CALIBRATED_SUPPORT.csv':12,
 'data/supplement/Figures_S1_S2/JOINT_BUDGET_POWER_PRICE.csv':3224,
 'data/main/Figure2/PANEL_C_COMPLETE_INVENTORY_RESPONSE.csv':432,
}
for f,n in assert_counts.items():
    if csv_counts.get(f)!=n:errors.append(f'Count mismatch {f}: {csv_counts.get(f)} != {n}')
for f,n in [('data/controls/FULL_CONTROL_SOLUTIONS.json',1700),('data/controls/CONTROL_LP_MATRICES.json',1700)]:
    if json_counts.get(f)!=n:errors.append(f'Count mismatch {f}')
summary=json.loads((ROOT/'data/controls/SUMMARY.json').read_text())
for file,sha in summary['frozen_model_hashes'].items():
    if hashlib.sha256((ROOT/file).read_bytes()).hexdigest()!=sha:errors.append('Frozen numerical kernel changed: '+file)
ledger=readcsv('data/evidence/SOURCE_INPUT_LEDGER_USD.csv')
if len({r['id'] for r in ledger})!=209:errors.append('Evidence IDs are not unique')
equations=readcsv('metadata/EQUATIONS.csv')
main={r['equation'] for r in equations if r['document']=='main'}
supp={r['equation'] for r in equations if r['document']=='SI'}
if main!={'1','2','3'} or supp!={f'S{i}' for i in range(1,37)}:errors.append('Equation coverage mismatch')
grid=readcsv('data/supplement/Figures_S1_S2/JOINT_BUDGET_POWER_PRICE.csv')
counts=Counter((r['inventory'],r['power_GWh']) for r in grid)
if len(counts)!=8 or any(n!=403 for n in counts.values()):errors.append('Resource-map dimensions mismatch')
report=dict(status='PASS' if not errors else 'FAIL',files_hash_checked=checked,
    csv_files=len(csv_counts),json_files=len(json_counts),evidence_rows=len(ledger),
    control_solutions=json_counts.get('data/controls/FULL_CONTROL_SOLUTIONS.json'),
    control_matrices=json_counts.get('data/controls/CONTROL_LP_MATRICES.json'),
    main_equations=sorted(main),supplementary_equations=len(supp),
    errors=errors,scope='Frozen payload checksums, CSV and JSON integrity, display links, evidence/control dimensions and frozen model hashes. Scientific result regeneration is reported separately.')
args.report.parent.mkdir(parents=True,exist_ok=True)
args.report.write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
raise SystemExit(0 if not errors else 1)
