from pathlib import Path
import re
from time import sleep

from cltk.corpus.utils.formatter import assemble_phi5_works_filepaths
from cltk.corpus.utils.formatter import phi5_plaintext_cleanup

from tqdm import tqdm

from process import Processor

class PHI5Corpus:
	
	def __init__(self):
		pass
	
	def get_filenames(self, limit=None):
		paths = assemble_phi5_works_filepaths()
		if limit is not None: paths = paths[:limit]
		return [Path(fn) for fn in paths]
	
	def get_text(self, fn):
		with open(fn, 'r') as f:
			text = f.read()
		text = phi5_plaintext_cleanup(text)
		text = re.sub(r'\b[IVXLCM]+\b', '', text) # Remove Roman numerals
		text = re.sub(r'\bdrach(m?)\.', 'drachmae', text) # Deal with a common abbreviation
		return text
	
	def test(self):
		for fn in self.get_filenames(10):
			text = self.get_text(fn)
			print(text)
			input()
	
	def process_and_save(self, fn):
		proc = Processor()
		for fn2 in tqdm(self.get_filenames()):
			text = self.get_text(fn2)
			proc.count(text)
			sleep(0.25) # Return control to the system occasionally so things don't crash (just in case)
		with open('phi5.full.tsv', 'w') as f:
			for word, count in proc.total_counts.most_common():
				f.write(f'{count}\t{word}\n')
		with open('phi5.exc.tsv', 'w') as f:
			for word, count in proc.total_counts.most_common(1000):
				f.write(f'{count}\t{word}\n')
		proc.save(fn)

if __name__ == '__main__':
	input()
	PHI5Corpus().process_and_save('phi5.pickle.bz2')
