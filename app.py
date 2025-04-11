from flask import Flask, render_template, request, jsonify, send_file
import os
import uuid
import requests
from bs4 import BeautifulSoup
import zipfile
import io
import threading
import time
from urllib.parse import urljoin, urlparse
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# In-memory storage for scraping jobs
jobs = {}

def is_valid_url(url):
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except:
        return False

def scrape_website(url, job_id):
    try:
        logger.info(f"Starting scrape for URL: {url}")
        
        # Update job status
        jobs[job_id] = {
            'status': 'in_progress',
            'progress': 0,
            'files': {
                'html': 0,
                'images': 0,
                'scripts': 0,
                'styles': 0
            }
        }
        
        # Create a temporary directory for this job
        temp_dir = f"temp_{job_id}"
        os.makedirs(temp_dir, exist_ok=True)
        
        # Set headers to mimic a browser
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        # Download the main page
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code != 200:
            raise Exception(f"Failed to fetch URL: {response.status_code}")
        
        # Parse the HTML
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Save the main HTML file
        with open(os.path.join(temp_dir, 'index.html'), 'w', encoding='utf-8') as f:
            f.write(response.text)
        jobs[job_id]['files']['html'] += 1
        
        # Find and download resources
        base_url = url
        resources = {
            'img': [],
            'script': [],
            'link': []
        }
        
        # Collect all resources
        for tag in soup.find_all(['img', 'script', 'link']):
            if tag.name == 'img' and tag.get('src'):
                resources['img'].append(tag['src'])
            elif tag.name == 'script' and tag.get('src'):
                resources['script'].append(tag['src'])
            elif tag.name == 'link' and tag.get('rel') == ['stylesheet'] and tag.get('href'):
                resources['link'].append(tag['href'])
        
        # Download resources
        total_resources = sum(len(res) for res in resources.values())
        downloaded = 0
        
        for resource_type, urls in resources.items():
            for resource_url in urls:
                try:
                    # Make absolute URL
                    abs_url = urljoin(base_url, resource_url)
                    
                    # Download the resource with timeout
                    res_response = requests.get(abs_url, headers=headers, timeout=10)
                    if res_response.status_code == 200:
                        # Create appropriate directory
                        res_dir = os.path.join(temp_dir, resource_type)
                        os.makedirs(res_dir, exist_ok=True)
                        
                        # Save the file
                        filename = os.path.basename(urlparse(abs_url).path) or f"file_{downloaded}"
                        filepath = os.path.join(res_dir, filename)
                        
                        with open(filepath, 'wb') as f:
                            f.write(res_response.content)
                        
                        # Update counters
                        if resource_type == 'img':
                            jobs[job_id]['files']['images'] += 1
                        elif resource_type == 'script':
                            jobs[job_id]['files']['scripts'] += 1
                        elif resource_type == 'link':
                            jobs[job_id]['files']['styles'] += 1
                    
                    downloaded += 1
                    progress = (downloaded / total_resources) * 100
                    jobs[job_id]['progress'] = int(progress)
                    
                except Exception as e:
                    logger.error(f"Error downloading {resource_url}: {str(e)}")
        
        # Create ZIP file
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, _, files in os.walk(temp_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, temp_dir)
                    zipf.write(file_path, arcname)
        
        # Clean up
        for root, dirs, files in os.walk(temp_dir, topdown=False):
            for name in files:
                os.remove(os.path.join(root, name))
            for name in dirs:
                os.rmdir(os.path.join(root, name))
        os.rmdir(temp_dir)
        
        # Update job status
        jobs[job_id]['status'] = 'completed'
        jobs[job_id]['zip_data'] = zip_buffer.getvalue()
        logger.info(f"Scraping completed for job {job_id}")
        
    except Exception as e:
        logger.error(f"Error in scrape_website: {str(e)}")
        jobs[job_id]['status'] = 'failed'
        jobs[job_id]['error'] = str(e)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/scrape', methods=['POST'])
def start_scrape():
    try:
        data = request.get_json()
        url = data.get('url')
        
        if not url or not is_valid_url(url):
            return jsonify({'error': 'Invalid URL'}), 400
        
        job_id = str(uuid.uuid4())
        logger.info(f"Starting new scraping job {job_id} for URL: {url}")
        
        # Start scraping in a separate thread
        thread = threading.Thread(target=scrape_website, args=(url, job_id))
        thread.daemon = True
        thread.start()
        
        return jsonify({'job_id': job_id})
    except Exception as e:
        logger.error(f"Error in start_scrape: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/status/<job_id>')
def get_status(job_id):
    try:
        if job_id not in jobs:
            return jsonify({'error': 'Job not found'}), 404
        
        job = jobs[job_id]
        return jsonify({
            'status': job['status'],
            'progress': job['progress'],
            'files': job['files']
        })
    except Exception as e:
        logger.error(f"Error in get_status: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/download/<job_id>')
def download(job_id):
    try:
        if job_id not in jobs or jobs[job_id]['status'] != 'completed':
            return jsonify({'error': 'File not ready'}), 404
        
        zip_data = jobs[job_id]['zip_data']
        response = send_file(
            io.BytesIO(zip_data),
            mimetype='application/zip',
            as_attachment=True,
            download_name=f'scraped_website_{job_id}.zip'
        )
        
        # Clean up
        del jobs[job_id]
        
        return response
    except Exception as e:
        logger.error(f"Error in download: {str(e)}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080) 