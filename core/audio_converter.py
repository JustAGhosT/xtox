"""
Audio format conversion utilities for WhatsApp and other audio formats.
"""

import subprocess
import shutil
from pathlib import Path
from typing import Optional, Union, Dict, List

try:
    from pydub import AudioSegment
    PYDUB_AVAILABLE = True
except ImportError:
    PYDUB_AVAILABLE = False


class AudioConverter:
    """Handle audio format conversion, especially WhatsApp OGG Opus files."""
    
    SUPPORTED_INPUT_FORMATS = {
        'ogg': 'OGG',
        'opus': 'OPUS',
        'mp3': 'MP3',
        'wav': 'WAV',
        'm4a': 'M4A',
        'aac': 'AAC',
        'flac': 'FLAC'
    }
    
    SUPPORTED_OUTPUT_FORMATS = {
        'mp3': 'MP3',
        'wav': 'WAV',
        'ogg': 'OGG',
        'm4a': 'M4A',
        'aac': 'AAC',
        'flac': 'FLAC'
    }
    
    def __init__(self):
        self._check_ffmpeg()
    
    def _check_ffmpeg(self):
        """Check if ffmpeg is available."""
        try:
            subprocess.run(['ffmpeg', '-version'], 
                         capture_output=True, 
                         check=True,
                         timeout=5)
            self.ffmpeg_available = True
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
            self.ffmpeg_available = False
    
    def convert_audio(
        self,
        input_path: Union[str, Path],
        output_path: Optional[Union[str, Path]] = None,
        target_format: str = 'mp3',
        bitrate: str = '192k',
        sample_rate: Optional[int] = None
    ) -> str:
        """
        Convert audio file to target format.
        
        Args:
            input_path: Path to input audio file
            output_path: Output path (auto-generated if None)
            target_format: Target format (mp3, wav, ogg, etc.)
            bitrate: Audio bitrate (e.g., '192k', '128k', '320k')
            sample_rate: Sample rate in Hz (optional)
            
        Returns:
            Path to converted audio file
        """
        input_path = Path(input_path)
        if not input_path.exists():
            raise FileNotFoundError(f"Audio file not found: {input_path}")
        
        # Validate input format
        input_ext = input_path.suffix.lower().lstrip('.')
        if input_ext not in self.SUPPORTED_INPUT_FORMATS:
            raise ValueError(f"Unsupported input format: {input_ext}")
        
        # Validate output format
        if target_format.lower() not in self.SUPPORTED_OUTPUT_FORMATS:
            raise ValueError(f"Unsupported output format: {target_format}")
        
        # Generate output path if not provided
        if output_path is None:
            output_path = input_path.with_suffix(f'.{target_format.lower()}')
        else:
            output_path = Path(output_path)
        
        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Use ffmpeg if available (more reliable for OGG Opus)
        if self.ffmpeg_available:
            return self._convert_with_ffmpeg(
                input_path, output_path, target_format, bitrate, sample_rate
            )
        elif PYDUB_AVAILABLE:
            return self._convert_with_pydub(
                input_path, output_path, target_format, bitrate, sample_rate
            )
        else:
            raise RuntimeError(
                "Neither ffmpeg nor pydub is available. "
                "Please install ffmpeg (recommended) or pydub with ffmpeg."
            )
    
    def _convert_with_ffmpeg(
        self,
        input_path: Path,
        output_path: Path,
        target_format: str,
        bitrate: str,
        sample_rate: Optional[int]
    ) -> str:
        """Convert audio using ffmpeg (most reliable for OGG Opus)."""
        cmd = ['ffmpeg', '-i', str(input_path), '-y']
        
        # Add format-specific options
        if target_format.lower() == 'mp3':
            cmd.extend(['-codec:a', 'libmp3lame', '-b:a', bitrate])
        elif target_format.lower() == 'wav':
            cmd.extend(['-codec:a', 'pcm_s16le'])
        elif target_format.lower() == 'ogg':
            cmd.extend(['-codec:a', 'libvorbis', '-b:a', bitrate])
        elif target_format.lower() == 'm4a':
            cmd.extend(['-codec:a', 'aac', '-b:a', bitrate])
        elif target_format.lower() == 'aac':
            cmd.extend(['-codec:a', 'aac', '-b:a', bitrate])
        elif target_format.lower() == 'flac':
            cmd.extend(['-codec:a', 'flac'])
        
        # Add sample rate if specified
        if sample_rate:
            cmd.extend(['-ar', str(sample_rate)])
        
        cmd.append(str(output_path))
        
        # Run ffmpeg
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if result.returncode != 0:
            error_msg = result.stderr or result.stdout
            raise RuntimeError(f"FFmpeg conversion failed: {error_msg}")
        
        if not output_path.exists():
            raise RuntimeError("Conversion completed but output file not found")
        
        return str(output_path)
    
    def _convert_with_pydub(
        self,
        input_path: Path,
        output_path: Path,
        target_format: str,
        bitrate: str,
        sample_rate: Optional[int]
    ) -> str:
        """Convert audio using pydub (requires ffmpeg)."""
        if not PYDUB_AVAILABLE:
            raise RuntimeError("pydub is not available")
        
        # Load audio file
        audio = AudioSegment.from_file(str(input_path))
        
        # Apply sample rate conversion if needed
        if sample_rate and audio.frame_rate != sample_rate:
            audio = audio.set_frame_rate(sample_rate)
        
        # Export to target format
        export_params = {}
        
        if target_format.lower() == 'mp3':
            # Extract bitrate number (e.g., '192k' -> 192)
            bitrate_num = int(bitrate.rstrip('k'))
            export_params['bitrate'] = bitrate
        elif target_format.lower() == 'wav':
            export_params['format'] = 'wav'
        elif target_format.lower() == 'ogg':
            export_params['format'] = 'ogg'
            export_params['codec'] = 'libvorbis'
            bitrate_num = int(bitrate.rstrip('k'))
            export_params['bitrate'] = bitrate
        
        audio.export(str(output_path), format=target_format.lower(), **export_params)
        
        return str(output_path)
    
    def get_audio_info(self, audio_path: Union[str, Path]) -> Dict:
        """Get audio file information."""
        audio_path = Path(audio_path)
        
        if not audio_path.exists():
            raise FileNotFoundError(f"Audio file not found: {audio_path}")
        
        info = {
            'file_path': str(audio_path),
            'file_size_kb': audio_path.stat().st_size / 1024,
            'format': audio_path.suffix.lower().lstrip('.')
        }
        
        # Try to get detailed info with ffmpeg
        if self.ffmpeg_available:
            try:
                result = subprocess.run(
                    ['ffprobe', '-v', 'quiet', '-print_format', 'json', '-show_format', '-show_streams', str(audio_path)],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                if result.returncode == 0:
                    import json
                    probe_data = json.loads(result.stdout)
                    if 'streams' in probe_data and len(probe_data['streams']) > 0:
                        stream = probe_data['streams'][0]
                        info['duration'] = float(stream.get('duration', 0))
                        info['bitrate'] = int(stream.get('bit_rate', 0)) // 1000 if stream.get('bit_rate') else None
                        info['sample_rate'] = int(stream.get('sample_rate', 0)) if stream.get('sample_rate') else None
                        info['channels'] = int(stream.get('channels', 0)) if stream.get('channels') else None
                        info['codec'] = stream.get('codec_name', 'unknown')
            except Exception:
                pass
        
        # Fallback to pydub if available
        elif PYDUB_AVAILABLE:
            try:
                audio = AudioSegment.from_file(str(audio_path))
                info['duration'] = len(audio) / 1000.0  # Convert to seconds
                info['sample_rate'] = audio.frame_rate
                info['channels'] = audio.channels
            except Exception:
                pass
        
        return info

