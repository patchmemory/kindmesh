def fix_duplicate_key():
    # Read the file
    with open('app/app.py', 'r') as file:
        content = file.read()
    
    # Fix the duplicate key parameter on line 1670
    content = content.replace(
        'default_interaction_type = st.text_input(\n                                "Default Interaction Type (if not mapped)", key="text_input_6473", \n                                "Other",\n                                key=f"{section}_default_type"\n                            )',
        'default_interaction_type = st.text_input(\n                                "Default Interaction Type (if not mapped)", \n                                "Other",\n                                key=f"{section}_default_type"\n                            )'
    )
    
    # Write the fixed content back to the file
    with open('app/app.py', 'w') as file:
        file.write(content)
    
    print("Fixed duplicate key parameter on line 1670")

if __name__ == "__main__":
    fix_duplicate_key()