import bz2
import pickle
from pathlib import Path
import random

import numpy as np
import matplotlib.pyplot as plt
import scipy.optimize as opt

from matplotlib.ticker import StrMethodFormatter # Needed for a hack to make formatting line up in the talk slides

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
		plt.plot(self.pxs, self.pys, format, label='Fitted Curve')
	
	def draw_asymptote(self, line='--', color='g', include_tick=True):
		y = self.popt[0]
		plt.axhline(y=y, linestyle=line, color=color, label='Prediction')
		if include_tick:
			newticks = [y]
			plt.yticks(list(plt.yticks()[0]) + newticks) # Add an extra tick to the y-axis
	
	def show(self): # Convenience method
		plt.xscale('log')
		plt.show()
	
	def csv(self):
		for x,y in zip(self.xs, self.ys):
			print(f'{x},{y}')

class CSVDataset(Dataset):
	def __init__(self, fn):
		with open(fn, 'r') as f:
			data = [row.split(',') for row in f.read().split('\n') if row]
		self.xs = np.array([float(d[0])*10000 for d in data])
		self.ys = np.array([float(d[1]) for d in data])
		self.func = hyperbolic
		self.p0 = np.array([max(self.ys), 300, -1, 1])

def basic():
	plt.rcParams.update({'font.size': 16})
	d = Dataset('math/latin_log_complete.pickle.bz2')
	d.fit_curve()
	d.mark_curve(xmax = max(d.xs)*10)
#	d.draw_data('r.')
	plt.plot(d.xs, d.ys, '.', color='#ff7070', label='With Digesta')
	print(d.popt)
	
	d2 = Dataset('math/latin_log.pickle.bz2')
	d2.fit_curve()
	d2.mark_curve(xmax = max(d.xs)*10)
#	d2.draw_data('b.')
	plt.plot(d2.xs, d2.ys, '.', color='#70c4ff', label='Without Digesta')
	print(d2.popt)
	
	d.draw_asymptote('--', 'r', False)
	d2.draw_asymptote('--', 'b')
	
	d.draw_curve('-k')
	d2.draw_curve('-k')
	
	plt.xlabel('Corpus Size (tokens)')
	plt.ylabel('Information Density (bits/syl)')
	plt.legend(loc='lower right')
	plt.gca().yaxis.set_major_formatter(StrMethodFormatter('{x:,.2f}')) # 2 decimal places
	d.show()

def figures_for_presentation():
	plt.rcParams.update({'font.size': 16})
	
	d = Dataset('math/latin_log.pickle.bz2')
	d.fit_curve()
	d.mark_curve(xmax = max(d.xs)*100)
#	d.draw_data('b.')
	plt.plot(d.xs, d.ys, '.', color='#70c4ff', label='Data')
	d.draw_curve('-k')
#	plt.plot(d.pxs, d.pys, '-k', alpha=0)
	d.draw_asymptote('--', 'r')
#	plt.axhline(y=d.popt[0], linestyle='--', color='r', alpha=0)
	plt.xlabel('Corpus Size (tokens)')
	plt.ylabel('Information Density (bits/syl)')
	
	plt.gca().yaxis.set_major_formatter(StrMethodFormatter('{x:,.2f}')) # 2 decimal places
#	newticks = [6.4]
#	plt.yticks(list(plt.yticks()[0]) + newticks) # Add an extra tick to the y-axis
	plt.legend()
	
	d.show()

def csv():
	d = CSVDataset('math/zipf.csv')
	d.fit_curve()
	d.mark_curve(xmax = max(d.xs)*10**15)
	d.draw_data('r.')
	d.draw_curve('-k')
	d.draw_asymptote('--', 'r')
	print(d.popt)
	d.show()

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
	plt.rcParams.update({'font.size': 16})
	vals = []
	
	d0 = Dataset('math/latin_log.pickle.bz2')
	d0.fit_curve()
	
	for auth in Path('math/latin_auth').glob('*.pickle.bz2'): # Use auth_all to include the Digesta
		if '0474' in auth.stem: continue # Remove Cicero if you want
		d = Dataset(auth)
		d.fit_curve()
		d.mark_curve(xmax=max(d0.xs)*10, npts=500)
		# old: random.choice('oDv^s')
		d.draw_data('.'+random.choice('bgmyc'))
		d.draw_curve('k')
#		d.draw_asymptote('--', 'k', include_tick=False)
		vals.append(d.popt[0])
		print(f'Without {auth.stem.split(".")[0]}: {d.popt[0]}')
	
#	d0.mark_curve(xmax=max(d0.xs)*10, npts=500)
#	d0.draw_data('.r')
#	d0.draw_curve('-k')
	d0.draw_asymptote('-', 'r')
	
	plt.xlabel('Corpus Size (tokens)')
	plt.ylabel('Information Density (bits/syl)')
	plt.gca().yaxis.set_major_formatter(StrMethodFormatter('{x:,.2f}'))
	
	print(f'Actual value: {d0.popt[0]}')
	print(f'Approximated value: {sum(vals)/len(vals)}')
	print(f'Approximated standard error: {np.std(vals, ddof=1)}')
	
	d0.show()

def latin_author_histogram():
	with bz2.open('data/latin/authors.pickle.bz2', 'r') as f:
		data = pickle.load(f)
	plt.hist(np.array(list(data.values())), bins=20)
	plt.show()

def latin_sylfreq_histogram():
	with bz2.open('math/latin_sylfreq.pickle.bz2', 'rb') as f:
		data = pickle.load(f)
	data.sort()
	plt.plot(data[::-1])
	plt.show()

if __name__ == '__main__': figures_for_presentation()
