#!/usr/bin/env python3
"""
Script to generate a test EPUB file for testing purposes.
"""
import ebooklib
from ebooklib import epub
import os

def create_test_epub():
    """Create a simple test EPUB file with sample content."""
    
    # Create a new EPUB book
    book = epub.EpubBook()
    
    # Set metadata
    book.set_identifier('test_epub_001')
    book.set_title('Test Book for DocTalk')
    book.set_language('en')
    book.add_author('DocTalk Test Author')
    
    # Chapter 1
    chapter1 = epub.EpubHtml(
        title='Introduction',
        file_name='chapter1.xhtml',
        lang='en'
    )
    chapter1.content = '''
    <html>
    <head>
        <title>Introduction</title>
    </head>
    <body>
        <h1>Introduction</h1>
        <p>This is a test EPUB file generated for testing the DocTalk application.</p>
        <p>The purpose of this book is to verify that the EPUB processor can correctly extract text content from EPUB files and convert it to speech.</p>
        <p>This chapter contains some sample text that should be readable by the text-to-speech engine.</p>
    </body>
    </html>
    '''
    
    # Chapter 2
    chapter2 = epub.EpubHtml(
        title='Chapter One',
        file_name='chapter2.xhtml',
        lang='en'
    )
    chapter2.content = '''
    <html>
    <head>
        <title>Chapter One</title>
    </head>
    <body>
        <h2>Chapter One: Getting Started</h2>
        <p>In this chapter, we will explore the basics of EPUB file structure.</p>
        <p>EPUB files are essentially ZIP archives containing HTML, CSS, and other resources.</p>
        <p>The content is organized into chapters, each represented as an HTML document.</p>
        <h3>Subsection One</h3>
        <p>This is a subsection within the chapter. It demonstrates how nested headings work.</p>
        <p>Multiple paragraphs can appear in a single chapter, and they should all be processed correctly.</p>
    </body>
    </html>
    '''
    
    # Chapter 3
    chapter3 = epub.EpubHtml(
        title='Conclusion',
        file_name='chapter3.xhtml',
        lang='en'
    )
    chapter3.content = '''
    <html>
    <head>
        <title>Conclusion</title>
    </head>
    <body>
        <h1>Conclusion</h1>
        <p>This concludes our test EPUB file.</p>
        <p>If you can hear this text being read aloud, then the EPUB processor is working correctly.</p>
        <p>Thank you for testing DocTalk!</p>
    </body>
    </html>
    '''
    
    # Add chapters to the book
    book.add_item(chapter1)
    book.add_item(chapter2)
    book.add_item(chapter3)
    
    # Create table of contents
    book.toc = (
        epub.Link('chapter1.xhtml', 'Introduction', 'intro'),
        epub.Link('chapter2.xhtml', 'Chapter One', 'ch1'),
        epub.Link('chapter3.xhtml', 'Conclusion', 'conclusion'),
    )
    
    # Add default NCX and Nav file
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())
    
    # Define CSS style
    style = '''
    @namespace epub "http://www.idpf.org/2007/ops";
    body {
        font-family: Arial, Helvetica, sans-serif;
    }
    h1 {
        font-size: 2em;
        text-align: center;
    }
    h2 {
        font-size: 1.5em;
        margin-top: 1em;
    }
    h3 {
        font-size: 1.2em;
        margin-top: 0.8em;
    }
    p {
        margin: 1em 0;
    }
    '''
    
    nav_css = epub.EpubItem(
        uid="nav_css",
        file_name="style/nav.css",
        media_type="text/css",
        content=style
    )
    book.add_item(nav_css)
    
    # Create spine
    book.spine = ['nav', chapter1, chapter2, chapter3]
    
    # Save the EPUB file
    output_path = os.path.join(os.path.dirname(__file__), 'test_book.epub')
    epub.write_epub(output_path, book, {})
    
    print(f"Test EPUB file created successfully: {output_path}")
    return output_path

if __name__ == '__main__':
    create_test_epub()

