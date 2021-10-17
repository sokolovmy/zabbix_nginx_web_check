cd ../src
echo %TEMP%
@echo remove old data
@rd /S /Q htmlcov
@del .coverage
@coverage erase
coverage run -m unittest discover -s ../tests
coverage report -m
coverage html
start ./htmlcov/index.html

