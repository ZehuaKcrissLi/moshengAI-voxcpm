#!/usr/bin/env python3
"""
正确地应用12月7日的修复：只修复缩进，不改imports
"""

def fix_infer_v2():
    """修复infer_v2.py的缩进问题"""
    filepath = 'index-tts/indextts/infer_v2.py'
    
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    fixed = 0
    
    # 修复第80行（第79行是try:）
    if len(lines) > 79:
        if 'self.qwen_emo' in lines[79] and not lines[79].startswith('            '):
            lines[79] = '            ' + lines[79].lstrip()
            fixed += 1
            print(f"✅ 修复 infer_v2.py:80 (try块缩进)")
    
    # 修复388-391行（else块内容）
    for i in [388, 389, 390]:
        if i < len(lines):
            if lines[i].strip() and not lines[i].startswith('        '):
                lines[i] = '        ' + lines[i].lstrip()
                fixed += 1
                print(f"✅ 修复 infer_v2.py:{i+1} (else块缩进)")
    
    if fixed > 0:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.writelines(lines)
        print(f"\n  infer_v2.py: 共修复 {fixed} 处缩进\n")
    
    return fixed

def fix_transformers_utils():
    """修复transformers_generation_utils.py的缩进"""
    filepath = 'index-tts/indextts/gpt/transformers_generation_utils.py'
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    lines = content.split('\n')
    fixed = 0
    
    # 查找并修复try块内的imports
    for i, line in enumerate(lines):
        if i > 30 and i < 100:
            if line.strip().startswith('from transformers') and not line.startswith('    '):
                # 检查上一行是不是try:
                if i > 0 and 'try:' in lines[i-1]:
                    lines[i] = '    ' + line.lstrip()
                    fixed += 1
                    print(f"✅ 修复transformers_generation_utils.py:{i+1} (try块缩进)")
    
    if fixed > 0:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))
        print(f"\n  transformers_generation_utils.py: 共修复 {fixed} 处缩进\n")
    
    return fixed

if __name__ == '__main__':
    print("🔧 应用缩进修复（12月7日的方案）")
    print("="*60)
    
    total_fixed = 0
    total_fixed += fix_infer_v2()
    total_fixed += fix_transformers_utils()
    
    print("="*60)
    if total_fixed > 0:
        print(f"✅ 共修复 {total_fixed} 处缩进问题")
    else:
        print("✅ 无需修复（可能已修复过）")
    
    print("\n⚠️  注意：这个修复只解决缩进问题")
    print("   如果仍有import错误，说明transformers版本本身有问题")
EOF
python3 apply_fixes_correct.py











