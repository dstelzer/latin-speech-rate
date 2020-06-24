#!/bin/sh

# Convert <br> to \n, remove the first three lines, remove the last three lines
sed 's/<br>/\n/g' WebCelex.html | sed 's:<html>.*</center>::' | tail -n +3 | head -n -3 > data.csv
grep -v "\\\\" data.csv || echo "Everything okay!"
wc -l data.csv

# Goal: 160xxx (596?)
# Columns that work: Word, Cob, IdNum, PhonStrsCLX, PhonStrsCPA, PhonStrsSAM
