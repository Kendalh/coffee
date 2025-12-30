import subprocess
import tempfile
import os
import signal
import json
from openai import OpenAI

def generate_code_llm(prompt: str, api_key: str, base_url: str = "https://api.deepseek.com") -> str:
    """
    使用DeepSeek API生成Python代码
    
    Args:
        prompt: 用户输入的描述，用于生成代码
        api_key: DeepSeek API密钥
        base_url: API基础URL
        
    Returns:
        生成的Python代码字符串
    """
    client = OpenAI(
        api_key=api_key,
        base_url=base_url
    )
    
    # 优化的提示词，确保只生成可运行的Python代码
    system_prompt = """你是一个专业的Python代码生成器。用户会给你一个需求描述，你需要返回可直接运行的Python代码。

重要要求：
1. 只返回Python代码，不要有任何解释文字、注释或标记
2. 代码必须是完整且可运行的
3. 不要使用markdown代码块格式（如```python ... ```）
4. 不要包含任何"以下是代码:"、"代码如下:"等前缀文字
5. 如果需要导入库，请在代码开头导入
6. 代码应该能够直接执行并产生输出 (将运行结果print在stdout中)
7. 不要使用需要外部文件或资源的代码
8. 确保代码安全，不要生成任何可能有害的操作
"""
    
    try:
        response = client.chat.completions.create(
            model="deepseek-coder",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,  # 低温度以获得更确定的输出
            max_tokens=8000
        )
        
        # 提取生成的代码
        code = response.choices[0].message.content
        
        # 简单清理：如果模型意外返回了markdown格式，提取代码部分
        lines = code.split("\n")
        if lines[0].startswith("```"):
            # 找到第一个```和最后一个```
            start_idx = 1
            end_idx = len(lines) - 1
            for i, line in enumerate(lines):
                if line.startswith("```") and i > 0:
                    end_idx = i
                    break
            code = "\n".join(lines[start_idx:end_idx])
        
        return code
    except Exception as e:
        print(f"[错误] 生成代码时出错: {e}")
        return ""

def run_python_code_in_subprocess(code: str, timeout: int = 5) -> dict:
    """
    在子进程中安全运行Python代码并返回结果。
    """
    # 1. 创建一个临时的Python文件来存放代码
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(code)
        temp_file_path = f.name

    result = {
        'output': '',
        'error': '',
        'return_code': None,
        'timed_out': False
    }

    try:
        # 2. 使用 subprocess 运行代码，设置超时和资源限制（仅Unix）
        # 注意：资源限制在Windows上不完善，安全依赖主进程权限。
        def preexec_fn():
            # 可选：设置子进程资源限制（如CPU时间、内存）
            import resource
            # 设置CPU时间限制（秒）
            resource.setrlimit(resource.RLIMIT_CPU, (timeout, timeout + 1))
            # 设置内存限制（字节），例如 100 MB
            # resource.setrlimit(resource.RLIMIT_AS, (100 * 1024 * 1024, 100 * 1024 * 1024))

        # 运行代码
        proc = subprocess.Popen(
            ['python3', temp_file_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            preexec_fn=preexec_fn if os.name == 'posix' else None
        )

        try:
            stdout, stderr = proc.communicate(timeout=timeout)
            result['return_code'] = proc.returncode
            result['output'] = stdout
            result['error'] = stderr
        except subprocess.TimeoutExpired:
            # 超时处理
            result['timed_out'] = True
            # 终止进程树（仅Unix）
            if os.name == 'posix':
                os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
            else:
                proc.terminate()
                proc.wait(timeout=1)
            result['error'] = f'Code execution timed out after {timeout} seconds.'
            proc.communicate() # 清理管道
    except Exception as e:
        result['error'] = str(e)
    finally:
        # 3. 清理临时文件
        os.unlink(temp_file_path)

    return result

# 示例用法
if __name__ == '__main__':
    # 请替换为你的DeepSeek API密钥
    API_KEY = "sk-de6d5dde9d384de294c14637d1018de2"
    
    print("DeepSeek Python代码生成与沙箱执行器")
    print("="*50)
    
    # 获取用户输入的需求描述
    user_prompt = input("请输入您想要生成的Python代码需求: ").strip()
    
    if not user_prompt:
        print("输入不能为空！")
    else:
        print("\n正在使用DeepSeek生成代码...")
        generated_code = generate_code_llm(user_prompt, API_KEY)
        
        if generated_code:
            print(f"\n生成的代码:\n{generated_code}")
            print("\n在沙箱中执行生成的代码...")
            
            # 在沙箱中运行生成的代码
            result = run_python_code_in_subprocess(generated_code, timeout=5)
            
            print(f"\n执行结果:")
            print(f"返回码: {result['return_code']}")
            print(f"输出:\n{result['output']}")
            if result['error']:
                print(f"错误:\n{result['error']}")
            if result['timed_out']:
                print("执行因超时而终止。")
        else:
            print("代码生成失败！")