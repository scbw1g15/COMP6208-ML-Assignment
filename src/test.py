import numpy as np
from scipy.interpolate import griddata # not quite the same as `matplotlib.mlab.griddata`

grid = np.random.random((10, 10))
mask = np.random.random((10, 10)) < 0.2

points = mask.nonzero()
values = grid[points]
gridcoords = np.meshgrid[:grid.shape(0), :grid.shape(1)]

outgrid = griddata(points, values, gridcoords, method='nearest') 