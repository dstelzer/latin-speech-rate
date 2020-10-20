import bz2
import pickle
from pathlib import Path
import random

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

def compare_bootstrap():
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

def compare_latin():
	d0 = Dataset('math/latin_log.pickle.bz2')
	d0.fit_curve()
	d0.mark_curve(xmax=max(d0.xs)*10, npts=500)
	d0.draw_data('hr')
	d0.draw_curve()
	d0.draw_asymptote()
	
	for i in range(15):
		d = Dataset(f'math/latin90/{i:02d}.pickle.bz2')
		d.fit_curve()
		d.mark_curve(xmax=max(d0.xs)*10, npts=500)
		d.draw_data('ob Dg vm ^k sy oc Db vg ^m sk oy Dc vb ^g sm ok'.split()[i])
		d.draw_curve()
		d.draw_asymptote()
	
	d0.show()

def compare_latin_authors():
	vals = []
	
	d0 = Dataset('math/latin_log.pickle.bz2')
	d0.fit_curve()
	
	for auth in Path('math/latin_auth').glob('*.pickle.bz2'):
		d = Dataset(auth)
		d.fit_curve()
		d.mark_curve(xmax=max(d0.xs)*10, npts=500)
		d.draw_data(random.choice('oDv^s')+random.choice('bgmkyc'))
		d.draw_curve()
		d.draw_asymptote()
		vals.append(d.popt[0])
		print(f'Without {auth.stem.split(".")[0]}: {d.popt[0]}')
	
	d0.mark_curve(xmax=max(d0.xs)*10, npts=500)
	d0.draw_data('hr')
	d0.draw_curve('-b')
	d0.draw_asymptote(color='r')
	
	print(f'Actual value: {d0.popt[0]}')
	print(f'Approximated value: {sum(vals)/len(vals)}')
	print(f'Approximated standard error: {np.std(vals, ddof=1)}')
	
	d0.show()

def latin_author_histogram():
	with bz2.open('data/latin/authors.pickle.bz2', 'r') as f:
		data = pickle.load(f)
	plt.hist(np.array(list(data.values())), bins=20)
	plt.show()

if __name__ == '__main__': compare_latin_authors()
