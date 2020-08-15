import re
from collections import Counter
import bz2
import pickle

from cltk.prosody.latin.syllabifier import Syllabifier
from cltk.prosody.latin.scansion_constants import ScansionConstants

# A hacky workaround for the fact that the macronizer isn't intended to be imported as a module
import sys
from pathlib import Path
# Change the following line to point to wherever Alatius's macronizer is installed
sys.path.insert(1, str(Path.cwd()/'latin-macronizer'))
from macronizer import Macronizer

from tqdm import tqdm # Progress bars are nice

BOUNDARY = '-'
KW = 'κ'
GW = 'γ'

EXTRA_CONSONANTS = KW + GW

VALID = 'abcdefghijklmnopqrstuvwxyzāēīōūȳ' + EXTRA_CONSONANTS

class Processor:
	
	def __init__(self):
		self.constants = ScansionConstants()
		self.constants.CONSONANTS += EXTRA_CONSONANTS
		self.constants.CONSONANTS_WO_H += EXTRA_CONSONANTS
		self.constants.MUTES += EXTRA_CONSONANTS
		
		self.constants.DIPTHONGS = ['ae', 'au', 'oe'] # Remove ui and eu and special-case those instead
		# TODO: ei?
		# Here are all the exceptions: the EU diphthong words, and anything common enough to be worth special-casing but not generalizable
		self.constants.UI_EXCEPTIONS.update({'neu':['neu'], 'ceu':['ceu'], 'seu':['seu'], 'heu':['heu'], 'heus':['heus'], 'deinde':['dein','de'], 'propter':['prop','ter'], 'quemadmodum':['quem','ad','mo','dum']})
		# Certain prefixes show assimilation - so the normal syllabification rules can deal with them just fine and we don't have to special-case them (and risk having casualties like *e-nim)
		for pref in ('en','ēn','sur','ēr','ēf','ac','ef','er'):
			self.constants.PREFIXES.remove(pref)
		# Others just cause problems because they're so common (*se-rvus), and the macronizer should mean they're not problems normally
		for pref in ('se','di'):
			self.constants.PREFIXES.remove(pref)
		
		self.macronizer = Macronizer()
		self.syllabifier = Syllabifier(self.constants, convert_i_to_j=False)
		
		self.total_counts = Counter()
	
	def macronize(self, text):
		return self.macronizer.macronize(text, domacronize=True, alsomaius=False, performutov=True, performitoj=True, markambigs=False)
	
	def clean(self, word):
		voiceless = f'([ptcqsf{KW}])'
		vowel = '([aeiouyāēīōūȳ])'
		prefix = '(ambi|ante|co|contra|contrā|de|dē|di|dī|ē|ex|extra|extrā|extro|infra|īnfrā|intro|intrō|iuxta|juxtā|ne|nē|prae|pre|pro|prō|quasi|re|rē|retro|retrō|se|sē|sine|supra|suprā|tra|trā|ultra|ultrā)' # Generated automatically from CLTK's "scansion constants" - prefixes ending in vowels
		# Note: specifically removed 'e' because it hit 'ejus' and such
		# ējiciō and such have a long ē so that should be fine
		full_prefix = '(' + '|'.join(self.constants.PREFIXES) + '|e|ē)' # As above, plus prefixes ending in consonants too
		invalid = '[^'+VALID+']'
		
		word = word.lower()
		word = re.sub(invalid, '', word) # Remove things that are not letters
		word = word.strip()
		if not word: return None
		if not re.search(vowel, word): return None # No vowels? Probably a single letter, we want to discard that
		
		word = re.sub(f'{full_prefix}ic(i|ī|ere)', r'\1jic\2', word) # The macronizer handles most instances of j, but not "hidden" j before i (which only appears in compounds of jaciō with vowel reduction)
		
		word = re.sub(f'b{voiceless}', r'p\1', word) # b → p / _ voiceless
		word = re.sub(f'd{voiceless}', r't\1', word) # d → t / _ voiceless
		# Presumably g → c / _ voiceless too, but this never happens
		# (as before s it's written x, and no prefix ends in g)
		word = re.sub('qu', f'{KW}', word) # represent kʷ as one letter
		word = re.sub(f'ngu{vowel}', fr'n{GW}\1', word) # likewise
		word = re.sub(f'{KW}u', 'cu', word) # kʷ → k / _ u
		word = re.sub(f'{GW}u', 'gu', word) # gʷ → g / _ u
		word = re.sub('x', 'cs', word) # represent sequence ks as cs
		word = re.sub('k', 'c', word) # both represent voiceless velar stop
		word = re.sub(f'{vowel}j{vowel}', r'\1jj\2', word) # intervocalic j double
		word = re.sub(f'{prefix}jj', r'\1j', word) # exception: after a prefix
		word = re.sub(f'{vowel}z{vowel}', r'\1zz\2', word) # intervocalic z double
	#	word = re.sub('rh', 'r', word) # TODO: was RH pronounced?
		
		return word
	
	def syllabify(self, word):
		return self.syllabifier.syllabify(word)
	
	def process(self, text):
		text = self.macronize(text)
		words = text.split()
		for word in words:
			word = self.clean(word)
			if not word: continue
			syls = self.syllabify(word)
			yield BOUNDARY.join(syls)
	
	def count(self, text): # Process a text and count its words
		data = Counter()
		for word in self.process(text):
			if not word: continue
			data[word] += 1
		self.total_counts |= data
	
	def save(self, fn): # Save counts to a file
		opener = bz2.open if str(fn).endswith('bz2') else open # Make sure we open the file the right way
		d = dict(self.total_counts)
		with opener(fn, 'wb') as f:
			pickle.dump(d, f)

if __name__ == '__main__':
	p = Processor()
	while True:
		print(' '.join(p.process(input('>'))))
