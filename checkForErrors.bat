:: 30wave
python python/fixPopfiles.py src/30wave/mvm_mannworks_30wave.pop -o processed/30wave/mvm_mannworks_30wave.pop -s mvm_mannworks.spawns.txt
python python/fixPopfiles.py src/30wave/mvm_coaltown_30wave.pop -o processed/30wave/mvm_coaltown_30wave.pop -s mvm_coaltown.spawns.txt
python python/fixPopfiles.py src/30wave/mvm_decoy_30wave.pop -o processed/30wave/mvm_decoy_30wave.pop -s mvm_decoy.spawns.txt
python python/fixPopfiles.py src/30wave/mvm_bigrock_30wave.pop -o processed/30wave/mvm_bigrock_30wave.pop -s mvm_bigrock.spawns.txt

:: 7wave
python python/fixPopfiles.py src/7wave/mvm_coaltown_7waves.pop -i includes/robot_standard_7waves.pop includes/robot_giant_7waves.pop -s mvm_coaltown.spawns.txt -o processed/7wave/mvm_coaltown_7waves.pop 
pause