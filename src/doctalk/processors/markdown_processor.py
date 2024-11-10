import markdown
from bs4 import BeautifulSoup
from ..utils.text_cleaner import process_text_for_speech

def markdown_to_text(markdown_text):
    """
    Convert Markdown text to cleaned plain text suitable for speech synthesis.
    
    This function performs the following steps:
    1. Converts Markdown to HTML using markdown library
    2. Parses the HTML using BeautifulSoup to extract raw text
    3. Processes the text to optimize it for speech synthesis
    
    Args:
        markdown_text (str): Raw markdown text to be converted
        
    Returns:
        str: Processed plain text ready for speech synthesis
        
    Example:
        >>> text = "# Title\\n\\nThis is **bold** and [a link](http://example.com)"
        >>> result = markdown_to_text(text)
        >>> print(result)
        "Title。This is bold and a link。"
    """
    # Convert Markdown to HTML
    # This step handles all markdown syntax and generates structured HTML
    html = markdown.markdown(markdown_text)
    
    # Parse HTML with BeautifulSoup
    # BeautifulSoup helps in extracting clean text from HTML while maintaining structure
    soup = BeautifulSoup(html, 'html.parser')
    
    # Extract raw text from HTML
    # This removes all HTML tags while preserving the content
    text = soup.get_text()
    
    # Process text for speech synthesis
    # This handles punctuation, spacing, and other text normalization
    text = process_text_for_speech(text)
    
    return text