import os

# Path to the app.py file
app_file_path = '/home/patch/PycharmProjects/KindMesh/app/app.py'

# Read the content of the file
with open(app_file_path, 'r') as file:
    content = file.read()

# Replace all instances of st.experimental_rerun() with st.rerun()
updated_content = content.replace('st.experimental_rerun()', 'st.rerun()')

# Write the updated content back to the file
with open(app_file_path, 'w') as file:
    file.write(updated_content)

print(f"Updated {app_file_path}: replaced all instances of st.experimental_rerun() with st.rerun()")