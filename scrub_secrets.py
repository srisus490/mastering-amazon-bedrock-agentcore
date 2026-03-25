import re

notebooks = [
    'capstone_project/notebooks/01-foundation.ipynb',
    'capstone_project/notebooks/02-runtime-setup.ipynb',
    'capstone_project/notebooks/03-gateway-integration.ipynb',
    'capstone_project/notebooks/05-identity-oauth.ipynb',
    'capstone_project/notebooks/07-browser-tools.ipynb',
    'capstone_project/notebooks/08-final-integration.ipynb',
]

patterns = [
    (r'AKIA[0-9A-Z]{16}', 'YOUR_AWS_ACCESS_KEY_ID'),
    (r'GOCSPX-[A-Za-z0-9_-]+', 'YOUR_GOOGLE_CLIENT_SECRET'),
    (r'[0-9]+-[a-z0-9]+\.apps\.googleusercontent\.com', 'YOUR_GOOGLE_CLIENT_ID.apps.googleusercontent.com'),
]

for path in notebooks:
    try:
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
        original = content
        for pattern, replacement in patterns:
            content = re.sub(pattern, replacement, content)
        if content != original:
            with open(path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f'Scrubbed: {path}')
        else:
            print(f'Clean:    {path}')
    except Exception as e:
        print(f'ERROR {path}: {e}')

print('Done.')
