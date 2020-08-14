#!/usr/bin/env python3

from collections import Counter
from math import log2
from itertools import product
import random

from tqdm import tqdm

LOG = True

BOUNDARY = '␣' # Something that doesn't appear in any transcriptions
DIVIDER = '-' # The symbol used to separate syllables

class Analysis:
	
	def __init__(self, prefix, suffix): # Configuration parameters
		self.prefix = prefix
		self.suffix = suffix
	
	def load_corpus(self, fn):
		raise NotImplemented
	
	def select_form(self, word):
		raise NotImplemented
	
	def select_count(self, word):
		raise NotImplemented
	
	def split_bigrams(self, word):
		form = self.select_form(word)
		if not form: return
		
		if self.prefix: form = BOUNDARY + DIVIDER + form
		if self.suffix: form = form + DIVIDER + BOUNDARY
		
		syls = form.split(DIVIDER)
		for a,b in zip(syls, syls[1:]):
			yield (a,b) # Not using `yield from` just for clarity's sake
	
	def split_unigrams(self, word):
		form = self.select_form(word)
		if not form: return
		
		for syl in form.split(DIVIDER):
			yield syl # Not using `yield from` just for clarity's sake
	
	def count_bigrams(self):
		self.bigrams = Counter()
		for word in self.corpus:
			count = self.select_count(word)
			for bg in self.split_bigrams(word):
				self.bigrams[bg] += count
		self.total_bigrams = sum(self.bigrams.values())
		if LOG: print(f'Found {self.total_bigrams} bigrams, {len(self.bigrams)} unique')
	
	def count_unigrams(self):
		self.unigrams = Counter()
		for word in self.corpus:
			count = self.select_count(word)
			for ug in self.split_unigrams(word):
				self.unigrams[ug] += count
		self.total_unigrams = sum(self.unigrams.values())
		if LOG: print(f'Found {self.total_unigrams} unigrams, {len(self.unigrams)} unique')
	
	def count_contexts(self):
		self.contexts = Counter()
		for word in self.corpus:
			count = self.select_count(word)
			for (c,_) in self.split_bigrams(word):
				self.contexts[c] += count
		self.total_contexts = sum(self.contexts.values())
		if LOG: print(f'Found {self.total_contexts} contexts, {len(self.contexts)} unique')
	
	def bigram_probability(self, bigram):
		return self.bigrams[bigram] / self.total_bigrams
	
	def unigram_probability(self, unigram):
		return self.unigrams[unigram] / self.total_unigrams
	
	def context_probability(self, context):
		return self.contexts[context] / self.total_contexts
	
	def entropy1(self): # First-order entropy (Shannon entropy)
		sum = 0
		def p(x): return self.unigram_probability(x)
		
		for x in tqdm(self.unigrams, leave=False):
			if p(x) == 0: continue
			sum += p(x) * log2(p(x))
		
		return -sum
	
	def entropy2(self): # Second-order entropy (information density)
		sum = 0
		def p(x, y=None):
			if y is None: return self.context_probability(x)
			else: return self.bigram_probability((x,y))
		
		for x,y in tqdm(self.bigrams, leave=False):
			if p(x,y) == 0 or p(x) == 0: continue
			sum += p(x,y) * log2( p(x,y) / p(x) )
		
		return -sum
	
	def do_things(self):
		self.count_unigrams()
		self.count_bigrams()
		self.count_contexts()
		e1 = self.entropy1()
		e2 = self.entropy2()
		
		print(f'SE: {e1}\nID: {e2}')

if __name__ == '__main__':
	raise NotImplemented
