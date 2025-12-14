#!/usr/bin/env python3
"""
根据12月7日的修复方案，批量修复IndexTTS的缩进和兼容性问题
"""
import re

files_to_fix = {
    'index-tts/indextts/infer_v2.py': [
        (79, 'self.qwen_emo'),  # try块内需要缩进
        (388, 'if emo_text'),    # else块内需要缩进
        (389, 'emo_text = text'),
        (390, 'emo_dict'),
    ],
    'index-tts/indextts/gpt/transformers_generation_utils.py': [
        (36, 'from transformers.integrations.fsdp'),  # try块内需要缩进
    ]
}

def fix_indentation(filepath, line_rules):
    """修复文件缩进"""
    print(f"修复: {filepath}")
    
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    fixed_count = 0
    for line_num, pattern in line_rules:
        idx = line_num - 1  # 转换为0-based索引
        if idx < len(lines):
            line = lines[idx]
            if pattern in line and not line.startswith('    '):
                # 添加4个空格缩进
                lines[idx] = '    ' + line.lstrip()
                print(f"  ✅ 第{line_num}行已修复缩进")
                fixed_count += 1
    
    if fixed_count > 0:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.writelines(lines)
        print(f"  共修复 {fixed_count} 处缩进\n")
    else:
        print(f"  无需修复\n")

def add_compatibility_imports():
    """添加兼容性imports到transformers_generation_utils.py"""
    filepath = 'index-tts/indextts/gpt/transformers_generation_utils.py'
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 如果已经有fallback，跳过
    if 'isin_mps_friendly' in content and 'def isin_mps_friendly' in content:
        print("transformers_generation_utils.py 已有兼容性修复")
        return
    
    # 在文件开头的imports后添加兼容性代码
    compatibility_code = '''
# ========== Compatibility fixes for transformers 4.40.0 ==========
# These imports may not be available in all transformers versions
# Add fallback implementations to ensure compatibility

# Fix 1: EncoderDecoderCache
try:
    from transformers.cache_utils import EncoderDecoderCache
except ImportError:
    EncoderDecoderCache = None

# Fix 2: OffloadedCache  
try:
    from transformers.cache_utils import OffloadedCache
except ImportError:
    OffloadedCache = None

# Fix 3: QuantizedCacheConfig
try:
    from transformers.cache_utils import QuantizedCacheConfig
except ImportError:
    class QuantizedCacheConfig:
        pass

# Fix 4: isin_mps_friendly
try:
    from transformers.pytorch_utils import isin_mps_friendly
except ImportError:
    import torch
    def isin_mps_friendly(elements, test_elements):
        if isinstance(test_elements, int):
            return elements == test_elements
        return torch.isin(elements, test_elements)

# Fix 5: ExtensionsTrie
try:
    from transformers.tokenization_utils import ExtensionsTrie
except ImportError:
    class ExtensionsTrie:
        def __init__(self, vocab):
            pass
# ========== End of compatibility fixes ==========
'''
    
    # 找到第一个from transformers import之后插入
    lines = content.split('\n')
    insert_pos = -1
    
    for i, line in enumerate(lines):
        if i > 20 and 'from transformers' in line and insert_pos == -1:
            # 在所有transformers imports之后插入
            if i < len(lines) - 1 and 'from transformers' not in lines[i+1]:
                insert_pos = i + 1
                break
    
    if insert_pos > 0:
        lines.insert(insert_pos, compatibility_code)
        new_content = '\n'.join(lines)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print("✅ transformers_generation_utils.py 已添加兼容性修复\n")
    else:
        print("⚠️  未找到合适的插入位置\n")

if __name__ == '__main__':
    print("🔧 应用IndexTTS修复...")
    print("="*60)
    
    # 修复缩进
    for filepath, rules in files_to_fix.items():
        fix_indentation(filepath, rules)
    
    # 添加兼容性imports
    add_compatibility_imports()
    
    print("="*60)
    print("✅ 所有修复已应用！")
    print("\n下一步：清理缓存并重启服务")
    print("  find . -name '__pycache__' -type d -delete")
    print("  pkill -f uvicorn && python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000")




