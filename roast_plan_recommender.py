import os
from openai import OpenAI
import json

def get_roast_recommendations(coffee_bean_features):
    """
    Get roast recommendations from LLM based on coffee bean features
    
    Args:
        coffee_bean_features (dict): Dictionary containing coffee bean characteristics
        
    Returns:
        dict: Structured JSON response with roast recommendations
    """
    
    # Structured prompt for the LLM
    system_prompt = """You are a professional coffee bean roaster. Based on the coffee bean characteristics (origin, variety, altitude, density, moisture content, processing method, grade) and the user's desired flavor profile, provide detailed roasting recommendations.

Please respond with a structured JSON format containing:
1. "general_suggestions": General roasting advice based on bean characteristics and desired flavor
2. "artisan_alog": Roasting profile data compatible with Artisan software (JSON format)

The roasting phases should include: Preheating, Loading Beans, Drying, Maillard Reaction, First Crack, Second Crack (if applicable), and Cooling Down.
For each phase, provide temperature settings and Rate of Rise (RoR) recommendations. 
The output contents should be in Chinese."""

    user_prompt = f"""Based on the following coffee bean characteristics, please provide roasting recommendations:

Bean Features (JSON format):
{json.dumps(coffee_bean_features, ensure_ascii=False, indent=2)}

Expected Output Format (JSON):
{{
    "general_suggestions": "General roasting advice...",
    "artisan_alog": {{
        "phases": [
            {{
                "phase": "Preheating",
                "temperature": "value",
                "ror": "value",
                "notes": "description"
            }}
        ]
    }}
}}

Please provide detailed temperature and RoR recommendations for each roasting phase."""

    client = OpenAI(
        # 若没有配置环境变量，请用百炼API Key将下行替换为：api_key="sk-xxx"
        api_key=os.getenv("DASHSCOPE_API_KEY", "sk-712886a429ba4813b5d8643ad8070219"),
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        timeout=60.0  # Set timeout to 60 seconds
    )

    try:
        completion = client.chat.completions.create(
            # 模型列表：https://help.aliyun.com/zh/model-studio/getting-started/models
            model="qwen-plus",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            response_format={"type": "json_object"},  # Request JSON format response
            timeout=60.0  # Set timeout to 60 seconds
        )
        
        # Parse and return the response
        response_data = json.loads(completion.choices[0].message.content)
        return response_data
        
    except Exception as e:
        # Return error response in the same format
        return {
            "error": str(e),
            "general_suggestions": "无法生成烘焙建议",
            "artisan_alog": {
                "phases": []
            }
        }