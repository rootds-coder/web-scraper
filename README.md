# Website Scraper

A modern web application that allows you to download entire websites with all their resources. Built with Flask and modern web technologies, this tool makes it easy to archive web pages with their assets.

![Website Scraper Screenshot](static/images/screenshot.png)

## Features

- 🌐 **Complete Website Download**: Downloads entire web pages including HTML, images, scripts, and stylesheets
- 🎯 **Resource Preservation**: Maintains original website structure and file organization
- 🚀 **Fast Processing**: Efficient parallel downloading of resources
- 📦 **ZIP Archive**: Creates a downloadable ZIP file with all website contents
- 💫 **Modern UI**: Clean, responsive interface with real-time progress updates
- 🔒 **Safe & Respectful**: Follows robots.txt guidelines and respects website terms of service

## Live Demo only Ui

Try it out: [Website Scraper](https://web-scraper-five-amber.vercel.app/)

## Tech Stack

- **Backend**: Python/Flask
- **Frontend**: HTML, TailwindCSS, JavaScript
- **Deployment**: Vercel
- **Dependencies**:
  - Flask
  - BeautifulSoup4
  - Requests
  - Other dependencies listed in requirements.txt

## Setup

1. Clone the repository:
```bash
git clone https://github.com/rootds-coder/web-scraper.git
cd website-scraper
```

2. Create a virtual environment and activate it:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Run the application:
```bash
python app.py
```

5. Visit `http://localhost:8080` in your browser

## Usage

1. Enter the URL of the website you want to scrape
2. Click "Start Scraping"
3. Wait for the process to complete
4. Download the ZIP file containing all website resources

## API Endpoints

- `GET /`: Main page
- `POST /scrape`: Start scraping a website
  - Body: `{ "url": "https://example.com" }`
- `GET /download/<job_id>`: Download the scraped website as ZIP


## Important Notes

- Only scrape websites you have permission to access
- Respect robots.txt and website terms of service
- Some websites may block automated requests
- Large websites may take longer to process

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Built with [Flask](https://flask.palletsprojects.com/)
- UI styled with [TailwindCSS](https://tailwindcss.com/)
- Icons from [Font Awesome](https://fontawesome.com/)

## Support

If you encounter any issues or have questions, please [open an issue](https://github.com/rootds-coder/website-scraper/issues). 

