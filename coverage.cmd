cd src
rd /S /Q htmlcov
rem coverage-3.9 erase
coverage-3.9 run -m unittest discover -s ../tests 
coverage-3.9 report -m
coverage-3.9 html
start ./htmlcov/index.html

