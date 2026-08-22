"""Tools for the BI Data Visualization Agent."""

import json
import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)


def validate_vega_lite_spec(spec_json: str) -> Dict[str, Any]:
    """Validates a Vega-Lite v5 JSON specification for correctness, data integrity, and structural validity.

    Args:
        spec_json: A JSON string containing the Vega-Lite specification.

    Returns:
        A dictionary with validation status ('VALID' or 'INVALID'), parsed schema details, or error messages.
    """
    try:
        # Strip code fences if present
        clean_json = spec_json.strip()
        if clean_json.startswith("```"):
            lines = clean_json.split("\n")
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            clean_json = "\n".join(lines).strip()

        parsed = json.loads(clean_json)

        if not isinstance(parsed, dict):
            return {
                "status": "INVALID",
                "error": "Specification must be a JSON object (dictionary).",
            }

        # Check essential Vega-Lite top-level keys
        errors = []
        if "$schema" not in parsed:
            parsed["$schema"] = "https://vega.github.io/schema/vega-lite/v5.json"

        if "mark" not in parsed and "layer" not in parsed and "hconcat" not in parsed and "vconcat" not in parsed:
            errors.append("Specification must contain 'mark', 'layer', 'hconcat', or 'vconcat'.")

        if "data" not in parsed:
            errors.append("Specification missing 'data' field.")
        elif isinstance(parsed.get("data"), dict):
            values = parsed["data"].get("values")
            if values is None:
                errors.append("'data' object must contain 'values' array.")
            elif not isinstance(values, list) or len(values) == 0:
                errors.append("'data.values' should be a non-empty list of data records.")

        if errors:
            return {
                "status": "INVALID",
                "errors": errors,
                "suggestion": "Ensure data.values contains the array of extracted records and a valid mark/encoding is defined.",
            }

        data_count = len(parsed.get("data", {}).get("values", []))
        mark_type = parsed.get("mark")
        if isinstance(mark_type, dict):
            mark_type = mark_type.get("type", "custom")

        return {
            "status": "VALID",
            "message": f"Valid Vega-Lite v5 specification with mark '{mark_type}' and {data_count} embedded data records.",
            "mark": mark_type,
            "data_record_count": data_count,
        }

    except json.JSONDecodeError as e:
        logger.warning("Vega-Lite JSON syntax error: %s", e)
        return {
            "status": "INVALID",
            "error": f"JSON syntax error: {str(e)}",
            "suggestion": "Check for trailing commas, unescaped quotes, or mismatched braces.",
        }
    except Exception as e:
        logger.exception("Unexpected error in validate_vega_lite_spec")
        return {
            "status": "INVALID",
            "error": str(e),
        }
