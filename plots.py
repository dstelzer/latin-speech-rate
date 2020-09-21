import bz2
import pickle

import numpy as np
import matplotlib.pyplot as plt
import scipy.optimize as opt

def exponential(x, a, b, c): # A(1-e^(-B(x-C))
	return a*(1 - np.exp(-b * (x-c)))
# p0: [max(self.ys), 1/min(self.xs), 0]

def hyperbolic(x, a, b, c, d): # A - B(x-C)^-D
	return a - b * (x-c) ** (-d)
# p0: [max(self.ys), 1/min(self.xs), -1, 1]

def logarithmic(x, a, b, c): # A ln B(x-C)
	return a * np.log(b * (x-c))
# p0: [1, 1, -1]

class Dataset:
	def __init__(self, fn):
		opener = bz2.open if str(fn).endswith('bz2') else open # Make sure we open the file the right way
		with opener(fn, 'rb') as f:
			data = pickle.load(f)
		
		self.xs = np.array([d[0] for d in data])
		self.ys = np.array([d[1] for d in data])
		
		self.func = hyperbolic
		self.p0 = np.array([max(self.ys), 1/min(self.xs), -1, 1])
	
	def draw_data(self, format='ob'):
		plt.plot(self.xs, self.ys, format)
	
	def fit_curve(self):
		self.popt, self.pcov = opt.curve_fit(self.func, self.xs, self.ys, p0=self.p0)
	
	def mark_curve(self, xmin=None, xmax=None, npts=100):
		if xmax is None: xmax = max(self.xs) # Default which can be changed
		if xmin is None: xmin = min(self.xs)
		self.pxs = np.linspace(xmin, xmax, npts)
		self.pys = self.func(self.pxs, *self.popt)
	
	def draw_curve(self, format='-r'):
		plt.plot(self.pxs, self.pys, format)
	
	def show(self): # Convenience method
		plt.show()
	
	def csv(self):
		for x,y in zip(self.xs, self.ys):
			print(f'{x},{y}')

if __name__ == '__main__':
	d = Dataset('math/english_filled.pickle.bz2')
	d.fit_curve()
	print(d.popt); print(d.pcov)
	d.mark_curve(xmax = max(d.xs)*1, npts=1000)
	d.draw_data()
	d.draw_curve()
	d.show()
