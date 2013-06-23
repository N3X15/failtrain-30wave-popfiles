import os,sys,re,io,logging,string

spawnpoints = []
entities=[]
entityBlocks = re.compile(b"\{\n[A-Za-z0-9/\-:.,_$%'()\[\]<> \n\"]+\n\}\n")
REG_DATA=re.compile(r'"([^"]+)" "([^"]+)"')

def process(stream):
    data = stream.read()
    return entityBlocks.findall(data)

def scanForEntities(file):
	i=0
	logging.info("Opening {0}...".format(file))
	with open(file,'rb') as stream:
		for block in process(stream):
			i+=1
			inEntity=False
			entityData={}
			#logging.info("FOUND BLOCK: {0}".format(repr(block)))
			strBlock = block.decode()
			for match in REG_DATA.findall(strBlock):
				i+=1
				#print(repr(match))
				entityData[match[0]]=match[1]
			entities.append(entityData)
	logging.info("Processed {0} blocks.".format(i))

def findSpawnpoints():
	for entity in entities:
		# "classname" "info_player_teamspawn"
		if "classname" in entity and entity['classname'] == 'info_player_teamspawn':
			if 'targetname' not in entity:
				continue
			if 'TeamNum' not in entity:
				continue
			if entity['TeamNum'] != '3':
				continue
			spawnpoint=entity['targetname']
			if spawnpoint not in spawnpoints:
				spawnpoints.append(spawnpoint)
	logging.info("Processed {0} entities and found {1} unique spawnpoints.".format(len(entities),len(spawnpoints)))


logging.basicConfig(format='%(asctime)s [%(levelname)-8s]: %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p', level=logging.DEBUG)

scanForEntities(sys.argv[1])
findSpawnpoints()

outfile =  os.path.splitext(os.path.split(sys.argv[1])[1])[0]+'.spawns.txt'
with open(outfile,'w') as f:
	for spawnpoint in sorted(spawnpoints):
		f.write(spawnpoint+"\n")
