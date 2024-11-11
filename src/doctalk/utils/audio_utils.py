import os
from mutagen.id3 import ID3, TIT2, TPE1, TALB, TDRC
import datetime
from mutagen.mp3 import MP3
from pydub import AudioSegment

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

def split_long_audio(input_mp3, max_duration=3600):
    """
    将长音频文件按照指定时长拆分成多个文件
    
    Args:
        input_mp3 (str): 输入MP3文件路径
        max_duration (int): 每个文件的最大时长（秒），默认3600秒（1小时）
    
    Returns:
        list: 拆分后的文件路径列表
    """
    try:
        # 获取音频时长
        audio = MP3(input_mp3)
        duration = audio.info.length
        
        # 如果时长未超过限制，直接返回原文件
        if duration <= max_duration:
            return [input_mp3]
            
        # 计算需要拆分的部分数
        num_parts = int(duration / max_duration) + 1
        print(f"音频时长超过{max_duration/3600}小时，将拆分为{num_parts}个文件")
        
        # 读取音频文件
        audio = AudioSegment.from_mp3(input_mp3)
        output_files = []
        
        # 按时长拆分并保存
        for i in range(num_parts):
            start_time = i * max_duration * 1000  # pydub使用毫秒
            end_time = min((i + 1) * max_duration * 1000, len(audio))
            
            # 生成输出文件名
            base_name = os.path.splitext(input_mp3)[0]
            output_file = f"{base_name}_part{i+1:02d}.mp3"
            
            # 截取并保存片段
            segment = audio[start_time:end_time]
            segment.export(output_file, format="mp3")
            output_files.append(output_file)
            
            print(f"已生成片段 {i+1}/{num_parts}: {output_file}")
            
        # 删除原始文件
        os.remove(input_mp3)
        return output_files
        
    except Exception as e:
        print(f"音频拆分失败: {str(e)}")
        return [input_mp3]  # 如果失败则返回原文件