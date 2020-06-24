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

INFILE = 'data'
OUTFILE = 'german'
COUNTER = 'Mann'

with open(f'{INFILE}.csv', 'r', newline='') as inf:
	read = csv.DictReader(inf, **params)
	data = []
	count = 0
	for row in read: # This could be a comprehension but that makes it hard to get both `count` and the filtered `data`
	#	if int(row[COUNTER]): data.append(dict(row))
		data.append(dict(row))
		count += 1
	print(data[0])
	with bz2.open(f'{OUTFILE}.pickle.bz2', 'wb') as outf:
		pickle.dump(data, outf)
	print(f'{count} forms read; {len(data)} saved')
