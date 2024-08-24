import requests
import csv
import json
import httpx
import time

# My API key
api_key = '98c8ae5a68b69ff18942c293c3474e33'

# Define the base URL for the SCOPUS Search API
base_url = 'https://api.elsevier.com/content/search/scopus'
abstract_base_url = 'https://api.elsevier.com/content/abstract/doi/'

def scopus_paper_date(paper_doi,apikey,retries=5):
    apikey=apikey
    headers={
        "X-ELS-APIKey":apikey,
        "Accept":'application/json'
         }
    timeout = httpx.Timeout(120.0, connect=120.0)
    client = httpx.Client(timeout=timeout,headers=headers)
    query="&view=FULL"
    url=f"https://api.elsevier.com/content/article/doi/"+paper_doi
    for attempt in range(retries):
        try:
            r = client.get(url)
            r.raise_for_status()  # Raises an exception for HTTP error codes
            return r
        except httpx.ReadTimeout:
            print(f"Timeout occurred, retrying ({attempt + 1}/{retries})...")
            time.sleep(10)  # Wait before retrying
        except httpx.HTTPStatusError as e:
            print(f"HTTP error occurred: {e}")
            break
    return None  # Return None if all retries fail
    return r

def download_articles_for_date_range(years):
    # Define the query parameters
    query_params = {
        'query': 'TITLE(NLP) OR ABS(NLP) OR KEY(NLP)',  # Search term in title, abstract, or keywords
        'apiKey': api_key,  # My API key
        'httpAccept': 'application/json',  # The response in JSON format
        'count': 10,  # Number of results to retrieve at once
        'date': years,  # Last 10 years
        'field': 'title,creator,publicationName,prism:coverDate,prism:doi',  # Wanted Fields
        'sort': '-pubyear',  # Sort by publication year descending
    }

    # Initialize a list to hold all articles
    all_articles = []

    # Initialize the start parameter for pagination
    start = 0
    total_results = 1  # Just to enter the loop

    # Loop through all available results (pagination)
    while start < 5000:
        # Update the start parameter for pagination
        query_params['start'] = start

        # Make the request
        response = requests.get(base_url, params=query_params)

        # Check if the request was successful
        if response.status_code == 200:
            # Parse the JSON response
            data = response.json()

            # Extract total results count (if available)
            total_results = int(data.get('search-results', {}).get('opensearch:totalResults', 0))

            # Extract relevant information from each article
            for entry in data.get('search-results', {}).get('entry', []):
                # Extract the title
                title = entry.get('dc:title', 'No Title')

                authors = entry.get('dc:creator', 'No Author')

                # Extract the journal name
                journal = entry.get('prism:publicationName', 'No Journal')

                # Extract the publication year
                year = entry.get('prism:coverDate', 'No Year').split('-')[0]

                # Extract the abstract
                doi = entry.get('prism:doi', 'No DOI')
                # Get document
                y = scopus_paper_date(doi, api_key)
                if y is None:
                    print(f"Skipping DOI {doi} due to repeated timeouts.")
                    continue
                # Parse document
                json_acceptable_string = y.text
                d = json.loads(json_acceptable_string)
                # Print document
                abstract = d['full-text-retrieval-response']['coredata']['dc:description']

                all_articles.append({
                    'Title': title,
                    'Authors': authors,
                    'Journal': journal,
                    'Year': year,
                    'Abstract': abstract
                })

            # Update the start parameter to move to the next set of results
            start += len(data.get('search-results', {}).get('entry', []))
            print(f"Downloaded {start} of {total_results} articles so far...")
            time.sleep(2)  # 2 seconds delay between requests

        else:
            print(f"Failed to retrieve data: {response.status_code}")
            print(response.text)
            break

    # Save the results to a CSV file
    with open('scopus_nlp_articles.csv', 'a', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['Title', 'Authors', 'Journal', 'Year', 'Abstract']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()
        for article in all_articles:
            writer.writerow(article)

    print(f"Downloaded {len(all_articles)} articles and saved to 'scopus_nlp_articles.csv'.")

# Download articles for each date range
date_ranges = ['2023-2024', '2021-2022', '2019-2020','2017-2018', '2016-2015']
for years in date_ranges:
    download_articles_for_date_range(years)

