import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from typing import Dict, List, Optional


class ComplianceModel:
    def __init__(self, url: str):
        self.url = url if url.startswith(('http://', 'https://')) else f'https://{url}'
        self.html = None
        self.soup = None
        self.results = {}
        
    def fetch_website(self) -> bool:
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = requests.get(self.url, headers=headers, timeout=10)
            response.raise_for_status()
            self.html = response.text
            self.soup = BeautifulSoup(self.html, 'lxml')
            return True
        except Exception as e:
            self.results['error'] = str(e)
            return False
    
    def detect_cookie_banner(self) -> Dict:
        keywords = [
            'cookie', 'cookies', 'consent', 'accept cookies', 
            'cookie policy', 'we use cookies', 'cookie consent',
            'cookie notice', 'cookie preferences', 'manage cookies'
        ]
        
        text = self.soup.get_text().lower()
        found_keywords = [k for k in keywords if k in text]
        
        banner_elements = self.soup.find_all(['div', 'section', 'aside'], 
                                             class_=lambda x: x and any(
                                                 term in str(x).lower() 
                                                 for term in ['cookie', 'consent', 'gdpr', 'privacy-banner']
                                             ))
        
        has_banner = len(found_keywords) > 0 or len(banner_elements) > 0
        
        self.results['cookie_banner'] = {
            'detected': has_banner,
            'keywords_found': found_keywords[:5],
            'banner_elements': len(banner_elements)
        }
        return self.results['cookie_banner']
    
    def detect_tracking_scripts(self) -> Dict:
        trackers = {
            'Google Analytics': ['google-analytics.com', 'googletagmanager.com', 'ga.js', 'analytics.js'],
            'Facebook Pixel': ['connect.facebook.net', 'facebook.com/tr'],
            'Google Ads': ['googleadservices.com', 'doubleclick.net'],
            'Hotjar': ['hotjar.com'],
            'Mixpanel': ['mixpanel.com'],
            'Segment': ['segment.com', 'cdn.segment.com'],
            'Intercom': ['intercom.io', 'widget.intercom.io'],
            'HubSpot': ['hubspot.com', 'hs-scripts.com'],
            'Salesforce': ['salesforce.com'],
            'LinkedIn Insight': ['snap.licdn.com']
        }
        
        scripts = self.soup.find_all('script')
        detected_trackers = {}
        all_scripts = []
        
        for script in scripts:
            src = script.get('src', '')
            content = script.string or ''
            all_scripts.append(src)
            
            for tracker_name, patterns in trackers.items():
                for pattern in patterns:
                    if pattern in src or pattern in content:
                        if tracker_name not in detected_trackers:
                            detected_trackers[tracker_name] = []
                        if src:
                            detected_trackers[tracker_name].append(src)
        
        self.results['tracking_scripts'] = {
            'detected_trackers': detected_trackers,
            'total_trackers': len(detected_trackers),
            'tracker_names': list(detected_trackers.keys()),
            'total_scripts': len(scripts)
        }
        return self.results['tracking_scripts']
    
    def get_privacy_policy(self) -> Dict:
        links = self.soup.find_all('a', href=True)
        privacy_links = []
        
        privacy_keywords = ['privacy', 'privacidad', 'datenschutz', 'confidentialité']
        
        for link in links:
            href = link.get('href', '')
            text = link.get_text().lower()
            
            if any(keyword in text or keyword in href.lower() for keyword in privacy_keywords):
                full_url = urljoin(self.url, href)
                privacy_links.append({
                    'url': full_url,
                    'text': link.get_text().strip()
                })
        
        unique_links = []
        seen_urls = set()
        for link in privacy_links:
            if link['url'] not in seen_urls:
                unique_links.append(link)
                seen_urls.add(link['url'])
        
        self.results['privacy_policy'] = {
            'found': len(unique_links) > 0,
            'links': unique_links[:3],
            'count': len(unique_links)
        }
        return self.results['privacy_policy']
    
    def detect_contact_information(self) -> Dict:
        contact_keywords = ['contact', 'email', 'phone', 'address', 'support']
        text = self.soup.get_text().lower()
        
        has_contact = any(keyword in text for keyword in contact_keywords)
        
        email_pattern = self.soup.find_all(string=lambda text: text and '@' in text)
        
        self.results['contact_info'] = {
            'detected': has_contact,
            'emails_found': len(email_pattern) > 0
        }
        return self.results['contact_info']
    
    def run_all(self) -> Dict:
        if not self.fetch_website():
            return self.results
        
        self.detect_cookie_banner()
        self.detect_tracking_scripts()
        self.get_privacy_policy()
        self.detect_contact_information()
        
        self.results['url'] = self.url
        self.results['scan_completed'] = True
        
        return self.results
