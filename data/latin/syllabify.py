import re

from cltk.stem.latin.syllabifier import Syllabifier

# A hacky workaround for the fact that the macronizer isn't intended to be imported as a module
import sys
from pathlib import Path
sys.path.insert(1, str(Path.cwd()/'latin-macronizer'))
from macronizer import Macronizer

from tqdm import tqdm

BOUNDARY = '/'

class Processor:
	
	def __init__(self):
		self.macronizer = Macronizer()
		self.syllabifier = Syllabifier()
	
	def macronize(self, text):
		return self.macronizer.macronize(text, domacronize=True, alsomaius=False, performutov=True, performitoj=True, markambigs=False)
	
	def clean(self, word):
		voiceless = '([ptcćqsf])'
		vowel = '([aeiouyāēīōūȳ])'
		
		word = word.lower().strip('.,!?:;-')
		
		word = re.sub(f'b{voiceless}', r'p\1', word) # b → p / _ voiceless
		word = re.sub(f'd{voiceless}', r't\1', word) # d → t / _ voiceless
		word = re.sub('qu', 'ć', word) # represent kʷ as ć
		word = re.sub(f'ngu{vowel}', r'nǵ\1', word) # represent gʷ as ǵ
		word = re.sub('ću', 'cu', word) # kʷ → k / _ u
		word = re.sub('ǵu', 'gu', word) # gʷ → g / _ u
		word = re.sub('x', 'cs', word) # represent sequence ks as cs
		word = re.sub('k', 'c', word) # both represent voiceless velar stop
		word = re.sub(f'{vowel}j{vowel}', r'\1jj\2', word) # intervocalic j double
		word = re.sub(f'{vowel}z{vowel}', r'\1zz\2', word) # intervocalic z double
	#	word = re.sub('rh', 'r', word) # TODO: was RH pronounced?
		
		word = re.sub(f'ic(i|ī|ere)', r'jic\1', word) # The macronizer handles most instances of j, but not "hidden" j before i (which only appears in compounds of jaciō with vowel reduction)
		
		word = re.sub(f'i{vowel}', r'iq\1', word) # Hacky workaround - put q after an actual i to make sure the syllabifier doesn't treat it as a j
		word = re.sub('(nc|mp)t', r'\1qt', word) # Another hacky workaround - the syllabifier gets these wrong
		
		return word
	
	def clean2(self, syls): # Hacky workaround for syllabifier bugs
		def is_vowelless(syl):
			return not any(v in syl for v in 'aeiouyāēīōūȳ')
		
		# We have two things to fix here: we should remove all Qs (which are used as separators in cases where we need to override the syllabifier), and when we see something like sum/p/tus, we should correct that to sump/tus.
		def clean_syl(syl, succ): # Takes a syllable and its successor
			syl = syl.replace('q', '')
			succ = succ.replace('q', '')
			if is_vowelless(syl): return ''
			if is_vowelless(succ): return syl+succ
			return syl
		
		syls.append('')
		# This mess of a line just calls clean_syl on every pair and gathers the results into a list, ignoring any blanks that come through
		return list(filter(None, (clean_syl(s1,s2) for (s1,s2) in zip(syls,syls[1:]))))
	
	def syllabify(self, word):
		return self.syllabifier.syllabify(word)
	
	def process(self, text):
		text = self.macronize(text)
		words = text.split()
		for word in tqdm(words, disable=(len(words)<10)):
			print(f'({word})')
			word = self.clean(word)
			print(f'({word})')
			syls = self.syllabify(word)
			syls = self.clean2(syls)
			yield BOUNDARY.join(syls)

if __name__ == '__main__':
	p = Processor()
	while True:
		print(' '.join(p.process(input('>'))))
