"""Verification script for Task 1 setup"""

import sys
from pathlib import Path


def check_file_exists(filepath: str) -> bool:
    """Check if a file exists"""
    exists = Path(filepath).exists()
    status = "✓" if exists else "✗"
    print(f"{status} {filepath}")
    return exists


def check_directory_exists(dirpath: str) -> bool:
    """Check if a directory exists"""
    exists = Path(dirpath).is_dir()
    status = "✓" if exists else "✗"
    print(f"{status} {dirpath}/")
    return exists


def main():
    """Run verification checks"""
    print("=" * 60)
    print("Task 1 Setup Verification")
    print("=" * 60)
    
    all_checks = []
    
    print("\n📁 Directory Structure:")
    all_checks.append(check_directory_exists("src"))
    all_checks.append(check_directory_exists("src/core"))
    all_checks.append(check_directory_exists("tests"))
    all_checks.append(check_directory_exists("config"))
    all_checks.append(check_directory_exists("docker"))
    
    print("\n📄 Core Files:")
    all_checks.append(check_file_exists("pyproject.toml"))
    all_checks.append(check_file_exists("docker-compose.yml"))
    all_checks.append(check_file_exists(".env.example"))
    all_checks.append(check_file_exists("Makefile"))
    all_checks.append(check_file_exists("README.md"))
    
    print("\n🐍 Source Code:")
    all_checks.append(check_file_exists("src/__init__.py"))
    all_checks.append(check_file_exists("src/core/__init__.py"))
    all_checks.append(check_file_exists("src/core/config.py"))
    all_checks.append(check_file_exists("src/core/logging.py"))
    
    print("\n🧪 Tests:")
    all_checks.append(check_file_exists("tests/__init__.py"))
    all_checks.append(check_file_exists("tests/conftest.py"))
    all_checks.append(check_file_exists("tests/test_config.py"))
    all_checks.append(check_file_exists("tests/test_logging.py"))
    
    print("\n🐳 Docker:")
    all_checks.append(check_file_exists("docker/README.md"))
    all_checks.append(check_file_exists("docker/rabbitmq/rabbitmq.conf"))
    all_checks.append(check_file_exists("docker/rabbitmq/definitions.json"))
    all_checks.append(check_file_exists("docker/init-scripts/postgres/01-init-schema.sql"))
    
    print("\n" + "=" * 60)
    if all(all_checks):
        print("✅ All checks passed! Task 1 is complete.")
        print("\nNext steps:")
        print("1. Install dependencies: pip install -e \".[dev]\"")
        print("2. Start Docker services: docker-compose up -d")
        print("3. Run tests: pytest tests/ -v")
        print("4. Move to Task 2: Implement core data models")
        return 0
    else:
        print("❌ Some checks failed. Please review the output above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
