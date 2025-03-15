# This program processes all archiving tasks

import os, shutil,configparser, subprocess, difflib, json, filecmp
from pathlib import Path
from datetime import datetime
from tarfile import data_filter

class IndexerException(Exception):
   def __init__(self, message):
        self.message = message
        super().__init__(self.message)

def get_config():
	_config = configparser.ConfigParser()

	try:
		with open(settings_file) as f:
			print("Settings File Detected:\n\t==>", settings_file)
			_config.read_file(f)
	except IOError:
		print("Settings file not found")

	return _config

def get_execution_details():
	data = {}
	details = {}
	# Load existing data
	try:
		with open(data_file, 'r') as file:
			data = json.load(file)
		details = data[exe_id]
		print(f"Processing Collection\n{idtab} {collection.upper()}:{category_type.upper()}")
		if (len(details) == 0):
			print(idtab, "Initial processing detected")
		else:
			print(idtab, f"Last processed on {details['Run Date Time']}")
	except IOError:
		print('WARNING: Missing previous execution data.')
	
	return data,details

def save_execution_details():
	exe_details['Run Date Time'] = timestamp
	
	exe_data[exe_id] = exe_details

	try:
		with open(data_file, 'w') as file:
			json.dump(exe_data, file, indent=4)
	except IOError:
		print('ERROR Saving execution details. Please verify output and loading.')


def run_indexer():
	folder_to_index		= config['Settings']['DocumentFolder']
	index_output_file	= Path(output_dir + '/' + file_prefix + '_Index.csv')
	index_debug_file	= Path(output_dir + '/' + file_prefix + '_Index_Debug.txt')
	index_error_file	= Path(output_dir + '/' + file_prefix + '_Index_Error.csv')
	
	print("Indexing started")
	print(idtab, "Document Folder", folder_to_index)
	
	#Powershell command arguments for indexer script
	ps_command = f"& '{indexer_script}' -foldersPath '{folder_to_index}' -outputCSV '{index_output_file}' "
	ps_command += f"6> '{index_error_file}' "
	ps_command += f"-Debug 5> '{index_debug_file}' " if (config['DEBUG']['indexer'].lower() == 'true') else ""	# Enable debug if set  

	#print(ps_command)

	result = subprocess.run([
		"powershell",
		"-ExecutionPolicy", "Bypass",
		"-Command", ps_command
	])

	# Check if current index generated is identical to last time index generated
	last_idx_identical = False
	last_idx_gen_dt	   = exe_details.get('Last Index Generated')
	if last_idx_gen_dt:
		last_idx_output_file = Path(output_dir + '/' + exe_id + '_' + last_idx_gen_dt + '_Index.csv')
		last_idx_error_file  = Path(output_dir + '/' + exe_id + '_' + last_idx_gen_dt + '_Index_Error.csv')
		if (filecmp.cmp(index_output_file, last_idx_output_file, shallow=False) and
		   filecmp.cmp(index_error_file, last_idx_error_file, shallow=False)):
			last_idx_identical = True
			os.remove(index_output_file)
			os.remove(index_debug_file)
			os.remove(index_error_file)
			print(idtab, "No new documents found since last time indexed.")


	# Check for new items if current index is different from last time
	if not last_idx_identical:
		exe_details['Last Index Generated'] = timestamp
		last_idx_loaded_file		= last_idx_output_file
		newlines = find_new_lines(last_idx_loaded_file, index_output_file)

		print(idtab, 'New Documents Identified   :', len(newlines))

		# Print the new lines in file2
		for line in newlines:
			print(line.strip())


def get_last_file(file_suffix):
	directory = Path(output_dir)
	pattern = f'{collection}_{category_type}_*_{file_suffix}'
	files = list(directory.glob(pattern))

	return max(files, key=extract_timestamp)


def extract_timestamp(file_name):
    # Split the filename and extract the timestamp part (yyyy-mm-dd_hh-mm)
	parts = file_name.stem.split('_')			# Split by underscores
	timestamp_str = parts[3] + '_' + parts[4]	# Concatenate the date and time part

	# Convert it to a datetime object
	return datetime.strptime(timestamp_str, "%Y-%m-%d_%H-%M-%S")

def find_new_lines(file1, file2):
	with open(file1, 'r') as f1, open(file2, 'r') as f2:
		# Read both files
		file1_lines = f1.readlines()
		file2_lines = f2.readlines()

		# Get the differences between the files using unified_diff
		#diff = difflib.unified_diff(file1_lines, file2_lines, fromfile=str(file1), tofile=str(file2))
		diff = difflib.ndiff(file1_lines, file2_lines)
		#print('\n'.join(diff))
		#TODO: It appears once you process the diff, you can't read the same content from it again, it appears to become empty

		# Extract only the new lines that are in file2
		new_lines = [line[1:] for line in diff if line.startswith('+ ')]
		
		if (len(new_lines) >= len(file2_lines)):
			raise IndexerException("Issues detected indexing file. Please verify correct document folder for collection & type")

		return new_lines


# BEGIN PROGRAM SETUP ------------------------------------------------------------------------------------

# Get the execution timestamp
timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
idtab = "\t==>"

# Get script paths
script_dir		= Path(__file__).parent.parent
temp_dir		= script_dir / 'temp'
settings_file	= script_dir / 'settings' / 'archive.ini'
data_file		= script_dir / 'settings' / 'mtiarchiver.dat'
indexer_script	= script_dir / 'powershell' / 'author_document_scan.ps1'

# Get config from settings file
config			= get_config()
output_dir		= config['Settings']['ScriptDataFolder']
collection		= config['Settings']['Collection'].replace(' ','_').lower().strip('"').strip("'")
category_type	= config['Settings']['CategoryType'].replace(' ','_').lower().strip('"').strip("'")

# Setup execution id and file prefix
exe_id		= f'{collection}_{category_type}'
file_prefix = f'{exe_id}_{timestamp}'

# Get the JSON data for previous execution details
exe_data, exe_details = get_execution_details()

# Setup directories
os.makedirs(output_dir, exist_ok=True)		# Output Directory

#shutil.rmtree(temp_dir)
os.makedirs(temp_dir, exist_ok=True)		# Temporary Working Directory

# Get execution data


# END PROGRAM SETUP -------------------------------------------------------------------------------------

try:
	run_indexer()
except IndexerException as ie:
	print("\nAborted Processing!\n    !!! ", ie)

save_execution_details()
