#!/usr/bin/env python3
"""
Solutio 360 - Open Core Model Hazırlama Script'i
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


# Community (MIT) vs Enterprise (Commercial) feature mapping
FEATURE_MAPPING = {
    "community": {
        "apps": ["core", "users", "complaints", "reports"],  # Basic reporting only
        "features": [
            "basic_auth",
            "simple_dashboard",
            "basic_reporting",
            "pwa_support",
            "rest_api",
            "basic_notifications",
        ],
        "excluded_models": [
            "MLInsight",
            "AnomalyDetection",
            "ModelPerformance",
            "ReinforcementLearningLog",
        ],
    },
    "enterprise": {
        "apps": [
            "analytics",  # Full AI/ML suite
            "saas_features",  # Multi-tenancy
            "enterprise_auth",  # SSO/LDAP
            "advanced_reporting",
            "integrations",
        ],
        "features": [
            "ai_ml_analytics",
            "advanced_dashboard",
            "sso_integration",
            "multitenancy",
            "advanced_reporting",
            "custom_branding",
            "enterprise_api",
            "audit_logging",
        ],
    },
}


def create_directory_structure():
    """Create open core directory structure"""
    print_info("Creating open core directory structure...")

    # Main directories
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

    # Copy core files
    core_files = [
        "manage.py",
        "requirements.txt",
        "docker-compose.yml",
        "Dockerfile",
        "static/",
        "templates/",
        "solutio_360/",
    ]

    for file_path in core_files:
        if Path(file_path).exists():
            if Path(file_path).is_dir():
                shutil.copytree(
                    file_path, community_dir / file_path, dirs_exist_ok=True
                )
            else:
                shutil.copy2(file_path, community_dir / file_path)

    # Copy community apps only
    for app in FEATURE_MAPPING["community"]["apps"]:
        app_path = Path(app)
        if app_path.exists():
            shutil.copytree(app_path, community_dir / app, dirs_exist_ok=True)

    print_success("Community edition created")


def create_enterprise_extensions():
    """Create enterprise extensions"""
    print_info("Creating enterprise extensions...")

    enterprise_dir = Path("solutio-360-enterprise")

    # Copy enterprise apps
    for app in FEATURE_MAPPING["enterprise"]["apps"]:
        app_path = Path(app)
        if app_path.exists():
            shutil.copytree(
                app_path, enterprise_dir / "extensions" / app, dirs_exist_ok=True
            )

    print_success("Enterprise extensions created")


def create_licenses():
    """Create license files for both editions"""
    print_info("Creating license files...")

    # MIT License for community
    mit_license = """MIT License

Copyright (c) 2024 [Your Name/Company]

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

    # Commercial License for enterprise
    commercial_license = """Commercial License

Copyright (c) 2024 [Your Name/Company]. All rights reserved.

This software is proprietary and confidential. Use is subject to a separate
commercial license agreement. Unauthorized use, distribution, or modification
is strictly prohibited.

For licensing information, contact: sales@solutio360.com"""

    # Write licenses
    with open("solutio-360-community/LICENSE", "w") as f:
        f.write(mit_license)

    with open("solutio-360-enterprise/LICENSE", "w") as f:
        f.write(commercial_license)

    print_success("License files created")


def create_documentation():
    """Create documentation for both editions"""
    print_info("Creating documentation...")

    # Community README
    community_readme = """# Solutio 360 Community Edition

![License](https://img.shields.io/badge/license-MIT-green)
![Python](https://img.shields.io/badge/python-3.11+-blue)
![Django](https://img.shields.io/badge/django-5.2+-green)

Modern, open-source complaint management system built with Django and PWA technologies.

## 🚀 Features

- ✅ **Complaint Management**: Create, track, and resolve complaints
- ✅ **User Management**: Role-based access control
- ✅ **Basic Reporting**: Standard reports and analytics
- ✅ **PWA Support**: Offline functionality and mobile app experience
- ✅ **REST API**: Full API access for integrations
- ✅ **Multi-language**: Turkish and English support

## 🆚 Community vs Enterprise

| Feature | Community | Enterprise |
|---------|-----------|------------|
| Basic Complaint Management | ✅ | ✅ |
| User Management | ✅ | ✅ |
| Basic Reporting | ✅ | ✅ |
| PWA Support | ✅ | ✅ |
| AI/ML Analytics | ❌ | ✅ |
| Advanced Dashboard | ❌ | ✅ |
| SSO Integration | ❌ | ✅ |
| Multi-tenant | ❌ | ✅ |
| Custom Branding | ❌ | ✅ |
| Priority Support | ❌ | ✅ |

## 📦 Installation

```bash
git clone https://github.com/yourusername/solutio-360-community
cd solutio-360-community
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

## 💼 Enterprise Edition

Need advanced features for your business? Check out [Solutio 360 Enterprise](https://solutio360.com/enterprise).

## 🤝 Contributing

We welcome contributions! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## 📄 License

This project is licensed under the MIT License - see [LICENSE](LICENSE) file.

## 🆘 Support

- Community Forum: [GitHub Discussions](https://github.com/yourusername/solutio-360-community/discussions)
- Documentation: [docs.solutio360.com](https://docs.solutio360.com)
- Enterprise Support: [sales@solutio360.com](mailto:sales@solutio360.com)
"""

    # Enterprise README
    enterprise_readme = """# Solutio 360 Enterprise Edition

Advanced complaint management platform with AI/ML analytics and enterprise features.

## 🚀 Enterprise Features

- 🤖 **AI/ML Analytics**: Sentiment analysis, auto-categorization, predictive insights
- 📊 **Advanced Dashboard**: Real-time analytics and custom visualizations  
- 🔐 **SSO Integration**: SAML, OIDC, LDAP/Active Directory
- 🏢 **Multi-tenant**: Serve multiple organizations from single instance
- 🎨 **Custom Branding**: White-label solutions with your brand
- 🔧 **Enterprise API**: Advanced API features and webhooks
- 📞 **Priority Support**: Dedicated support team and SLA guarantees

## 💰 Pricing

- **Starter**: $199/month (up to 50 users)
- **Professional**: $499/month (up to 500 users)  
- **Enterprise**: Custom pricing (unlimited users)

## 📞 Contact

- Sales: sales@solutio360.com
- Support: enterprise@solutio360.com
- Phone: +90 XXX XXX XX XX

## 📄 License

Commercial license. All rights reserved.
"""

    # Write documentation
    with open("solutio-360-community/README.md", "w") as f:
        f.write(community_readme)

    with open("solutio-360-enterprise/README.md", "w") as f:
        f.write(enterprise_readme)

    print_success("Documentation created")


def create_build_scripts():
    """Create build scripts for releases"""
    print_info("Creating build scripts...")

    # Community build script
    community_build = """#!/bin/bash
# Solutio 360 Community - Build Script

echo "🏗️ Building Solutio 360 Community Edition..."

# Install dependencies
pip install -r requirements.txt

# Run tests
python manage.py test

# Collect static files
python manage.py collectstatic --noinput

# Build Docker image
docker build -t solutio360-community:latest .

echo "✅ Community edition build complete!"
"""

    # Enterprise build script
    enterprise_build = """#!/bin/bash
# Solutio 360 Enterprise - Build Script

echo "🏗️ Building Solutio 360 Enterprise Edition..."

# Check license
if [ ! -f "license.key" ]; then
    echo "❌ Enterprise license key required!"
    exit 1
fi

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-enterprise.txt

# Run tests
python manage.py test
python manage.py test_enterprise

# Collect static files
python manage.py collectstatic --noinput

# Build Docker image
docker build -t solutio360-enterprise:latest .

echo "✅ Enterprise edition build complete!"
"""

    # Write build scripts
    Path("scripts/build").mkdir(parents=True, exist_ok=True)

    with open("scripts/build/build_community.sh", "w") as f:
        f.write(community_build)

    with open("scripts/build/build_enterprise.sh", "w") as f:
        f.write(enterprise_build)

    # Make executable
    os.chmod("scripts/build/build_community.sh", 0o755)
    os.chmod("scripts/build/build_enterprise.sh", 0o755)

    print_success("Build scripts created")


def create_marketing_materials():
    """Create marketing comparison materials"""
    print_info("Creating marketing materials...")

    # Feature comparison JSON
    comparison = {
        "last_updated": datetime.now().isoformat(),
        "editions": {
            "community": {
                "name": "Community Edition",
                "license": "MIT",
                "price": "Free",
                "features": FEATURE_MAPPING["community"]["features"],
            },
            "enterprise": {
                "name": "Enterprise Edition",
                "license": "Commercial",
                "price": "$199-999/month",
                "features": FEATURE_MAPPING["enterprise"]["features"],
            },
        },
    }

    Path("marketing").mkdir(exist_ok=True)
    with open("marketing/feature_comparison.json", "w") as f:
        json.dump(comparison, f, indent=2)

    print_success("Marketing materials created")


def main():
    """Main function"""
    print(f"{Colors.BOLD}🚀 Solutio 360 - Open Core Model Hazırlama{Colors.END}")
    print("=" * 60)

    print_warning("Bu script mevcut proje yapısını modify edecek!")
    response = input("Devam etmek istiyor musunuz? (y/n): ")

    if response.lower() != "y":
        print_error("İşlem iptal edildi.")
        return

    try:
        # Execute all steps
        create_directory_structure()
        create_community_edition()
        create_enterprise_extensions()
        create_licenses()
        create_documentation()
        create_build_scripts()
        create_marketing_materials()

        print("\n" + "=" * 60)
        print_success("🎉 Open Core model hazırlığı tamamlandı!")
        print("\n📁 Oluşturulan yapı:")
        print("├── solutio-360-community/     (MIT License)")
        print("├── solutio-360-enterprise/    (Commercial License)")
        print("├── docs/                      (Documentation)")
        print("├── scripts/build/             (Build scripts)")
        print("├── marketing/                 (Marketing materials)")
        print("└── legal/                     (Legal documents)")

        print(f"\n{Colors.BOLD}📋 Sonraki Adımlar:{Colors.END}")
        print("1. Kişisel/şirket bilgilerini güncelleyin")
        print("2. GitHub'da iki ayrı repository oluşturun")
        print("3. Community version'u public, Enterprise'ı private yapın")
        print("4. Website ve pricing sayfası hazırlayın")
        print("5. Marketing kampanyası başlatın")

    except Exception as e:
        print_error(f"Hata oluştu: {e}")


if __name__ == "__main__":
    main()
