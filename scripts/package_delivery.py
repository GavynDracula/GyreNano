"""Package reviewed STL files and instructions; verify contents and preserve source hashes."""
from pathlib import Path
import hashlib,json,zipfile,importlib.metadata,sys,platform
R=Path(__file__).resolve().parents[1]
def sha(f):
 h=hashlib.sha256()
 with f.open('rb') as stream:
  for chunk in iter(lambda:stream.read(1048576),b''):h.update(chunk)
 return h.hexdigest()
archive=json.loads((R/'archive/before-print-preparation-manifest.json').read_text())['files']
masters=[f'exports/{side}-{part}-development.stl' for side in ['left','right'] for part in ['closed','bottom']]
masters += ['exports/right-closed-v11.stl','exports/left-bottom-development.step','exports/right-bottom-development.step']
for name in masters:assert sha(R/name)==archive[name]['sha256'],name
assert json.loads((R/'reports/current-checks.json').read_text())['all_passed']
assert json.loads((R/'reports/fdm-slicing.json').read_text())['status']=='passed'
assert json.loads((R/'reports/fdm-slicing-arachne.json').read_text())['status']=='passed'
env={'python':sys.version,'executable':sys.executable,'platform':platform.platform(),'packages':{n:importlib.metadata.version(n) for n in ['numpy','scipy','trimesh','manifold3d','rtree','matplotlib','Pillow']},'mesh_support':str(Path.home()/'Library/Application Support/Codex/Tools/Keyboard/mesh-python'),'slicer':'Bambu Studio 02.09.01.70'}
(R/'reports/runtime-environment.json').write_text(json.dumps(env,indent=2))
files=[f for f in (R/'exports/print').iterdir() if f.is_file()]+[R/'exports/trials/right-ball-thumb-fit.stl',R/'exports/trials/right-holder-usb-fit.stl',R/'docs/FDM-PRINTING.md',R/'previews/fdm-trials.png']
entries={str(f.relative_to(R)):{'bytes':f.stat().st_size,'sha256':sha(f)} for f in files}
readme='''# Gyre Nano — 洄流 V11 FDM trial pack\n\nStart with docs/FDM-PRINTING.md.\n\n- exports/trials: validated holder/USB and ball/thumb trials.\n- exports/print: four unchanged complete enclosure STL parts.\n- previews/fdm-trials.png: actual trial geometry; orange marks crop faces.\n\nUnits: mm. Scale: 100%. Bottoms have their own print datum.\nThe pack passed geometry and reference-profile slicing checks, but has not been physically printed or fitted.\nDo not infer the complete adapter installation motion from the cropped trial.\nNo machine-specific G-code is included.\nMechanical derived design: BastardKB and original authors, CC BY-NC-SA 4.0.\n'''
package=R/'exports/gyre-nano-v11-fdm-trial-pack.zip'
with zipfile.ZipFile(package,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
 for f in files:z.write(f,str(f.relative_to(R)))
 z.writestr('README.md',readme)
 z.writestr('SHA256.json',json.dumps(entries,indent=2))
with zipfile.ZipFile(package) as z:
 for name,meta in entries.items():
  h=hashlib.sha256()
  with z.open(name) as stream:
   for chunk in iter(lambda:stream.read(1048576),b''):h.update(chunk)
  assert h.hexdigest()==meta['sha256'],name
print('PACK VERIFIED',package.stat().st_size,'bytes; engineering master hashes unchanged.',flush=True)
# Relocated current paths; the old V11 hash file remains a historical record.
current=[]
for sub in ['src','checks','scripts','parameters','docs','previews','exports','reports']:
 current.extend(f for f in (R/sub).rglob('*') if f.is_file() and '__pycache__' not in f.parts and f.name not in ['current-artifacts.json','.DS_Store'])
current += [R/'README.md',R/'PROGRESS.md',R/'assembly.scad']
manifest={'units':'mm','engineering_masters_unchanged_from_archive':masters,'delivery_archive':str(package.relative_to(R)),'files':{str(f.relative_to(R)):{'bytes':f.stat().st_size,'sha256':sha(f)} for f in sorted(set(current))}}
(R/'reports/current-artifacts.json').write_text(json.dumps(manifest,indent=2))
