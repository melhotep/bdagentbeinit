# apify-actor-python-template

This is a template for creating Python actors on the Apify platform.

## Requirements

Python 3.9+

## Getting started

### Install dependencies

```bash
pip install -r requirements.txt
```

### Run locally

```bash
python -m src
```

## Deployment to Apify

There are two ways to deploy this actor to Apify:

### 1. Using the Apify CLI

Install the Apify CLI:

```bash
npm install -g apify-cli
```

Deploy the actor:

```bash
apify push
```

### 2. Using the Apify Console

1. Go to [Apify Console](https://console.apify.com/)
2. Click on "Create new" > "Actor"
3. Choose "Custom actor"
4. Set the name and click "Create"
5. In the "Source" tab, click "Upload ZIP" and select the ZIP file of this project
6. Click "Save"

## Input

The actor accepts the following input parameters:

- `urls` (Array): List of URLs to scrape
- `query` (String): Search query to use
- `maxPages` (Number): Maximum number of pages to scrape per site

Example input:

```json
{
  "urls": [
    "https://www.adnoc.ae/en/search?query=iraq+oil",
    "https://english.ahram.org.eg/UI/Front/Search.aspx?Text=iraq%20oil",
    "https://www.aljazeera.com/search/iraq%20oil?sort=date"
  ],
  "query": "iraq oil",
  "maxPages": 1
}
```

## Output

The actor outputs a dataset of news articles with the following fields:

- `title`: Article title
- `url`: Article URL
- `date`: Publication date
- `snippet`: Article snippet or summary
- `source`: Source website name
- `query`: Search query used
- `source_url`: Original search URL

## Customization

To add support for additional websites, modify the `site_scrapers.py` file and add a new scraper class for the website.
