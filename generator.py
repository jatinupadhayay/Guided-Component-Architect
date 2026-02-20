import json

def load_design_system():
    with open("design-system.json", "r") as f:
        return json.load(f)
