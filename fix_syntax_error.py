import re

def fix_app_py():
    # Read the file
    with open('app/app.py', 'r') as file:
        content = file.read()
    
    # Fix the syntax errors in the file
    # 1. Fix line 229
    content = content.replace(
        'recipient_key = st.text_input("Recipient Key (required, key="text_input_3908")")',
        'recipient_key = st.text_input("Recipient Key (required)", key="text_input_3908")'
    )
    
    # 2. Fix line 334
    content = content.replace(
        'recipient_key = st.text_input("Recipient Key (required, key="text_input_3908")")',
        'recipient_key = st.text_input("Recipient Key (required)", key="text_input_3908")'
    )
    
    # 3. Fix line 595
    content = content.replace(
        'new_recipient_key = st.text_input("Recipient Key (required, key="text_input_3908")")',
        'new_recipient_key = st.text_input("Recipient Key (required)", key="text_input_3908")'
    )
    
    # 4. Fix line 1670
    content = content.replace(
        '"Default Interaction Type (if not mapped, key="text_input_6473")"',
        '"Default Interaction Type (if not mapped)", key="text_input_6473"'
    )
    
    # Write the fixed content back to the file
    with open('app/app.py', 'w') as file:
        file.write(content)
    
    print("Fixed syntax errors in app.py")

if __name__ == "__main__":
    fix_app_py()