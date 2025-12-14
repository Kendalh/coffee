import json
import base64
import requests
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
- 这个PDF文件共有{pdf_page_count}页
- 请严格按照实际页数来组织输出，不要生成超过实际页数的内容
- 页码从1开始计数，最大不超过{pdf_page_count}

要求：
1. 逐段分析文本中有咖啡豆信息的部分
2. 为每个咖啡豆提取以下字段：
   - 编号 (code)
   - 咖啡豆名 (name)
   - 风味属性 (flavor_profile) - 用逗号分隔的风味描述
   - 每公斤价格 (price_per_kg) - 以1KG价格为准，如果没有则置空，必须为数字
   - 整包价 (price_per_pkg) - 如果没有则置空，必须为数字
   - 品种 (variety)
   - 产区 (origin) - 可能是产地、产区、庄园
   - 等级 (grade)
   - 海拔 (altitude) - 格式如"1200-1500M"
   - 密度值 (density) - 格式如"853g/l"
   - 处理法 (processing_method)
   - 产季 (harvest_season)

3. 输出要求：
   - **只输出一个完整的JSON数组，不要有任何其他文字**
   - **JSON数组必须是完整和有效的**
   - **不要在JSON后面添加解释或其他文字**
   - 如果价格是"售罄"或"售馨"，price_per_kg设为null
   - 如果某些字段缺失，设为null或空字符串

4. 输出示例：
[
  {{
    "page": 1,
    "coffee_beans": [
      {{
        "code": "S1-2S",
        "name": "印度尼西亚 苏门答腊 黄金曼特宁21日",
        "flavor_profile": "干净，醇厚度高，莓果，花香，香料，黑巧克力，高脂",
        "price_per_kg": 126.0,
        "price_per_pkg": 120,
        "origin": "苏门答腊",
        "grade": "G1",
        "altitude": "1600-1800M",
        "density": "853g/l",
        "processing_method": "水洗",
        "harvest_season": "2024"
      }}
    ]
  }}
]

请确保：
1. 只输出JSON，不要有其他文本
2. 严格按照要求的字段结构
3. 处理所有段落中的咖啡豆信息
4. 如果同一段落有多个咖啡豆，都包含在coffee_beans数组中
5. page字段应该对应PDF的实际页码（从1开始，最大不超过{pdf_page_count}）
6. 绝对不要生成超过{pdf_page_count}页的内容
7. **最重要：只输出JSON，不要有任何额外的文字说明**
"""
        return prompt
    
    def analyze_pdf_streaming(self, pdf_path: str) -> List[Dict[str, Any]]:
        """使用DeepSeek API流式分析PDF文件"""
        
        # 获取PDF页数
        pdf_page_count = self.get_pdf_page_count(pdf_path)
        print(f"PDF文件总页数: {pdf_page_count}")
        
        # 提取PDF文本内容
        pdf_text = self.extract_text_from_pdf(pdf_path)
        if not pdf_text:
            print("无法从PDF文件中提取文本")
            return []
        
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
            "stream": True,
            "max_tokens": 8000  # DeepSeek's limit is 8192
        }
        
        print("开始分析PDF文件...")
        try:
            response = requests.post(
                self.api_url,
                headers=headers,
                json=payload,
                stream=True
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
            
            # 从响应中提取JSON部分
            try:
                # 查找第一个完整的JSON对象或数组
                json_str = self.extract_first_json_object(full_response)
                
                if json_str:
                    # Removed verbose printing to speed up the process
                    # print(f"成功提取JSON，长度: {len(json_str)} 字符")
                    # 尝试解析JSON
                    try:
                        result = json.loads(json_str)
                    except json.JSONDecodeError as je:
                        # 如果直接解析失败，尝试修复常见的JSON问题
                        # Removed verbose printing to speed up the process
                        # print(f"直接JSON解析失败，尝试修复: {je}")
                        fixed_json = self.fix_json_format(json_str)
                        if fixed_json:
                            result = json.loads(fixed_json)
                        else:
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
                    # Removed verbose printing to speed up the process
                    # print("未找到有效的JSON数据")
                    # 打印部分响应以便调试
                    # print(f"响应预览: {full_response[:500]}...")
                    return []
                    
            except json.JSONDecodeError as e:
                # Removed verbose printing to speed up the process
                # print(f"JSON解析错误: {e}")
                # print(f"原始响应长度: {len(full_response)} 字符")
                # 打印部分响应以便调试
                # print(f"响应预览: {full_response[:500]}...")
                return []
                
        except Exception as e:
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
    
    def fix_json_format(self, json_str: str) -> str:
        """
        尝试修复常见的JSON格式问题
        """
        if not json_str:
            return ""
        
        # 移除可能的额外内容
        # 查找最后一个可能的结束括号
        last_brace = json_str.rfind('}')
        last_bracket = json_str.rfind(']')
        
        if last_brace != -1 or last_bracket != -1:
            # 选择较晚出现的结束符号
            end_pos = max(last_brace, last_bracket)
            json_str = json_str[:end_pos + 1]
        
        # 确保字符串以正确的结束符号结尾
        if json_str.endswith(',') or json_str.endswith(':'):
            json_str = json_str[:-1]
        
        # 清理字符串
        json_str = json_str.strip()
        
        # 确保以 [ 或 { 开始，以 ] 或 } 结束
        if json_str and not (json_str.startswith('{') or json_str.startswith('[')):
            # 尝试找到第一个合法的开始符号
            brace_pos = json_str.find('{')
            bracket_pos = json_str.find('[')
            
            if brace_pos != -1 and (bracket_pos == -1 or brace_pos < bracket_pos):
                json_str = json_str[brace_pos:]
            elif bracket_pos != -1:
                json_str = json_str[bracket_pos:]
        
        # 确保以正确的结束符号结尾
        if json_str:
            starts_with_brace = json_str.startswith('{')
            starts_with_bracket = json_str.startswith('[')
            
            if starts_with_brace and not json_str.endswith('}'):
                # 尝试修复
                brace_count = json_str.count('{') - json_str.count('}')
                if brace_count > 0:
                    json_str += '}' * brace_count
            elif starts_with_bracket and not json_str.endswith(']'):
                # 尝试修复
                bracket_count = json_str.count('[') - json_str.count(']')
                if bracket_count > 0:
                    json_str += ']' * bracket_count
        
        return json_str.strip()
    
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
                    "flavor_profile": str(bean.get("flavor_profile", "")),
                    "price_per_kg": price,
                    "price_per_pkg": bean.get("price_per_pkg"),  # 保持原类型
                    "origin": str(bean.get("origin", "")),
                    "grade": str(bean.get("grade", "")),
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
        results = analyzer.analyze_pdf_streaming(pdf_path)
        
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