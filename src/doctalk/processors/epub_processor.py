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
                # Skip navigation and table of contents files
                file_name = item.get_name()
                if file_name and any(skip in file_name.lower() for skip in ['nav', 'toc', 'ncx', 'cover']):
                    continue
                
                # Parse chapter's HTML content
                content_bytes = item.get_content()
                if not content_bytes:
                    continue
                    
                soup = BeautifulSoup(content_bytes, 'html.parser')
                
                # Remove script and style elements
                # These elements should not be read in audio
                for script in soup(["script", "style"]):
                    script.decompose()
                
                # Get text content to check if chapter has actual content
                body_text = soup.get_text()
                if not body_text or not body_text.strip():
                    continue
                
                # Extract and add chapter title if present
                # Look for the first heading element as chapter title
                chapter_title = soup.find(['h1', 'h2', 'h3'])
                if chapter_title:
                    title_text = chapter_title.get_text().strip()
                    if title_text:
                        texts.append(f"## {title_text}\n\n")
                
                # Convert chapter content to plain text
                # Using html2text to handle complex HTML structures
                content = h.handle(str(soup))
                
                # Only add if content has actual text (not just whitespace)
                if content and content.strip():
                    texts.append(content + "\n\n")
                
            except Exception as e:
                print(f"Warning: Error processing chapter ({item.get_name()}): {str(e)}")
                continue
    
    # Join all text parts
    combined_text = "\n".join(texts)
    
    # Check if we have any actual content
    if not combined_text or not combined_text.strip():
        raise ValueError(f"EPUB file '{epub_path}' contains no extractable text content")
    
    # Process for speech synthesis
    processed_text = process_text_for_speech(combined_text)
    
    # Final validation
    if not processed_text or not processed_text.strip():
        raise ValueError(f"EPUB file '{epub_path}' produced no valid text after processing")
    
    return processed_text