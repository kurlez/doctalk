"""
Tests for EPUB processing functionality.
"""
import unittest
import os
import sys
from pathlib import Path

# Add the src directory to the Python path
src_path = Path(__file__).parent.parent / 'src'
sys.path.insert(0, str(src_path))

# Import the function to test
from doctalk.processors.epub_processor import epub_to_text


class TestEpubProcessor(unittest.TestCase):
    """Test cases for EPUB to text conversion."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test fixtures before running tests."""
        # Get the path to the test EPUB file
        cls.test_epub_path = os.path.join(
            os.path.dirname(__file__),
            'test_book.epub'
        )
        
        # Verify the test EPUB file exists
        if not os.path.exists(cls.test_epub_path):
            raise FileNotFoundError(
                f"Test EPUB file not found: {cls.test_epub_path}\n"
                "Please run tests/generate_test_epub.py first to create the test file."
            )
    
    def test_epub_file_exists(self):
        """Test that the test EPUB file exists."""
        self.assertTrue(
            os.path.exists(self.test_epub_path),
            "Test EPUB file should exist"
        )
    
    def test_epub_to_text_returns_string(self):
        """Test that epub_to_text returns a string."""
        result = epub_to_text(self.test_epub_path)
        self.assertIsInstance(result, str, "Result should be a string")
        self.assertGreater(len(result), 0, "Result should not be empty")
    
    def test_epub_title_extraction(self):
        """Test that the book title is extracted correctly."""
        result = epub_to_text(self.test_epub_path)
        # The title "Test Book for DocTalk" should be processed
        # After processing, markdown headers are removed but title text should still be present
        result_lower = result.lower()
        # Check that key words from the title appear (title might be split or processed)
        title_words = ["test", "book", "doctalk"]
        found_words = sum(1 for word in title_words if word in result_lower)
        self.assertGreaterEqual(found_words, 2,
                               "At least some title words should be present in the output")
    
    def test_chapter_content_extraction(self):
        """Test that chapter content is extracted."""
        result = epub_to_text(self.test_epub_path)
        
        # Check for content from Chapter 1 (Introduction)
        self.assertIn("test epub file", result.lower(),
                     "Introduction chapter content should be present")
        self.assertIn("doctalk application", result.lower(),
                     "Introduction chapter content should be present")
        
        # Check for content from Chapter 2 (Chapter One)
        self.assertIn("getting started", result.lower(),
                     "Chapter One content should be present")
        self.assertIn("epub files", result.lower(),
                     "Chapter One content should be present")
        
        # Check for content from Chapter 3 (Conclusion)
        self.assertIn("conclusion", result.lower(),
                     "Conclusion chapter content should be present")
        self.assertIn("thank you", result.lower(),
                     "Conclusion chapter content should be present")
    
    def test_heading_extraction(self):
        """Test that chapter headings are extracted."""
        result = epub_to_text(self.test_epub_path)
        
        # Headings should be present (though markdown headers are removed by text_cleaner)
        # The heading text should still be in the content
        self.assertIn("introduction", result.lower(),
                     "Introduction heading should be present")
        self.assertIn("chapter one", result.lower(),
                     "Chapter One heading should be present")
        self.assertIn("subsection one", result.lower(),
                     "Subsection heading should be present")
    
    def test_html_removal(self):
        """Test that HTML tags are properly removed."""
        result = epub_to_text(self.test_epub_path)
        
        # HTML tags should not appear in the output
        self.assertNotIn("<html>", result, "HTML tags should be removed")
        self.assertNotIn("<body>", result, "HTML tags should be removed")
        self.assertNotIn("<p>", result, "HTML tags should be removed")
        self.assertNotIn("<h1>", result, "HTML tags should be removed")
        self.assertNotIn("<h2>", result, "HTML tags should be removed")
        self.assertNotIn("<h3>", result, "HTML tags should be removed")
    
    def test_paragraph_content_preserved(self):
        """Test that paragraph content is preserved."""
        result = epub_to_text(self.test_epub_path)
        
        # Check for specific paragraph content
        expected_phrases = [
            "purpose of this book",
            "verify that the epub processor",
            "basics of epub file structure",
            "zip archives containing html",
            "working correctly"
        ]
        
        result_lower = result.lower()
        for phrase in expected_phrases:
            self.assertIn(phrase, result_lower,
                         f"Expected phrase '{phrase}' should be present in output")
    
    def test_text_processing_for_speech(self):
        """Test that text is processed for speech synthesis."""
        result = epub_to_text(self.test_epub_path)
        
        # After processing, the text should have Chinese punctuation
        # (based on text_cleaner.py converting English punctuation to Chinese)
        # Check that the text is not empty and has been processed
        self.assertGreater(len(result), 0, "Processed text should not be empty")
        
        # The text should have some punctuation (Chinese or English)
        # Just verify it's been processed and has content
        word_count = len(result.split())
        self.assertGreater(word_count, 10, 
                          "Processed text should contain multiple words")
    
    def test_multiple_chapters_processed(self):
        """Test that all chapters are processed."""
        result = epub_to_text(self.test_epub_path)
        
        # Count unique chapter identifiers
        chapter_indicators = [
            "introduction",
            "chapter one",
            "getting started",
            "subsection",
            "conclusion"
        ]
        
        found_count = sum(1 for indicator in chapter_indicators 
                         if indicator in result.lower())
        self.assertGreaterEqual(found_count, 3,
                               "At least 3 chapters should be processed")
    
    def test_nonexistent_file_raises_error(self):
        """Test that a non-existent file raises an appropriate error."""
        nonexistent_path = os.path.join(
            os.path.dirname(__file__),
            'nonexistent_book.epub'
        )
        
        with self.assertRaises((FileNotFoundError, OSError)):
            epub_to_text(nonexistent_path)
    
    def test_output_format(self):
        """Test that output format is suitable for speech synthesis."""
        result = epub_to_text(self.test_epub_path)
        
        # Output should be clean text (no HTML, no markdown syntax)
        # Check that it doesn't contain markdown headers
        self.assertNotIn("##", result, 
                        "Markdown headers should be removed")
        self.assertNotIn("# ", result, 
                        "Markdown headers should be removed")
        
        # Output should be a single string (not a list)
        self.assertIsInstance(result, str)


if __name__ == '__main__':
    unittest.main()

