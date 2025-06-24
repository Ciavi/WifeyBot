import json


class Configuration:
    conf_path: str
    conf_raw_json: object

    def __init__(self, path: str):
        self.conf_path = path
        with open(path, 'r') as file:
            data = json.load(file)
            for key, value in data.items():
                if isinstance(value, dict):
                    sub_config = Configuration(None)
                    for sub_key, sub_value in value.items():
                        setattr(sub_config, sub_key, sub_value)
                    setattr(self, key, sub_config)
                else:
                    setattr(self, key, value)

    def __str__(self):
        return json.dumps(self.__dict__, indent=4)