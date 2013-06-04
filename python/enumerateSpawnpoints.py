import os,sys,re,io

REG_SPAWNPOINT = re.compile(r'[Ww]here\s+([a-zA-Z0-9_-]+)')

spawnpoints = []
i=0
sys.stderr.write("Opening {0}...".format(sys.argv[1]))
with open(sys.argv[1],'r') as r:
	for line in r:
		i+=1
		match=REG_SPAWNPOINT.search(line)
		if match is not None:
			spawnpoint=match.group(1).strip()
			if spawnpoint not in spawnpoints:
				spawnpoints.append(spawnpoint)
				print(spawnpoint)
sys.stderr.write("Processed {0} lines.".format(i))