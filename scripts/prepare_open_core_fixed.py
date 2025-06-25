#!/usr/bin/env python3
"""
Solutio 360 - Open Core Model Hazırlama Script'i (Fixed)
Mevcut projeden community ve enterprise versiyonları ayırır
"""

import json
import os
import shutil
from datetime import datetime
from pathlib import Path


# Renkli output için
class Colors:
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    BLUE = "\033[94m"
    END = "\033[0m"
    BOLD = "\033[1m"


def print_info(msg):
    print(f"{Colors.BLUE}[INFO]{Colors.END} {msg}")


def print_success(msg):
    print(f"{Colors.GREEN}[SUCCESS]{Colors.END} {msg}")


def print_warning(msg):
    print(f"{Colors.YELLOW}[WARNING]{Colors.END} {msg}")


def print_error(msg):
    print(f"{Colors.RED}[ERROR]{Colors.END} {msg}")


def create_directory_structure():
    """Create open core directory structure"""
    print_info("Creating open core directory structure...")

    directories = [
        "solutio-360-community/",
        "solutio-360-enterprise/",
        "solutio-360-enterprise/extensions/",
        "docs/community/",
        "docs/enterprise/",
        "scripts/build/",
        "marketing/",
        "legal/",
    ]

    for dir_path in directories:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
        print_success(f"Created: {dir_path}")


def create_community_edition():
    """Create community edition (MIT licensed)"""
    print_info("Creating community edition...")

    community_dir = Path("solutio-360-community")

    # Core apps for community
    community_apps = ["core", "users", "complaints", "reports"]

    # Copy basic files
    basic_files = ["manage.py", "requirements.txt", "pytest.ini"]

    for file_path in basic_files:
        if Path(file_path).exists():
            shutil.copy2(file_path, community_dir / file_path)
            print_success(f"Copied: {file_path}")

    # Copy community apps
    for app in community_apps:
        app_path = Path(app)
        if app_path.exists():
            dest_path = community_dir / app
            if dest_path.exists():
                shutil.rmtree(dest_path)
            shutil.copytree(app_path, dest_path)
            print_success(f"Copied app: {app}")

    # Copy essential directories
    essential_dirs = ["static", "templates", "solutio_360"]
    for dir_name in essential_dirs:
        if Path(dir_name).exists():
            dest_path = community_dir / dir_name
            if dest_path.exists():
                shutil.rmtree(dest_path)
            shutil.copytree(dir_name, dest_path)
            print_success(f"Copied directory: {dir_name}")


def create_enterprise_extensions():
    """Create enterprise extensions"""
    print_info("Creating enterprise extensions...")

    enterprise_dir = Path("solutio-360-enterprise")

    # Enterprise apps
    enterprise_apps = ["analytics", "saas_features"]

    for app in enterprise_apps:
        app_path = Path(app)
        if app_path.exists():
            dest_path = enterprise_dir / "extensions" / app
            if dest_path.exists():
                shutil.rmtree(dest_path)
            shutil.copytree(app_path, dest_path)
            print_success(f"Created enterprise extension: {app}")


def create_license_files():
    """Create license files"""
    print_info("Creating license files...")

    # MIT License for community
    mit_license = """MIT License

Copyright (c) 2024 Solutio 360 Team

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE."""

    # Commercial License
    commercial_license = """Commercial License

Copyright (c) 2024 Solutio 360 Team. All rights reserved.

This software is proprietary and confidential. Use is subject to a separate
commercial license agreement. Unauthorized use, distribution, or modification
is strictly prohibited.

For licensing information, contact: sales@solutio360.com"""

    # Write licenses
    with open("solutio-360-community/LICENSE", "w", encoding="utf-8") as f:
        f.write(mit_license)

    with open("solutio-360-enterprise/LICENSE", "w", encoding="utf-8") as f:
        f.write(commercial_license)

    print_success("License files created")


def create_readme_files():
    """Create README files"""
    print_info("Creating README files...")

    # Community README
    community_readme = """# Solutio 360 Community Edition

Modern, open-source complaint management system built with Django and PWA technologies.

## Features

- Complaint Management: Create, track, and resolve complaints
- User Management: Role-based access control  
- Basic Reporting: Standard reports and analytics
- PWA Support: Offline functionality and mobile app experience
- REST API: Full API access for integrations
- Multi-language: Turkish and English support

## Installation

```bash
git clone https://github.com/yourusername/solutio-360-community
cd solutio-360-community
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

## Enterprise Edition

Need advanced features? Check out Solutio 360 Enterprise with AI/ML analytics, 
SSO integration, and multi-tenant support.

## License

MIT License - see LICENSE file for details.
"""

    # Enterprise README
    enterprise_readme = """# Solutio 360 Enterprise Edition

Advanced complaint management platform with AI/ML analytics and enterprise features.

## Enterprise Features

- AI/ML Analytics: Sentiment analysis, auto-categorization, predictive insights
- Advanced Dashboard: Real-time analytics and custom visualizations
- SSO Integration: SAML, OIDC, LDAP/Active Directory  
- Multi-tenant: Serve multiple organizations
- Custom Branding: White-label solutions
- Priority Support: Dedicated support team

## Contact

- Sales: sales@solutio360.com
- Support: enterprise@solutio360.com

## License

Commercial license. All rights reserved.
"""

    # Write README files
    with open("solutio-360-community/README.md", "w", encoding="utf-8") as f:
        f.write(community_readme)

    with open("solutio-360-enterprise/README.md", "w", encoding="utf-8") as f:
        f.write(enterprise_readme)

    print_success("README files created")


def create_gitignore():
    """Create .gitignore files"""
    print_info("Creating .gitignore files...")

    gitignore_content = """# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Django
*.log
local_settings.py
db.sqlite3
media

# Environment
.env
.venv
env/
venv/
ENV/

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db
"""

    with open("solutio-360-community/.gitignore", "w", encoding="utf-8") as f:
        f.write(gitignore_content)

    with open("solutio-360-enterprise/.gitignore", "w", encoding="utf-8") as f:
        f.write(gitignore_content)

    print_success(".gitignore files created")


def main():
    """Main function"""
    print("Solutio 360 - Open Core Model Hazırlama (Auto Mode)")
    print("=" * 60)

    try:
        create_directory_structure()
        create_community_edition()
        create_enterprise_extensions()
        create_license_files()
        create_readme_files()
        create_gitignore()

        print("\n" + "=" * 60)
        print_success("Open Core model hazırlığı tamamlandı!")
        print("\nOluşturulan yapı:")
        print("├── solutio-360-community/     (MIT License)")
        print("├── solutio-360-enterprise/    (Commercial License)")
        print("├── docs/                      (Documentation)")
        print("├── scripts/build/             (Build scripts)")
        print("├── marketing/                 (Marketing materials)")
        print("└── legal/                     (Legal documents)")

        print("\nSonraki Adımlar:")
        print("1. GitHub repositories oluştur")
        print("2. Community version'u public yap")
        print("3. Enterprise version'u private yap")
        print("4. Website ve pricing hazırla")

    except Exception as e:
        print_error(f"Hata oluştu: {e}")


if __name__ == "__main__":
    main()
