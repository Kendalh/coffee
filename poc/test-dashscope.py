import os
from openai import OpenAI
import json

# Coffee bean features structure
coffee_bean_features = {
    "origin": "Colombia",
    "variety": "Geisha",
    "density": "High",
    "altitude": 1800,
    "moisture_content": 11.7,
    "processing_method": "Washed",
    "grade": "Supremo",
    "desired_flavor": "Floral & Tea-like"
}

# Structured prompt for the LLM
system_prompt = """You are a professional coffee bean roaster. Based on the coffee bean characteristics (origin, variety, altitude, density, moisture content, processing method, grade) and the user's desired flavor profile, provide detailed roasting recommendations.

Please respond with a structured JSON format containing:
1. "general_suggestions": General roasting advice based on bean characteristics and desired flavor
2. "artisan_alog": Roasting profile data compatible with Artisan software (JSON format)

The roasting phases should include: Preheating, Loading Beans, Drying, Maillard Reaction, First Crack, Second Crack (if applicable), and Cooling Down.
For each phase, provide temperature settings and Rate of Rise (RoR) recommendations. 
The output contents should be in Chinese. 
"""

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

Please provide detailed temperature and RoR recommendations for each roasting phase.
"""

client = OpenAI(
    # 若没有配置环境变量，请用百炼API Key将下行替换为：api_key="sk-xxx"
    api_key="sk-712886a429ba4813b5d8643ad8070219",
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
)

completion = client.chat.completions.create(
    # 模型列表：https://help.aliyun.com/zh/model-studio/getting-started/models
    model="qwen-plus",
    messages=[
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ],
    response_format={"type": "json_object"}  # Request JSON format response
)

# Parse the response and print in a nicely formatted way
response_data = json.loads(completion.choices[0].message.content)

print("=" * 60)
print("COFFEE ROASTING RECOMMENDATIONS")
print("=" * 60)

print("\n📍 GENERAL SUGGESTIONS:")
print("-" * 30)
print(response_data.get("general_suggestions", "No general suggestions provided"))

print("\n📋 ARTISAN ALOG PROFILES:")
print("-" * 30)
phases = response_data.get("artisan_alog", {}).get("phases", [])
for i, phase in enumerate(phases, 1):
    print(f"\n{i}. {phase.get('phase', 'Unknown Phase')}")
    print(f"   Temperature: {phase.get('temperature', 'N/A')}")
    print(f"   RoR: {phase.get('ror', 'N/A')}")
    print(f"   Notes: {phase.get('notes', 'No notes provided')}")

print("\n" + "=" * 60)