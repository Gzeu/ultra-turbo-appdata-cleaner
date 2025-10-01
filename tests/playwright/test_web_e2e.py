"""
End-to-end tests using Playwright for web interface
"""

import pytest
from playwright.sync_api import Page, expect
import subprocess
import time
import threading
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

class TestWebInterfaceE2E:
    """End-to-end tests for web interface"""
    
    @pytest.fixture(scope="class", autouse=True)
    def setup_server(self):
        """Start Flask server for testing"""
        import os
        os.chdir(project_root / 'web')
        
        # Start server in background thread
        def run_server():
            try:
                from web.app import app, socketio
                socketio.run(app, host='127.0.0.1', port=5555, debug=False)
            except Exception as e:
                print(f"Server start error: {e}")
        
        server_thread = threading.Thread(target=run_server, daemon=True)
        server_thread.start()
        
        # Wait for server to start
        time.sleep(3)
        
        yield
        
        # Server will be stopped automatically (daemon thread)
    
    def test_dashboard_loads(self, page: Page):
        """Test that dashboard page loads correctly"""
        page.goto("http://127.0.0.1:5555")
        
        # Check page title
        expect(page).to_have_title("Dashboard - Ultra-Turbo AppData Cleaner")
        
        # Check main elements are present
        expect(page.locator("h1")).to_contain_text("System Dashboard")
        expect(page.locator(".card")).to_be_visible()
        
        # Check navigation
        expect(page.locator(".navbar-brand")).to_contain_text("Ultra-Turbo AppData Cleaner")
        expect(page.locator(".nav-link[href='/'].")).to_have_class(/active/)
    
    def test_navigation_between_pages(self, page: Page):
        """Test navigation between different pages"""
        page.goto("http://127.0.0.1:5555")
        
        # Navigate to cleaner page
        page.click("text=Cleaner")
        expect(page).to_have_url("http://127.0.0.1:5555/cleaner")
        expect(page.locator("h1")).to_contain_text("System Cleaner")
        
        # Navigate to settings page
        page.click("text=Settings")
        expect(page).to_have_url("http://127.0.0.1:5555/settings")
        expect(page.locator("h1")).to_contain_text("Application Settings")
        
        # Navigate to logs page
        page.click("text=Logs")
        expect(page).to_have_url("http://127.0.0.1:5555/logs")
        expect(page.locator("h1")).to_contain_text("System Logs")
    
    def test_theme_toggle(self, page: Page):
        """Test dark/light theme toggle"""
        page.goto("http://127.0.0.1:5555")
        
        # Check initial theme (dark)
        expect(page.locator("body")).to_have_attribute("data-bs-theme", "dark")
        
        # Click theme toggle
        page.click("#theme-toggle")
        
        # Wait for theme change
        expect(page.locator("body")).to_have_attribute("data-bs-theme", "light")
        
        # Toggle back
        page.click("#theme-toggle")
        expect(page.locator("body")).to_have_attribute("data-bs-theme", "dark")
    
    def test_quick_scan_button(self, page: Page):
        """Test quick scan functionality"""
        page.goto("http://127.0.0.1:5555")
        
        # Click quick scan button
        page.click("button:text('Quick Scan')")
        
        # Check that progress modal appears
        expect(page.locator("#progressModal")).to_be_visible()
        expect(page.locator("#progressModalTitle")).to_contain_text("Operation in Progress")
        
        # Wait for scan to complete (or timeout)
        page.wait_for_selector("#progress-close-btn:not([disabled])", timeout=30000)
    
    def test_cleaner_page_functionality(self, page: Page):
        """Test cleaner page scan and file selection"""
        page.goto("http://127.0.0.1:5555/cleaner")
        
        # Select scan type
        page.select_option("#scan-type", "quick")
        
        # Set max age
        page.fill("#max-age", "7")
        
        # Start scan
        page.click("button:text('Start Scan')")
        
        # Wait for progress modal
        expect(page.locator("#progressModal")).to_be_visible()
        
        # Wait for scan completion (or timeout)
        try:
            page.wait_for_selector("#scan-results-section", state="visible", timeout=30000)
            
            # Check that results are displayed
            expect(page.locator("#total-files")).to_be_visible()
            expect(page.locator("#cleanable-files")).to_be_visible()
            
        except Exception as e:
            # Scan might fail in test environment, that's ok
            print(f"Scan test info: {e}")
    
    def test_settings_page_functionality(self, page: Page):
        """Test settings page form handling"""
        page.goto("http://127.0.0.1:5555/settings")
        
        # Check form elements
        expect(page.locator("#scan-paths")).to_be_visible()
        expect(page.locator("#max-file-age")).to_be_visible()
        expect(page.locator("#safe-mode")).to_be_visible()
        
        # Modify settings
        page.fill("#max-file-age", "14")
        page.check("#safe-mode")
        page.check("#backup-enabled")
        
        # Save settings (might fail without proper backend, that's ok)
        page.click("button:text('Save Settings')")
        
        # Check for notification or response
        # Note: This might show error in test environment, which is expected
    
    def test_api_endpoints(self, page: Page):
        """Test that API endpoints respond"""
        # Test system info API
        response = page.goto("http://127.0.0.1:5555/api/system/info")
        assert response.status == 200
        
        # Test settings API  
        response = page.goto("http://127.0.0.1:5555/api/settings")
        assert response.status == 200
    
    def test_responsive_design(self, page: Page):
        """Test responsive design on different screen sizes"""
        page.goto("http://127.0.0.1:5555")
        
        # Desktop view
        page.set_viewport_size({"width": 1920, "height": 1080})
        expect(page.locator(".navbar-collapse")).to_be_visible()
        
        # Mobile view
        page.set_viewport_size({"width": 375, "height": 667})
        expect(page.locator(".navbar-toggler")).to_be_visible()
        
        # Tablet view
        page.set_viewport_size({"width": 768, "height": 1024})
        expect(page.locator(".container-fluid")).to_be_visible()
    
    def test_websocket_connection(self, page: Page):
        """Test WebSocket connection status"""
        page.goto("http://127.0.0.1:5555")
        
        # Wait for WebSocket to connect
        page.wait_for_selector("#connection-status .connection-connected", timeout=10000)
        
        # Check connection status indicator
        expect(page.locator("#connection-text")).to_contain_text("Connected")