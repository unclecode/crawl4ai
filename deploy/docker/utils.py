import json
from datetime import datetime

class CrawlJSONEncoder(json.JSONEncoder):
    """Custom JSON encoder for crawler results"""
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        if isinstance(obj, bytes):
            return obj.decode('utf-8', errors='ignore')
        if hasattr(obj, 'model_dump'):
            return obj.model_dump()
        if hasattr(obj, '__dict__'):
            return {k: v for k, v in obj.__dict__.items() if not k.startswith('_')}
        return str(obj)  # Fallback to string representation

def serialize_result(result) -> dict:
    """Safely serialize a crawler result"""
    try:
        # Convert to dict handling special cases
        if hasattr(result, 'model_dump'):
            result_dict = result.model_dump()
        else:
            result_dict = {
                k: v for k, v in result.__dict__.items()
                if not k.startswith('_')
            }

        # Remove known non-serializable objects
        result_dict.pop('ssl_certificate', None)
        result_dict.pop('downloaded_files', None)

        return result_dict
    except Exception as e:
        print(f"Error serializing result: {e}")
        return {"error": str(e), "url": getattr(result, 'url', 'unknown')}