"""Offline geometry/slicing review. Machine-specific G-code stays in temporary storage."""
from pathlib import Path
import json,subprocess,tempfile,hashlib,re,concurrent.futures,argparse
args=argparse.ArgumentParser();args.add_argument('--variant',choices=['classic','arachne'],default='classic');args.add_argument('--model',action='append');args.add_argument('--public-3mf',action='store_true');options=args.parse_args()
R=Path(__file__).resolve().parents[1]
SLICER=Path('/Applications/BambuStudio.app/Contents/MacOS/BambuStudio')
CONFIG=R/'parameters/fdm-reference'
TMP=Path(tempfile.mkdtemp(prefix='nano-fdm-review-'))
suffix=('-public-3mf' if options.public_3mf else '')+('' if options.variant=='classic' else '-arachne')
LOGS=R/'reports'/('slicing-logs'+suffix);LOGS.mkdir(parents=True,exist_ok=True)
def sha(path):
 h=hashlib.sha256()
 with path.open('rb') as stream:
  for block in iter(lambda:stream.read(1048576),b''):h.update(block)
 return h.hexdigest()
inputs=[R/'exports'/f'{side}-{part}-development.stl' for side in ['left','right'] for part in ['closed','bottom']]
inputs += [R/'exports/trials'/f'{name}.stl' for name in ['right-ball-thumb-fit','right-holder-usb-fit']]
if options.public_3mf:inputs=sorted((R.parent/'files/3x5').glob('*.3mf'))+sorted((R.parent/'files/trials').glob('*.3mf'))
if options.model:inputs=[p for p in inputs if p.stem in options.model]
assert inputs
def run(path):
 name=path.stem;folder=TMP/name;folder.mkdir();(folder/'output').mkdir()
 process=json.loads((CONFIG/'process.json').read_text());process['wall_generator']=options.variant
 if '-bottom-' in name:process['enable_support']='0'
 (folder/'process.json').write_text(json.dumps(process,indent=2))
 command=[str(SLICER),'--datadir',str(folder/'user'),'--debug','2','--load-settings',str(CONFIG/'machine.json')+';'+str(folder/'process.json'),'--load-filaments',str(CONFIG/'filament.json'),'--orient','0','--arrange','1','--slice','0','--outputdir',str(folder/'output'),str(path)]
 log=LOGS/(name+'.log')
 with log.open('w') as stream:result=subprocess.run(command,stdout=stream,stderr=subprocess.STDOUT,cwd=R,timeout=240)
 gcode=folder/'output/plate_1.gcode';header='';tail=''
 if gcode.exists():
  with gcode.open() as stream:header=''.join(stream.readline() for _ in range(15))
  with gcode.open('rb') as stream:stream.seek(max(0,gcode.stat().st_size-4096));tail=stream.read().decode(errors='replace')
 row={'model':str(path.relative_to(R.parent)),'model_sha256':sha(path),'exit_code':result.returncode,'gcode_complete_marker':'; EXECUTABLE_BLOCK_END' in tail,'reference_profile':'Bambu A1 0.4 / Generic PLA / 0.20 mm, 3 perimeters, 15% infill; NOT the users confirmed printer','wall_generator':options.variant,'support_enabled':process['enable_support']=='1','log':str(log.relative_to(R)),'temporary_gcode':str(gcode),'command':command}
 for key,pattern in [('estimated_model_time',r'model printing time: ([^;\n]+)'),('estimated_weight_g',r'total filament weight \[g\] : ([0-9.]+)'),('layers',r'total layer number: (\d+)')]:
  match=re.search(pattern,header);row[key]=match[1] if match else None
 row['warnings']=[s for s in log.read_text().splitlines() if '[warning]' in s or '[error]' in s]
 print(name,result.returncode,row.get('estimated_model_time'),row.get('estimated_weight_g'),flush=True)
 return row
with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:rows=list(pool.map(run,inputs))
report={'status':'passed' if all(x['exit_code']==0 and x['gcode_complete_marker'] for x in rows) else 'failed','scope':'Slicer toolpath generation with a reference profile. Not a physical fit test or a printer-specific production job. No 3MF thumbnail export: macOS GUI registration previously aborted headless runs.','config_sha256':{name:sha(CONFIG/(name+'.json')) for name in ['machine','process','filament']},'results':rows}
(R/'reports'/('fdm-slicing'+suffix+'.json')).write_text(json.dumps(report,indent=2))
assert report['status']=='passed'
