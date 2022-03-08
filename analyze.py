#!/usr/bin/env python3

from collections import Counter
from math import log2
from itertools import product
import random
import pickle
import bz2
from pathlib import Path

import numpy as np

from tqdm import tqdm, trange

class Analysis: # Simplest version of the analysis, takes a Counter mapping words to counts
	
	def __init__(self, log=True, progbar=True, boundary='␣', divider='-', csize=None, smoothing=0): # Configuration parameters go here
		self.log = log
		self.progbar = progbar
		self.boundary = boundary # Something that doesn't appear in any transcriptions
		self.divider = divider # The symbol used to separate syllables
		self.csize = csize # Corpus size (if we want to lower it)
		self.smoothing = smoothing # Laplace smoothing
	
	def special_loading_code(self): # Anything special to be done to the corpus
		pass
	
	def load_corpus(self, fn):
		opener = bz2.open if str(fn).endswith('bz2') else open # Make sure we open the file the right way
		with opener(fn, 'rb') as f:
			self.corpus = pickle.load(f)
		if self.log: print(f'Loaded {len(self.corpus)} words from {fn}')
		
		self.special_loading_code()
		
		types = len(self.corpus)
		tokens = sum(self.corpus.values())
		if self.log: print(f'Types: {types} Tokens: {tokens}')
		self.tokens = tokens
		
		self.original_corpus = self.corpus # For reduction experiments
	
	def inflate_corpus(self): # Call this once before doing any reductions
		self.inflated_corpus = []
		for word, count in self.corpus.items():
			for _ in range(count):
				self.inflated_corpus.append(word)
	
	def reduce_corpus(self, desired_size=None, reduce_by=None, bootstrap=False):
		
		self.corpus = Counter(self.corpus) # HACK TODO FIX
		
		current_size = sum(self.corpus.values())
		
		if (reduce_by is None) == (desired_size is None): # == is xnor for bools
			raise ValueError('Must supply exactly one of desired_size or reduced_by')
		if reduce_by is None: reduce_by = current_size - desired_size # How many to throw away
		else: desired_size = current_size - reduce_by # How many to keep
		
		if desired_size > current_size and not bootstrap:
			raise ValueError('Asked for a larger corpus than is available', desired_size, current_size)
		if desired_size == current_size and not bootstrap:
			return # No changes needed
		if desired_size <= 0:
			raise ValueError(desired_size)
		
		invert = (reduce_by < desired_size and not bootstrap) # For efficiency, it's sometimes better to select the data points to _remove_ instead of the ones to keep.
		sample_size = reduce_by if invert else desired_size
		
		if bootstrap:
			words = list(self.corpus.keys())
			weights = [self.corpus[w] for w in words]
			raw_sample = random.choices(words, weights, k=sample_size)
		else:
			raw_sample = random.sample(self.inflated_corpus, sample_size)
		
		sample = Counter()
		for word in raw_sample:
			sample[word] += 1
		
		if invert:
			self.corpus = self.corpus - sample 
		else:
			self.corpus = sample
		
		if self.log: print(f'Created reduced corpus of size {sum(self.corpus.values())}')
	
	def autoreduce(self):
		self.inflate_corpus()
		if self.csize is not None: self.reduce_corpus(desired_size = self.csize)
	
	def unreduce(self):
		self.corpus = self.original_corpus
	
	def split_bigrams(self, word):
		if not word: return
		
		# Use prefix, but not suffix, as clarified in Oh's thesis
		word = self.boundary + self.divider + word
		
		syls = word.split(self.divider)
		for a,b in zip(syls, syls[1:]):
			yield (a,b) # Not using `yield from` just for clarity's sake
	
	def split_unigrams(self, word):
		if not word: return
		
		for syl in word.split(self.divider):
			yield syl # Not using `yield from` just for clarity's sake
	
	def count_bigrams(self):
		self.bigrams = Counter()
		for word, count in self.corpus.items():
			for bg in self.split_bigrams(word):
				self.bigrams[bg] += count
		self.total_bigrams = sum(self.bigrams.values())
		if self.log: print(f'Found {self.total_bigrams} bigrams, {len(self.bigrams)} unique')
	
	def count_unigrams(self):
		self.unigrams = Counter()
		for word, count in self.corpus.items():
			for ug in self.split_unigrams(word):
				self.unigrams[ug] += count
		self.total_unigrams = sum(self.unigrams.values())
		if self.log: print(f'Found {self.total_unigrams} unigrams, {len(self.unigrams)} unique')
	
	def count_contexts(self):
		self.contexts = Counter()
		for word, count in self.corpus.items():
			for (c,_) in self.split_bigrams(word):
				self.contexts[c] += count
		self.total_contexts = sum(self.contexts.values())
		if self.log: print(f'Found {self.total_contexts} contexts, {len(self.contexts)} unique')
	
	def bigram_probability(self, bigram):
		return self.bigrams[bigram] / self.total_bigrams
	
	def unigram_probability(self, unigram):
		return self.unigrams[unigram] / self.total_unigrams
	
	def context_probability(self, context):
		return self.contexts[context] / self.total_contexts
	
	def entropy1(self): # First-order entropy (Shannon entropy)
		sum = 0
		def p(x): return self.unigram_probability(x)
		
		for x in tqdm(self.unigrams, leave=False, disable=(not self.progbar)):
			if p(x) == 0: continue # By convention, 0 × log2(0) = 0
			sum += p(x) * log2(p(x))
		
		return -sum
	
	def entropy2(self): # Second-order entropy (information density)
		sum = 0
		def p(x, y=None): # Overloaded to provide both p(x) and p(x,y)
			if y is None: return self.context_probability(x)
			else: return self.bigram_probability((x,y))
		
		for x,y in tqdm(self.bigrams, leave=False, disable=(not self.progbar)):
			if p(x,y) == 0 or p(x) == 0: continue # Convention as above
			sum += p(x,y) * log2( p(x,y) / p(x) )
		
		return -sum
	
	def do_things(self):
		self.autoreduce()
		self.count_unigrams()
		self.count_bigrams()
		self.count_contexts()
		e1 = self.entropy1()
		e2 = self.entropy2()
		return e1, e2
	
	def calculate_reduced_e2(self, n=1, bottom=5_000, top=None, npts=100, save=None, logscale=True, bootstrap=False, cut_top=False):
		if top is None: top = self.tokens
		if logscale:
			lb = np.log10(bottom)
			lt = np.log10(top)
			xs = np.logspace(lb, lt, npts)
		else:
			xs = np.linspace(bottom, top, npts)
		xs = np.rint(xs).astype(int) # We need integers only
		np.random.shuffle(xs) # Shuffle it to make the progress bar work better
		data = []
		self.inflate_corpus()
		if cut_top:
			self.reduce_corpus(desired_size=top, bootstrap=False)
			self.original_corpus = self.corpus
			self.inflate_corpus()
		for x in tqdm(xs):
			for _ in tqdm(range(n), leave=False, disable=(n<2)):
				self.reduce_corpus(desired_size=x, bootstrap=bootstrap)
				self.count_unigrams()
				self.count_bigrams()
				self.count_contexts()
				y = self.entropy2()
				data.append((x,y))
				self.unreduce()
		
		data.sort() # Undo the shuffling we did earlier
		
		if save is not None: # Save to a file
			opener = bz2.open if str(save).endswith('bz2') else open # Make sure we open the file the right way
			with opener(save, 'wb') as f:
				pickle.dump(data, f)
		
		return data
	
	def bootstrap_for_confidence(self, n, save=None):
		self.inflate_corpus()
		x = self.tokens
		data = []
		for _ in trange(n):
			self.reduce_corpus(desired_size=x, bootstrap=True)
			self.count_unigrams()
			self.count_bigrams()
			self.count_contexts()
			y = self.entropy2()
			data.append((x,y))
		
		if save is not None: # Save to a file
			opener = bz2.open if str(save).endswith('bz2') else open # Make sure we open the file the right way
			with opener(save, 'wb') as f:
				pickle.dump(data, f)
		
		return data
	
	def dump_frequencies(self, save=None):
		arr = np.array(list(self.unigrams.values()))
		if save is not None:
			opener = bz2.open if str(save).endswith('bz2') else open # Make sure we open the file the right way
			with opener(save, 'wb') as f:
				pickle.dump(arr, f)
		return arr

def confidence_test():
	input()
	analyzer = Analysis(log=False)
	analyzer.load_corpus('data/latin/phi5.pickle.bz2')
	analyzer.bootstrap_for_confidence(n=25, save='math/latin_confidence.pickle.bz2')

def simple_test():
	input()
	analyzer = Analysis(log=False)
	analyzer.load_corpus('data/latin/phi5_new.pickle.bz2')
	analyzer.calculate_reduced_e2(logscale=True, npts=200, n=5, save='math/latin_log_new.pickle.bz2', bootstrap=False)

def size_test():
	input()
	analyzer = Analysis(log=False)
	for i in trange(10):
		analyzer.load_corpus(f'data/latin/90/{i:02d}.pickle.bz2')
	#	print(analyzer.tokens)
	#	top = analyzer.tokens * 100
		analyzer.calculate_reduced_e2(logscale=True, npts=200, n=1, save=f'math/latin90/{i:02d}.pickle.bz2', bootstrap=False)

def auth_test():
	input()
	analyzer = Analysis(log=False)
	for auth in tqdm(list(Path('data/latin/auth_complete_new/').glob('*.pickle.bz2'))):
		analyzer.load_corpus(auth)
		analyzer.calculate_reduced_e2(logscale=True, npts=200, n=1, save=Path('math/latin_auth_complete_new')/auth.name, bootstrap=False)

def basic():
	an = Analysis()
	an.load_corpus('data/latin/phi5_new.pickle.bz2')
	e1, e2 = an.do_things()
	print(f'SE: {e1}\nID: {e2}')

def freqs():
	an = Analysis()
	an.load_corpus('data/latin/phi5_complete_new.pickle.bz2')
	an.count_unigrams()
	an.dump_frequencies('math/latin_sylfreq.pickle.bz2')
	print(max(an.unigrams.items(), key=lambda a:a[1]))
	print(min(an.unigrams.items(), key=lambda a:a[1]))
	e1, e2 = an.do_things()
	print(f'SE: {e1}\nID: {e2}')

def misc_stats():
	an = Analysis()
	print('Number of syllables in top 20000 words')
	an.load_corpus('data/latin/phi5_new.pickle.bz2')
	an.corpus = Counter(dict(Counter(an.corpus).most_common(20000)))
	an.count_unigrams()
	print(len(an.unigrams))
	print(list(an.unigrams.keys())[:100])
	print('Most complex syllable')
	an.load_corpus('data/latin/phi5_new.pickle.bz2')
	an.count_unigrams()
	tops = sorted(an.unigrams.keys(), key=len, reverse=True)
	with open('complex_syllables.csv', 'w') as f:
		f.write('\n'.join(tops[:1000]))
	print('Written')

if __name__ == '__main__': auth_test()
