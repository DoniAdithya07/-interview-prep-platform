from fastapi import HTTPException, UploadFile, status

try:
    import whisper
except ImportError:
    whisper = None


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
        model = whisper.load_model("base")
        result = model.transcribe(content)
        return result.get("text", "").strip() or "No transcript generated."
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Transcription failed: {exc}",
        ) from exc
