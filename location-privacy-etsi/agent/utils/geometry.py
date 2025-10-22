# A file of auxiliary geometric scripts.
import numpy as np


# Computes a weighted area of the triangle spanned by
# three given points x,y,z. The area is:
# - positive, if z is left of xy
# - negative, if z is right of xy
# - zero, if z lies on the line xy
def weighted_area(x,y,z):
    mat = np.matrix([
        [1, x[0], x[1]],
        [1, y[0], y[1]],
        [1, z[0], z[1]],
    ])
    return 0.5 * np.linalg.det(mat)


# Decides if a point lies within a convex polygon or not.
# P: A polygon, given by a list of points sorted counterclockwise
# x: The point to be checked for membership in the polygon
def point_in_convex_polygon(P, x):
    for i in range(len(P)-1):
        if weighted_area(P[i], P[i + 1], x) < 0:
            return False
    return True
