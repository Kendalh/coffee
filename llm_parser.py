import json
import base64
import requests
from requests.exceptions import Timeout
from typing import List, Dict, Any
import time
import PyPDF2


class CoffeeBeanPDFAnalyzer: 

    def __init__(self, api_key: str, model: str = "deepseek-chat"):
        self.api_key = api_key
        self.model = model
        self.api_url = "https://api.deepseek.com/v1/chat/completions"
        
    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """从PDF文件中提取文本内容"""
        text = ""
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
        except Exception as e:
            print(f"读取PDF文件时出错: {e}")
            return ""
        
        return text
    
    def get_pdf_page_count(self, pdf_path: str) -> int:
        """获取PDF文件的总页数"""
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                return len(pdf_reader.pages)
        except Exception as e:
            print(f"获取PDF页数时出错: {e}")
            return 0
    
    def create_prompt(self, pdf_page_count: int) -> str:
        """创建分析PDF的提示词"""
        prompt = f"""

请你分析以下咖啡生豆报价单的文本内容，提取所有咖啡豆信息。

重要说明：
1. 这个PDF文件共有{pdf_page_count}页
2. 请严格按照实际页数来组织输出，不要生成超过实际页数的内容
3. 从第1页开始，逐页处理
4. 每页内从上到下逐行扫描
5. 发现咖啡豆编号时，开始提取当前豆子
6. 当前豆子提取完成后，才继续扫描下一个
7. **绝对禁止**跨页借用信息

** 解析咖啡豆信息 首要规则 第一优先级（必须遵守）**
- 先检查豆子是否有"售馨"，"售罄"，"售 馨"，"售 罄"字样。记住这个豆已经sold out，并立即将price_per_kg和price_per_pkg设置为null，并跳过所有后续价格提取步骤。
- 价格必须来自当前咖啡豆专属的价格表格行。如果当前豆子没有专属的价格表格行，无论页面其他位置有什么数字，price_per_kg和price_per_pkg都必须设置为null。绝对禁止从其他豆子的价格行中借用数字。

**关键价格解析规则（必须遵守）：**
1. **表格结构识别**：
   - 价格表格通常有4列，表头为：`1KG` | `5KG` | `15或30KG` | `整包价`
   - 每行价格对应一个咖啡豆条目

2. **价格字段对应关系**：
   - `price_per_kg` → **第一列**（"1KG"列）的价格数字
   - `price_per_pkg` → **第四列**（"整包价"列）的价格数字
   - **忽略**中间的第2、3列（5KG和15/30KG）的价格

3. **价格数字提取格式**：
   - 无论格式是 `Y/24/KG`、`Y 24/KG`、`Y24/KG` 还是 `Y24/KG`，都提取中间的纯数字
   - 示例转换：
     - `Y/24/KG` → `24.0`
     - `Y 77/KG` → `77.0`
     - `Y74/KG` → `74.0`
     - `Y/85/KG` → `85.0`

4. 当咖啡豆只有单行价格（没有4列表格）时：
  - 格式示例：`590元/KG`、`398元/KG`、`￥130/KG`
  - 处理规则：
  - `price_per_kg` = 提取数字部分（如 `590元/KG` → `590.0`）
  - `price_per_pkg` = `null`（因为没有整包价）

解析要求：
1. 逐段分析文本中有咖啡豆信息的部分
2. 为每个咖啡豆提取以下字段：
   - 编号 (code)
   - 咖啡豆名 (name) - 抽取中文名 
   - 国家 (country) - 包含在咖啡豆名中，抽取中文名
   - 风味属性 (flavor_profile) - 用逗号分隔的风味描述
   - 每公斤价格 (price_per_kg) 
   - 整包价 (price_per_pkg) 

   ** 以下属性通常在PDF中以 “字段：值”的形式展现，请抽取文件原内容 **
   - 品种 (variety)
   - 产区 (origin) - 可能是产地、产区、庄园
   - 等级 (grade)
   - 含水量 (humidity) - 格式为 "13.7%"
   - 海拔 (altitude) - 格式如"1200-1500M"
   - 密度值 (density) - 格式如"853g/l" (通常在800-900 g/l间)
   - 处理法 (processing_method)
   - 产季 (harvest_season)

3. 输出要求：
   - **只输出一个完整的JSON数组，不要有任何其他文字**
   - **JSON数组必须是完整和有效的**
   - **不要在JSON后面添加解释或其他文字**
   - 如果豆子已经"售罄"或"售馨"，或被标记为Sold Out，price_per_kg和price_per_pkg都必须设置设为null
   - 如果某些字段缺失，设为null或空字符串

4. 输出示例：
[
  {{
    "page": 1,
    "coffee_beans": [
      {{
        "code": "S1-2S",
        "name": "印度尼西亚 苏门答腊 黄金曼特宁21日",
        "country": "印度尼西亚",
        "flavor_profile": "干净，醇厚度高，莓果，花香，香料，黑巧克力，高脂",
        "price_per_kg": 126.0,
        "price_per_pkg": 120,
        "origin": "Sumatra",
        "grade": "G1",
        "humidity": "13.7%",
        "altitude": "1600-1800M",
        "density": "853g/l",
        "processing_method": "水洗",
        "harvest_season": "2024年"
      }}
    ]
  }}
]

请确保：
1. **重要：只输出JSON，不要有其他文本**
2. 严格按照要求的字段结构
3. 处理所有段落中的咖啡豆信息
4. 如果同一段落有多个咖啡豆，都包含在coffee_beans数组中
5. page字段应该对应PDF的实际页码（从1开始，最大不超过{pdf_page_count}）
"""
        return prompt
    
    def _prepare_pdf_analysis(self, pdf_path: str, temperature: float, streaming: bool) -> tuple:
        """准备PDF分析的公共部分"""
        # 获取PDF页数
        pdf_page_count = self.get_pdf_page_count(pdf_path)
        print(f"PDF文件总页数: {pdf_page_count}")
        
        # 提取PDF文本内容
        pdf_text = self.extract_text_from_pdf(pdf_path)
        if not pdf_text:
            print("无法从PDF文件中提取文本")
            return None, None, None
        
        # 截断文本以避免token限制
        max_chars = 100000 
        if len(pdf_text) > max_chars:
            pdf_text = pdf_text[:max_chars]
            print(f"截断PDF文本至{max_chars}字符")
        
        # 准备请求
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "user",
                    "content": self.create_prompt(pdf_page_count) + f"\n\n以下是PDF文件的内容：\n\n{pdf_text}"
                }
            ],
            "stream": streaming,
            "temperature": temperature,  # Lower temperature for less creativity
            "max_tokens": 8100  # DeepSeek's limit is 8192
        }
        
        return headers, payload, pdf_page_count
    
    def _process_response_content(self, content: str, pdf_path: str) -> List[Dict[str, Any]]:
        """处理响应内容的公共部分"""
        # 从响应中提取JSON部分
        try:
            # 查找第一个完整的JSON对象或数组
            json_str = self.extract_first_json_object(content)
            
            if json_str:
                # 尝试解析JSON
                try:
                    result = json.loads(json_str)
                except json.JSONDecodeError as je:
                    raise je  # 重新抛出原始异常
                    
                # 验证和清理数据
                cleaned_result = self.clean_results(result)
                
                # 验证页数不超过实际PDF页数
                pdf_page_count = self.get_pdf_page_count(pdf_path)
                filtered_result = []
                for page_data in cleaned_result:
                    page_num = page_data.get("page", 0)
                    if isinstance(page_num, int) and 1 <= page_num <= pdf_page_count:
                        filtered_result.append(page_data)
                    elif isinstance(page_num, int) and page_num > pdf_page_count:
                        print(f"警告: 跳过超出PDF范围的页面 {page_num} (PDF只有{pdf_page_count}页)")
                    else:
                        print(f"警告: 跳过无效页面编号 {page_num}")
                
                return filtered_result
            else:
                print("未找到有效的JSON数据")
                # 打印部分响应以便调试
                print(f"响应预览: {content[:500]}...")
                return []
                
        except json.JSONDecodeError as e:
            print(f"JSON解析错误: {e}")
            print(f"原始响应长度: {len(content)} 字符")
            # 打印部分响应以便调试
            print(f"响应预览: {content[:500]}...")
            return []
    
    def analyze_pdf_streaming(self, pdf_path: str, temperature: float = 0.1) -> List[Dict[str, Any]]:
        """使用DeepSeek API流式分析PDF文件"""
        # 准备分析
        preparation_result = self._prepare_pdf_analysis(pdf_path, temperature, True)
        if preparation_result[0] is None:  # headers is None
            return []
        
        headers, payload, pdf_page_count = preparation_result
        
        print("开始分析PDF文件...")
        try:
            response = requests.post(
                self.api_url,
                headers=headers,
                json=payload,
                stream=True,
                timeout=600  # 10 minute timeout
            )
            
            if response.status_code != 200:
                return []
            
            # 收集流式响应
            full_response = ""
            for line in response.iter_lines():
                if line:
                    line = line.decode('utf-8')
                    
                    # 处理SSE格式
                    if line.startswith("data: "):
                        data = line[6:]  # 去掉"data: "前缀
                        
                        if data == "[DONE]":
                            print("\n流式响应结束")
                            break
                        
                        try:
                            chunk = json.loads(data)
                            if "choices" in chunk and len(chunk["choices"]) > 0:
                                delta = chunk["choices"][0].get("delta", {})
                                content = delta.get("content", "")
                                
                                if content:
                                    full_response += content
                                    # Removed verbose printing to speed up the process
                                    # print(content, end="", flush=True)
                                    
                        except json.JSONDecodeError:
                            continue
            
            print("\n" + "=" * 50)
            
            # 处理响应内容
            return self._process_response_content(full_response, pdf_path)
                
        except Timeout:
            print("请求超时 (10分钟). 跳过文件处理")
            return []
        except Exception as e:
            print(f"分析过程中出现错误: {e}")
            return []
    
    def analyze_pdf(self, pdf_path: str, temperature: float = 0.1) -> List[Dict[str, Any]]:
        """使用DeepSeek API非流式分析PDF文件"""
        # 准备分析
        preparation_result = self._prepare_pdf_analysis(pdf_path, temperature, False)
        if preparation_result[0] is None:  # headers is None
            return []
        
        headers, payload, pdf_page_count = preparation_result
        
        print("开始分析PDF文件...")
        try:
            response = requests.post(
                self.api_url,
                headers=headers,
                json=payload,
                timeout=600  # 10 minute timeout
            )
            
            if response.status_code != 200:
                print(f"API请求失败，状态码: {response.status_code}")
                return []
            
            # 解析响应
            response_data = response.json()
            
            if "choices" in response_data and len(response_data["choices"]) > 0:
                content = response_data["choices"][0]["message"]["content"]
                
                # 处理响应内容
                return self._process_response_content(content, pdf_path)
            else:
                print("响应中没有找到有效内容")
                return []
                
        except Timeout:
            print("请求超时 (10分钟). 跳过文件处理")
            return []
        except Exception as e:
            print(f"分析过程中出现错误: {e}")
            return []
    
    def extract_first_json_object(self, text: str) -> str:
        """
        从文本中提取第一个完整的JSON对象或数组
        """
        # 查找第一个 '{' 或 '[' 的位置
        start_brace = text.find('{')
        start_bracket = text.find('[')
        
        # 确定起始位置
        if start_brace == -1 and start_bracket == -1:
            return ""
        elif start_brace == -1:
            start_pos = start_bracket
            end_char = ']'
        elif start_bracket == -1:
            start_pos = start_brace
            end_char = '}'
        else:
            # 选择更早出现的
            if start_brace < start_bracket:
                start_pos = start_brace
                end_char = '}'
            else:
                start_pos = start_bracket
                end_char = ']'
        
        # 从起始位置开始查找匹配的结束符号
        bracket_count = 0
        in_string = False
        escape_next = False
        
        for i in range(start_pos, len(text)):
            char = text[i]
            
            # 处理转义字符
            if escape_next:
                escape_next = False
                continue
                
            if char == '\\':
                escape_next = True
                continue
                
            # 处理字符串
            if char == '"' and not escape_next:
                in_string = not in_string
                continue
                
            # 如果在字符串内，跳过所有字符
            if in_string:
                continue
                
            # 计算括号
            if (end_char == ']' and char == '[') or (end_char == '}' and char == '{'):
                bracket_count += 1
            elif (end_char == ']' and char == ']') or (end_char == '}' and char == '}'):
                bracket_count -= 1
                if bracket_count == 0:
                    # 找到了匹配的结束符号
                    json_str = text[start_pos:i+1]
                    # 清理JSON字符串
                    json_str = json_str.replace('\n', '').replace('\r', '')
                    json_str = ' '.join(json_str.split())
                    # Removed verbose printing to speed up the process
                    # print(f"提取的JSON片段长度: {len(json_str)} 字符")
                    return json_str
        
        # 如果没有找到完整的JSON对象，尝试简单提取
        if start_pos != -1:
            # 尝试提取从开始位置到某个合理长度的内容
            end_pos = min(start_pos + 10000, len(text))  # 限制长度
            json_str = text[start_pos:end_pos]
            # 尝试清理并返回
            json_str = json_str.replace('\n', '').replace('\r', '')
            json_str = ' '.join(json_str.split())
            # Removed verbose printing to speed up the process
            # print(f"尝试提取不完整JSON片段，长度: {len(json_str)} 字符")
            return json_str
        
        # 如果没有找到完整的JSON对象，返回空字符串
        return ""    
    

    def clean_results(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """清理和验证提取的结果"""
        if not isinstance(results, list):
            print(f"警告: 期望的结果是列表类型，但得到的是 {type(results)}")
            return []
        
        cleaned = []
        
        for i, page_data in enumerate(results):
            if not isinstance(page_data, dict):
                print(f"警告: 第{i+1}个项目不是字典类型，跳过")
                continue
                
            page_num = page_data.get("page", 0)
            coffee_beans = page_data.get("coffee_beans", [])
            
            # 验证page_num
            if not isinstance(page_num, int) or page_num <= 0:
                print(f"警告: 无效的页面编号 {page_num}，使用索引 {i+1}")
                page_num = i + 1
            
            # 验证coffee_beans
            if not isinstance(coffee_beans, list):
                print(f"警告: 页面 {page_num} 的coffee_beans不是列表类型，跳过")
                coffee_beans = []
            
            cleaned_beans = []
            for j, bean in enumerate(coffee_beans):
                if not isinstance(bean, dict):
                    print(f"警告: 页面 {page_num} 的第{j+1}个咖啡豆不是字典类型，跳过")
                    continue
                
                # 清理价格字段
                price = bean.get("price_per_kg")
                if isinstance(price, str):
                    # 尝试从字符串中提取数字
                    import re
                    price_match = re.search(r'[\d.]+', str(price))
                    if price_match:
                        try:
                            price = float(price_match.group())
                        except ValueError:
                            price = None
                    elif price in ["售罄", "售馨", "售罄", "售完"]:
                        price = None
                    else:
                        price = None
                elif not isinstance(price, (int, float)) and price is not None:
                    price = None
                
                # 确保所有必需字段都存在且为正确类型
                cleaned_bean = {
                    "code": str(bean.get("code", "")),
                    "name": str(bean.get("name", "")),
                    "country": str(bean.get("country", "")),
                    "flavor_profile": str(bean.get("flavor_profile", "")),
                    "price_per_kg": price,
                    "price_per_pkg": bean.get("price_per_pkg"),  # 保持原类型
                    "origin": str(bean.get("origin", "")),
                    "grade": str(bean.get("grade", "")),
                    "humidity": str(bean.get("humidity", "")),
                    "altitude": str(bean.get("altitude", "")),
                    "density": str(bean.get("density", "")),
                    "processing_method": str(bean.get("processing_method", "")),
                    "harvest_season": str(bean.get("harvest_season", "")),
                    "variety": str(bean.get("variety", ""))
                }
                
                cleaned_beans.append(cleaned_bean)
            
            if cleaned_beans:  # 只添加有数据的页面
                cleaned.append({
                    "page": page_num,
                    "coffee_beans": cleaned_beans
                })
        
        return cleaned
    
    def save_to_json(self, results: List[Dict[str, Any]], output_path: str):
        """将结果保存为JSON文件"""
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
            print(f"\n结果已保存到: {output_path}")
        except Exception as e:
            print(f"保存JSON文件时出错: {e}")
    
    def print_summary(self, results: List[Dict[str, Any]]):
        """打印分析摘要"""
        total_pages = len(results)
        total_coffees = sum(len(page["coffee_beans"]) for page in results)
        
        print("\n" + "=" * 50)
        print("分析摘要:")
        print(f"处理的总页数: {total_pages}")
        print(f"提取的咖啡豆总数: {total_coffees}")
        print("=" * 50)
        
        # 按页面打印统计
        for page in results:
            page_num = page["page"]
            count = len(page["coffee_beans"])
            print(f"页面 {page_num}: {count} 个咖啡豆")


# 使用示例
def main():
    import argparse
    import os
    import sys
    
    # 设置命令行参数
    parser = argparse.ArgumentParser(description="Parse coffee bean quotation PDFs using DeepSeek API")
    parser.add_argument("pdf_files", nargs="+", help="Input PDF files to parse")
    parser.add_argument("-o", "--output-dir", default="silver_data", help="Output directory for JSON files")
    parser.add_argument("--api-key", default="sk-de6d5dde9d384de294c14637d1018de2", help="DeepSeek API key")
    parser.add_argument("--streaming", action="store_true", help="Use streaming API (default: False)")
    parser.add_argument("--temperature", type=float, default=0.1, help="Temperature for LLM creativity (default: 0.2)")
    
    args = parser.parse_args()
    
    # 确保输出目录存在
    os.makedirs(args.output_dir, exist_ok=True)
    
    # 创建分析器实例
    analyzer = CoffeeBeanPDFAnalyzer(api_key=args.api_key)
    
    # 处理每个PDF文件
    for pdf_path in args.pdf_files:
        if not os.path.exists(pdf_path):
            print(f"警告: 文件不存在 {pdf_path}")
            continue
            
        if not pdf_path.lower().endswith('.pdf'):
            print(f"警告: 不是PDF文件 {pdf_path}")
            continue
        
        print(f"\n开始分析PDF文件: {pdf_path}")
        
        # 分析PDF
        if args.streaming:
            results = analyzer.analyze_pdf_streaming(pdf_path, temperature=args.temperature)
        else:
            results = analyzer.analyze_pdf(pdf_path, temperature=args.temperature)
        
        if results is not None and len(results) > 0:
            # 生成输出文件路径
            pdf_filename = os.path.basename(pdf_path)
            json_filename = os.path.splitext(pdf_filename)[0] + ".json"
            output_path = os.path.join(args.output_dir, json_filename)
            
            # 确保输出目录存在
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # 打印摘要
            analyzer.print_summary(results)
            
            # 保存到JSON文件
            analyzer.save_to_json(results, output_path)
        else:
            print(f"未提取到任何数据或提取过程出现错误: {pdf_path}")


if __name__ == "__main__":
    main()