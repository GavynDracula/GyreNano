"""Global minimum-bending top skin with measured switch planes and clearance bounds.
No local RBF/mask stacking and no post-export vertex smoothing. Units: mm.
"""
from pathlib import Path
import json
import numpy as np
import trimesh
from scipy.sparse import diags,eye,kron
from scipy.sparse.linalg import spsolve
from scipy.spatial import ConvexHull,Delaunay,cKDTree
from scipy.interpolate import RectBivariateSpline
from matplotlib.path import Path as PolygonPath
ROOT=Path(__file__).resolve().parent.parent
SOLVE_GRID=.5
EXPORT_GRID=.3
LAND_RADIUS=9.0
TENSION=.015
PRIOR_WEIGHT=.0005

def poly_distance(points,poly):
 dist=np.full(len(points),np.inf)
 for p,q in zip(poly,np.roll(poly,-1,axis=0)):
  d=q-p;t=np.clip(((points-p)@d)/(d@d),0,1)
  dist=np.minimum(dist,np.linalg.norm(points-p-t[:,None]*d,axis=1))
 dist[PolygonPath(poly).contains_points(points)]=0
 return dist

def plane_height(points,p):
 c=np.array(p['center']);n=np.array(p['normal'])
 return c[2]-((points-c[:2])@n[:2])/n[2]

def build(side):
 outline=np.array(json.load(open(ROOT/'references'/f'{side}-v3-outline.json'))['outer'])
 lo=outline.min(0)-2;hi=outline.max(0)+2
 xs=np.arange(lo[0],hi[0]+SOLVE_GRID,SOLVE_GRID);ys=np.arange(lo[1],hi[1]+SOLVE_GRID,SOLVE_GRID)
 xx,yy=np.meshgrid(xs,ys);points=np.column_stack((xx.ravel(),yy.ravel()));N=len(points)
 nx=len(xs);ny=len(ys)
 dx=diags([-np.ones(nx-1),np.ones(nx-1)],[0,1],shape=(nx-1,nx))/SOLVE_GRID
 dy=diags([-np.ones(ny-1),np.ones(ny-1)],[0,1],shape=(ny-1,ny))/SOLVE_GRID
 dxx=diags([np.ones(nx-2),-2*np.ones(nx-2),np.ones(nx-2)],[0,1,2],shape=(nx-2,nx))/SOLVE_GRID**2
 dyy=diags([np.ones(ny-2),-2*np.ones(ny-2),np.ones(ny-2)],[0,1,2],shape=(ny-2,ny))/SOLVE_GRID**2
 A=kron(eye(ny),dxx.T@dxx)+kron(dyy.T@dyy,eye(nx))+2*kron(dy.T@dy,dx.T@dx)
 A=(A+TENSION*(kron(eye(ny),dx.T@dx)+kron(dy.T@dy,eye(nx)))+PRIOR_WEIGHT*eye(N)).tocsr()
 planes=json.load(open(ROOT/'references'/f'{side}-switch-planes.json'))
 fixed=np.full(N,np.nan);priority=np.full(N,-np.inf);floor=np.full(N,3.);upper=np.full(N,np.inf)
 for i,p in enumerate(planes):
  c=np.array(p['center']);n=np.array(p['normal']);x=np.array(p['x']);y=np.cross(n,x)
  h=plane_height(points,p);uv=(np.column_stack((points,h))-c)@np.column_stack((x,y))
  mask=np.max(abs(uv),axis=1)<=LAND_RADIUS
  if (side=='right' and i==7) or (side=='left' and i==16):
   corner=np.maximum(abs(uv)-6.9,0)
   mask=np.linalg.norm(corner,axis=1)<=2.4
  select=mask&(h>priority);fixed[select]=h[select];priority[select]=h[select]
  # The thumb/ball junction needs lateral as well as vertical socket cover.
  # A vertical-only clearance produces a knife-thin cliff on this steep flank.
  margin=2.4 if side=='right' and i==7 else 0
  extent=9.8+margin
  corners=np.array([c+u*x+v*y+d*n for u in [-extent,extent] for v in [-extent,extent] for d in [-11-margin,-4+margin]])
  eq=ConvexHull(corners).equations;eq=eq[eq[:,2]>1e-7]
  ceil=np.min((-points@eq[:,:2].T-eq[:,3])/eq[:,2],axis=1)+(0 if margin else 2.4)
  poly=corners[ConvexHull(corners[:,:2]).vertices,:2]
  inside=PolygonPath(poly).contains_points(points)
  floor[inside]=np.maximum(floor[inside],ceil[inside])
 if side=='right':
  ball=json.load(open(ROOT/'references/ball-surface.json'));poly=np.array(ball['outline'])[:,:2]
  h=plane_height(points,ball)
  bn=np.array(ball['normal']);bc=np.array(ball['center']);bu=np.array([bn[2],0,-bn[0]]);bv=np.cross(bn,bu)
  radial=np.linalg.norm((np.column_stack((points,h))-bc)@np.column_stack((bu,bv)),axis=1)
  # There is no roof inside the ball opening, so socket constraints there
  # must not create phantom humps. Pin the inner seating rim; let outer tabs blend.
  floor[radial<20.0]=3
  rim_band=poly_distance(points,poly)<3.0
  floor[rim_band]=np.maximum(floor[rim_band],h[rim_band])
  mask=radial<20.0
  # The conservative square socket envelope can overlap the ball's projected
  # outline. Do not impose contradictory elevations at those grid points.
  mask&=(floor<=h)&(~np.isfinite(fixed))
  fixed[mask]=h[mask]
  # Prevent the fair sheet from overshooting the real ball rim and making
  # a raised crest. Socket cover remains a lower bound, not a tall ridge.
  local=poly_distance(points,poly)<6.0
  cap=h+.35
  for kp in planes:
   kh=plane_height(points,kp);kc=np.array(kp['center']);kn=np.array(kp['normal']);kx=np.array(kp['x']);ky=np.cross(kn,kx)
   kuv=(np.column_stack((points,kh))-kc)@np.column_stack((kx,ky))
   distance=np.linalg.norm(np.maximum(abs(kuv)-8.4,0),axis=1)
   t=np.clip(1-distance/10,0,1);weight=t*t*t*(10+t*(-15+6*t))
   cap=np.maximum(cap,h+.35+np.maximum(kh-h,0)*weight)
  upper[local]=np.maximum(cap[local],floor[local]+.1)
  p=planes[7];th=plane_height(points,p);tc=np.array(p['center']);tn=np.array(p['normal']);tx=np.array(p['x']);ty=np.cross(tn,tx)
  tuv=(np.column_stack((points,th))-tc)@np.column_stack((tx,ty))
  thumb=(tuv[:,0]>3)&(tuv[:,1]>3)&(tuv[:,0]<17)&(tuv[:,1]<17)
  upper[thumb]=np.minimum(upper[thumb],np.maximum(th[thumb]+.1,floor[thumb]+.1))
 if side=='left':
  old=np.load(ROOT/'references/left-fair-field-v5.npz')
  old_height=RectBivariateSpline(old['y'],old['x'],old['z']).ev(points[:,1],points[:,0])
  upper=np.maximum(old_height+.01,floor+.01)
  for ki in [16]:
   kp=planes[ki];kh=plane_height(points,kp);kc=np.array(kp['center']);kn=np.array(kp['normal']);kx=np.array(kp['x']);ky=np.cross(kn,kx)
   uv=(np.column_stack((points,kh))-kc)@np.column_stack((kx,ky))
   distance=np.maximum(np.linalg.norm(np.maximum(abs(uv)-6.9,0),axis=1)-2.4,0)
   local=(distance<12)&(uv[:,0]>3)&(uv[:,1]>3)&(uv[:,0]<18)&(uv[:,1]<18)
   cap=kh+.05-.4*distance+.02*distance**2
   upper[local]=np.minimum(upper[local],np.maximum(cap[local],floor[local]+.1))
 # Boundary conditions are the measured plate planes; a weak quadratic prior
 # only stabilizes free outer flanks far from all mounting interfaces.
 centers=np.array([p['center'] for p in planes]);u=centers[:,0]/100;v=centers[:,1]/100
 design=np.column_stack((u*u,u*v,v*v,u,v,np.ones(len(u))))
 coef=np.linalg.lstsq(design,centers[:,2],rcond=None)[0]
 u=points[:,0]/100;v=points[:,1]/100
 prior=np.column_stack((u*u,u*v,v*v,u,v,np.ones(N)))@coef
 rhs=PRIOR_WEIGHT*prior
 locked=np.isfinite(fixed)
 print(side,'nodes',N,'fixed',int(locked.sum()),'fixed clearance conflicts',int((locked&(floor>fixed+.01)).sum()),flush=True)
 # Active-set quadratic solve: each iteration solves the global smooth sheet,
 # then activates violated lower clearance bounds. No local bump is added.
 active_low=np.zeros(N,dtype=bool);active_high=np.zeros(N,dtype=bool);z=prior.copy();z[locked]=fixed[locked]
 changes=[]
 for it in range(600):
  pinned=locked|active_low|active_high;known=np.where(locked,fixed,np.where(active_high,upper,floor))
  free=~pinned
  z[pinned]=known[pinned]
  z[free]=spsolve(A[free][:,free],rhs[free]-A[free][:,pinned]@z[pinned])
  gradient=A@z-rhs
  low=free&(z<floor-1e-5);high=free&(z>upper+1e-5)
  release_low=active_low&(gradient<-.0001);release_high=active_high&(gradient>.0001)
  if not low.any() and not high.any() and not release_low.any() and not release_high.any():break
  if low.any() or high.any():active_low|=low;active_high|=high
  else:active_low[release_low]=False;active_high[release_high]=False
  changes.append([int(low.sum()),int(high.sum()),int(release_low.sum()),int(release_high.sum())])
  if it%20==0:print(side,'iteration',it,'active set changes',changes[-1],flush=True)
 else:raise RuntimeError('Global fairing bounds did not converge')
 active=active_low|active_high
 print(side,'solve iterations',it,'active bounds',int(active.sum()),flush=True)
 z=z.reshape(ny,nx)
 np.savez_compressed(ROOT/'references'/f'{side}-fair-field-v7.npz',x=xs,y=ys,z=z,fixed=fixed.reshape(ny,nx),floor=floor.reshape(ny,nx),upper=upper.reshape(ny,nx))
 spline=RectBivariateSpline(ys,xs,z,kx=3,ky=3,s=0)
 xx,yy=np.meshgrid(np.arange(outline[:,0].min(),outline[:,0].max(),EXPORT_GRID),np.arange(outline[:,1].min(),outline[:,1].max(),EXPORT_GRID))
 grid=np.column_stack((xx.ravel(),yy.ravel()))
 grid=grid[PolygonPath(outline).contains_points(grid,radius=-.4)]
 grid=grid[cKDTree(outline).query(grid)[0]>.4]
 fine=np.vstack((outline,grid));height=spline.ev(fine[:,1],fine[:,0])
 top=np.column_stack((fine,height));count=len(fine);nb=len(outline)
 vertices=np.vstack((top,np.column_stack((outline,np.zeros(nb)))))
 triangles=Delaunay(fine).simplices.tolist()
 for i in range(nb):
  j=(i+1)%nb;triangles.extend([[j,i,count+i],[j,count+i,count+j]])
 for i in range(1,nb-1):triangles.append([count,count+i+1,count+i])
 mesh=trimesh.Trimesh(vertices,triangles,process=True)
 if mesh.volume<0:mesh.invert()
 assert mesh.is_watertight and mesh.is_winding_consistent
 (ROOT/'references'/f'{side}-rounded-envelope.stl').write_text(trimesh.exchange.stl.export_stl_ascii(mesh))
 return {'nodes':N,'iterations':it,'clearance_active_nodes':int(active.sum()),'min_height_mm':float(height.min()),'max_height_mm':float(height.max()),'changes':changes,'bending_energy':float(z.ravel()@(A@z.ravel()))}
if __name__=='__main__':
 import sys
 report=json.loads((ROOT/'reports/fair-surface-v7-checks.json').read_text()) if (ROOT/'reports/fair-surface-v7-checks.json').exists() else {}
 for side in (sys.argv[1:] or ['left','right']):report[side]=build(side)
 (ROOT/'reports/fair-surface-v7-checks.json').write_text(json.dumps(report,indent=2))
