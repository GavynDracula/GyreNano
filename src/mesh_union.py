"""Mesh boolean fallback after OCC fuse timeout / CGAL import failure.
Dependencies: numpy, trimesh, manifold3d. Outputs remain development parts.
"""
from pathlib import Path
import numpy as np
import trimesh
import manifold3d as mf
import json

ROOT=Path(__file__).resolve().parent.parent
def manifold(mesh):
    solid=mf.Manifold(mf.Mesh64(np.asarray(mesh.vertices,dtype=np.float64),np.asarray(mesh.faces,dtype=np.uint64)))
    assert solid.status()==mf.Error.NoError, str(solid.status())
    return solid


def load_regression(name):
    """Read losslessly compressed historical fixtures without expanding the workspace."""
    import gzip
    with gzip.open(ROOT/'references/regression'/(name+'.gz'), 'rb') as stream:
        return trimesh.load(stream, file_type='stl')
