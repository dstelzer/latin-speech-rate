#!/usr/bin/env python3

import csv
import pickle
import bz2

params = {
	'delimiter' : '\\',
	'escapechar' : '\x1b', # ASCII escape character - will never appear
#	'quotechar' : '\x0e', # "Shift Out", does nothing
	'strict' : True,
	'quoting' : csv.QUOTE_NONE, # Ensure it doesn't misinterpret quote marks
}

params2 = {
	'delimiter' : '\t',
	'escapechar' : '\x1b',
	'strict' : True,
	'quoting' : csv.QUOTE_NONE,
}

INFILE = 'data.csv'
OUTFILE = 'english.pickle.bz2'
COUNTER = 'CobW'

alphabetic = 'abcdefghijklmnopqrstuvwxyz'

def do_processing(parameters=params, infile=INFILE, outfile=OUTFILE, counter=COUNTER):
	with open(infile, 'r', newline='') as inf:
		read = csv.DictReader(inf, **parameters)
		data = []
		count = 0
		tokens = 0
		printed = False
		for row in read: # This could be a comprehension but that makes it hard to get both `count` and the filtered `data`
		#	if int(row[COUNTER]): data.append(dict(row))
			if not printed:
				print('Keys:', ', '.join(row.keys()))
				printed = True
			count += 1
			tokens += int(row[counter])
		#	if any(c not in alphabetic for c in row['Word'].lower()): continue # Oh's thesis indicates that words with nonalphabetics were removed
			data.append(dict(row))
		print('First line:', data[0])
		with bz2.open(outfile, 'wb') as outf:
			pickle.dump(data, outf)
		print(f'{count} forms read; {len(data)} saved')
		print(f'Tokens: {tokens}')
