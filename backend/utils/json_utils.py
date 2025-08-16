from fastapi.responses import JSONResponse
import json

class CustomJSONResponse(JSONResponse):
    """
    自定义JSONResponse类，确保中文字符不被转义
    """
    media_type = "application/json; charset=utf-8"
    
    def render(self, content):
        return json.dumps(
            content,
            ensure_ascii=False,  # 确保中文字符不被转义
            allow_nan=False,
            indent=None,
            separators=(",", ":"),
        ).encode("utf-8")