#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
JetBrains License Key Fetcher
Fetches license keys for JetBrains products from various online sources.
"""

import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime, timedelta
import os
import time
import random
import json
import sys
import logging
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
from typing import List, Set, Dict, Optional
try:
    from github import Github, RateLimitExceededException
except ImportError:
    Github = None
    RateLimitExceededException = Exception

__version__ = "2.0.0"

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class JetBrainsKeyFetcher:
    def __init__(self, days_back: int = 365, output_file: str = "jetbrains_licenses.txt", 
                 max_workers: int = 10, github_token: Optional[str] = None, 
                 log_file: Optional[str] = "fetcher.log") -> None:
        """
        Initialize the JetBrains license key fetcher.
        
        Args:
            days_back: Number of days to look back for licenses
            output_file: File to save found licenses
            max_workers: Maximum number of concurrent workers
            github_token: Optional GitHub API token for increased rate limits
            log_file: File to save detailed logs
        """
        self.days_back = days_back
        self.output_file = output_file
        self.max_workers = max_workers
        self.github_token = github_token
        self.all_licenses: Set[str] = set()
        self.session = requests.Session()
        self.github = Github(github_token) if github_token and Github else None
        
        # Setup logging to file if specified
        if log_file:
            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(logging.DEBUG)
            formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        
        # HTTP headers for web requests
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml",
            "Accept-Language": "en-US,en;q=0.9",
            "Referer": "https://gitee.com/",
            "Connection": "keep-alive",
        }
        
        # Multiple license patterns to catch different formats
        self.license_patterns = [
            r'[A-Z0-9]{5}-[A-Z0-9]{5}-[A-Z0-9]{5}-[A-Z0-9]{5}-[A-Z0-9]{5}',  # Standard format
            r'[A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9]{4}',              # Alternative format
            r'[A-Z0-9]{6}-[A-Z0-9]{6}-[A-Z0-9]{6}',                          # Another format
            r'[A-Z0-9]{3}-[A-Z0-9]{6}-[A-Z0-9]{6}',                          # Yet another format
        ]
        
        # Sources to check for licenses - expanded list
        self.sources = [
            # Gitee repositories
            {"type": "gitee", "name": "pengzhile/ide-eval-resetter", "path": "data/{date}.txt"},
            {"type": "gitee", "name": "superbeyone/J2_B5_A5_C4", "path": "licenses/2025/{date}.md"},
            {"type": "gitee", "name": "pengzhile/ide-eval-resetter", "path": "data/licenses_{date}.txt"},
            {"type": "gitee", "name": "superbeyone/J2_B5_A5_C4", "path": "licenses/2024/{date}.md"},
            {"type": "gitee", "name": "pengzhile/ide-eval-resetter", "path": "data/{date}.txt"},
            # GitHub repositories (will use API if token provided)
            {"type": "github", "name": "jetlicense/keys", "path": "keys/{date}.txt"},
            {"type": "github", "name": "idekeys/jetbrains", "path": "licenses/{date}.md"},
            {"type": "github", "name": "labarmaley64/1ac-JetBrains-PyCharmc-ne", "path": "README.md"},
            {"type": "github", "name": "0xbug/JLS", "path": "README.md"}
        ]
        
        # License server URLs to check
        self.license_servers = [
            "https://jetlicense.nss.im",
            "https://license4j.com",
            "https://licenseserver.jetbrains.com"
        ]
        
        # New scraping strategies
        self.scraping_strategies = [
            self.scrape_github_search,
            self.scrape_gitee_search,
            self.scrape_forum_posts,
            self.scrape_pastebin_sites
        ]
        
        # Create cache directory if it doesn't exist
        self.cache_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cache")
        os.makedirs(self.cache_dir, exist_ok=True)
        
        # Cache file for licenses
        self.cache_file = os.path.join(self.cache_dir, "license_cache.json")
        self.load_cache()
        logger.info(f"Initialized fetcher with {len(self.all_licenses)} cached licenses")

    def load_cache(self) -> None:
        """Load previously found licenses from cache."""
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, 'r') as f:
                    cached_data = json.load(f)
                    self.all_licenses = set(cached_data.get("licenses", []))
            except Exception as e:
                logger.error(f"Error loading cache: {e}")

    def save_licenses(self) -> None:
        """Save found licenses to the output file with proper file handling."""
        if not self.all_licenses:
            logger.warning("No new licenses found to save.")
            return

        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(os.path.abspath(self.output_file)), exist_ok=True)
            
            # Read existing licenses to avoid duplicates
            existing_licenses = set()
            if os.path.exists(self.output_file):
                with open(self.output_file, 'r', encoding='utf-8') as f:
                    existing_licenses = {line.strip() for line in f if line.strip()}
            
            # Add new licenses
            all_licenses = existing_licenses.union(self.all_licenses)
            
            # Write all licenses back to file
            with open(self.output_file, 'w', encoding='utf-8') as f:
                for license_key in sorted(all_licenses):
                    if license_key:  # Skip empty lines
                        f.write(f"{license_key}\n")
            
            new_count = len(self.all_licenses - existing_licenses)
            if new_count > 0:
                logger.info(f"Added {new_count} new licenses to {self.output_file} (Total: {len(all_licenses)})")
            else:
                logger.info("No new licenses to add")
                
        except Exception as e:
            logger.error(f"Error saving licenses: {e}", exc_info=True)
            raise

    def save_cache(self) -> None:
        """Save found licenses to cache."""
        try:
            with open(self.cache_file, 'w') as f:
                json.dump({"licenses": list(self.all_licenses)}, f)
        except Exception as e:
            logger.error(f"Error saving cache: {e}")

    def generate_dates(self) -> List[str]:
        """Generate a list of dates in multiple formats going back specified number of days."""
        dates = []
        today = datetime.now()
        
        for i in range(self.days_back):
            date = today - timedelta(days=i)
            # Generate multiple date formats
            dates.append(date.strftime("%Y-%m-%d"))
            dates.append(date.strftime("%m-%d"))  # MM-DD format
        
        # Also try different years
        current_year = today.year
        for year in range(current_year-2, current_year+2):
            for month in range(1, 13):
                for day in [1, 15]:  # Try 1st and 15th of each month
                    try:
                        date = datetime(year, month, day)
                        dates.append(date.strftime("%Y-%m-%d"))
                    except ValueError:
                        pass
        
        return list(set(dates))  # Remove duplicates

    def construct_urls(self, date: str, source: Dict) -> List[str]:
        """Construct and normalize possible URLs for the given date/source, avoiding malformed duplicates."""
        urls: List[str] = []
        repo_type = source["type"]
        repo_name = source["name"]
        path_template = source["path"]

        try:
            # Render the template
            path = path_template.format(date=date)

            # Helper to ensure we don't double-prepend blob/raw when the template already has them
            def gitee_url(sub_path: str) -> str:
                return f"https://gitee.com/{repo_name}/{sub_path.lstrip('/')}"

            def github_blob_url(sub_path: str) -> str:
                return f"https://github.com/{repo_name}/{sub_path.lstrip('/')}"

            if repo_type == "gitee":
                # If the template already contains blob/ or raw/, use as-is and also try the alt form.
                if path.startswith("blob/") or path.startswith("raw/"):
                    urls.append(gitee_url(path))
                    # Swap blob ↔ raw to try the alternative
                    if path.startswith("blob/"):
                        urls.append(gitee_url(path.replace("blob/", "raw/", 1)))
                    else:
                        urls.append(gitee_url(path.replace("raw/", "blob/", 1)))
                else:
                    # Standard patterns
                    urls.extend([
                        gitee_url(f"blob/master/{path}"),
                        gitee_url(f"raw/master/{path}"),
                        gitee_url(path),
                    ])

                # If date was YYYY-MM-DD, also attempt year/month/day components if placeholders exist
                if "-" in date and any(t in path_template for t in ("{year}", "{month}", "{day}")):
                    year, month, day = date.split("-")
                    component_path = path_template.format(date=date, year=year, month=month, day=day)
                    if component_path != path:
                        urls.append(gitee_url(component_path))

            elif repo_type == "github":
                # If path already starts with blob/ or raw/, respect it
                if path.startswith("blob/") or path.startswith("raw/"):
                    urls.append(github_blob_url(path))
                    # Attempt raw.githubusercontent.com equivalent if possible
                    if path.startswith("blob/"):
                        strip_prefix = path.replace("blob/", "", 1)
                        urls.append(f"https://raw.githubusercontent.com/{repo_name}/main/{strip_prefix}")
                    elif path.startswith("raw/"):
                        # Provide blob form
                        urls.append(github_blob_url(path.replace("raw/", "blob/", 1)))
                else:
                    # Standard forms
                    urls.append(github_blob_url(f"blob/main/{path}"))
                    urls.append(f"https://raw.githubusercontent.com/{repo_name}/main/{path}")
        except Exception as e:
            logger.warning(f"Error constructing URLs for {repo_name} with date {date}: {e}")

        # Deduplicate
        return list(dict.fromkeys(urls))

    def fetch_license_keys_web(self, url: str) -> List[str]:
        """Fetch and extract license keys from the given URL using web scraping."""
        try:
            # Add a small delay to avoid rate limiting
            time.sleep(random.uniform(0.5, 2.0))
            
            response = self.session.get(url, headers=self.headers, timeout=15)
            response.raise_for_status()
            
            # Check if we're looking at HTML or raw content
            if "text/html" in response.headers.get("Content-Type", ""):
                # Parse HTML content
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Try different selectors that might contain the license data
                content_elements = [
                    soup.select_one('.blob_content'),
                    soup.select_one('#code-preview'),
                    soup.select_one('.file_content'),
                    soup.select_one('pre'),
                    soup.select_one('.highlight'),
                    soup.select_one('textarea.content'),
                    soup.select_one('.readme'),
                    soup.select_one('.markdown-body')
                ]
                
                content = ""
                for element in content_elements:
                    if element:
                        content += element.get_text() + "\n"
            else:
                # Raw content
                content = response.text
            
            # Extract license keys using multiple regex patterns
            licenses = []
            for pattern in self.license_patterns:
                licenses.extend(re.findall(pattern, content, re.IGNORECASE | re.MULTILINE))
            
            # Filter valid licenses and add metadata
            valid_licenses = []
            for lic in licenses:
                if self.validate_license(lic):
                    valid_licenses.append(f"{lic} | Source: {url} | Date: {datetime.now().strftime('%Y-%m-%d')}")
            
            if valid_licenses:
                logger.info(f"Found {len(valid_licenses)} license(s) at {url}")
                return valid_licenses
            return []
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching {url}: {e}")
        except Exception as e:
            logger.error(f"Unexpected error processing {url}: {e}")
        return []

    def fetch_license_keys_github(self, repo_name: str, path: str) -> List[str]:
        """Fetch license keys using GitHub API if available."""
        if not self.github:
            return []
        
        try:
            repo = self.github.get_repo(repo_name)
            contents = repo.get_contents(path)
            content = contents.decoded_content.decode('utf-8', errors='ignore')
            
            # Extract license keys using multiple regex patterns
            licenses = []
            for pattern in self.license_patterns:
                licenses.extend(re.findall(pattern, content, re.IGNORECASE | re.MULTILINE))
            
            # Filter valid licenses and add metadata
            valid_licenses = []
            for lic in licenses:
                if self.validate_license(lic):
                    valid_licenses.append(f"{lic} | Source: GitHub {repo_name}/{path} | Date: {datetime.now().strftime('%Y-%m-%d')}")
            
            if valid_licenses:
                logger.info(f"Found {len(valid_licenses)} license(s) in GitHub repo {repo_name}/{path}")
                return valid_licenses
            return []
        except RateLimitExceededException:
            logger.warning(f"GitHub API rate limit exceeded for {repo_name}")
            return []
        except Exception as e:
            logger.error(f"Error fetching from GitHub {repo_name}/{path}: {e}")
            return []

    def validate_license(self, license_key: str) -> bool:
        """Validate if a license key matches expected patterns and check expiration."""
        # Remove any whitespace and convert to uppercase
        license_key = ''.join(license_key.split()).upper()
        
        # Check against known patterns
        patterns = [
            r'^[A-Z0-9]{5}-[A-Z0-9]{5}-[A-Z0-9]{5}-[A-Z0-9]{5}-[A-Z0-9]{5}$',
            r'^[A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9]{4}$',
            r'^[A-Z0-9]{6}-[A-Z0-9]{6}-[A-Z0-9]{6}$',
            r'^[A-Z0-9]{3}-[A-Z0-9]{6}-[A-Z0-9]{6}$'
        ]
        
        # First check if the key matches any pattern
        if not any(re.match(pattern, license_key) for pattern in patterns):
            return False
        
        # Check if license contains an expiration date
        expiration_match = re.search(r'EXP=([0-9]{4}-[0-9]{2}-[0-9]{2})', license_key)
        if expiration_match:
            expiration_date = expiration_match.group(1)
            try:
                exp_date = datetime.strptime(expiration_date, '%Y-%m-%d')
                if exp_date < datetime.now():
                    logger.debug(f"License expired: {license_key}")
                    return False
            except ValueError:
                pass
        
        return True

    def deduplicate_licenses(self, licenses: List[str]) -> List[str]:
        """Remove duplicate licenses while preserving metadata."""
        unique_licenses = []
        seen_keys = set()
        
        for lic in licenses:
            # Extract the actual license key part
            key_part = lic.split(' | ')[0]
            if key_part not in seen_keys:
                seen_keys.add(key_part)
                unique_licenses.append(lic)
            else:
                logger.debug(f"Removed duplicate license: {key_part}")
        
        return unique_licenses

    def process_date(self, date: str) -> Set[str]:
        """Process a single date to find license keys across all sources."""
        found_licenses = set()
        all_urls = []
        github_tasks = []
        
        # Construct URLs for all sources
        for source in self.sources:
            if source["type"] == "github" and self.github:
                try:
                    path = source["path"].format(date=date)
                    github_tasks.append((source["name"], path))
                except Exception:
                    continue
            else:
                urls = self.construct_urls(date, source)
                all_urls.extend(urls)
        
        # Process web scraping tasks
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = [executor.submit(self.fetch_license_keys_web, url) for url in all_urls]
            for future in as_completed(futures):
                licenses = future.result()
                if licenses:
                    found_licenses.update(licenses)
        
        # Process GitHub API tasks if available
        for repo_name, path in github_tasks:
            licenses = self.fetch_license_keys_github(repo_name, path)
            if licenses:
                found_licenses.update(licenses)
        
        return found_licenses

    def check_license_servers(self) -> List[str]:
        """Check known license servers for valid responses or license information."""
        valid_servers = []
        logger.info("Checking known license servers...")
        
        for server_url in self.license_servers:
            try:
                response = self.session.get(server_url, headers=self.headers, timeout=10)
                if response.status_code == 200:
                    logger.info(f"License server active: {server_url}")
                    valid_servers.append(server_url)
                    
                    # Try to extract any license information from response
                    content = response.text
                    licenses = []
                    for pattern in self.license_patterns:
                        licenses.extend(re.findall(pattern, content, re.IGNORECASE | re.MULTILINE))
                    
                    valid_licenses = []
                    for lic in licenses:
                        if self.validate_license(lic):
                            valid_licenses.append(f"{lic} | Source: Server {server_url} | Date: {datetime.now().strftime('%Y-%m-%d')}")
                    if valid_licenses:
                        logger.info(f"Found {len(valid_licenses)} license(s) on server {server_url}")
                        return valid_licenses
                else:
                    logger.debug(f"License server {server_url} returned status {response.status_code}")
            except Exception as e:
                logger.error(f"Error checking license server {server_url}: {e}")
        
        # If no licenses found directly, return list of active servers for further investigation
        if valid_servers and not valid_licenses:
            logger.info(f"Found {len(valid_servers)} active license servers, but no direct licenses")
        return []

    def scrape_github_search(self, query: str) -> List[str]:
        """Scrape GitHub search results for license keys."""
        # Implementation would use GitHub API or web scraping
        # Placeholder for actual implementation
        return []

    def scrape_gitee_search(self, query: str) -> List[str]:
        """Scrape Gitee search results for license keys."""
        # Implementation would use Gitee API or web scraping
        return []

    def scrape_forum_posts(self) -> List[str]:
        """Scrape developer forums for license key sharing."""
        # Implementation would scrape known forums
        return []

    def scrape_pastebin_sites(self) -> List[str]:
        """Scrape pastebin-like sites for shared license keys."""
        # Implementation would scrape pastebin sites
        return []

    def run(self) -> int:
        """Main method to run the license key fetcher. Returns number of new licenses found."""
        logger.info(f"Starting JetBrains license key fetcher (last {self.days_back} days)")
        
        # Clear the output file to avoid duplicates
        try:
            with open(self.output_file, 'w', encoding='utf-8') as f:
                f.write("JetBrains License Keys Report\n")
                f.write("=============================\n\n")
                f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        except Exception as e:
            logger.error(f"Error clearing output file: {e}")
        
        dates = self.generate_dates()
        total_licenses = 0
        total_duplicates = 0
        
        # First check known license servers
        server_licenses = self.check_license_servers()
        server_licenses = self.deduplicate_licenses(server_licenses)
        new_server_licenses = set(server_licenses) - set([lic.split(' | ')[0] for lic in self.all_licenses])
        if new_server_licenses:
            self.all_licenses.update(new_server_licenses)
            total_licenses += len(new_server_licenses)
            with open(self.output_file, 'a', encoding='utf-8') as f:
                f.write("Licenses from Servers:\n")
                for lic in sorted(new_server_licenses):
                    f.write(f"- {lic}\n")
                f.write("\n")
            logger.info(f"Found {len(new_server_licenses)} new license(s) from license servers")
        
        with tqdm(total=len(dates), desc="Processing dates") as pbar:
            for date in dates:
                found_licenses = self.process_date(date)
                found_licenses = self.deduplicate_licenses(found_licenses)
                
                # Add new licenses to our set
                new_licenses = set(found_licenses) - set([lic.split(' | ')[0] for lic in self.all_licenses])
                if new_licenses:
                    self.all_licenses.update(new_licenses)
                    total_licenses += len(new_licenses)
                    
                    # Save to file with formatted output
                    with open(self.output_file, 'a', encoding='utf-8') as f:
                        f.write(f"Licenses for {date}:\n")
                        for lic in sorted(new_licenses):
                            f.write(f"- {lic}\n")
                        f.write("\n")
                    
                    logger.info(f"Found {len(new_licenses)} new license(s) for {date}")
                
                pbar.update(1)
        
        # Run additional scraping strategies
        logger.info("Running additional scraping strategies...")
        for strategy in self.scraping_strategies:
            try:
                licenses = strategy()
                # Process found licenses
            except Exception as e:
                logger.error(f"Error in scraping strategy: {e}")
        
        # Save cache
        self.save_cache()
        
        # Add summary to the output file
        try:
            with open(self.output_file, 'a', encoding='utf-8') as f:
                f.write("\nSummary\n")
                f.write("=======\n")
                f.write(f"Total new licenses found: {total_licenses}\n")
                f.write(f"Total licenses in cache: {len(self.all_licenses)}\n")
                f.write(f"Processing completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        except Exception as e:
            logger.error(f"Error writing summary: {e}")
        
        logger.info(f"Completed! Found {total_licenses} new license(s) in total.")
        logger.info(f"All licenses saved to: {os.path.abspath(self.output_file)}")
        return total_licenses

def main() -> None:
    """Parse command line arguments and run the fetcher."""
    parser = argparse.ArgumentParser(
        description='Fetch JetBrains license keys from various sources.',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument('--days', type=int, default=30, help='Number of days to look back')
    parser.add_argument('--output', type=str, default='jetbrains_licenses.txt', 
                        help='Output file path')
    parser.add_argument('--workers', type=int, default=5, 
                        help='Maximum number of concurrent workers')
    parser.add_argument('--github-token', type=str, default=None,
                        help='GitHub API token for increased rate limits (optional)')
    parser.add_argument('--log-file', type=str, default='fetcher.log',
                        help='Log file path for detailed logging')
    parser.add_argument('--verbose', action='store_true',
                        help='Enable verbose logging')
    parser.add_argument('--version', action='version', version=f'%(prog)s {__version__}')
    
    args = parser.parse_args()
    
    # Set logging level based on verbose flag
    if args.verbose:
        logger.setLevel(logging.DEBUG)
        for handler in logger.handlers:
            handler.setLevel(logging.DEBUG)
    
    fetcher = JetBrainsKeyFetcher(
        days_back=args.days,
        output_file=args.output,
        max_workers=args.workers,
        github_token=args.github_token,
        log_file=args.log_file
    )
    
    start_time = time.time()
    new_licenses = fetcher.run()
    elapsed = time.time() - start_time
    
    logger.info(f"Completed in {elapsed:.2f} seconds")
    if new_licenses > 0:
        logger.info(f"Found {new_licenses} new license key(s)! Check {args.output}")
    else:
        logger.info("No new license keys found.")

if __name__ == "__main__":
    main()