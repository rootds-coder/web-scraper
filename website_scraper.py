import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin
import zipfile
import shutil
import time

class WebsiteScraper:
    def __init__(self, url):
        self.url = url
        self.base_dir = None
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })

    def create_base_dir(self):
        domain = urlparse(self.url).netloc
        if not domain:
            raise Exception('Invalid URL: could not extract domain')

        timestamp = int(time.time())
        self.base_dir = os.path.join('downloads', f"{domain}_{timestamp}")
        
        os.makedirs(self.base_dir, exist_ok=True)
        if not os.access(self.base_dir, os.W_OK):
            raise Exception(f"Directory is not writable: {self.base_dir}")
        
        return self.base_dir

    def download_file(self, url, save_path):
        try:
            response = self.session.get(url, stream=True, timeout=30)
            response.raise_for_status()
            
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            
            with open(save_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            return True
        except Exception as e:
            print(f"Failed to download {url}: {str(e)}")
            return False

    def extract_resources(self, html, base_url):
        resources = []
        soup = BeautifulSoup(html, 'html.parser')
        
        # Find all resources
        for tag in soup.find_all(['img', 'script', 'link', 'source']):
            url = None
            if tag.name == 'img':
                url = tag.get('src')
            elif tag.name == 'script':
                url = tag.get('src')
            elif tag.name == 'link' and tag.get('rel') == ['stylesheet']:
                url = tag.get('href')
            elif tag.name == 'source':
                url = tag.get('src')
            
            if url:
                absolute_url = self.make_absolute_url(url, base_url)
                if absolute_url:
                    resources.append({
                        'type': tag.name,
                        'url': absolute_url,
                        'path': self.get_resource_path(absolute_url)
                    })
        
        return resources

    def make_absolute_url(self, url, base_url):
        if not url:
            return None
        
        # Skip data URLs and anchors
        if url.startswith('data:') or url.startswith('#'):
            return None
        
        # Already absolute URL
        if url.startswith(('http://', 'https://')):
            return url
        
        # Handle protocol-relative URLs
        if url.startswith('//'):
            scheme = urlparse(base_url).scheme
            return f"{scheme}:{url}"
        
        # Handle relative URLs
        return urljoin(base_url, url)

    def get_resource_path(self, url):
        path = urlparse(url).path
        if not path:
            path = '/index.html'
        
        # Remove leading slash
        path = path.lstrip('/')
        
        # Ensure filename exists
        if not os.path.splitext(path)[1]:
            path = os.path.join(path, 'index.html')
        
        return os.path.join(self.base_dir, path)

    def scrape(self):
        try:
            # Create base directory
            self.create_base_dir()
            
            # Download main page
            response = self.session.get(self.url, timeout=30)
            response.raise_for_status()
            
            # Save main page
            main_page_path = os.path.join(self.base_dir, 'index.html')
            with open(main_page_path, 'wb') as f:
                f.write(response.content)
            
            # Extract resources
            resources = self.extract_resources(response.text, self.url)
            total_resources = len(resources)
            
            # Download resources
            downloaded = 0
            for resource in resources:
                if self.download_file(resource['url'], resource['path']):
                    downloaded += 1
            
            # Create ZIP file
            zip_path = os.path.join('downloads', f"rootcoder_{os.path.basename(self.base_dir)}.zip")
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for root, _, files in os.walk(self.base_dir):
                    for file in files:
                        file_path = os.path.join(root, file)
                        arcname = os.path.relpath(file_path, self.base_dir)
                        zipf.write(file_path, arcname)
            
            # Clean up
            shutil.rmtree(self.base_dir)
            
            return zip_path
            
        except Exception as e:
            if self.base_dir and os.path.exists(self.base_dir):
                shutil.rmtree(self.base_dir)
            raise Exception(f"Scraping failed: {str(e)}") 