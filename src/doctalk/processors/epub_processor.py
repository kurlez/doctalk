import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup
import html2text
from ..utils.text_cleaner import process_text_for_speech

def epub_to_text(epub_path):
    """
    Convert an EPUB file to plain text suitable for speech synthesis.
    
    This function performs the following steps:
    1. Reads and parses the EPUB file
    2. Extracts book metadata (title)
    3. Processes each chapter sequentially
    4. Cleans and formats the text for optimal speech synthesis
    
    Args:
        epub_path (str): Path to the EPUB file
        
    Returns:
        str: Processed plain text ready for speech synthesis
        
    Note:
        The function handles various EPUB structures:
        - Book title from metadata
        - Chapter titles from headings
        - Content from paragraphs
        All HTML formatting is stripped and text is normalized
    """
    book = epub.read_epub(epub_path)
    texts = []
    
    # Configure HTML to text converter
    # Ignore various HTML elements that wouldn't make sense in speech
    h = html2text.HTML2Text()
    h.ignore_links = True        # Don't include URL texts
    h.ignore_images = True       # Skip image descriptions
    h.ignore_tables = True       # Convert tables to simple text
    h.ignore_emphasis = True     # Ignore bold/italic formatting
    
    # Extract book title from metadata
    title = book.get_metadata('DC', 'title')
    if title:
        texts.append(f"# {title[0][0]}\n\n")
    
    # Process each chapter in the book
    for item in book.get_items():
        if item.get_type() == ebooklib.ITEM_DOCUMENT:
            try:
                # Parse chapter's HTML content
                soup = BeautifulSoup(item.get_content(), 'html.parser')
                
                # Remove script and style elements
                # These elements should not be read in audio
                for script in soup(["script", "style"]):
                    script.decompose()
                
                # Extract and add chapter title if present
                # Look for the first heading element as chapter title
                chapter_title = soup.find(['h1', 'h2', 'h3'])
                if chapter_title:
                    texts.append(f"## {chapter_title.get_text().strip()}\n\n")
                
                # Convert chapter content to plain text
                # Using html2text to handle complex HTML structures
                content = h.handle(str(soup))
                texts.append(content + "\n\n")
                
            except Exception as e:
                print(f"Warning: Error processing chapter: {str(e)}")
                continue
    
    # Join all text parts and process for speech synthesis
    return process_text_for_speech("\n".join(texts))