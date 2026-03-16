import yaml
import re
import os

def load_rules(filepath: str) -> list:
    if not os.path.exists(filepath):
        return []
    
    with open(filepath, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    
    rules = (data or {}).get("rules", [])
    
    # kompilasi regex supaya lebih efisien saat pencocokan
    for rule in rules:
        if rule.get("operator") == "regex" and "pattern" in rule:
            rule["compiled_pattern"] = re.compile(
                rule["pattern"], re.IGNORECASE
            )
    
    return rules