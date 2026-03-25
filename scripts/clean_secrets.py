#!/usr/bin/env python3
"""
Script to remove hardcoded secrets from notebook files.
Replaces real credentials with placeholder references to environment variables.
"""
import json
import re
import os

notebooks = [
    'capstone_project/notebooks/01-foundation.ipynb',
    'capstone_project/notebooks/02-runtime-setup.ipynb',
    'capstone_project/notebooks/03-gateway-integration.ipynb',
    'capstone_project/notebooks/04-memory-implementation.ipynb',
    'capstone_project/notebooks/05-identity-oauth.ipynb',
    'capstone_project/notebooks/06-code-interpreter.ipynb',
    'capstone_project/notebooks/07-browser-tools.ipynb',
    'capstone_project/notebooks/08-final-integration.ipynb',
]

# Regex patterns and their replacements
replacements = [
    # AWS Access Key ID (starts with AKIA)
    (r'(AKIA[A-Z0-9]{16})', 'YOUR_AWS_ACCESS_KEY_ID'),
    # AWS Secret Access Key (40 char base64-like string after secret key assignment)
    (r"(AWS_SECRET_ACCESS_KEY['\"]?\s*[=:]\s*['\"])([A-Za-z0-9/+=]{39,41})(['\"])",
     r'\1YOUR_AWS_SECRET_ACCESS_KEY\3'),
    # Google OAuth Client ID
    (r'(\d{12}-[a-z0-9]{32}\.apps\.googleusercontent\.com)', 'YOUR_GOOGLE_CLIENT_ID.apps.googleusercontent.com'),
    # Google OAuth Client Secret (GOCSPX- prefix)
    (r'(GOCSPX-[A-Za-z0-9_-]{28})', 'YOUR_GOOGLE_CLIENT_SECRET'),
    # os.environ assignments with hardcoded values
    (r"(os\.environ\[['\"]AWS_ACCESS_KEY_ID['\"]\]\s*=\s*['\"])AKIA[A-Z0-9]{16}(['\"])",
     r"\1YOUR_AWS_ACCESS_KEY_ID\2"),
    (r"(os\.environ\[['\"]AWS_SECRET_ACCESS_KEY['\"]\]\s*=\s*['\"])[A-Za-z0-9/+=]{39,41}(['\"])",
     r"\1YOUR_AWS_SECRET_ACCESS_KEY\2"),
]

def clean_notebook(path):
    if not os.path.exists(path):
        print(f"  SKIP (not found): {path}")
        return

    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()

    original = content
    for pattern, replacement in replacements:
        content = re.sub(pattern, replacement, content)

    if content != original:
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"  CLEANED: {path}")
    else:
        print(f"  OK (no secrets found): {path}")

print("Scanning and cleaning secrets from notebooks...\n")
for nb in notebooks:
    clean_notebook(nb)

print("\nDone. Verify changes with: git diff")
