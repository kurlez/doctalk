import re

def replace_urls(text):
    """
    Replace URLs in the text with "网址"
    """
    url_pattern = re.compile(
        r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
    )
    return url_pattern.sub('网址', text)

def clean_markdown_syntax(text):
    """
    Clean Markdown syntax markers and special characters
    """
    # Remove URLs
    text = replace_urls(text)
    
    # Clean Markdown syntax markers
    patterns = [
        (r'#{1,6}\s*', ''),           # Headers (#, ##, ###, etc.)
        (r'\*\*?(.*?)\*\*?', r'\1'),  # Bold and Italic (* and **)
        (r'__?(.*?)__?', r'\1'),      # Bold and Italic (_ and __)
        (r'`[^`]*`', ''),             # Inline code
        (r'^\s*[-+*]\s+', ''),        # Unordered list markers
        (r'^\s*\d+\.\s+', ''),        # Ordered list markers
        (r'\[(.*?)\]\(.*?\)', r'\1'), # Links
        (r'!\[.*?\]\(.*?\)', ''),     # Images
        (r'(?m)^>\s*(.*?)$', r'\1'),  # Blockquotes
        (r'~{1,2}(.*?)~{1,2}', r'\1'),# Strikethrough
        (r'\|', '，'),                # Table separators to Chinese comma
        (r'^\s*[-=]{3,}\s*$', ''),    # Horizontal rules
        (r'\\\*', '*'),               # Escaped asterisks
        (r'\\`', '`'),                # Escaped backticks
        (r'\\#', '#'),                # Escaped hash symbols
        (r'\\-', '-'),                # Escaped hyphens
        (r'\\([\\`*_{}[\]()#+\-.!])', r'\1'), # Other escaped characters
    ]
    
    # Apply all cleaning patterns
    for pattern, replacement in patterns:
        text = re.sub(pattern, replacement, text, flags=re.MULTILINE)
    
    return text

def process_text_for_speech(text):
    """
    Process text to make it more suitable for speech synthesis
    """
    # Clean Markdown syntax and special characters
    text = clean_markdown_syntax(text)
    
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text)
    
    # Add pause after periods, question marks, and exclamation marks
    text = re.sub(r'([。！？?!.])', r'\1，', text)
    
    # Handle mixed Chinese/English text
    text = re.sub(r'([A-Za-z])([\u4e00-\u9fff])', r'\1 \2', text)
    text = re.sub(r'([\u4e00-\u9fff])([A-Za-z])', r'\1 \2', text)
    
    # Convert common punctuation marks to Chinese equivalents
    punctuation_map = {
        ':': '：',
        ';': '；',
        ',': '，',
        '!': '！',
        '?': '？',
        '(': '（',
        ')': '）',
        '[': '【',
        ']': '】',
        '{': '（',
        '}': '）'
    }
    for en_punct, zh_punct in punctuation_map.items():
        text = text.replace(en_punct, zh_punct)
    
    # Remove duplicate punctuation marks
    text = re.sub(r'[，。！？：；]+', lambda m: m.group(0)[-1], text)
    text = re.sub(r'\n+', '\n', text)
    text = text.replace('\n', '。\n')
    
    # Final cleanup
    text = text.strip()
    text = re.sub(r'。+', '。', text)  # Remove duplicate periods
    text = re.sub(r'，+', '，', text)  # Remove duplicate commas
    
    return text