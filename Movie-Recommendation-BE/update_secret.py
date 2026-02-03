import os
import secrets
from django.core.management.utils import get_random_secret_key

env_path = 'c:\\Users\\USER\\Desktop\\PROJECTS\\alx-project-nexus\\Movie-Recommendation-BE\\.env'

with open(env_path, 'r') as f:
    lines = f.readlines()

new_key = get_random_secret_key()
found = False
for i, line in enumerate(lines):
    if line.startswith('SECRET_KEY='):
        lines[i] = f'SECRET_KEY={new_key}\n'
        found = True
    if line.startswith('# Generate new key:'):
        # Update the comment to show correct Windows syntax
        lines[i] = '# Generate new key (Windows): python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"\n'

if not found:
    lines.append(f'SECRET_KEY={new_key}\n')

with open(env_path, 'w') as f:
    f.writelines(lines)

print(f"Updated SECRET_KEY in {env_path}")
