"""Check the exact six-point example: seven lenses, three components, one.
Closed-ball lens adjacency is tested by enumerating minimum enclosing disks
of the union of the two index pairs, up to floating-point tolerance.
"""
from itertools import combinations
import math
import numpy as np

def minimum_radius(points: np.ndarray) -> float:
    candidates = [(x,0.0) for x in points]
    for a,b in combinations(points,2):
        c = (a+b)/2
        candidates.append((c,float(np.linalg.norm(a-c))))
    for a,b,c in combinations(points,3):
        matrix = 2*np.stack((b-a,c-a))
        if abs(np.linalg.det(matrix)) < 1e-12:
            continue
        centre = np.linalg.solve(matrix,[b@b-a@a,c@c-a@a])
        candidates.append((centre,float(np.linalg.norm(a-centre))))
    return min(r for c,r in candidates if np.all(np.linalg.norm(points-c,axis=1) <= r+1e-9))

def component_count(points: np.ndarray,radius: float) -> int:
    pairs = [p for p in combinations(range(6),2) if minimum_radius(points[list(p)]) <= radius+1e-9]
    parent = list(range(len(pairs)))
    def root(i: int) -> int:
        while parent[i] != i:
            i = parent[i]
        return i
    for i,j in combinations(range(len(pairs)),2):
        indices = sorted(set(pairs[i]) | set(pairs[j]))
        if minimum_radius(points[indices]) <= radius+1e-9:
            parent[root(i)] = root(j)
    return len({root(i) for i in range(len(pairs))})

def main() -> None:
    r = 1.2
    h = r*math.sqrt(3)
    X = np.array([[-r-h,r],[-r-h,-r],[-r,0],[r,0],[r+h,r],[r+h,-r]])
    radii = [1.25,2*r/math.sqrt(3),r*math.sqrt(2+math.sqrt(3))]
    counts = [component_count(X,t) for t in radii]
    if counts != [7,3,1]:
        raise AssertionError(f'Incorrect 2-NN hierarchy: {counts}')
    # K=2 excludes self: conventional DBSCAN min_samples=3.
    from sklearn.cluster import DBSCAN
    before = DBSCAN(eps=2*r-1e-6,min_samples=3).fit_predict(X)
    after = DBSCAN(eps=2*r+1e-6,min_samples=3).fit_predict(X)
    if not np.all(before == -1) or len(set(after)) != 1 or after[0] < 0:
        raise AssertionError('DBSCAN does not have the expected flat merge.')
    print('PASS six-point geometry: 7 -> 3 -> 1; DBSCAN merges once at epsilon=2r.')

if __name__ == '__main__':
    main()
