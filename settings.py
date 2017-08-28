import json
import os

# Load settings from filepath.
# Returns dict on success.
# Returns None if new settings file created.
def loadSettings(filepath):
    # create settings file if it doesn't exist
    if not os.path.isfile(os.path.abspath(filepath)):
        with open(filepath, 'w') as file_obj:
            file_obj.write('{}')
            return None

    # read settings from file and convert to python dict
    with open(filepath) as file_obj:
        file_contents = file_obj.read()
        settings_dict = json.loads(file_contents)
        return settings_dict

# save settings_dict to filepath as json
def saveSettings(filepath, settings_dict):
    with open(filepath, 'w') as file_obj:
        file_obj.write(json.dumps(settings_dict, sort_keys=True, indent=4))
