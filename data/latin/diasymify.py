# Take a corpus from corpus.py and turn it into proper input to DiaSim

from enum import Enum
import bz2
import pickle
import csv
import re
from pathlib import Path
import subprocess as sp
import random

from tqdm import tqdm, trange

from trie import Trie
from undiasimify import FrenchWord

class Stress(Enum):
	NONE = ''
	PRIMARY = 'ˈ'
	SECONDARY = 'ˌ'

LATIN_TO_IPA = {
	'a':'ɑ',
	'v':'w',
	'g':'ɡ',
	'c':'k',
	
	'κ':'k w',
#	'qv':'k w', # Caused by an error in the corpus, now corrected
	'q':'k', # Should never happen, but can due to macronization errors
	'γ':'ɡ w',
	'th':'t̪ʰ',
	'ph':'pʰ', # Not actually found in FLLex but appears in Greek loans; according to symbolDefs.csv their system can handle it
	'ch':'kʰ',
	
	'ā':'ɑː',
	'ē':'eː',
	'ī':'iː',
	'ō':'oː',
	'ū':'uː',
	'ȳ':'yː',
	'ae':'a e̯', # Slightly idiosyncratic representation of diphthongs but we work with what DiaSim wants
	'oe':'o e̯',
	'au':'ɑ w',
	
	't':'t̪',
	'd':'d̪',
	'n':'n̪',
}
LATIN_TO_IPA.update({c:c for c in 'befhijklmoprsuwyz'}) # These need no change - w shouldn't be in there but occasionally appears in the corpus for unknown reasons and it seems like it should always correspond to [w]
LATIN_TO_IPA = Trie(LATIN_TO_IPA) # Prefix tree for greedy translit

class LatinSyllable: # Represents one Latin syllable to convert to IPA for DiaSim
	def __init__(self, sounds, stress=Stress.NONE):
		self.sounds = sounds
		self.stress = stress
	
	def is_heavy(self):
		match = re.fullmatch(r'(.*)([aeiouyāēīōūȳ]+)(.*)', self.sounds)
		if not match: raise ValueError('Could not parse syllable', self.sounds)
		onset, nucleus, coda = match.group(1, 2, 3)
		if len(nucleus) > 1 or nucleus in set('āēīōūȳ'):
			return True
		if coda:
			return True
		return False
	
	def output(self):
		out = ' '.join(LATIN_TO_IPA.tokenize(self.sounds))
		if self.stress:
			out = re.sub(r'([ɑaeiouy])', fr'{self.stress.value}\1', out, count=1) # Insert stress before the first vowel in the syllable
		return out

class LatinWord: # Represents a sequence of Latin syllables that we're converting to IPA for DiaSim
	def __init__(self, sylls):
		if isinstance(sylls, str): sylls = sylls.split('-')
		self.sylls = [LatinSyllable(s) for s in sylls]
		self.handle_stress()
	
	def handle_stress(self): # DiaSim wants primary stress marked on the stressed syllable, and secondary stress marked on the initial syllable
		self.sylls[0].stress = Stress.SECONDARY
		if len(self.sylls) < 3: # Stress initial
			self.sylls[0].stress = Stress.PRIMARY
		elif self.sylls[-2].is_heavy(): # Stress penult if heavy
			self.sylls[-2].stress = Stress.PRIMARY
		else: # Stress antepenult otherwise
			self.sylls[-3].stress = Stress.PRIMARY
	
	def output(self):
		return ' '.join(s.output() for s in self.sylls)

class Lemma: # Represents a Latin word and its frequency
	def __init__(self, latin, count):
		self.latin = latin
		self.count = count
		self.ipa_wide = LatinWord(latin).output()
		self.ipa = re.sub(' ', '', self.ipa_wide)
	
	def __hash__(self): # IPA is considered the key because that's the only part that survives the round trip through DiaSim so that's what we need to identify it by
		return hash(self.ipa)

class Corpus:
	def __init__(self, counts=None):
		self.data = {}
		self.reflexes = {}
		warnings = []
		self.ids = {}
		
		if not counts: return
		for word, freq in tqdm(counts.items()):
			lemma = Lemma(word, freq)
			if lemma.ipa in self.data:
				txt = f'Warning: Two words with same IPA: {lemma.ipa} {lemma.latin} {self.data[lemma.ipa].latin}'
	#			print(txt)
				warnings.append(txt)
				self.data[lemma.ipa].count += lemma.count
			else:
				self.data[lemma.ipa] = lemma
		
		with open('corpuswarnings.log', 'w') as f:
			f.write('\n'.join(warnings))
	
	@classmethod
	def from_file(cls, fn):
		opener = bz2.open if str(fn).endswith('bz2') else open
		with opener(fn, 'rb') as f:
			d = pickle.load(f)
		if isinstance(d, Corpus): return d
		return cls(d)
	
	def save_file(self, fn):
		opener = bz2.open if str(fn).endswith('bz2') else open
		with opener(fn, 'wb') as f:
			pickle.dump(self, f)
	
	def save_lexes(self, fn, chunksize=10000):
		fn = Path(fn) # In case a string was passed
		fn.mkdir(parents=True, exist_ok=True) # This is the directory we'll put our output data in
		biglist = list(self.data.values())
		for i, start in enumerate(trange(0, len(biglist), chunksize)):
			chunk = biglist[start:start+chunksize]
			with open(fn / f'{i}.lex', 'w') as f:
				for lemma in chunk:
					f.write(f'{lemma.ipa_wide} $ {lemma.latin}\n')
	
	def add_reflexes(self, fn): # Wrapper that can take a directory instead of a file for convenience
		fn = Path(fn)
		if fn.is_dir():
			for child in tqdm(list(fn.glob('**/*_output_graph.csv'))):
				self.add_reflexes_single(child)
		else:
			self.add_reflexes_single(fn)
	
	def add_reflexes_single(self, fn):
		fn = Path(fn)
		with open(fn, 'r', newline='') as f:
			reader = csv.reader(f, delimiter='|')
			firstline = next(reader)
			headers = [x.strip() for x in firstline]
			eras = headers[1:] + ['Classical No Stress', 'Classical KW No Stress']
			if hasattr(self, 'eras') and self.eras != eras: raise ValueError('Mismatched eras', self.eras, eras, fn)
			self.eras = eras
			
			for line in tqdm(reader, total=10000, disable=True): # Set to default chunk size for now
				fields = [x.strip(' #') for x in line]
				fields[0] = int(fields[0]) # ID number
				ipa = fields[1]
				self.ids[ipa] = fn.parent.name+'_'+str(fields[0])
				# Copy in the reflex from each era
				self.reflexes[ipa] = {h:FrenchWord(f) for h,f in zip(headers[1:], fields[1:])}
				# Then put in two special ones
				self.reflexes[ipa]['Classical No Stress'] = FrenchWord(ipa, stress=False)
				self.reflexes[ipa]['Classical KW No Stress'] = FrenchWord(ipa, stress=False, kw_correction=True)
	
	def output_corpora(self, fn):
		fn = Path(fn) # In case a string was passed
		fn.mkdir(parents=True, exist_ok=True) # This is the directory we'll put our output data in
		for era in tqdm(self.eras):
			dout = { self.reflexes[id][era].output(sep='-') : self.data[id] for id in self.data } # reflex : count
			with bz2.open(fn / (era + '.pickle.bz2'), 'wb') as f:
				pickle.dump(dout, f)
	
	def output_csv(self, fn):
		headings = ['ID'] + self.eras
		with open(fn, 'w', newline='') as f:
			write = csv.writer(f)
			write.writerow(headings)
			for id in tqdm(self.data):
				row = [self.ids[id]] + [self.reflexes[id][era].output() for era in self.eras]
				write.writerow(row)

def filelen(fn): # Let's see if this can work with tqdm
	with open(fn, 'r') as f:
		return len(f)

DIASIMDIR = (Path(__file__) / '..' / '..' / '..' / 'DiaSim').resolve()
DIACLEF = Path('./DiaCLEF_Black').resolve()
def run_diasim_on(lexfn, outdir, cwd=DIASIMDIR, clef=DIACLEF, replace=False):
	lexfn = Path(lexfn).resolve()
	outdir = Path(outdir).resolve()
	outfn = outdir / lexfn.stem
	process = cwd / 'derive.sh'
#	print(lexfn, outdir, outfn, cwd)
	if (outfn / 'derivation').exists() and not replace: # This file isn't filled in until the end so we can confirm it ran fully and wasn't interrupted
		print(f'(Skipped existing {lexfn.stem})')
		return
	print(f'Working on {lexfn.stem}...')
	outfn.mkdir(parents=True, exist_ok=True) # So that we can stick stdout and stderr files in there
	with open(outfn/'out.log', 'w') as outf:
		with open(outfn/'err.log', 'w') as errf:
			sp.run([process, '-lex', lexfn, '-rules', clef, '-out', outfn], cwd=cwd, stdout=outf, stderr=errf)

def run_diasim(lexdir, outdir, cwd=DIASIMDIR, replace=False, shuffle=True):
	lexdir = Path(lexdir)
	targets = list(lexdir.iterdir())
	if shuffle: random.shuffle(targets) # Means if we run this script multiple times at once we can do calculations in parallel
	for lexfn in tqdm(targets):
		run_diasim_on(lexfn, outdir, cwd=cwd, replace=replace)

if __name__ == '__main__':
	input()
	c = Corpus.from_file('phi5_diachronic.pickle.bz2')
#	c = Corpus.from_file('phi5.pickle.bz2')
	print('Corpus loaded')
#	c.save_lexes('phi5_lex') # directory
#	print('Lexes output')
#	run_diasim('./phi5_lex', './phi5_diasim')
#	print('DiaSim run')
#	c.add_reflexes('./phi5_diasim')
#	print('Reflexes loaded')
	c.output_corpora('phi5_diachronic')
	print('Individual corpora output')
#	c.save_file('phi5_diachronic.pickle.bz2')
#	print('Complete corpus output')
	c.output_csv('phi5_diachronic.csv')
	print('CSV output')
