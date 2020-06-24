#!/usr/bin/env python3

from collections import Counter
from math import log2
from itertools import product
import random
# Also need these for reading the compressed data file
import pickle
import bz2

from tqdm import tqdm

# Current results for English, using (True, False, True, CobW, SAM, None): 9.42676, 6.98057
# Current results for German, using (True, False, True, MannW, SAM, None): 

LOG = False

BOUNDARY = '␣' # Something that doesn't appear in the SAMPA variant CELEX uses
DIVIDER = '-' # The symbol used to separate syllables

class CelexAnalysis:
	
	def __init__(self, prefix, suffix, stress, freq='Cob', phon='SAM', csize=None, smoothing=0): # Configuration parameters
		self.prefix = prefix
		self.suffix = suffix
		self.stress = stress
		self.freq = freq
		self.phon = phon
		self.csize = csize
		self.smoothing = smoothing
	
	def reduce_corpus(self, size): # HACK clean this up
		population = [word['IdNum'] for word in self.corpus]
		weights = [int(word[self.freq])+1 for word in self.corpus]
		new_corpus = { word['IdNum']:word.copy() for word in self.corpus }
		for word in new_corpus.values(): word[self.freq] = 0
		
		for choice in random.choices(population, weights, k=size):
			new_corpus[choice][self.freq] += 1
		
		self.corpus = list(new_corpus.values())
		if LOG: print(f'Created reduced corpus of size {sum(word[self.freq] for word in self.corpus)}')
	
	def autoreduce(self):
		if self.csize is not None: self.reduce_corpus(self.csize)
	
	def select_form(self, word): # Return either a phonological form that includes stress, or one that does not.
		if self.stress: return word['PhonStrs'+self.phon]
		else: return word['PhonSyl'+self.phon]
	
	def select_count(self, word):
	#	return int(word[self.freq]) # self.freq is the name of the metric we're using for frequency: Cob (COBUILD total), CobW (COBUILD Written), or CobS (COBUILD spoken).
		f = int(word[self.freq])
		return f + self.smoothing
	
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
	
	def load_corpus(self, fn):
		opener = bz2.open if str(fn).endswith('bz2') else open # Make sure we open the file the right way
		with opener(fn, 'rb') as f:
			self.corpus = pickle.load(f)
		if LOG: print(f'Loaded {len(self.corpus)} words from {fn}')
		
		types = len(self.corpus)
		tokens = sum(int(word[self.freq]) for word in self.corpus)
		if LOG: print(f'Types: {types} Tokens: {tokens}')
		self.tokens = tokens
	
	def bigram_probability(self, bigram):
		return self.bigrams[bigram] / self.total_bigrams
	
	def unigram_probability(self, unigram):
	#	if unigram == BOUNDARY: return 1
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
		
	#	for x,y in tqdm(product(self.unigrams, repeat=2), total=len(self.unigrams)**2):
	#	printed_so_far = set()
		for x,y in tqdm(self.bigrams, leave=False):
			if p(x,y) == 0 or p(x) == 0: continue
			sum += p(x,y) * log2( p(x,y) / p(x) )
	#		if x not in printed_so_far:
	#			printed_so_far.add(x)
	#			print(f'\t\tp({x}) = {p(x)}')
		
		return -sum
	
	def do_things(self):
		self.autoreduce()
		self.count_unigrams()
		self.count_bigrams()
		self.count_contexts()
		e1 = self.entropy1()
		e2 = self.entropy2()
		
		def b(r): return '#' if r else '-'
		
		print(f'Results ({b(self.prefix)}{b(self.suffix)}{b(self.stress)} {self.freq} {self.csize} {self.smoothing}):\n\tSE: {e1}\n\tID: {e2}')
	#	print(e1)

if __name__ == '__main__':
	input()
	for params in product([True], [False], [True], ['CobW'], ['SAM'], [5000,10000,20000,30000,40000,50000,60000,70000,80000,90000,None], [0]):
#	for params in product([True], [False], [True], ['Mann','MannW'], ['SAM'], [None], [0,1]):
		analyzer = CelexAnalysis(*params)
		analyzer.load_corpus('data/english.pickle.bz2')
		analyzer.do_things()
		print()
