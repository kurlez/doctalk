import asyncio
from edge_tts import Communicate
import argparse
import os
import re
import subprocess
import shutil
from pathlib import Path
import glob

from doctalk.processors.markdown_processor import markdown_to_text
from doctalk.processors.epub_processor import epub_to_text
from doctalk.utils.audio_utils import split_text_into_chunks, set_mp3_metadata, split_long_audio

# Define available Chinese female voices
CHINESE_FEMALE_VOICES = {
    "xiaoxiao": "zh-CN-XiaoxiaoNeural",    # Warm and vivid
    "xiaoyi": "zh-CN-XiaoyiNeural",        # Gentle and natural
    "xiaoxuan": "zh-CN-XiaoxuanNeural",    # Mature and elegant
    "xiaozhen": "zh-CN-XiaozhenNeural",    # Emotional and sincere
    "xiaohan": "zh-CN-XiaohanNeural",      # Warm and sweet
    "xiaomeng": "zh-CN-XiaomengNeural"     # Cute and energetic
}

def check_ffmpeg_available():
    """
    Check if ffmpeg is installed and available in the system PATH.
    
    Returns:
        bool: True if ffmpeg is available, False otherwise
    """
    # First check if ffmpeg command exists in PATH
    ffmpeg_path = shutil.which('ffmpeg')
    if ffmpeg_path is None:
        return False
    
    # Try to run ffmpeg -version to verify it works
    try:
        result = subprocess.run(
            ['ffmpeg', '-version'],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=5
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        return False

def is_valid_text_for_tts(text):
    """
    Check if text contains valid content for TTS (not just whitespace or special chars).
    
    Args:
        text (str): Text to validate
        
    Returns:
        bool: True if text is valid for TTS
    """
    if not text or not text.strip():
        return False
    
    # Remove all whitespace and check if there's actual content
    content = ''.join(text.split())
    if not content:
        return False
    
    # Check if there's at least some alphanumeric or Chinese characters
    has_content = bool(re.search(r'[\u4e00-\u9fff\w]', content))
    return has_content

async def text_to_speech(text, voice="xiaoxiao", output_file="output.mp3"):
    """
    Convert text to speech using Edge TTS.
    
    This function handles:
    - Text chunking for long content
    - Multiple audio file generation
    - Audio file merging
    - Temporary file cleanup
    
    Args:
        text (str): Text to be converted to speech
        voice (str): Voice ID to use (default: xiaoxiao)
        output_file (str): Path for the output audio file
    """
    try:
        voice_id = CHINESE_FEMALE_VOICES.get(voice.lower(), CHINESE_FEMALE_VOICES["xiaoxiao"])
        
        # Validate text before processing
        if not text or not text.strip():
            raise ValueError("Empty text provided for speech synthesis")
        
        if not is_valid_text_for_tts(text):
            raise ValueError("Text contains no valid content for speech synthesis (only whitespace or special characters)")
        
        # Split text into manageable chunks
        chunks = split_text_into_chunks(text)
        
        # Filter out empty or invalid chunks
        valid_chunks = [chunk for chunk in chunks if is_valid_text_for_tts(chunk)]
        
        if not valid_chunks:
            raise ValueError("No valid text chunks after processing (all chunks were empty or invalid)")
        
        # Handle single chunk case with retry logic
        if len(valid_chunks) == 1:
            max_retries = 3
            initial_delay = 1.0
            
            for attempt in range(max_retries):
                try:
                    communicate = Communicate(valid_chunks[0], voice_id)
                    await communicate.save(output_file)
                    return  # Success
                except Exception as e:
                    error_str = str(e)
                    is_rate_limit = '401' in error_str or 'rate limit' in error_str.lower() or '429' in error_str
                    
                    if attempt < max_retries - 1:
                        delay = initial_delay * (2 ** attempt)
                        print(f"Warning: Failed (attempt {attempt + 1}/{max_retries}): {error_str}")
                        if is_rate_limit:
                            print(f"  Rate limit detected, waiting {delay:.1f} seconds before retry...")
                        else:
                            print(f"  Retrying in {delay:.1f} seconds...")
                        await asyncio.sleep(delay)
                    else:
                        # Final attempt failed
                        raise ValueError(f"Failed to process text after {max_retries} attempts: {error_str}")
        
        # Process multiple chunks with retry logic and rate limiting
        temp_files = []
        max_retries = 3
        initial_delay = 1.0  # Initial delay in seconds
        chunk_delay = 0.5  # Delay between chunks to avoid rate limiting
        
        for i, chunk in enumerate(valid_chunks):
            if not is_valid_text_for_tts(chunk):
                print(f"Warning: Skipping invalid chunk {i+1}")
                continue
            
            # Add delay between chunks to avoid rate limiting
            if i > 0:
                await asyncio.sleep(chunk_delay)
                
            temp_file = f"temp_{i}.mp3"
            success = False
            
            # Retry logic with exponential backoff
            for attempt in range(max_retries):
                try:
                    communicate = Communicate(chunk, voice_id)
                    await communicate.save(temp_file)
                    temp_files.append(temp_file)
                    success = True
                    break  # Success, exit retry loop
                    
                except Exception as e:
                    error_str = str(e)
                    # Check if it's a rate limit or 401 error
                    is_rate_limit = '401' in error_str or 'rate limit' in error_str.lower() or '429' in error_str
                    
                    if attempt < max_retries - 1:
                        # Calculate exponential backoff delay
                        delay = initial_delay * (2 ** attempt)
                        print(f"Warning: Chunk {i+1} failed (attempt {attempt + 1}/{max_retries}): {error_str}")
                        if is_rate_limit:
                            print(f"  Rate limit detected, waiting {delay:.1f} seconds before retry...")
                        else:
                            print(f"  Retrying in {delay:.1f} seconds...")
                        await asyncio.sleep(delay)
                    else:
                        # Final attempt failed
                        print(f"Warning: Failed to process chunk {i+1} after {max_retries} attempts: {error_str}")
                        # Clean up failed temp file
                        if os.path.exists(temp_file):
                            try:
                                os.remove(temp_file)
                            except:
                                pass
            
            if not success:
                # If this chunk failed completely, we continue with other chunks
                # but track that we had failures
                continue
        
        if not temp_files:
            raise ValueError("No audio files were successfully generated from any chunks")
        
        # Merge audio files if multiple chunks exist
        if len(temp_files) > 1:
            # Check if ffmpeg is available before merging
            if not check_ffmpeg_available():
                raise RuntimeError(
                    "ffmpeg is not installed or not available in PATH. "
                    "ffmpeg is required for merging multiple audio chunks. "
                    "Please install ffmpeg from https://ffmpeg.org/download.html"
                )
            
            # Create file list for ffmpeg
            with open('files.txt', 'w', encoding='utf-8') as f:
                for temp_file in temp_files:
                    f.write(f"file '{temp_file}'\n")
            
            # Merge using ffmpeg
            result = subprocess.run(
                ['ffmpeg', '-f', 'concat', '-safe', '0', '-i', 'files.txt', '-c', 'copy', output_file],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
                timeout=300
            )
            os.remove('files.txt')
            
            if result.returncode != 0:
                error_msg = result.stderr.decode('utf-8', errors='ignore') if result.stderr else "Unknown error"
                raise RuntimeError(f"Failed to merge audio files with ffmpeg: {error_msg}")
        else:
            # Simply rename if only one temp file
            os.rename(temp_files[0], output_file)
        
        # Cleanup temporary files
        for temp_file in temp_files:
            try:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
            except Exception as e:
                print(f"Warning: Failed to clean up temporary file: {e}")
                
    except Exception as e:
        print(f"Error: Text processing failed: {e}")
        raise

def read_file(file_path):
    """
    Read file content with UTF-8 encoding.
    
    Args:
        file_path (str): Path to the file to read
        
    Returns:
        str: File content as string
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read()

def list_available_voices():
    """
    Display all available voice options with their IDs.
    """
    print("\nAvailable Chinese Female Voices:")
    print("-" * 40)
    for name, voice_id in CHINESE_FEMALE_VOICES.items():
        print(f"Voice Name: {name:<10} (Voice ID: {voice_id})")
    print("-" * 40)

async def process_single_file(input_file, output_dir, voice):
    """
    Process a single file (Markdown or EPUB) to audio.
    
    Args:
        input_file (str): Path to input file
        output_dir (str): Directory for output audio file
        voice (str): Voice ID to use for synthesis
    """
    os.makedirs(output_dir, exist_ok=True)
    
    title = os.path.splitext(os.path.basename(input_file))[0]
    output_mp3 = os.path.join(output_dir, f"{title}.mp3")
    
    print(f"Processing file: {input_file}")
    try:
        # Choose processor based on file type
        if input_file.lower().endswith('.epub'):
            print("Detected EPUB file, converting...")
            text = epub_to_text(input_file)
        else:  # Assume markdown
            text = markdown_to_text(read_file(input_file))
        
        # Convert to speech
        await text_to_speech(text, voice, output_mp3)
        
        # Set audio metadata
        set_mp3_metadata(
            mp3_file=output_mp3,
            title=title,
            artist=f"Edge TTS - {voice}",
            album="Audio Book"
        )
        
        print(f"✓ Generated audio: {output_mp3}")
        
        # 在生成MP3文件后，检查并拆分长音频
        output_files = split_long_audio(output_mp3)
        
        # 为拆分后的每个文件设置元数据
        if len(output_files) > 1:
            for i, file in enumerate(output_files, 1):
                set_mp3_metadata(
                    mp3_file=file,
                    title=f"{title} (Part {i})",
                    artist=f"Edge TTS - {voice}",
                    album="Audio Book"
                )
                print(f"✓ 已处理音频片段 {i}/{len(output_files)}")
        
    except Exception as e:
        print(f"✗ Processing failed: {input_file}")
        print(f"  Error message: {str(e)}")
        if os.path.exists(output_mp3):
            os.remove(output_mp3)

async def process_files(input_paths, output_dir, voice):
    """
    Process multiple files or directories.
    
    Args:
        input_paths (list): List of file or directory paths
        output_dir (str): Directory for output audio files
        voice (str): Voice ID to use for synthesis
    """
    files_to_process = []
    
    # Collect all files to process
    for input_path in input_paths:
        # Expand user home directory (~) and resolve relative paths
        expanded_path = os.path.expanduser(str(input_path))
        path = Path(expanded_path).resolve()
        
        if path.is_dir():
            # Collect all supported files from directory
            files_to_process.extend(glob.glob(str(path / "**/*.md"), recursive=True))
            files_to_process.extend(glob.glob(str(path / "**/*.epub"), recursive=True))
        elif path.is_file() and path.suffix.lower() in ['.md', '.epub']:
            files_to_process.append(str(path))
    
    if not files_to_process:
        print("No supported files found!")
        return
    
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"\nFound {len(files_to_process)} files")
    print("-" * 40)
    
    # Process each file
    for file in files_to_process:
        await process_single_file(file, output_dir, voice)

def main():
    """
    Main entry point for the command line interface.
    """
    parser = argparse.ArgumentParser(description='Convert Markdown or EPUB files to speech audio')
    parser.add_argument('--input', '-i', nargs='+', required=True,
                      help='Input file or directory paths (supports .md and .epub files)')
    parser.add_argument('--output-dir', '-o', default='output',
                      help='Output directory path (default: output)')
    parser.add_argument('--voice', '-v', default='xiaoxiao',
                      choices=CHINESE_FEMALE_VOICES.keys(),
                      help='Select voice (default: xiaoxiao)')
    parser.add_argument('--list', '-l', action='store_true',
                      help='Display all available voice options')
    
    args = parser.parse_args()
    
    if args.list:
        list_available_voices()
        return
    
    # Check if ffmpeg is available before processing
    if not check_ffmpeg_available():
        print("ERROR: ffmpeg is not installed or not available in PATH.")
        print("ffmpeg is required for audio processing operations.")
        print("Please install ffmpeg from: https://ffmpeg.org/download.html")
        print("\nWindows users can:")
        print("  1. Download from https://www.gyan.dev/ffmpeg/builds/")
        print("  2. Extract and add ffmpeg.exe to your system PATH")
        print("  3. Or use: winget install ffmpeg")
        return 1
    
    print(f"Using voice: {args.voice}")
    asyncio.run(process_files(args.input, args.output_dir, args.voice))
    print("\nAll files processed!")
    return 0

if __name__ == "__main__":
    main()