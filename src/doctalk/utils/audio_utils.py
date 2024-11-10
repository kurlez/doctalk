import os
from mutagen.id3 import ID3, TIT2, TPE1, TALB, TDRC
import datetime

def split_text_into_chunks(text, max_length=4900):
    """
    Split long text into smaller chunks suitable for edge-tts processing.
    
    Args:
        text (str): The input text to be split
        max_length (int): Maximum length of each chunk (default: 4900)
        
    Returns:
        list: A list of text chunks, each within the max_length limit
    """
    if not text:
        return []
        
    chunks = []
    current_chunk = ""
    
    # Split text into sentences by punctuation marks
    sentences = []
    temp = ""
    for char in text:
        temp += char
        if char in '。！？!?.':  # Chinese and English punctuation marks
            sentences.append(temp)
            temp = ""
    if temp:  # Add the last sentence if it doesn't end with punctuation
        sentences.append(temp)
    
    # Combine sentences into chunks
    for sentence in sentences:
        if len(current_chunk) + len(sentence) < max_length:
            current_chunk += sentence
        else:
            if current_chunk:
                chunks.append(current_chunk)
            current_chunk = sentence
    
    # Add the last chunk if not empty
    if current_chunk:
        chunks.append(current_chunk)
    
    return chunks if chunks else [text]

def set_mp3_metadata(mp3_file, title, artist="Edge TTS", album="Markdown Audio"):
    """
    Set metadata (ID3 tags) for the MP3 file.
    
    Args:
        mp3_file (str): Path to the MP3 file
        title (str): Title for the audio file
        artist (str): Artist name (default: "Edge TTS")
        album (str): Album name (default: "Markdown Audio")
        
    Note:
        This function adds or updates ID3 tags including:
        - Title (TIT2)
        - Artist (TPE1)
        - Album (TALB)
        - Year (TDRC) - set to current year
    """
    try:
        # Try to load existing ID3 tags, create new if none exist
        try:
            audio = ID3(mp3_file)
        except:
            audio = ID3()

        # Set title tag
        audio.add(TIT2(encoding=3, text=title))
        
        # Set artist tag
        audio.add(TPE1(encoding=3, text=artist))
        
        # Set album tag
        audio.add(TALB(encoding=3, text=album))
        
        # Set year tag to current year
        current_year = str(datetime.datetime.now().year)
        audio.add(TDRC(encoding=3, text=current_year))
        
        # Save changes to file
        audio.save(mp3_file)
        print(f"Added metadata to file: {mp3_file}")
        
    except Exception as e:
        print(f"Error setting MP3 metadata: {e}")