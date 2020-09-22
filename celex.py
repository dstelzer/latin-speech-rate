#!/usr/bin/env python3

from collections import Counter
from math import log2
from itertools import product
import random

from tqdm import tqdm

from analyze import Analysis

# Current results for English: 9.42676, 6.98057
# Goal: 9.51, 7.09
# (True, CobW, DISC)
# Using CobW instead of Cob because it matches "17M tokens"
ENGLISH = {'stress':True, 'freq':'CobW', 'phon':'DISC'}

# Current results for German: 9.27457, 6.07757
# Goal: 9.30, 6.08
# (True, Mann, SAM)
# Using Mann instead of MannW because it matches "5M tokens"

# EDIT: Using Dr Oh's newly-provided data, German results match exactly!
# True, Word Mann, DISC
# 9.303958490082131 6.082567690505002
GERMAN = {'stress':True, 'freq':'Word Mann', 'phon':'DISC', 'divider':' '}

class CelexAnalysis(Analysis):
	
	def __init__(self, stress, freq, phon, *args, **kwargs): # Configuration parameters
		super().__init__(*args, **kwargs)
		self.stress = stress
		self.freq = freq
		self.phon = phon
	
	def select_form(self, word): # Return either a phonological form that includes stress, or one that does not.
		if self.stress: return word['PhonStrs'+self.phon]
		else: return word['PhonSyl'+self.phon]
	
	def select_count(self, word):
		f = int(word[self.freq]) # self.freq is the name of the metric we're using for frequency: Cob (COBUILD total), CobW (COBUILD Written), or CobS (COBUILD spoken).
		return f + self.smoothing
	
	def special_loading_code(self): # Preprocess the corpus into the form we want
		new = Counter()
		word = self.corpus[0]
		print('Viable tags:', ' '.join(word.keys()))
		for word in self.corpus: # Have to do it this way instead of a dict comprehension to account for homophones (thus add, don't replace)
			new[self.select_form(word)] += self.select_count(word)
		self.corpus = new

def confidence_test():
	input()
	analyzer = CelexAnalysis(log=False, **ENGLISH)
	analyzer.load_corpus('data/english.pickle.bz2')
	analyzer.bootstrap_for_confidence(n=25, save='math/english_confidence.pickle.bz2')

def size_test():
	input()
	analyzer = CelexAnalysis(log=False, **ENGLISH)
	analyzer.load_corpus('data/english.pickle.bz2')
	top = analyzer.tokens * 10
	analyzer.calculate_reduced_e2(n=2, save='math/english_bootstrap.pickle.bz2', logscale=True, npts=200, bootstrap=True, top=top)

def basic_analysis():
	input()
	analyzer = CelexAnalysis(log=False, **GERMAN)
	analyzer.load_corpus('data/german.pickle.bz2')
	e1, e2 = analyzer.do_things()
	print(e1)
	print(e2)

if __name__ == '__main__':
	confidence_test()
