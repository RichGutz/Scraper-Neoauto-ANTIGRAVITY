import re

try:
    with open('debug_neoauto.html', 'r', encoding='utf-8') as f:
        content = f.read()

    print(f"Content length: {len(content)}")
    
    # Pattern 1: The one I used
    pattern1 = r'"slug":"(/auto/(?:usado|nuevo)/[^"]+)"'
    matches1 = re.findall(pattern1, content)
    print(f"Pattern 1 matches: {len(matches1)}")
    if matches1:
        print(f"Sample 1: {matches1[0]}")

    # Pattern 2: Escaped quotes?
    # Trying to match \"slug\":\"...
    pattern2 = r'\\"slug\\":\\"(/auto/(?:usado|nuevo)/[^"]+)\\"'
    matches2 = re.findall(pattern2, content)
    print(f"Pattern 2 (escaped) matches: {len(matches2)}")
    if matches2:
        print(f"Sample 2: {matches2[0]}")
        
    # Pattern 3: Simple
    pattern3 = r'slug":"([^"]+)"'
    matches3 = re.findall(pattern3, content)
    print(f"Pattern 3 (simple) matches: {len(matches3)}")
    for i, m in enumerate(matches3[:5]):
        print(f"  {i}: {m}")

except Exception as e:
    print(f"Error: {e}")
