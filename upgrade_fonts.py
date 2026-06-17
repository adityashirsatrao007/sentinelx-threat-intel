import os
import re

directory = 'frontend/src'

replacements = {
    r'text-\[9px\]': 'text-xs',
    r'text-\[10px\]': 'text-sm',
    r'text-\[11px\]': 'text-sm',
    r'text-\[12px\]': 'text-base',
    r'text-xs': 'text-sm'
}

for root, _, files in os.walk(directory):
    for file in files:
        if file.endswith('.tsx'):
            filepath = os.path.join(root, file)
            with open(filepath, 'r') as f:
                content = f.read()
            
            # Temporarily protect 'text-xs' if we are replacing it
            # But since text-xs to text-sm is straightforward, we can just do it in order
            
            new_content = content
            for old, new in replacements.items():
                new_content = re.sub(old, new, new_content)
                
            if content != new_content:
                with open(filepath, 'w') as f:
                    f.write(new_content)
                print(f"Updated {filepath}")

