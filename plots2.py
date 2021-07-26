from collections import defaultdict
import csv

import matplotlib.pyplot as plt
import numpy as np
import numpy.random as rand
import scipy.stats as stat

def get_data():
	data = defaultdict(list)
	with open('published_data.tsv', 'r', newline='') as f:
		read = csv.DictReader(f, delimiter='\t')
		for row in read:
			ns = float(row['NS']) # number of syllables
			dur = float(row['Duration']) # speech duration
			sr = ns / dur # speech rate
			lang = row['Language']
			data[lang].append(sr)
	return data

def generate_data(mu, sigma, n=150, rng=rand.default_rng()):
	# The final parameter is a cheap way to make a static variable
	# Since it'll only be instantiated once (when the function is defined)
	return rng.normal(loc=mu, scale=sigma, size=n)

def make_plot(langs, data):
	d2 = [np.array(data[lang]) for lang in langs]
	plt.violinplot(d2, showmeans=True)
	plt.xticks(range(1,len(langs)+1), langs)
	plt.ylabel('Speech rate (syllables per second)')
	plt.show()

def violin_manual(data, pos, color, fake=None): # Manual version so we can fine-tune the behavior
	# Based on http://pyinsci.blogspot.com/2009/09/violin-plot-with-matplotlib.html
	if fake is None:
		k = stat.gaussian_kde(data)
		m = k.dataset.min()
		M = k.dataset.max()
		x = np.linspace(m, M, 100)
		y = k.evaluate(x)
		mu = np.mean(data)
		sigma = np.std(data)
		print(mu, sigma)
	else:
		mu, sigma = fake
		m = mu-2*sigma
		M = mu+2*sigma
		x = np.linspace(m, M, 100)
		y = stat.norm.pdf(x, mu, sigma)
	w = 1/3
	w2 = 1/6
	w3 = 1/9
	y /= y.max(); y *= w # Scale to desired width
	ax = plt.gca()
	ax.fill_betweenx(x, pos, pos+y, edgecolor=color, facecolor=color, alpha=0.5)
	ax.fill_betweenx(x, pos, pos-y, edgecolor=color, facecolor=color, alpha=0.5)
	plt.hlines(mu, pos-w2, pos+w2, color=color)
	plt.hlines(mu+sigma, pos-w3, pos+w3, color=color)
	plt.hlines(mu-sigma, pos-w3, pos+w3, color=color)

def make_plot_2():
	plt.rcParams.update({'font.size': 20})
	data = get_data()
#	langs = ['CAT', 'FRA', 'ITA', 'SPA']
#	colors = 'ybgr'
	langs = ['VIE', 'ENG', 'JPN']
	colors = 'ybr'
	d2 = [np.array(data[lang]) for lang in langs]
	for i, (d, c) in enumerate(zip(d2, colors)):
		violin_manual(d, i, c)
	violin_manual([], i+1, 'k', (6.29, 0.82))
	langs += ['LAT']
	plt.xticks(range(len(langs)), langs)
	plt.ylabel('Speech rate (syllables per second)')
	plt.grid(axis='y', linestyle=':', color='k', alpha=0.5)
	plt.show()

if __name__ == '__main__': make_plot_2()
