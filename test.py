from scipy.spatial import distance_matrix
import numpy as np

# Define two sets of points
points_a = np.array([[1, 2], [3, 4], [5, 6]])

# Compute the distance matrix
dist_matrix = distance_matrix(points_a, points_a)

print("Distance Matrix:\n", dist_matrix)