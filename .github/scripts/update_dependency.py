import fileinput
from pathlib import Path


package = 'amazon-braket-sdk'
path = Path.cwd().parent.resolve()
for line in fileinput.input('setup.py', inplace=True):
	replaced_line = line if package not in line else f'\"{package} @ file://{path}\"\n'
	print(replaced_line, end='')

