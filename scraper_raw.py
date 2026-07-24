import asyncio
import nest_asyncio
from urllib.parse import urljoin, urlparse, urldefrag
from bs4 import BeautifulSoup
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, CacheMode, MemoryAdaptiveDispatcher

nest_asyncio.apply()

async def crawl_single_site_async(crawler, start_url, max_pages, ignore_words, run_config, dispatcher):
    IGNORE_EXTS = ('.pdf', '.jpg', '.jpeg', '.png', '.gif', '.zip', '.rar', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', '.mp3', '.mp4', '.avi', '.svg')
        
    data = []
    error_message = None
    page_errors = []
    max_depth = 5
    
    base_domain = urlparse(start_url).netloc
    visited = set()

    def normalize_url(url):
        return urldefrag(url)[0]

    current_urls = {normalize_url(start_url)}
    
    try:
        for depth in range(max_depth):
            if len(data) >= max_pages:
                break
            
            urls_to_crawl = []
            for u in current_urls:
                if u not in visited:
                    parsed_u = urlparse(u)
                    should_ignore = any(word.lower() in u.lower() for word in ignore_words)
                    is_ignored_ext = parsed_u.path.rstrip('/').lower().endswith(IGNORE_EXTS)
                    if not should_ignore and not is_ignored_ext and parsed_u.netloc == base_domain:
                        urls_to_crawl.append(u)
            
            urls_to_crawl = urls_to_crawl[:max_pages - len(data)]
            
            if not urls_to_crawl:
                break

            results = await crawler.arun_many(urls=urls_to_crawl, config=run_config, dispatcher=dispatcher)
            next_level_urls = set()

            for result in results:
                norm_url = normalize_url(result.url)
                visited.add(norm_url)
                
                if not result.success:
                    page_errors.append({
                        "url": result.url,
                        "error": getattr(result, 'error_message', 'Unknown error')
                    })
                    continue
                    
                if result.success and (result.markdown or result.html):
                    title = "No Title"
                    content = result.markdown if result.markdown else ""
                    
                    if result.html:
                        soup = BeautifulSoup(result.html, 'html.parser')
                        title_tag = soup.find('title')
                        if title_tag:
                            title = title_tag.text.strip()
                        if not content:
                            content = soup.get_text(separator='\n', strip=True)
                    
                    import re
                    from datetime import datetime, timezone
                    
                    # Clean up content_text
                    content = re.sub(r'!\[.*?\]\([^\)]+\)', '', content)
                    content = re.sub(r'\[([^\]]*)\]\([^\)]+\)', r'\1', content)
                    gdpr_regex = r'\*?\s*Privacy Overview\s+\*?\s*Strictly Necessary Cookies\s+Privacy Overview\s+This website uses cookies.*?Enable All Save Settings\n?'
                    content = re.sub(gdpr_regex, '', content, flags=re.IGNORECASE | re.DOTALL)
                    cookie_notice_regex = r'We are using cookies to give you the best experience on our website\.\s+You can find out more about which cookies we are using or switch them off in settings\.\s+Accept\s+.*?Close GDPR Cookie Settings'
                    content = re.sub(cookie_notice_regex, '', content, flags=re.IGNORECASE | re.DOTALL)
                    content = re.sub(r'\n{3,}', '\n\n', content).strip()
                    
                    item_id_str = "utem_" + re.sub(r'[^a-zA-Z0-9]', '_', urlparse(result.url).netloc + urlparse(result.url).path).strip('_')
                    
                    meta_desc = None
                    meta_kw = None
                    if result.html:
                        desc_tag = soup.find('meta', attrs={'name': 'description'})
                        if desc_tag: meta_desc = desc_tag.get('content')
                        kw_tag = soup.find('meta', attrs={'name': 'keywords'})
                        if kw_tag: meta_kw = kw_tag.get('content')
                        
                    metadata = {
                        "source_domain": urlparse(result.url).netloc,
                        "language": "en",
                        "page_type": "content_page",
                        "last_update": "",
                        "canonical_url": result.url,
                        "meta_description": meta_desc,
                        "meta_keywords": meta_kw,
                        "crawled_at_utc": datetime.now(timezone.utc).isoformat(),
                        "record_ID": len(data) + 1
                    }
                    
                    item = {
                        "id": item_id_str,
                        "url": result.url,
                        "title": title,
                        "metadata": metadata,
                        "content_text": content
                    }
                    data.append(item)

                    if hasattr(result, 'links') and isinstance(result.links, dict):
                        for link in result.links.get("internal", []):
                            href = link.get("href", "")
                            if href:
                                next_url = normalize_url(urljoin(result.url, href))
                                if next_url not in visited:
                                    parsed_next = urlparse(next_url)
                                    if not parsed_next.path.rstrip('/').lower().endswith(IGNORE_EXTS):
                                        next_level_urls.add(next_url)
                                    
            current_urls = next_level_urls

    except Exception as e:
        error_message = f"Error during crawl on {start_url}: {str(e)}"

    if not data and not error_message:
        if page_errors:
            error_message = f"Failed on {page_errors[0]['url']}: {page_errors[0]['error']}"
        else:
            error_message = f"No text found on {start_url}"
        
    return data, error_message, page_errors

async def scrape_multiple_pages_async(start_urls, max_pages=5, ignore_words=None):
    if ignore_words is None:
        ignore_words = []
        
    if isinstance(start_urls, str):
        start_urls = [start_urls]
        
    max_concurrent = 5
    
    run_config = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS, 
        stream=False,
    )
    
    dispatcher = MemoryAdaptiveDispatcher(
        memory_threshold_percent=95.0,
        check_interval=1.0,
        max_session_permit=max_concurrent
    )

    all_results = {}

    try:
        async with AsyncWebCrawler() as crawler:
            tasks = []
            for url in start_urls:
                tasks.append(crawl_single_site_async(crawler, url, max_pages, ignore_words, run_config, dispatcher))
                
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for idx, res in enumerate(results):
                url = start_urls[idx]
                if isinstance(res, Exception):
                    all_results[url] = {"data": [], "error": f"Fatal error on {url}: {str(res)}", "page_errors": []}
                else:
                    data, err, p_errors = res
                    all_results[url] = {"data": data if data else [], "error": err, "page_errors": p_errors}
    except Exception as e:
        all_results["crawler_error"] = {"data": [], "error": f"Crawler session error: {str(e)}", "page_errors": []}

    return all_results

def scrape_multiple_pages(start_urls, max_pages=5, ignore_words=None):
    import sys
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
        
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
    import nest_asyncio
    nest_asyncio.apply(loop)
    
    return loop.run_until_complete(scrape_multiple_pages_async(start_urls, max_pages, ignore_words))