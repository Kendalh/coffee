import pdfplumber
import re
import pandas as pd
from collections import OrderedDict

class CoffeeExtractor:
    """咖啡豆提取器 - 最终版本"""
    
    def __init__(self):
        self.coffee_beans = []
        self.current_section = None
        self.current_bean = None
        
        # 预编译正则表达式，提高性能
        self.id_patterns = [
            re.compile(r'^[A-Z][0-9]+-[0-9A-Z]+[A-Z]?$'),
            re.compile(r'^[A-Z]-[0-9]+[A-Z]?$'),
            re.compile(r'^[A-Z][A-Z]-[0-9]+$'),
            re.compile(r'^[A-Z][0-9]+-[0-9]+$'),
        ]
        
        # 常见的国家/地区列表，用于去重
        self.country_keywords = [
            '印度尼西亚', '印尼', '苏门答腊', '印度', '越南', '乌干达', '巴布亚新几内亚',
            '洪都拉斯', '秘鲁', '巴西', '哥斯达黎加', '危地马拉', '哥伦比亚',
            '坦桑尼亚', '肯尼亚', '埃塞俄比亚', '萨尔瓦多', '巴拿马', '卢旺达',
            '牙买加', '墨西哥', '中国', '云南', '普洱'
        ]
        
        # 常见的等级标识
        self.grade_keywords = ['AAA', 'AA', 'A', 'G1', 'G2', 'G3', 'G4', 'G5', 
                              'PB', 'SHB', 'EP', 'GP', 'FAQ', 'NY2', 'NY3',
                              'SC', 'FC', 'SS', 'Y', 'AB', 'Supremo', 'GR1']
        
        # 价格相关的关键词
        self.price_keywords = ['1KG', '5KG', '30KG', '整包价', '整色价', '¥', '元/KG']
    
    def clean_for_match(self, text):
        """清理文本用于匹配（去除所有空格）"""
        if not text:
            return ''
        return re.sub(r'[\s　]', '', text)
    
    def clean_bean_id(self, id_text):
        """清理咖啡豆ID，移除NEW等无关内容"""
        # 移除NEW字样（可能在ID前后）
        cleaned = re.sub(r'\s*NEW\s*', '', id_text, flags=re.IGNORECASE)
        cleaned = cleaned.strip()
        return cleaned
    
    def is_coffee_bean_id(self, line):
        """检查是否是咖啡豆ID"""
        line = line.strip()
        
        # 先清理掉NEW字样
        cleaned_line = self.clean_bean_id(line)
        
        # 检查是否匹配任一模式
        for pattern in self.id_patterns:
            if pattern.match(cleaned_line):
                return True
        
        # 额外的检查：如果行很短且包含连字符和数字，也可能是ID
        if len(cleaned_line) <= 10 and '-' in cleaned_line and any(c.isdigit() for c in cleaned_line):
            return True
            
        return False
    
    def is_field_line(self, line):
        """检查是否是字段行（包含冒号或特定关键词）"""
        field_keywords = ['风味', '风吹', '含水量', '密度值', '产品', '产区', 
                         '规格', '海拔', '处理法', '品种', '等级', '产季']
        
        if '：' in line or ':' in line:
            return True
        
        for keyword in field_keywords:
            if keyword in line:
                return True
        
        return False
    
    def is_price_line(self, line):
        """检查是否是价格行"""
        for keyword in self.price_keywords:
            if keyword in line:
                return True
        return False
    
    def extract_bean_name_from_lines(self, lines, start_idx):
        """
        从多行文本中提取咖啡豆名
        策略：收集ID后的连续行，直到遇到字段行、价格行或新ID
        """
        name_parts = []
        idx = start_idx
        
        while idx < len(lines):
            line = lines[idx].strip()
            if not line:
                idx += 1
                continue
            
            # 停止条件
            if (self.is_field_line(line) or 
                self.is_price_line(line) or 
                self.is_coffee_bean_id(line)):
                break
            
            # 清理干扰词
            cleaned_line = self.clean_name_line(line)
            if cleaned_line:
                name_parts.append(cleaned_line)
            
            idx += 1
        
        if name_parts:
            # 合并所有部分
            full_name = ''.join(name_parts)
            # 应用去重和清理
            final_name = self.finalize_bean_name(full_name)
            return final_name, idx - 1
        
        return '', start_idx
    
    def clean_name_line(self, line):
        """清理名称行中的干扰内容"""
        # 移除常见的干扰标记
        interference_patterns = [
            r'\bNEW\b', r'\bnew\b',
            r'\d{4}\s*新产季',
            r'\d{4}\s*产季',
            r'-\s*NEW',
            r'-\s*\d{4}新产季',
            r'售馨', r'售罄',
            r'特惠', r'促销',
        ]
        
        cleaned = line
        for pattern in interference_patterns:
            cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE)
        
        return cleaned.strip()
    
    def finalize_bean_name(self, raw_name):
        """
        最终处理咖啡豆名：去重、清理、格式化
        """
        if not raw_name:
            return ''
        
        # 1. 去除所有空格
        no_spaces = re.sub(r'\s+', '', raw_name)
        
        # 2. 去除重复的国家/地区名
        deduplicated = self.remove_duplicate_country(no_spaces)
        
        # 3. 提取有效部分（中文、数字、等级标识等）
        final_name = self.extract_valid_name_parts(deduplicated)
        
        return final_name
    
    def remove_duplicate_country(self, text):
        """去除重复的国家/地区名称"""
        if not text:
            return text
        
        # 检查是否有明显的重复模式
        for country in self.country_keywords:
            # 模式：国家名连续出现两次
            pattern1 = country + country
            if pattern1 in text:
                # 替换为一次
                text = text.replace(pattern1, country)
            
            # 模式：国家名后紧跟着包含该国家名的更长字符串
            for other_country in self.country_keywords:
                if country != other_country and country in other_country:
                    pattern2 = country + other_country
                    if pattern2 in text:
                        text = text.replace(pattern2, other_country)
        
        return text
    
    def extract_valid_name_parts(self, text):
        """从文本中提取有效的名称部分"""
        if not text:
            return ''
        
        # 构建匹配模式：中文、数字、英文字母（用于等级标识）、常见标点
        pattern = r'[\u4e00-\u9fffA-Za-z0-9\-]+'
        
        matches = re.findall(pattern, text)
        if not matches:
            return ''
        
        # 过滤掉可能是价格的部分
        filtered_matches = []
        for match in matches:
            # 检查是否是价格相关（包含KG、价格数字等）
            if self.is_likely_price_part(match):
                continue
            
            # 检查是否是有效的名称部分
            if self.is_valid_name_part(match):
                filtered_matches.append(match)
        
        if filtered_matches:
            return ''.join(filtered_matches)
        
        return ''
    
    def is_likely_price_part(self, text):
        """检查文本是否可能是价格部分"""
        # 包含KG且主要是数字或价格相关
        if 'KG' in text.upper() and (text.isdigit() or re.search(r'\d+', text)):
            return True
        
        # 包含价格关键词
        price_indicators = ['1KG', '5KG', '30KG', '¥', '元']
        for indicator in price_indicators:
            if indicator in text:
                return True
        
        return False
    
    def is_valid_name_part(self, text):
        """检查是否是有效的名称部分"""
        if not text or len(text) < 1:
            return False
        
        # 如果是纯数字且长度超过4，可能是价格或规格，不是名称
        if text.isdigit() and len(text) > 4:
            return False
        
        # 如果是常见的价格模式，过滤掉
        if re.match(r'^\d+KG$', text.upper()):
            return False
        
        # 包含中文，保留
        if re.search(r'[\u4e00-\u9fff]', text):
            return True
        
        # 是常见的等级标识，保留
        if text.upper() in [g.upper() for g in self.grade_keywords]:
            return True
        
        # 是数字或字母数字组合（可能是等级标识），保留
        if re.match(r'^[A-Za-z]+\d+$', text) or re.match(r'^\d+[A-Za-z]+$', text):
            return True
        
        # 是纯数字（可能代表目数或其他规格），保留
        if text.isdigit():
            return True
        
        # 其他情况，如果主要是字母，且不是常见单词，可能是英文名称，过滤掉
        if text.isalpha() and len(text) > 2:
            # 检查是否是常见的英文咖啡术语
            coffee_terms = ['COSTA', 'RICA', 'BRAZIL', 'COLOMBIA', 'ETHIOPIA', 
                           'GUATEMALA', 'HONDURAS', 'INDONESIA', 'SUMATRA']
            if text.upper() not in coffee_terms:
                return False
        
        return True
    
    def extract_flavor(self, line):
        """从行中提取风味描述"""
        # 清理常见的无关标记
        line = re.sub(r'\s*(NEW|-\s*NEW|2024新产季|2023产季|新品)\s*', '', line, flags=re.IGNORECASE)
        
        # 提取冒号后的内容
        if '：' in line:
            parts = line.split('：', 1)
            if len(parts) > 1:
                flavor = parts[1].strip()
                # 进一步清理
                flavor = re.sub(r'^\s*[:：]\s*', '', flavor)
                return flavor
        elif ':' in line:
            parts = line.split(':', 1)
            if len(parts) > 1:
                flavor = parts[1].strip()
                return flavor
        
        # 如果没有冒号，直接返回整行
        return line.strip()
    
    def extract_from_pdf(self, pdf_path):
        """从PDF提取数据的主函数"""
        print("开始提取咖啡豆数据...")
        
        with pdfplumber.open(pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages, 1):
                # 提取文本并分割成行
                text = page.extract_text()
                if not text:
                    continue
                    
                lines = text.split('\n')
                
                for line_num, raw_line in enumerate(lines):
                    line = raw_line.strip()
                    if not line:
                        continue
                    
                    # 1. 检测分区变化
                    cleaned_line = self.clean_for_match(line)
                    
                    if '常用生豆报价单' in cleaned_line:
                        self.current_section = '常用'
                        continue
                    
                    if '精品生豆报价单' in cleaned_line:
                        self.current_section = '精品'
                        continue
                    
                    # 2. 只在目标分区处理数据
                    if self.current_section in ['常用', '精品']:
                        # 检测是否为咖啡豆ID
                        if self.is_coffee_bean_id(line):
                            # 保存前一个咖啡豆（只保存有名称的）
                            if self.current_bean and self.current_bean.get('编号'):
                                if self.current_bean.get('咖啡豆名'):
                                    self.coffee_beans.append(self.current_bean)
                            
                            # 开始新条目
                            self.current_bean = OrderedDict()
                            self.current_bean['类型'] = self.current_section
                            self.current_bean['编号'] = self.clean_bean_id(line)
                            self.current_bean['咖啡豆名'] = ''
                            self.current_bean['风味'] = ''
                            
                            # 提取咖啡豆名（可能跨越多行）
                            if line_num + 1 < len(lines):
                                bean_name, new_idx = self.extract_bean_name_from_lines(lines, line_num + 1)
                                if bean_name:
                                    self.current_bean['咖啡豆名'] = bean_name
                        
                        # 3. 如果当前有咖啡豆条目，处理风味
                        elif self.current_bean and self.current_bean.get('编号'):
                            # 提取风味
                            if not self.current_bean['风味']:
                                if '风味' in line or '风吹' in line:
                                    flavor = self.extract_flavor(line)
                                    if flavor:
                                        self.current_bean['风味'] = flavor
        
        # 保存最后一个条目（只保存有名称的）
        if self.current_bean and self.current_bean.get('编号'):
            if self.current_bean.get('咖啡豆名'):
                self.coffee_beans.append(self.current_bean)
        
        print(f"提取完成，共获得 {len(self.coffee_beans)} 条有效咖啡豆记录。")
        return self.coffee_beans

def save_results(beans, filename="coffee_final.csv"):
    """保存结果到CSV"""
    if not beans:
        print("未提取到任何有效数据")
        return None
    
    df = pd.DataFrame(beans)
    
    # 确保列顺序
    desired_columns = ['类型', '编号', '咖啡豆名', '风味']
    existing_columns = [col for col in desired_columns if col in df.columns]
    df = df[existing_columns]
    
    # 保存到CSV
    df.to_csv(filename, index=False, encoding='utf-8-sig')
    print(f"\n✅ 数据已保存到 {filename}")
    print(f"📊 共提取了 {len(df)} 条记录")
    
    # 显示统计信息
    print("\n📈 按类型统计:")
    if '类型' in df.columns:
        type_counts = df['类型'].value_counts()
        for bean_type, count in type_counts.items():
            print(f"   {bean_type}: {count} 条")
    
    # 显示字段填充率
    print("\n🔍 字段填充率:")
    for field in ['编号', '咖啡豆名', '风味']:
        if field in df.columns:
            filled = df[field].astype(bool).sum()
            rate = filled / len(df) * 100
            print(f"   {field}: {filled}/{len(df)} ({rate:.1f}%)")
    
    # 显示前几条记录
    print(f"\n👀 前10条记录预览:")
    print(df.head(10).to_string(index=False))
    
    return df

# ========== 主程序 ==========
if __name__ == "__main__":
    pdf_file = "金粽_202512.pdf"
    output_file = "coffee_202512.csv"
    
    print("=" * 60)
    print("咖啡豆数据提取器 - 最终版本")
    print("=" * 60)
    
    # 创建提取器并提取数据
    extractor = CoffeeExtractor()
    coffee_data = extractor.extract_from_pdf(pdf_file)
    
    # 保存结果
    df = save_results(coffee_data, output_file)
    
    print("\n" + "=" * 60)
    print("程序执行完成")
    print("=" * 60)