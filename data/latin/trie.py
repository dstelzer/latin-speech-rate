# Super basic trie (prefix tree) implementation scavenged from another project
# Should be easy to replace later if needed
# But this is an easy way to do greedy transliteration

from collections import defaultdict

def TrieNode(): return defaultdict(TrieNode)

class Trie:
	def __init__(self, data=None):
		self.root = TrieNode()
		
		if data:
			self.extend(data)
	
	def extend(self, data):
		for k, v in data.items():
			self.insert(k, v)
	
	def insert(self, key, value):
		stem = self.root
		for step in key:
			stem = stem[step]
		if None in stem:
			raise KeyError('{}/{}: key exists with value {}'.format(key, value, stem[None]))
			return
		stem[None] = value
	
	def findlongest(self, key):
		letters_last = 0
		value_last = None
		letters_now = 0
		
		stem = self.root
		
		for letter in key:
			if letter not in stem:
				if None in stem:
					return stem[None], letters_now
				else:
					return value_last, letters_last
			else:
				stem = stem[letter]
				letters_now += 1
				if None in stem:
					letters_last = letters_now
					value_last = stem[None]
		return value_last, letters_last
	
	def tokenize(self, text, *, default=None):
		while text:
			token, eaten = self.findlongest(text)
			
			if eaten == 0: # Problem: didn't find it!
				if default is not None:
					if isinstance(default, str): # This is a string
						v = default
					else: # Otherwise it should be a routine
						v = default(text[0])
					
					text = text[1:] # Skip one character
					yield v # and return the default value
					continue
				else:
					raise ValueError(text[:10]+('...' if len(text) > 10 else '')) # Didn't find any match!
			
			text = text[eaten:]
			yield token
	
	def __iadd__(self, other):
		self.extend(other)
		return self
