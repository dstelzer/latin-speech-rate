#!/usr/bin/env python3

from collections import Counter
from math import log2
from itertools import product
import random
import pickle
import bz2

from tqdm import tqdm

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
	
	def reduce_corpus(self, size): # HACK clean this up
		population = list(self.corpus.keys())
		weights = list(self.corpus.values())
		new_corpus = Counter()
		
		for choice in random.choices(population, weights, k=size):
			new_corpus[choice] += 1
		
		self.corpus = dict(new_corpus())
		if self.LOG: print(f'Created reduced corpus of size {sum(self.corpus.values())}')
	
	def autoreduce(self):
		if self.csize is not None: self.reduce_corpus(self.csize)
	
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

if __name__ == '__main__':
	an = Analysis()
	an.load_corpus('data/latin/phi5.pickle.bz2')
	e1, e2 = an.do_things()
	print(f'SE: {e1}\nID: {e2}')
