import asyncio
from edge_tts import Communicate
import argparse
import os
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
        
        if not text.strip():
            print(f"Warning: Empty text, skipping processing")
            return
        
        # Split text into manageable chunks
        chunks = split_text_into_chunks(text)
        
        # Handle single chunk case
        if len(chunks) == 1:
            communicate = Communicate(chunks[0], voice_id)
            await communicate.save(output_file)
            return
        
        # Process multiple chunks
        temp_files = []
        for i, chunk in enumerate(chunks):
            if not chunk.strip():
                continue
                
            temp_file = f"temp_{i}.mp3"
            temp_files.append(temp_file)
            communicate = Communicate(chunk, voice_id)
            await communicate.save(temp_file)
        
        if not temp_files:
            print(f"Warning: No audio content generated")
            return
        
        # Merge audio files if multiple chunks exist
        if len(temp_files) > 1:
            # Create file list for ffmpeg
            with open('files.txt', 'w', encoding='utf-8') as f:
                for temp_file in temp_files:
                    f.write(f"file '{temp_file}'\n")
            
            # Merge using ffmpeg
            os.system(f'ffmpeg -f concat -safe 0 -i files.txt -c copy "{output_file}"')
            os.remove('files.txt')
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
        path = Path(input_path)
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
    
    print(f"Using voice: {args.voice}")
    asyncio.run(process_files(args.input, args.output_dir, args.voice))
    print("\nAll files processed!")

if __name__ == "__main__":
    main()