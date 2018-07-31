#! /bin/bash
pip3 install requests
pip3 install python-dateutil --upgrade
pip3 install bs4
echo Please wait while we display the current trends in the provided date range
python webScraper.py "$1" "$2"
if [ -d "Result" ]
then
	for file in Result/*
	do
		open "$file"
	done
fi