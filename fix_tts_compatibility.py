#!/usr/bin/env python3
"""
批量修复IndexTTS的transformers兼容性问题
添加fallback imports
"""
import os
import re

# 需要修复的文件
files_to_fix = [
    '/scratch/kcriss/MoshengAI/index-tts/indextts/gpt/transformers_generation_utils.py',
]

# 修复is_hqq_available
def fix_is_hqq_available(content):
    # 找到import transformers.utils的位置
    pattern = r'from transformers\.utils import.*'
    
    # 添加try-except
    fallback = '''# Compatibility: is_hqq_available not in older transformers
try:
    from transformers.utils import is_hqq_available
except ImportError:
    def is_hqq_available():
        return False'''
    
    # 如果已经有try-except就跳过
    if 'is_hqq_available' in content and 'except ImportError' in content:
        return content
    
    # 在适当位置插入
    lines = content.split('\n')
    new_lines = []
    imported = False
    
    for i, line in enumerate(lines):
        new_lines.append(line)
        # 在最后一个 from transformers 后插入
        if 'from transformers' in line and not imported and i < 100:
            # 检查后面几行是否还有transformers import
            has_more = False
            for j in range(i+1, min(i+5, len(lines))):
                if 'from transformers' in lines[j]:
                    has_more = True
                    break
            
            if not has_more:
                new_lines.append('')
                new_lines.append(fallback)
                imported = True
    
    return '\n'.join(new_lines)

def main():
    print("🔧 开始修复IndexTTS兼容性问题...")
    
    for filepath in files_to_fix:
        if not os.path.exists(filepath):
            print(f"⚠️  文件不存在: {filepath}")
            continue
        
        print(f"处理: {filepath}")
        
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # 应用修复
        content = fix_is_hqq_available(content)
        
        if content != original_content:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"  ✅ 已修复")
        else:
            print(f"  ℹ️  无需修改")
    
    print("\n✅ 修复完成！")

if __name__ == '__main__':
    main()











