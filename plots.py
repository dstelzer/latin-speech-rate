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
# p0: [max(self.ys), 300, -1, 1]

def logarithmic(x, a, b, c): # A ln B(x-C)
	return a * np.log(b * (x-c))
# p0: [1, 1, -1]

def logb(b, x): # Wrapper around np.log for using an arbitrary base
	return np.log(x) / np.log(b)

class Dataset:
	def __init__(self, fn):
		opener = bz2.open if str(fn).endswith('bz2') else open # Make sure we open the file the right way
		with opener(fn, 'rb') as f:
			data = pickle.load(f)
		
		self.xs = np.array([d[0] for d in data])
		self.ys = np.array([d[1] for d in data])
		
		self.func = hyperbolic
		self.p0 = np.array([max(self.ys), 300, -1, 1])
	
	def draw_data(self, format='ob'):
		plt.plot(self.xs, self.ys, format)
	
	def fit_curve(self):
		self.popt, self.pcov = opt.curve_fit(self.func, self.xs, self.ys, p0=self.p0)
	
	def mark_curve(self, xmin=None, xmax=None, npts=100):
		if xmax is None: xmax = max(self.xs) # Default which can be changed
		if xmin is None: xmin = min(self.xs)
		xnl = np.log10(xmin)
		xxl = np.log10(xmax)
		self.pxs = np.logspace(xnl, xxl, npts)
		self.pys = self.func(self.pxs, *self.popt)
	
	def draw_curve(self, format='-r'):
		plt.plot(self.pxs, self.pys, format)
	
	def draw_asymptote(self, line='--', color='g'):
		y = self.popt[0]
		plt.axhline(y=y, linestyle=line, color=color)
	
	def show(self): # Convenience method
		plt.xscale('log')
		plt.show()
	
	def csv(self):
		for x,y in zip(self.xs, self.ys):
			print(f'{x},{y}')

if __name__ == '__main__':
	d0 = Dataset('math/english_log.pickle.bz2')
	d0.fit_curve()
	print(d0.popt)
	
	d = Dataset('math/english_bootstrap.pickle.bz2')
	d.fit_curve()
	print(d.popt)
	d.mark_curve(xmax = max(d.xs)*10, npts=1000)
	d.draw_data()
	
	d0.mark_curve(xmax = max(d.xs)*10, npts=1000)
	d0.draw_data('Dg')
	d0.draw_curve()
	d0.draw_asymptote()
	
	d.draw_curve()
	d.draw_asymptote()
	d.show()
