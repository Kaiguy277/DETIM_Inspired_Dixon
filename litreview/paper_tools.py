"""
Academic paper search and retrieval toolkit for Dixon Glacier thesis.

Provides unified interface to:
- OpenAlex (primary search; 240M papers, open-access URLs, no auth)
- CrossRef (authoritative DOI metadata verification)
- Unpaywall (legal open-access PDFs)
- arXiv (preprints)
- Semantic Scholar (citation graphs, rate-limited)

Usage:
    from paper_tools import PaperFinder
    pf = PaperFinder()

    # Search
    results = pf.search("glacier temperature index calibration")

    # Verify a DOI
    meta = pf.verify_doi("10.1017/jog.2021.41")

    # Find open-access PDF
    url = pf.find_oa_pdf("10.3389/feart.2015.00054")

    # Download PDF to papers_verified/
    pf.download("10.1017/aog.2023.57")
"""
import os
import json
import time
import urllib.request
import urllib.parse
from pathlib import Path
from typing import Optional

# Contact email for API politeness (use user's email where APIs request it)
EMAIL = "kai.myers.a@gmail.com"
PAPERS_DIR = Path(__file__).parent.parent / "papers_verified"
PAPERS_DIR.mkdir(exist_ok=True)


def _http_get(url: str, timeout: int = 15, retries: int = 2) -> dict:
    """GET JSON with polite User-Agent and retries on rate limit."""
    headers = {'User-Agent': f'thesis-research/1.0 (mailto:{EMAIL})'}
    for attempt in range(retries + 1):
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return json.loads(resp.read().decode())
        except urllib.error.HTTPError as e:
            if e.code == 429 and attempt < retries:
                time.sleep(2 ** (attempt + 1))
                continue
            raise
        except Exception as e:
            if attempt < retries:
                time.sleep(1)
                continue
            raise


class PaperFinder:
    """Unified paper search/verification/download."""

    def search(self, query: str, per_page: int = 10,
               year_range: Optional[tuple] = None,
               source: str = "openalex") -> list:
        """Search for papers. Returns list of dicts with title, authors, year, doi, oa_url."""
        if source == "openalex":
            return self._openalex_search(query, per_page, year_range)
        elif source == "crossref":
            return self._crossref_search(query, per_page, year_range)
        elif source == "arxiv":
            return self._arxiv_search(query, per_page)
        else:
            raise ValueError(f"Unknown source: {source}")

    def _openalex_search(self, query, per_page, year_range):
        q = urllib.parse.quote(query)
        url = f"https://api.openalex.org/works?search={q}&per-page={per_page}"
        if year_range:
            url += f"&filter=from_publication_date:{year_range[0]}-01-01,to_publication_date:{year_range[1]}-12-31"
        url += f"&mailto={EMAIL}"
        data = _http_get(url)
        results = []
        for item in data.get('results', []):
            authors = item.get('authorships', []) or []
            first = authors[0].get('author', {}).get('display_name', '?') if authors else '?'
            last_name = first.split()[-1] if first != '?' else '?'
            results.append({
                'title': item.get('title') or '',
                'authors': [a.get('author', {}).get('display_name', '?') for a in authors[:5]],
                'first_author_last': last_name,
                'n_authors': len(authors),
                'year': item.get('publication_year'),
                'doi': (item.get('doi') or '').replace('https://doi.org/', ''),
                'journal': ((item.get('primary_location') or {}).get('source') or {}).get('display_name', ''),
                'oa_url': (item.get('open_access') or {}).get('oa_url', ''),
                'is_oa': (item.get('open_access') or {}).get('is_oa', False),
                'citations': item.get('cited_by_count', 0),
                'abstract_inv': item.get('abstract_inverted_index'),
            })
        return results

    def _crossref_search(self, query, per_page, year_range):
        q = urllib.parse.quote(query)
        url = f"https://api.crossref.org/works?query={q}&rows={per_page}"
        if year_range:
            url += f"&filter=from-pub-date:{year_range[0]},until-pub-date:{year_range[1]}"
        data = _http_get(url)
        results = []
        for item in data.get('message', {}).get('items', []):
            authors = item.get('author', []) or []
            results.append({
                'title': (item.get('title', ['']) or [''])[0],
                'authors': [f"{a.get('given', '?')} {a.get('family', '?')}" for a in authors[:5]],
                'first_author_last': authors[0].get('family', '?') if authors else '?',
                'n_authors': len(authors),
                'year': ((item.get('issued') or {}).get('date-parts', [[None]])[0] or [None])[0],
                'doi': item.get('DOI', ''),
                'journal': (item.get('container-title', ['']) or [''])[0],
                'citations': item.get('is-referenced-by-count', 0),
            })
        return results

    def _arxiv_search(self, query, per_page):
        import arxiv
        search = arxiv.Search(query=query, max_results=per_page)
        results = []
        for r in search.results():
            results.append({
                'title': r.title,
                'authors': [a.name for a in r.authors],
                'first_author_last': r.authors[0].name.split()[-1] if r.authors else '?',
                'n_authors': len(r.authors),
                'year': r.published.year,
                'doi': r.doi or '',
                'journal': 'arXiv preprint',
                'arxiv_id': r.entry_id.split('/')[-1],
                'pdf_url': r.pdf_url,
                'abstract': r.summary,
            })
        return results

    def verify_doi(self, doi: str) -> Optional[dict]:
        """Verify a DOI exists and return its metadata."""
        doi = doi.replace('https://doi.org/', '').strip()
        try:
            data = _http_get(f"https://api.crossref.org/works/{doi}")
            msg = data['message']
            authors = msg.get('author', []) or []
            return {
                'doi': doi,
                'exists': True,
                'title': (msg.get('title', ['']) or [''])[0],
                'authors': [f"{a.get('given', '?')} {a.get('family', '?')}" for a in authors[:5]],
                'n_authors': len(authors),
                'year': ((msg.get('issued') or {}).get('date-parts', [[None]])[0] or [None])[0],
                'journal': (msg.get('container-title', ['']) or [''])[0],
            }
        except Exception as e:
            return {'doi': doi, 'exists': False, 'error': str(e)[:100]}

    def find_oa_pdf(self, doi: str) -> Optional[str]:
        """Find legal open-access PDF URL for a DOI."""
        doi = doi.replace('https://doi.org/', '').strip()

        # Try OpenAlex first
        try:
            data = _http_get(f"https://api.openalex.org/works/https://doi.org/{doi}?mailto={EMAIL}")
            oa = data.get('open_access', {}) or {}
            if oa.get('is_oa') and oa.get('oa_url'):
                return oa['oa_url']
        except Exception:
            pass

        # Try Unpaywall
        try:
            data = _http_get(f"https://api.unpaywall.org/v2/{doi}?email={EMAIL}")
            if data.get('is_oa'):
                best = data.get('best_oa_location') or {}
                return best.get('url_for_pdf') or best.get('url')
        except Exception:
            pass

        return None

    def download(self, doi: str, filename: Optional[str] = None) -> Optional[Path]:
        """Download OA PDF for a DOI to papers_verified/. Returns path or None."""
        url = self.find_oa_pdf(doi)
        if not url:
            print(f"  No open-access PDF for {doi}")
            return None

        if not filename:
            safe_doi = doi.replace('/', '_').replace('.', '_')
            filename = f"{safe_doi}.pdf"

        dest = PAPERS_DIR / filename
        if dest.exists():
            print(f"  Already have: {dest.name}")
            return dest

        try:
            req = urllib.request.Request(url, headers={
                'User-Agent': f'thesis-research/1.0 (mailto:{EMAIL})'
            })
            with urllib.request.urlopen(req, timeout=30) as resp:
                content = resp.read()
            dest.write_bytes(content)
            print(f"  Downloaded: {dest.name} ({len(content)//1024} KB) from {url}")
            return dest
        except Exception as e:
            print(f"  Download failed for {doi}: {e}")
            return None

    def get_abstract(self, doi: str) -> Optional[str]:
        """Retrieve abstract via OpenAlex (inverted index → text)."""
        doi = doi.replace('https://doi.org/', '').strip()
        try:
            data = _http_get(f"https://api.openalex.org/works/https://doi.org/{doi}?mailto={EMAIL}")
            inv = data.get('abstract_inverted_index')
            if not inv:
                return None
            # Reconstruct: inverted index is {word: [positions]}
            positions = {}
            for word, pos_list in inv.items():
                for pos in pos_list:
                    positions[pos] = word
            words = [positions.get(i, '') for i in range(max(positions.keys()) + 1)] if positions else []
            return ' '.join(words)
        except Exception:
            return None

    def citations_of(self, doi: str, max_results: int = 20) -> list:
        """Find papers that cite this DOI via OpenAlex."""
        doi = doi.replace('https://doi.org/', '').strip()
        try:
            work = _http_get(f"https://api.openalex.org/works/https://doi.org/{doi}?mailto={EMAIL}")
            work_id = work.get('id', '').replace('https://openalex.org/', '')
            if not work_id:
                return []
            data = _http_get(
                f"https://api.openalex.org/works?filter=cites:{work_id}&per-page={max_results}&mailto={EMAIL}"
            )
            results = []
            for item in data.get('results', []):
                authors = item.get('authorships', []) or []
                first = authors[0].get('author', {}).get('display_name', '?') if authors else '?'
                results.append({
                    'title': item.get('title', ''),
                    'first_author': first,
                    'year': item.get('publication_year'),
                    'doi': (item.get('doi') or '').replace('https://doi.org/', ''),
                    'journal': ((item.get('primary_location') or {}).get('source') or {}).get('display_name', ''),
                    'citations': item.get('cited_by_count', 0),
                })
            return results
        except Exception as e:
            print(f"Citations lookup failed: {e}")
            return []


def format_results(results: list, fields: list = None) -> str:
    """Pretty-print search results."""
    if not results:
        return "  (no results)"
    out = []
    for r in results:
        author_str = r.get('first_author_last') or r.get('first_author', '?')
        n = r.get('n_authors', '?')
        author_display = f"{author_str} et al." if n != 1 else author_str
        year = r.get('year', '?')
        title = (r.get('title') or '')[:100]
        journal = (r.get('journal') or '')[:50]
        doi = r.get('doi', '')
        oa_tag = " [OA]" if r.get('is_oa') else ""
        cites = r.get('citations', 0)
        out.append(f"  {author_display} ({year}){oa_tag} — cites: {cites}")
        out.append(f"    {title}")
        out.append(f"    {journal} — DOI: {doi}")
    return '\n'.join(out)


if __name__ == '__main__':
    import sys
    pf = PaperFinder()
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        if cmd == 'search':
            query = ' '.join(sys.argv[2:])
            print(format_results(pf.search(query)))
        elif cmd == 'verify':
            print(json.dumps(pf.verify_doi(sys.argv[2]), indent=2))
        elif cmd == 'download':
            pf.download(sys.argv[2])
        elif cmd == 'abstract':
            print(pf.get_abstract(sys.argv[2]))
    else:
        print("Usage: paper_tools.py [search|verify|download|abstract] <args>")
