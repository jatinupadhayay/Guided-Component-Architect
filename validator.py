import json
import re
from typing import List, Tuple, Dict, Optional

class CodeValidator:
    
    def __init__(self, design_system: Dict):
        self.design_system = design_system

    def validate(self, raw_json: str) -> Tuple[List[str], Optional[Dict]]:
        errors = []
        try:
            # Clean possible markdown wrapping
            cleaned_json = re.sub(r"```json\n?|\n?```", "", raw_json).strip()
            code_dict = json.loads(cleaned_json)
        except json.JSONDecodeError:
            return ["Invalid JSON format or non-JSON output generated."], None

        # Check for required parts (CSS can be an empty string — that's valid)
        for part in ["html", "typescript"]:
            if part not in code_dict or not code_dict[part]:
                errors.append(f"Missing or empty component part: {part}")
        if "css" not in code_dict:
            errors.append("Missing component part: css")


        if not errors:
            errors.extend(self._check_syntax(code_dict))
            errors.extend(self._check_design_compliance(code_dict))

        return errors, code_dict

    def _check_syntax(self, code_dict: Dict) -> List[str]:
        syntax_errors = []
        for key in ["typescript", "css"]:
            content = code_dict.get(key, "")
            if content.count("{") != content.count("}"):
                syntax_errors.append(f"Unbalanced curly braces in {key}")
            if content.count("(") != content.count(")"):
                syntax_errors.append(f"Unbalanced parentheses in {key}")
        return syntax_errors

    def _check_design_compliance(self, code_dict: Dict) -> List[str]:
        design_errors = []
        tokens = self.design_system.get("tokens", {})
        
        # Check for primary color usage as a mandatory requirement
        primary_color = tokens.get("primary-color", "").lower()
        full_code = (code_dict.get("html", "") + code_dict.get("css", "")).lower()
        
        if primary_color and primary_color not in full_code:
            design_errors.append(f"Design Token Violation: Primary color '{primary_color}' was not used.")
            
        return design_errors
