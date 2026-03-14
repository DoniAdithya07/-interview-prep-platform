import os
from io import BytesIO

from fastapi import HTTPException, UploadFile, status

try:
    import whisper
except ImportError:
    whisper = None

try:
    import imageio_ffmpeg
except ImportError:
    imageio_ffmpeg = None


async def transcribe_audio(upload: UploadFile) -> str:
    content = await upload.read()
    await upload.close()
    if not content:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Audio file is empty")
    if whisper is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Whisper is not installed on the server.",
        )

    try:
        if imageio_ffmpeg is not None:
            ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
            ffmpeg_dir = os.path.dirname(ffmpeg_exe)
            current_path = os.environ.get("PATH", "")
            if ffmpeg_dir and ffmpeg_dir not in current_path.split(os.pathsep):
                os.environ["PATH"] = os.pathsep.join([ffmpeg_dir, current_path]) if current_path else ffmpeg_dir
        model = whisper.load_model("base")
        with BytesIO(content) as buffer:
            # Whisper expects a file path or numpy audio; temp-file path is the simplest portable route.
            import tempfile

            with tempfile.NamedTemporaryFile(delete=False, suffix=".webm") as temp_file:
                temp_file.write(buffer.read())
                temp_file.flush()
                result = model.transcribe(temp_file.name)
        transcript = str(result.get("text", "")).strip()
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Whisper transcription failed: {exc}",
        ) from exc

    if not transcript:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Could not transcribe the audio clearly.",
        )
    return transcript
