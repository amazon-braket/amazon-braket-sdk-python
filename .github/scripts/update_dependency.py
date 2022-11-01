import fileinput
from pathlib import Path


package = 'amazon-braket-sdk'
path = Path.cwd().parent.resolve()
print(f"Current path is {path}")

print("Contents are")
for p in Path(path).iterdir():
    print(p)

for line in fileinput.input('setup.py', inplace=True):
	replaced_line = line if package not in line else f'\"{package} @ file://{path}/{package}-python\",\n'
	print(replaced_line, end='')

with open('setup.py', 'r') as f:
    print(f.read())

