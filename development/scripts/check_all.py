"""Re-run current engineering checks; keep verbose evidence in reports/check-logs."""
from pathlib import Path
import concurrent.futures,json,subprocess,sys,time
R=Path(__file__).resolve().parents[1];logs=R/'reports/check-logs';logs.mkdir(parents=True,exist_ok=True)
names=['verify_keys.py','verify_assembly.py','verify_hardware_v7.py','verify_roof.py','verify_lower_connectivity_v7.py','verify_inner_window_v11.py','verify_junction_v11.py','verify_ball_rim_v11.py','verify_trackball_v11.py','verify_ball34_v11.py','verify_partition_v11.py']
def check(name):
 start=time.monotonic();log=logs/(name+'.log')
 with log.open('w') as stream:result=subprocess.run([sys.executable,str(R/'checks'/name)],cwd=R,stdout=stream,stderr=subprocess.STDOUT,timeout=240)
 row={'check':name,'exit_code':result.returncode,'seconds':round(time.monotonic()-start,2),'log':str(log.relative_to(R))}
 print(name,result.returncode,flush=True);return row
with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:results=list(pool.map(check,names))
(R/'reports/current-checks.json').write_text(json.dumps({'checks':results,'all_passed':all(r['exit_code']==0 for r in results)},indent=2))
assert all(r['exit_code']==0 for r in results)
