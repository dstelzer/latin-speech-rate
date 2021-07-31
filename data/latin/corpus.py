from pathlib import Path
import re
from time import sleep
import random
import pickle
import bz2
from collections import Counter

from cltk.corpus.utils.formatter import assemble_phi5_author_filepaths, assemble_phi5_works_filepaths
from cltk.corpus.utils.formatter import phi5_plaintext_cleanup
from cltk.corpus.latin.phi5_index import PHI5_INDEX

from tqdm import tqdm, trange

from process import Processor

# Authors with large numbers of words
IMPORTANT_AUTHORS = {
	'LAT0474', # Cicero - possibly should be removed from consideration because he singlehandedly has over a million words in the corpus, and is definitional to classical Latin style
#	'LAT2806', # Justinian (Digesta) - excluded below for being an outlier, due to the formulaic nature of legal precedents
	'LAT0914', # Livy
	'LAT0978', # Pliny
	'LAT2349', # Servius
	'LAT1017', # Seneca Jr
	'LAT1002', # Quintilian
	'LAT0959', # Ovid
	'LAT0119', # Plautus
	'LAT1351', # Tacitus
	'LAT1254', # Gellius
	'LAT0845', # Columella
	'LAT2331', # Scriptores Historiae Augustae
	'LAT1212', # Apuleius
	'LAT0836', # Celsus
	# The above are all authors with more than 100k words in the corpus
#	'LAT2806', # Including Justinian again just as a demonstration - remove when running on `auth` rather than `auth_all`
}

GLOBAL_EXCLUSIONS = {
	'LAT9999', # A bibliography file that should not be included
	'LAT2806', # Justinian's Digesta, which is an outlier that pulls the whole value down
}

class PHI5Corpus:
	
	def __init__(self):
		pass
	
	def get_filenames(self, limit=None, authorial=True, chance=1.0, exclude=(), include=None, shuffle=False):
		
		def chosen(fn): # Random chance of selection
			stem = Path(fn).stem
			if stem in GLOBAL_EXCLUSIONS: return False
			if stem in exclude: return False
			if include is not None and stem not in include: return False
			if not (random.random() < chance): return False
			return True
		
		paths = assemble_phi5_author_filepaths() if authorial else assemble_phi5_works_filepaths()
	#	print('\n'.join(paths))
	#	input()
		if limit is not None: paths = paths[:limit]
		
		paths = [Path(fn) for fn in paths if chosen(fn)]
		if shuffle: random.shuffle(paths)
		return paths
	
	def get_text(self, fn):
		with open(fn, 'r') as f:
			text = f.read()
		text = phi5_plaintext_cleanup(text)
		text = re.sub(r'\b[IVXLCM]+\b', '', text) # Remove Roman numerals
		text = re.sub(r'\bdrach(m?)\.', 'drachmae', text) # Deal with a common abbreviation
		return text
	
	def get_name(self, fn):
		name = fn.stem
		if name not in PHI5_INDEX: raise ValueError(name, fn)
		return PHI5_INDEX[name]
	
	def test(self):
		for fn in self.get_filenames(10):
			text = self.get_text(fn)
			print(text)
			input()
	
	def get_author_data(self):
		data = {}
		proc = Processor()
		for fn in tqdm(self.get_filenames(authorial=True)):
			name = self.get_name(fn)
			text = self.get_text(fn)
			words = text.split()
			id = fn.stem
			tag = (name, id)
			
			data[tag] = 0
			for word in words: # Count how many words survive proc.clean
				if proc.clean(word):
					data[tag] += 1
		
		return data
	
	def process_and_save(self, fn, check=False, precomputed=None, overwrite=True, hack_notes=False, **kwargs):
		if fn is not None and Path(fn).exists() and not overwrite:
			print(f'({fn} already exists, skipping it and moving on)')
			return
		
		if hack_notes:
			with open('hack_notes.csv', 'w') as f:
				f.write('Author,Count,Prev,Next\n')
		
		if precomputed is None: # Allow passing in a Processor instance that's already done some analysis
			proc = Processor()
		else:
			proc = precomputed.copy()
		
		for fn2 in tqdm(self.get_filenames(**kwargs)):
			text = self.get_text(fn2)
			prev = sum(proc.total_counts.values())
			proc.count(text)
			new = sum(proc.total_counts.values())
			if hack_notes:
				with open('hack_notes.csv', 'a') as f:
					f.write(f'{fn2.stem},{prev},{new},{new-prev}\n')
			sleep(0.25) # Return control to the system occasionally so things don't crash (just in case)
		if check:
			with open('phi5.full.tsv', 'w') as f:
				for word, count in proc.total_counts.most_common():
					f.write(f'{count}\t{word}\n')
			with open('phi5.exc.tsv', 'w') as f:
				for word, count in proc.total_counts.most_common(1000):
					f.write(f'{count}\t{word}\n')
		
		if fn is not None:
			proc.save(fn)
		return proc # In case it's wanted for later processing

def main_run_complete():
	input()
	PHI5Corpus().process_and_save('phi5_new.pickle.bz2', authorial=True, shuffle=False)

def main_run_probability():
	input()
	for i in trange(10):
		PHI5Corpus().process_and_save(f'90/{i:02d}.pickle.bz2', chance=0.9)

def main_run_complete_hack(): # Like main_run_complete but using a checkpoint
	input()
	c = PHI5Corpus()
	pfn = Path('author_checkpoint.pickle.bz2')
	if not pfn.exists(): raise ValueError('No checkpoint to load from')
	with bz2.open(pfn, 'rb') as f:
		proc = Processor()
		proc.total_counts = pickle.load(f)
	c.process_and_save(f'phi5.pickle.bz2', authorial=True, include=IMPORTANT_AUTHORS, precomputed=proc, overwrite=True, shuffle=True)

def main_run_authors():
	input()
	c = PHI5Corpus()
	# First, do the processing without any important authors
	pfn = Path('author_checkpoint.pickle.bz2')
	if pfn.exists():
		with bz2.open(pfn, 'rb') as f:
			proc = Processor()
			proc.total_counts = pickle.load(f)
		print('(Opened existing checkpoint)')
	else:
		proc = c.process_and_save(None, authorial=True, exclude=IMPORTANT_AUTHORS)
		with bz2.open(pfn, 'wb') as f:
			pickle.dump(proc.total_counts, f)
		print('(Checkpoint saved)')
	# Then, go through and process the set of important authors, minus each one individually
	for auth in tqdm(IMPORTANT_AUTHORS):
		print(f'Working on {auth}')
		c.process_and_save(f'auth_all/{auth}.pickle.bz2', authorial=True, include=IMPORTANT_AUTHORS-{auth}, precomputed=proc, overwrite=False, shuffle=True)

def main_run_authors_redux():
	input()
	c = PHI5Corpus()
	with bz2.open('phi5_new.pickle.bz2', 'r') as f:
		complete = Counter(pickle.load(f))
	for auth in tqdm(list(Path('auth_solo').glob('*.pickle.bz2'))):
		with bz2.open(auth, 'r') as f:
			d = Counter(pickle.load(f))
		new = complete - d
		if sum(new.values()) != sum(complete.values()) - sum(d.values()):
			raise ValueError(sum(new.values()), sum(complete.values()), sum(d.values()))
		path = Path('auth_new') / auth.name
		with bz2.open(path, 'w') as f:
			pickle.dump(dict(new), f)

# Make a corpus for each author individually
def compute_solo_author_data():
	input()
	path = Path('auth_solo')
	c = PHI5Corpus()
	# Miscellaneous
	c.process_and_save(path/f'MISC.pickle.bz2', authorial=True, exclude=IMPORTANT_AUTHORS, overwrite=False, shuffle=True)
	# Authors
	for auth in tqdm(IMPORTANT_AUTHORS):
		c.process_and_save(path/f'{auth}.pickle.bz2', authorial=True, include=(auth,), overwrite=False, shuffle=True)

# Save an overview of different authors' tokens
def author_data():
	input()
	data = PHI5Corpus().get_author_data()
	with bz2.open('authors.pickle.bz2', 'w') as f:
		pickle.dump(data, f)
	with open('authors.tsv', 'w') as f:
		for (name, id), words in sorted(data.items()):
			f.write(f'{name}\t{id}\t{words}\n')
	print('Done')

# Test calculating different authors' types and tokens.
# THIS ONE DOES NOT WORK PROPERLY
def author_data_2():
	input()
	with bz2.open('phi5.pickle.bz2', 'r') as f:
		d_tot = Counter(pickle.load(f))
	c1, c2 = len(d_tot), sum(d_tot.values())
	print('Total', c1, c2)
	for auth in Path('auth').glob('*.pickle.bz2'):
		with bz2.open(auth, 'r') as f:
			d = Counter(pickle.load(f))
		d2 = d_tot - d
		t1, t2 = len(d2), sum(d2.values())
		print(auth.stem, t1, t2)
	for auth in ['author_checkpoint.pickle.bz2']:
		with bz2.open(auth, 'r') as f:
			d = Counter(pickle.load(f))
		t1, t2 = len(d), sum(d.values())
		print(auth, t1, t2)
	input()

# Test calculating different authors' types and tokens.
# THIS ONE WORKS
def author_data_3():
	with bz2.open('phi5_new.pickle.bz2', 'r') as f:
		d_tot = pickle.load(f)
	c1, c2 = len(d_tot), sum(d_tot.values())
	print('Total', c1, c2)
	for auth in Path('auth_solo').glob('*.pickle.bz2'):
		with bz2.open(auth, 'r') as f:
			d = pickle.load(f)
		t1, t2 = len(d), sum(d.values())
		print(auth.stem, t1, t2)
		c1 -= t1; c2 -= t2
	print('Unaccounted for', c1 if c1>0 else 0, c2)
	input()

def author_data_misc():
	with bz2.open('author_checkpoint.pickle.bz2', 'r') as f:
		d = pickle.load(f)
	c1, c2 = len(d), sum(d.values())
	print('Misc', c1, c2)
	input()

if __name__ == '__main__': author_data()
