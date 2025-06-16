import re

def fix_columns_in_app_py():
    # Read the file
    with open('app/app.py', 'r') as file:
        content = file.read()
    
    # Fix the st.columns() calls that incorrectly have a key argument
    pattern = r'(col\d+(?:,\s*col\d+)*)\s*=\s*st\.columns\(\d+,\s*key=[^)]+\)'
    replacement = r'\1 = st.columns(2)'
    
    content = re.sub(pattern, replacement, content)
    
    # Write the fixed content back to the file
    with open('app/app.py', 'w') as file:
        file.write(content)
    
    print("Fixed st.columns() calls in app.py")

if __name__ == "__main__":
    fix_columns_in_app_py()