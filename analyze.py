#!/usr/bin/env python3

from collections import Counter
from math import log2
from itertools import product
import random
import pickle
import bz2

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
	
	def reduce_corpus(self, desired_size=None, reduce_by=None):
		
		self.original_corpus = self.corpus
		self.corpus = self.corpus.copy()
		
		def get_random_datapoint():
			# Choose a word at random, weighted by frequency
			# (So effectively choosing a random data point)
			return random.choices(list(self.corpus.keys()), list(self.corpus.values()))[0]
			# The [0] is needed because random.choices, by default,
			# returns a list containing a single element.
		
		current_size = sum(self.corpus.values())
		
		if (reduce_by is None) == (desired_size is None): # == is xnor for bools
			raise ValueError('Must supply exactly one of desired_size or reduced_by')
		if reduce_by is None: reduce_by = current_size - desired_size # How many to throw away
		else: desired_size = current_size - reduce_by # How many to keep
		
		if desired_size > current_size:
			raise ValueError('Asked for a larger corpus than is available', desired_size, current_size)
		if desired_size <= 0:
			raise ValueError(desired_size)
		if desired_size == current_size:
			return # No changes needed
		
		additive = desired_size < reduce_by # If the desired size is less than the reduction amount, we can speed things up considerably by putting `desired_size` values into a new corpus rather than taking `reduce_by` values out of the existing one
		
		if additive:
			new_corpus = Counter()
			count = desired_size
		else:
			count = reduce_by
		
		for _ in trange(count):
			key = get_random_datapoint() # Choose a data point
			self.corpus[key] -= 1 # And trash it
			if additive: new_corpus[key] += 1
		
		if additive: self.corpus = new_corpus
		
		if self.log: print(f'Created reduced corpus of size {sum(self.corpus.values())}')
	
	def reduce_corpus_2(self, desired_size=None, reduce_by=None):
		
		self.original_corpus = self.corpus
		
		current_size = sum(self.corpus.values())
		
		if (reduce_by is None) == (desired_size is None): # == is xnor for bools
			raise ValueError('Must supply exactly one of desired_size or reduced_by')
		if reduce_by is None: reduce_by = current_size - desired_size # How many to throw away
		else: desired_size = current_size - reduce_by # How many to keep
		
		if desired_size > current_size:
			raise ValueError('Asked for a larger corpus than is available', desired_size, current_size)
		if desired_size <= 0:
			raise ValueError(desired_size)
		if desired_size == current_size:
			return # No changes needed
		
		word_to_id, id_to_word = dict(), dict()
		for i, word in enumerate(self.corpus):
			word_to_id[word] = i
			id_to_word[i] = word
		
		extended_corpus = []
		print('Making extended corpus')
		for word, count in tqdm(self.corpus.items(), leave=False):
			id = word_to_id[word]
			for _ in range(count):
				extended_corpus.append(id)
		
		print('Selecting from extended corpus')
		choice = random.sample(extended_corpus, desired_size)
		
		print('Creating new corpus')
		new_corpus = Counter()
		for id in choice:
			new_corpus[id_to_word[id]] += 1
		
		self.corpus = new_corpus
		
		if self.log: print(f'Created reduced corpus of size {sum(self.corpus.values())}')
	
	def autoreduce(self):
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
	
	def calculate_reduced_e2(self, n=1):
		xs = [5000, 10000, 20000, 30000, 40000, 50000, 60000, 70000, 80000, 90000]
		data = []
		for x in tqdm(xs):
			for _ in trange(n):
				self.reduce_corpus_2(desired_size=x)
				self.count_unigrams()
				self.count_bigrams()
				self.count_contexts()
				y = self.entropy2()
				data.append((x,y))
				self.unreduce()
		return data

if __name__ == '__main__':
	an = Analysis()
	an.load_corpus('data/latin/phi5.pickle.bz2')
	e1, e2 = an.do_things()
	print(f'SE: {e1}\nID: {e2}')
