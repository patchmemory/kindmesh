import re

# Read the file
with open('app/app.py', 'r') as file:
    content = file.read()

# Define a function to add keys to text_input calls
def add_key_to_text_input(match):
    # Extract the label from the match
    label = match.group(1)
    # Create a key based on the label
    key = re.sub(r'[^a-zA-Z0-9_]', '_', label.lower())
    # Check if there's already a key parameter
    if 'key=' in match.group(0):
        return match.group(0)  # Return unchanged if key already exists
    # Check if there are other parameters
    if match.group(2):
        # Add key parameter before the closing parenthesis
        return f'st.text_input({label}, {match.group(2)}, key="{key}")'
    else:
        # Add key parameter as the only parameter after the label
        return f'st.text_input({label}, key="{key}")'

# Use regex to find and replace text_input calls
pattern = r'st\.text_input\(([^,]+)(?:,\s*([^)]+))?\)'
modified_content = re.sub(pattern, add_key_to_text_input, content)

# Write the modified content back to the file
with open('app/app.py', 'w') as file:
    file.write(modified_content)

print("Modified app.py to add keys to all text_input calls")