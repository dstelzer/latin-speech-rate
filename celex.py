#!/usr/bin/env python3

from collections import Counter
from math import log2
from itertools import product
import random
# Need these for reading the compressed data file
import pickle
import bz2

from tqdm import tqdm

from analyze import Analysis

# Current results for English: 9.42676, 6.98057
# Goal: 9.51, 7.09
# (True, False, True, CobW, SAM, None, 0)
# Using CobW instead of Cob because it matches "17M tokens"

# Current results for German: 9.27457, 6.07757
# Goal: 9.30, 6.08
# (True, False, True, Mann, SAM, None, 0)
# Using Mann instead of MannW because it matches "5M tokens"

# EDIT: Using Dr Oh's newly-provided data, German results match exactly!
# True, False, True, Word Mann, DISC, None, 0
# 9.303958490082131 6.082567690505002

LOG = True

BOUNDARY = '␣' # Something that doesn't appear in the SAMPA variant CELEX uses
DIVIDER = '-' # The symbol used to separate syllables

class CelexAnalysis(Analysis):
	
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
		f = int(word[self.freq]) # self.freq is the name of the metric we're using for frequency: Cob (COBUILD total), CobW (COBUILD Written), or CobS (COBUILD spoken).
		return f + self.smoothing
	
	def load_corpus(self, fn):
		opener = bz2.open if str(fn).endswith('bz2') else open # Make sure we open the file the right way
		with opener(fn, 'rb') as f:
			self.corpus = pickle.load(f)
		if LOG: print(f'Loaded {len(self.corpus)} words from {fn}')
		
		types = len(self.corpus)
		tokens = sum(int(word[self.freq]) for word in self.corpus)
		if LOG: print(f'Types: {types} Tokens: {tokens}')
		self.tokens = tokens
	
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
#	for params in product([True], [False], [True], ['CobW'], ['SAM'], [5000,10000,20000,30000,40000,50000,60000,70000,80000,90000,None], [0]):
	for params in product([True], [False], [True], ['CobW'], ['DISC'], [None], [0]):
		analyzer = CelexAnalysis(*params)
		analyzer.load_corpus('data/english.pickle.bz2')
		analyzer.do_things()
		print()
