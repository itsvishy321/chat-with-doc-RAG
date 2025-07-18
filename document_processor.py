import requests
from bs4 import BeautifulSoup
import re

class DocumentProcessor:
    def __init__(self):
        self.chunk_size = 1000
        self.chunk_overlap = 200
        
    def fetch_content(self, url):
        """Fetch and extract text content from URL"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            
            # Parse HTML
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
            
            # Extract text
            text = soup.get_text()
            
            # Clean up text
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = ' '.join(chunk for chunk in chunks if chunk)
            
            # Remove extra whitespace
            text = re.sub(r'\s+', ' ', text).strip()
            
            if not text:
                raise ValueError("No text content found in the document")
                
            return text
            
        except Exception as e:
            raise Exception(f"Error fetching content from {url}: {str(e)}")
    
    def chunk_content(self, content):
        """Split content into overlapping chunks"""
        if len(content) <= self.chunk_size:
            return [content]
        
        chunks = []
        start = 0
        
        while start < len(content):
            end = start + self.chunk_size
            
            # If not at the end, try to break at a sentence or word boundary
            if end < len(content):
                # Look for sentence boundary
                sentence_end = content.rfind('.', start, end)
                if sentence_end > start + self.chunk_size // 2:
                    end = sentence_end + 1
                else:
                    # Look for word boundary
                    word_end = content.rfind(' ', start, end)
                    if word_end > start + self.chunk_size // 2:
                        end = word_end
            
            chunk = content[start:end].strip()
            if chunk:
                chunks.append(chunk)
            
            # Move start position with overlap
            start = end - self.chunk_overlap
            if start >= len(content):
                break
        
        return chunks