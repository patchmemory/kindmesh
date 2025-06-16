import re

def fix_app_py():
    # Read the file
    with open('app/app.py', 'r') as file:
        content = file.read()
    
    # Fix the syntax errors in the file
    # Replace problematic text_input calls with correctly formatted ones
    content = content.replace(
        'recipient_key = st.text_input("Recipient Key (required, key="text_input_3908")", value=st.session_state.recipient_key if "recipient_key" in st.session_state else "", key="_recipient_key__required__")',
        'recipient_key = st.text_input("Recipient Key (required)", value=st.session_state.recipient_key if "recipient_key" in st.session_state else "", key="recipient_key_required")'
    )
    
    content = content.replace(
        'recipient_pseudonym = st.text_input("Recipient Pseudonym (optional, key="text_input_7088")")',
        'recipient_pseudonym = st.text_input("Recipient Pseudonym (optional)", key="recipient_pseudonym_optional")'
    )
    
    # Fix the employment_q3_1 text_input
    content = content.replace(
        'employment_q3_1 = st.text_input(\n                        "If Yes, what is your highest degree level",\n                        value=existing_data.get("employment_q3_1", "", key="__________________________if_yes")\n                    )',
        'employment_q3_1 = st.text_input(\n                        "If Yes, what is your highest degree level",\n                        value=existing_data.get("employment_q3_1", ""),\n                        key="employment_q3_1"\n                    )'
    )
    
    # Fix any other text_input calls without key arguments
    pattern = r'st\.text_input\(([^,]+)(?:,\s*([^)]+))?\)'
    
    def add_key(match):
        full_match = match.group(0)
        
        # Skip if already has a key parameter
        if 'key=' in full_match:
            return full_match
        
        # Extract the label
        label_match = re.search(r'"([^"]*)"', match.group(1))
        if not label_match:
            return full_match
        
        label = label_match.group(1)
        key = re.sub(r'[^a-zA-Z0-9_]', '_', label.lower())
        
        # Find the position of the closing parenthesis
        closing_paren_pos = full_match.rfind(')')
        
        # Insert the key parameter before the closing parenthesis
        return full_match[:closing_paren_pos] + f', key="{key}"' + full_match[closing_paren_pos:]
    
    content = re.sub(pattern, add_key, content)
    
    # Write the fixed content back to the file
    with open('app/app.py', 'w') as file:
        file.write(content)
    
    print("Fixed app.py")

if __name__ == "__main__":
    fix_app_py()