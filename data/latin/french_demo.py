import re
from functools import cache

from tqdm import tqdm

import sys
sys.path.insert(1, '../../../CLTK/cltk/')

from process import Processor, VALID
from diasimify import LatinWord, Corpus, Lemma
from undiasimify import orthographize

class Frenchifier:
	def __init__(self, corpus, era='Input'):
		self.corpus = corpus
		self.era = era
		self.proc = Processor()
	
	@cache
	def ipaify(self, word):
		clean = self.proc.clean(word)
		if not clean: return None
		syls = self.proc.syllabify(clean)
		ipa = LatinWord(syls).output()
		return re.sub(' ', '', ipa) # Remove spaces; this is the best way
	
	def convert_word(self, word, ortho=False):
		# word should match \w+
		ipa = self.ipaify(word)
		if ipa is None: return word
		if ipa not in self.corpus.reflexes:
			raise KeyError(word, ipa)
		if ortho:
			return ''.join(orthographize(self.corpus.reflexes[ipa][self.era].output(sep='')))
		return self.corpus.reflexes[ipa][self.era].output(sep='.') # Standard syllable delimiter
	
	def convert_text(self, text, era=None, ortho=False):
		if era: self.era = era
		text = self.proc.macronize(text)
		units = re.split(r'([a-zA-ZāēīōūȳĀĒĪŌŪȲ]+)', text)
		res = []
	#	print(units)
		for i, unit in enumerate(tqdm(units)):
			if i%2: unit = self.convert_word(unit, ortho) # With re.split, odd-numbered units are matches, even-numbered units are in-betweens (potentially including empty strings to make the numbers line up)
			res.append(unit)
		return ''.join(res)
	
	def convert_text_multi(self, text):
		d = { era:self.convert_text(text, era) for era in self.corpus.eras }
		d['French Ortho'] = self.convert_text(text, 'Output {GOLD}', True)
		return d
	
	def convert_file(self, fn):
		with open(fn, 'r') as f:
			return self.convert_text(f.read())
	
	def convert_file_multi(self, fn):
		with open(fn, 'r') as f:
			return self.convert_text_multi(f.read())

if __name__ == '__main__':
	f = Frenchifier(Corpus.from_file('phi5_diachronic.pickle.bz2'))
	print('Ready')
	data = f.convert_file_multi('demo_latin.txt')
	print('Converted')
	with open('demo_french.txt', 'w') as f:
		f.write('\n\n'.join(k.upper()+'\n'+v for k,v in data.items()))
	print('Saved')
