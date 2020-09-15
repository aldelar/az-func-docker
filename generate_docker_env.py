import json

config_json = json.load(open('local.settings.json'))['Values']
config_env = open('local.settings.env','w')

for key in config_json:
    config_env.write(key+'='+config_json[key]+'\n')