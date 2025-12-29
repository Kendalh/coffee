import json
import re
import time
from typing import Dict, List, Any, Optional
from openai import OpenAI
from sql_query_tool import SQLQueryTool


class DeepSeekReActAgent:
    """基于DeepSeek API的ReAct智能体，专门用于咖啡豆数据库查询"""
    
    def __init__(self, api_key: str, base_url: str = "https://api.deepseek.com"):
        """
        初始化ReAct智能体
        
        Args:
            api_key: DeepSeek API密钥
            base_url: API基础URL
        """
        self.client = OpenAI(
            api_key=api_key,
            base_url=base_url
        )
        
        # 初始化SQL查询工具
        try:
            self.sql_tool = SQLQueryTool(db_path="coffee_beans.db")
        except FileNotFoundError as e:
            print(f"警告: {e}")
            print("请确保coffee_beans.db数据库文件存在")
            self.sql_tool = None
        
        # 对话历史记录
        self.conversation_history = []
        
        # 工具定义（仅SQL查询工具）
        self.tools = {
            "sql_query_tool": self.sql_query_tool
        }
        
        # ReAct系统提示词
        self.system_prompt = """你是一个ReAct（Reasoning+Acting）智能体，专门处理咖啡豆数据库的查询问题。

## 响应格式要求：
你必须严格按以下格式输出：

## ReAct 工作流程：
1. **思考（Reasoning）**：分析问题，理解需要什么数据
2. **行动（Acting）**：如果需要数据库查询，调用 sql_query_tool
3. **观察（Observation）**：处理查询返回的结果
4. **重复**：基于观察继续思考，直到可以给出最终答案
**最终答案**：[清晰完整的答案]

## 可用工具：
1. sql_query_tool - 执行SQL查询并返回结果
   - 参数：query（SQL查询语句字符串）

## 数据库结构：
咖啡豆数据库包含coffee_bean表，主要字段有：
**注意，这个表是一个有时间戳 （data_year, data_month）的咖啡豆快照数据表；每个时间戳记录了该时间的一个咖啡豆信息快照；获取最新数据需要获取到最新的（data_year, data_month）时间戳。**
- name: 咖啡豆名称
- type: 类型（premium/common）
- country: 产地国家
- flavor_profile: 风味描述详情
- flavor_category: 风味类别, 口感调性 - 优先查询此字段
- origin: 产区
- plot: 地块
- estate: 庄园
- price_per_kg: 每公斤价格
- price_per_pkg: 每包价格
- grade: 等级
- altitude: 种植海拔
- density: 密度
- humidity: 湿度
- processing_method: 加工方法
- variety: 品种
- provider: 数据提供商
- data_year: 快照数据年份
- data_month: 快照数据月份

最新数据时间表格 latest_data：
- provider: 数据提供商
- data_year: 数据年份
- data_month: 数据月份

## 数据库表查询要求：
** 当用户没有询问历史数据（如历史价格、价格趋势等）时，请使用latest_data中记录的最新数据时间戳（最新快照）查询。如：
WITH latest AS (
    SELECT 
        provider,
        data_year,
        data_month
    FROM latest_data
    WHERE provider = '金粽'
)
SELECT 
    cb.*
FROM coffee_bean cb
INNER JOIN latest l
    ON cb.provider = l.provider
    AND cb.data_year = l.data_year
    AND cb.data_month = l.data_month

** 当用户询问历史数据时，才可以不去Join latest_data 表去获取历史咖啡豆数据

** 当用户问题中有“咖啡风味”类型的描述时（如推荐水果调性的咖啡；有坚果口味的咖啡；等），先将该描述先转变为flavor_category字段的查询过滤条件，再进行查询。**
flavor_category中有如下8中风味类型：
"明亮果酸型"  
"花香茶感型"  
"果汁感热带水果型" 
"均衡圆润型"
"巧克力坚果调型" 
"焦糖甜感型" 
"酒香发酵型" 
"烟熏木质型"  

## ReAct过程示例：
用户：巴西有多少种咖啡豆？

思考：用户想知道巴西产的咖啡豆种类数量。我需要查询coffee_bean表，筛选country为'巴西'的记录，并计数。根据数据库查询要求，我需要连接latest_data表以获取最新数据。
行动：sql_query_tool({"query": "WITH latest AS (SELECT provider, data_year, data_month FROM latest_data WHERE provider = '金粽') SELECT COUNT(*) as brazil_coffee_count FROM coffee_bean cb INNER JOIN latest l ON cb.provider = l.provider AND cb.data_year = l.data_year AND cb.data_month = l.data_month WHERE cb.country = '巴西'"})
观察：{"success": true, "results": [{"brazil_coffee_count": 15}], "columns": ["brazil_coffee_count"], "row_count": 1}
思考：查询结果显示巴西有15种咖啡豆。
最终答案：巴西有15种咖啡豆。

## 重要规则：
1. 只有在需要数据库查询时才使用工具
2. 确保SQL查询语法正确
3. 基于查询结果进行推理
4. 不要编造数据，只使用工具返回的结果
5. 在查询时注意使用正确的表名和字段名
6. 不要试图将用户的问题翻译为英语（如国家名）
7. **行动**后，不要自己编造**观察**内容，系统会提供真实的工具执行结果作为**观察**
"""
    
    def parse_react_response(self, response_text: str) -> Dict[str, str]:
       """
       解析ReAct格式的响应
           
       Args:
           response_text: 模型返回的文本
               
       Returns:
           包含各个部分的字典
       """
       result = {
           "thought": "",
           "action": "",
           "observation": "",
           "final_answer": ""
       }
           
       # 提取思考部分 - 尝试匹配带星号和不带星号的格式
       thought_match = re.search(r'(?:\*\*思考\*\*|思考)：([\s\S]*?)(?=(?:\*\*行动\*\*|行动)|(?:\*\*观察\*\*|观察)|(?:\*\*最终答案\*\*|最终答案)|$)', response_text)
       if thought_match:
           result["thought"] = thought_match.group(1).strip()
           
       # 提取行动部分 - 尝试匹配带星号和不带星号的格式
       action_match = re.search(r'(?:\*\*行动\*\*|行动)：([\s\S]*?)(?=(?:\*\*观察\*\*|观察)|(?:\*\*最终答案\*\*|最终答案)|$)', response_text)
       if action_match:
           result["action"] = action_match.group(1).strip()
           
       # 提取观察部分 - 尝试匹配带星号和不带星号的格式
       observation_match = re.search(r'(?:\*\*观察\*\*|观察)：([\s\S]*?)(?=(?:\*\*思考\*\*|思考)|(?:\*\*最终答案\*\*|最终答案)|$)', response_text)
       if observation_match:
           result["observation"] = observation_match.group(1).strip()
           
       # 提取最终答案 - 尝试匹配带星号和不带星号的格式
       answer_match = re.search(r'(?:\*\*最终答案\*\*|最终答案)：([\s\S]*?)(?=(?:\*\*思考\*\*|思考)|(?:\*\*行动\*\*|行动)|(?:\*\*观察\*\*|观察)|$)', response_text)
       if answer_match:
           result["final_answer"] = answer_match.group(1).strip()
           
       return result
       
    def extract_sql_query(self, action_text: str) -> Optional[str]:
       """
       从行动文本中提取SQL查询
           
       Args:
           action_text: 行动文本，格式如：sql_query_tool({"query": "SELECT ..."})
               
       Returns:
           SQL查询语句或None
       """
       try:
           # 匹配JSON参数
           match = re.search(r'sql_query_tool\(({.*})\)', action_text)
           if match:
               params = json.loads(match.group(1))
               return params.get("query", "")
               
           # 尝试其他格式
           match = re.search(r'query["\']?\s*:\s*["\']([^"\']+)"\'', action_text)
           if match:
               return match.group(1)
                   
       except (json.JSONDecodeError, AttributeError) as e:
           print(f"[警告] 解析SQL查询失败: {e}")
           
       return None
       
    def sql_query_tool(self, query: str) -> Dict[str, Any]:
           
        """
        SQL查询工具，用于执行针对咖啡豆数据库的查询
        
        Args:
            query: SQL查询语句
            
        Returns:
            查询结果字典
        """
        if self.sql_tool is None:
            return {
                "error": "数据库工具未初始化，请确保coffee_beans.db文件存在",
                "success": False,
                "results": None,
                "columns": [],
                "row_count": 0
            }
        
        try:
            result = self.sql_tool.run_query(query)
            return result
        except Exception as e:
            return {
                "error": f"执行SQL查询时出错: {str(e)}",
                "success": False,
                "results": None,
                "columns": [],
                "row_count": 0
            }
    
    def solve(self, question: str, max_steps: int = 7) -> str:
        """
        使用ReAct模式解决问题
        
        Args:
            question: 用户问题
            max_steps: 最大思考步骤
            
        Returns:
            最终答案
        """
        print(f"\n{'='*60}")
        print(f"问题: {question}")
        print(f"{'='*60}")
        
        # 检查数据库是否可用
        if self.sql_tool is None:
            error_msg = "数据库连接失败。请确保coffee_beans.db文件存在。"
            print(f"[错误] {error_msg}")
            return error_msg
        
        # 重置对话历史
        self.conversation_history = []
        
        # 添加系统提示
        self.conversation_history.append({
            "role": "system", 
            "content": self.system_prompt
        })
        
        # 添加用户问题
        self.conversation_history.append({
            "role": "user",
            "content": question
        })
        
        # ReAct循环
        for step in range(1, max_steps + 1):
            print(f"\n--- 步骤 {step} ---")
            
            try:
                # 定义可用工具
                tools = [{
                    "type": "function",
                    "function": {
                        "name": "sql_query_tool",
                        "description": "执行SQL查询并返回结果",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "query": {
                                    "type": "string",
                                    "description": "SQL查询语句"
                                }
                            },
                            "required": ["query"]
                        }
                    }
                }]
                
                # 调用DeepSeek API
                response = self.client.chat.completions.create(
                    model="deepseek-chat",
                    messages=self.conversation_history,
                    tools=tools,
                    tool_choice="auto",
                    temperature=0.1,  # 低温度以获得更确定的输出
                    max_tokens=8100
                )
                
                response_msg = response.choices[0].message
                response_text = response_msg.content
                
                print(f"模型响应:\n{response_text}")
                
                # 检查是否有结构化的工具调用（优先级最高）
                if hasattr(response_msg, 'tool_calls') and response_msg.tool_calls:
                    # 处理结构化工具调用
                    for tool_call in response_msg.tool_calls:
                        if tool_call.function.name == "sql_query_tool":
                            print(f"工具调用: {tool_call.function.name}")
                            
                            # 解析函数参数
                            args = json.loads(tool_call.function.arguments)
                            sql_query = args.get("query", "")
                            
                            if not sql_query:
                                print("[错误] 无法从工具调用中提取SQL查询")
                                break
                            
                            print(f"执行查询: {sql_query}")
                            
                            # 执行工具
                            tool_result = self.tools["sql_query_tool"](sql_query)
                            
                            # 检查工具执行结果
                            if not tool_result.get("success", False):
                                error_msg = tool_result.get("error", "未知错误")
                                print(f"[错误] 工具执行失败: {error_msg}")
                                observation = f"错误: {error_msg}"
                            else:
                                observation = json.dumps(tool_result, ensure_ascii=False)
                            
                            print(f"观察: {observation}")
                            
                            # 更新对话历史 - 添加工具调用信息
                            self.conversation_history.append({
                                "role": "assistant",
                                "content": response_text,
                                "tool_calls": [{
                                    "id": tool_call.id,
                                    "function": {
                                        "name": tool_call.function.name,
                                        "arguments": tool_call.function.arguments
                                    },
                                    "type": "function"
                                }]
                            })
                            
                            # 添加工具结果
                            self.conversation_history.append({
                                "role": "tool",
                                "content": observation,
                                "tool_call_id": tool_call.id
                            })
                            
                            # 跳出循环以继续下一轮
                            break    
                        else:
                            print(f"未知工具调用: {tool_call.function.name}")
                            break
                else:
                    # 没有结构化工具调用，按ReAct格式解析响应
                    parsed = self.parse_react_response(response_text)
                    print(parsed)
                    
                    # 记录思考
                    if parsed["thought"]:
                        print(f"思考: {parsed['thought']}")
                    
                    # 检查是否有最终答案
                    if parsed["final_answer"]:
                        print(f"\n✓ 找到最终答案!")
                        return parsed["final_answer"]
                    
                    # 检查是否需要行动
                    if parsed["action"] and "sql_query_tool" in parsed["action"]:
                        print(f"行动: {parsed['action']}")
                        
                        # 提取SQL查询
                        sql_query = self.extract_sql_query(parsed["action"])
                        if not sql_query:
                            print("[错误] 无法从行动中提取SQL查询")
                            break
                        
                        # 执行工具
                        tool_result = self.tools["sql_query_tool"](sql_query)
                        
                        # 检查工具执行结果
                        if not tool_result.get("success", False):
                            error_msg = tool_result.get("error", "未知错误")
                            print(f"[错误] 工具执行失败: {error_msg}")
                            observation = f"错误: {error_msg}"
                        else:
                            observation = json.dumps(tool_result, ensure_ascii=False)

                        print(f"观察: {observation}")
                        
                        # 更新对话历史
                        self.conversation_history.append({
                            "role": "assistant",
                            "content": response_text
                        })
                        
                        # 添加观察结果
                        self.conversation_history.append({
                            "role": "user",
                            "content": f"**观察**：{observation}\n\n请基于这个观察继续思考。"
                        })
                    
                    else:
                        # 没有行动也没有最终答案，可能出错了
                        print("[警告] 响应中没有工具调用、行动或最终答案")
                        break
            except Exception as e:
                print(f"[错误] API调用失败: {e}")
                break
        
        print(f"\n✗ 达到最大步骤限制 ({max_steps}) 或出现错误")
        return "抱歉，我无法完成这个分析。请尝试更具体的问题或联系管理员。"
    
    def interactive_mode(self):
        """咖啡豆数据库查询的交互式模式"""
        print("="*60)
        print("DeepSeek ReAct Agent - 咖啡豆数据库查询助手")
        print("="*60)
        print("输入 'quit' 或 'exit' 退出")
        print("-"*60)
        
        while True:
            try:
                # 获取用户输入
                question = input("\n请输入您的问题: ").strip()
                
                if question.lower() in ['quit', 'exit', '退出', 'q']:
                    print("再见！")
                    break
                
                if not question:
                    print("问题不能为空！")
                    continue
                
                # 解决问题
                answer = self.solve(question)
                
                print(f"\n{'='*60}")
                print(f"最终答案: {answer}")
                print(f"{'='*60}")
                
            except KeyboardInterrupt:
                print("\n\n程序被用户中断")
                break
            except Exception as e:
                print(f"\n[错误] {e}")


# 使用示例
def main():
    # 请替换为你的DeepSeek API密钥
    API_KEY = "sk-de6d5dde9d384de294c14637d1018de2"
    
    # 检查数据库文件是否存在
    import os
    if not os.path.exists("coffee_beans.db"):
        print("警告: coffee_beans.db 数据库文件不存在。请先运行 sqlite_populator.py 创建数据库。")
    
    # 创建ReAct智能体
    agent = DeepSeekReActAgent(api_key=API_KEY)
    
    # 示例1: 测试模式
    print("测试模式运行示例...")
    
    test_questions = [
        #"中国有多少种咖啡豆？列出这些豆、品种、价格",
        #"最贵的5种咖啡豆是什么？它们主要来自哪些国家？",
        #"有哪些来自埃塞俄比亚的优质咖啡豆，且性价比较高？",
        #"巴拿马最贵的豆是什么？它的价格历史趋势是怎样的？",
        #"推荐3款价格便宜、适中、贵的带有水果调性的咖啡",
        "推荐两款不同价位的瑰夏咖啡豆"
    ]
    
    for i, question in enumerate(test_questions, 1):
        print(f"\n\n示例 {i}:")
        answer = agent.solve(question)
        print(f"\n答案: {answer}")
        print("-"*60)
    
    # 示例2: 交互式模式
    # agent.interactive_mode()


if __name__ == "__main__":
    main()