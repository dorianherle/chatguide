import yaml
import json

def read_yaml_to_dict(file_path):
    with open(file_path, 'r') as file:
        data = yaml.safe_load(file)
    return data

# Example usage
if __name__ == "__main__":
    config_dict = read_yaml_to_dict('chatbot_config.yaml')
    # pretty print the config_dict
    print(json.dumps(config_dict, indent=4))
