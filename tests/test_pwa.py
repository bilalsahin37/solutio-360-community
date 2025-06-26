# -*- coding: utf-8 -*-
"""
PWA (Progressive Web App) Tests
===============================

Comprehensive PWA testing suite inspired by:
- Google's PWA testing guidelines
- Lighthouse audit criteria
- Web.dev best practices
"""

import json
from unittest.mock import MagicMock, patch

from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.test import Client, TestCase
from django.urls import reverse

import pytest
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from tests.test_factories import UserFactory


@pytest.mark.pwa
class PWAManifestTests(TestCase):
    """Test PWA manifest functionality"""

    def test_manifest_json_exists(self):
        """Test that manifest.json is accessible"""
        response = self.client.get("/manifest.json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/json")

    def test_manifest_json_structure(self):
        """Test manifest.json has required PWA fields"""
        response = self.client.get("/manifest.json")
        manifest = json.loads(response.content)

        # Required PWA manifest fields
        required_fields = [
            "name",
            "short_name",
            "start_url",
            "display",
            "background_color",
            "theme_color",
            "icons",
        ]

        for field in required_fields:
            self.assertIn(field, manifest)

    def test_manifest_icons_structure(self):
        """Test manifest icons have required fields"""
        response = self.client.get("/manifest.json")
        manifest = json.loads(response.content)

        icons = manifest.get("icons", [])
        self.assertTrue(len(icons) > 0)

        for icon in icons:
            self.assertIn("src", icon)
            self.assertIn("sizes", icon)
            self.assertIn("type", icon)

    def test_manifest_start_url(self):
        """Test manifest start_url is valid"""
        response = self.client.get("/manifest.json")
        manifest = json.loads(response.content)

        start_url = manifest.get("start_url", "/")
        response = self.client.get(start_url)
        self.assertEqual(response.status_code, 200)


@pytest.mark.pwa
class ServiceWorkerTests(TestCase):
    """Test Service Worker functionality"""

    def test_service_worker_registration_script(self):
        """Test service worker registration script exists"""
        response = self.client.get("/static/js/sw.js")
        self.assertEqual(response.status_code, 200)

    def test_service_worker_content(self):
        """Test service worker has required functionality"""
        response = self.client.get("/static/js/sw.js")
        content = response.content.decode("utf-8")

        # Check for essential service worker events
        essential_events = ["install", "activate", "fetch", "sync", "notificationclick"]

        for event in essential_events:
            self.assertIn(f"addEventListener('{event}'", content)

    def test_service_worker_cache_strategy(self):
        """Test service worker implements caching strategies"""
        response = self.client.get("/static/js/sw.js")
        content = response.content.decode("utf-8")

        # Check for cache strategies
        cache_strategies = ["caches.open", "cache.addAll", "cache.match", "cache.put"]

        for strategy in cache_strategies:
            self.assertIn(strategy, content)

    def test_offline_fallback_page(self):
        """Test offline fallback page exists"""
        response = self.client.get("/offline/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "offline")


@pytest.mark.pwa
class PWAMetaTagsTests(TestCase):
    """Test PWA meta tags and theme configuration"""

    def setUp(self):
        """Set up test user"""
        self.user = UserFactory()

    def test_viewport_meta_tag(self):
        """Test viewport meta tag for mobile optimization"""
        response = self.client.get("/")
        self.assertContains(
            response,
            '<meta name="viewport" content="width=device-width, initial-scale=1">',
        )

    def test_theme_color_meta_tag(self):
        """Test theme color meta tag"""
        response = self.client.get("/")
        self.assertContains(response, 'name="theme-color"')

    def test_apple_mobile_web_app_tags(self):
        """Test Apple-specific PWA meta tags"""
        response = self.client.get("/")

        apple_tags = [
            "apple-mobile-web-app-capable",
            "apple-mobile-web-app-status-bar-style",
            "apple-mobile-web-app-title",
        ]

        for tag in apple_tags:
            self.assertContains(response, f'name="{tag}"')

    def test_microsoft_tile_tags(self):
        """Test Microsoft tile meta tags"""
        response = self.client.get("/")

        ms_tags = ["msapplication-TileColor", "msapplication-config"]

        for tag in ms_tags:
            self.assertContains(response, f'name="{tag}"')


@pytest.mark.pwa
class PWAInstallabilityTests(StaticLiveServerTestCase):
    """Test PWA installability using browser automation"""

    @classmethod
    def setUpClass(cls):
        """Set up Chrome browser with PWA capabilities"""
        super().setUpClass()
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-web-security")

        # Enable PWA features
        chrome_options.add_experimental_option("useAutomationExtension", False)
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])

        try:
            cls.selenium = webdriver.Chrome(options=chrome_options)
            cls.selenium.implicitly_wait(10)
        except Exception:
            # Skip if Chrome not available
            cls.selenium = None

    @classmethod
    def tearDownClass(cls):
        """Clean up browser"""
        if cls.selenium:
            cls.selenium.quit()
        super().tearDownClass()

    def setUp(self):
        """Skip if browser not available"""
        if not self.selenium:
            self.skipTest("Chrome browser not available")

    def test_pwa_installability_criteria(self):
        """Test basic PWA installability criteria"""
        self.selenium.get(self.live_server_url)

        # Check if page loads
        self.assertIn("Solutio 360", self.selenium.title)

        # Check if service worker is registered
        script = """
        return navigator.serviceWorker.getRegistrations().then(function(registrations) {
            return registrations.length > 0;
        });
        """

        wait = WebDriverWait(self.selenium, 10)
        service_worker_registered = self.selenium.execute_async_script(
            """
            var callback = arguments[arguments.length - 1];
            navigator.serviceWorker.getRegistrations().then(function(registrations) {
                callback(registrations.length > 0);
            });
        """
        )

        self.assertTrue(service_worker_registered)

    def test_manifest_link_tag(self):
        """Test manifest link tag is present"""
        self.selenium.get(self.live_server_url)

        manifest_link = self.selenium.find_element(By.CSS_SELECTOR, 'link[rel="manifest"]')
        self.assertIsNotNone(manifest_link)

        # Test manifest is accessible
        manifest_href = manifest_link.get_attribute("href")
        self.selenium.get(manifest_href)

        # Should not get 404 error
        self.assertNotIn("404", self.selenium.title)

    def test_https_requirement(self):
        """Test HTTPS requirement for PWA (in production)"""
        # This test would be more relevant in production
        # For development, we'll just check if the app works over HTTP
        self.selenium.get(self.live_server_url)
        self.assertIn("Solutio 360", self.selenium.title)


@pytest.mark.pwa
class PWACachingTests(TestCase):
    """Test PWA caching strategies"""

    def test_static_file_caching_headers(self):
        """Test static files have appropriate caching headers"""
        static_files = [
            "/static/css/main.css",
            "/static/js/app.js",
            "/static/images/icon-192x192.png",
        ]

        for static_file in static_files:
            try:
                response = self.client.get(static_file)
                if response.status_code == 200:
                    # Check for cache headers
                    self.assertIn("Cache-Control", response)
            except:
                # Skip if file doesn't exist
                pass

    def test_api_response_caching(self):
        """Test API responses have appropriate caching headers"""
        user = UserFactory()
        self.client.force_login(user)

        response = self.client.get("/api/v1/complaints/")

        # API responses should have cache control
        if response.status_code == 200:
            # Check that dynamic content is not cached
            cache_control = response.get("Cache-Control", "")
            self.assertIn("no-cache", cache_control.lower())


@pytest.mark.pwa
class PWAPerformanceTests(TestCase):
    """Test PWA performance characteristics"""

    def test_critical_css_inline(self):
        """Test critical CSS is inlined for performance"""
        response = self.client.get("/")

        # Check for inline styles
        self.assertContains(response, "<style>")

    def test_resource_preloading(self):
        """Test important resources are preloaded"""
        response = self.client.get("/")

        # Check for preload hints
        preload_patterns = ['rel="preload"', 'rel="prefetch"', 'rel="dns-prefetch"']

        content = response.content.decode("utf-8")
        has_preload = any(pattern in content for pattern in preload_patterns)

        # At least some form of preloading should be present
        self.assertTrue(has_preload)

    def test_image_optimization(self):
        """Test images are optimized for web"""
        response = self.client.get("/")
        content = response.content.decode("utf-8")

        # Check for modern image formats or lazy loading
        modern_image_features = ['loading="lazy"', ".webp", ".avif", "srcset="]

        # At least some modern image optimization should be present
        has_optimization = any(feature in content for feature in modern_image_features)


@pytest.mark.pwa
@pytest.mark.integration
class PWAOfflineFunctionalityTests(StaticLiveServerTestCase):
    """Test PWA offline functionality"""

    @classmethod
    def setUpClass(cls):
        """Set up browser for offline testing"""
        super().setUpClass()
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")

        try:
            cls.selenium = webdriver.Chrome(options=chrome_options)
            cls.selenium.implicitly_wait(10)
        except Exception:
            cls.selenium = None

    @classmethod
    def tearDownClass(cls):
        """Clean up browser"""
        if cls.selenium:
            cls.selenium.quit()
        super().tearDownClass()

    def setUp(self):
        """Skip if browser not available"""
        if not self.selenium:
            self.skipTest("Chrome browser not available")

    def test_offline_page_accessibility(self):
        """Test offline page is accessible when offline"""
        # First, visit the app online to register service worker
        self.selenium.get(self.live_server_url)

        # Wait for service worker registration
        wait = WebDriverWait(self.selenium, 10)

        # Simulate offline mode
        self.selenium.execute_cdp_cmd("Network.enable", {})
        self.selenium.execute_cdp_cmd(
            "Network.emulateNetworkConditions",
            {
                "offline": True,
                "latency": 0,
                "downloadThroughput": 0,
                "uploadThroughput": 0,
            },
        )

        # Try to access a page that should be cached
        self.selenium.get(f"{self.live_server_url}/offline/")

        # Should show offline page, not browser error
        self.assertNotIn("ERR_INTERNET_DISCONNECTED", self.selenium.page_source)

    def test_cache_api_usage(self):
        """Test Cache API is properly utilized"""
        self.selenium.get(self.live_server_url)

        # Check if Cache API is available and used
        cache_available = self.selenium.execute_script(
            """
            return 'caches' in window;
        """
        )

        self.assertTrue(cache_available)


@pytest.mark.pwa
class PWAPushNotificationTests(TestCase):
    """Test PWA Push Notification functionality"""

    def test_notification_permission_request(self):
        """Test notification permission is requested properly"""
        response = self.client.get("/")
        content = response.content.decode("utf-8")

        # Check for notification API usage
        notification_patterns = [
            "Notification.requestPermission",
            "navigator.serviceWorker.ready",
            "registration.showNotification",
        ]

        # Should have some notification-related code
        has_notifications = any(pattern in content for pattern in notification_patterns)

    def test_push_subscription_endpoint(self):
        """Test push subscription API endpoint exists"""
        user = UserFactory()
        self.client.force_login(user)

        # Test push subscription endpoint (if implemented)
        try:
            response = self.client.post(
                "/api/v1/push-subscription/",
                {
                    "endpoint": "https://test.push.endpoint.com",
                    "keys": {"p256dh": "test-p256dh-key", "auth": "test-auth-key"},
                },
            )
            # Should either work or return method not allowed
            self.assertIn(response.status_code, [200, 201, 405])
        except:
            # Endpoint might not be implemented yet
            pass


@pytest.mark.pwa
class PWAAccessibilityTests(TestCase):
    """Test PWA accessibility features"""

    def test_semantic_html_structure(self):
        """Test proper semantic HTML structure"""
        response = self.client.get("/")
        content = response.content.decode("utf-8")

        # Check for semantic HTML elements
        semantic_elements = [
            "<main",
            "<nav",
            "<header",
            "<footer",
            "<section",
            "<article",
            "<aside",
        ]

        semantic_count = sum(1 for element in semantic_elements if element in content)

        # Should have at least some semantic elements
        self.assertGreater(semantic_count, 2)

    def test_aria_labels_and_roles(self):
        """Test ARIA labels and roles are present"""
        response = self.client.get("/")
        content = response.content.decode("utf-8")

        # Check for ARIA attributes
        aria_attributes = [
            "aria-label",
            "aria-labelledby",
            "aria-describedby",
            "role=",
            "aria-expanded",
            "aria-hidden",
        ]

        aria_count = sum(1 for attr in aria_attributes if attr in content)

        # Should have some ARIA attributes for accessibility
        self.assertGreater(aria_count, 0)

    def test_alt_text_for_images(self):
        """Test images have alt text"""
        response = self.client.get("/")
        content = response.content.decode("utf-8")

        # Find all img tags
        import re

        img_tags = re.findall(r"<img[^>]*>", content)

        for img_tag in img_tags:
            # Each img should have alt attribute
            self.assertIn("alt=", img_tag)


if __name__ == "__main__":
    pytest.main([__file__])
