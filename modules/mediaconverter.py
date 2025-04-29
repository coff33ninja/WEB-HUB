from nicegui import ui
import ffmpeg
from pathlib import Path
import os

from modules.media import add_to_playlist  # Import add_to_playlist for playlist integration


def render():
    with ui.card().classes("p-6 bg-gray-700"):
        ui.label("Media Converter").classes("text-2xl font-semibold text-gray-100 mb-4")
        input_file = ui.upload(
            label="Upload Media File",
            auto_upload=True,
        ).props("accept=audio/*,video/*").classes("bg-gray-600 text-white rounded mb-4")
        output_format = ui.select(
            ["mp3", "wav", "mp4", "avi"], value="mp3", label="Output Format"
        ).classes("bg-gray-600 text-white rounded w-full mb-4")
        bitrate = ui.input("Bitrate (e.g., 128k)", value="128k").classes("bg-gray-600 text-white rounded w-full mb-2")
        resolution = ui.input("Resolution (e.g., 1280x720)").classes("bg-gray-600 text-white rounded w-full mb-4")
        output_label = ui.label().classes("text-gray-100")

        def convert_file(e):
            input_path = Path("media") / e.name
            os.makedirs("media", exist_ok=True)
            with open(input_path, "wb") as f:
                f.write(e.content.read())
            output_path = input_path.with_suffix(f".{output_format.value}")
            try:
                stream = ffmpeg.input(str(input_path))
                # Prepare output options
                output_kwargs = {
                    "format": output_format.value,
                    "ab": bitrate.value,
                }
                # For video formats, handle resolution scaling and codecs
                if output_format.value in ["mp4", "avi"]:
                    # If resolution is provided, add scale filter
                    if resolution.value.strip():
                        width_height = resolution.value.strip().split("x")
                        if len(width_height) == 2 and all(s.isdigit() for s in width_height):
                            width, height = width_height
                            stream = stream.filter("scale", width, height)
                    # Set video codec to libx264 for mp4 and mpeg4 for avi
                    if output_format.value == "mp4":
                        output_kwargs["vcodec"] = "libx264"
                    elif output_format.value == "avi":
                        output_kwargs["vcodec"] = "mpeg4"
                    # Set audio codec to aac for video formats
                    output_kwargs["acodec"] = "aac"
                else:
                    # For audio formats, copy video codec (none) and set audio codec to libmp3lame or pcm_s16le
                    output_kwargs["vcodec"] = "copy"
                    if output_format.value == "mp3":
                        output_kwargs["acodec"] = "libmp3lame"
                    elif output_format.value == "wav":
                        output_kwargs["acodec"] = "pcm_s16le"
                    else:
                        output_kwargs["acodec"] = "copy"

                stream = ffmpeg.output(stream, str(output_path), **output_kwargs)
                ffmpeg.run(stream)
                ui.notify(f"Converted to {output_path.name}", type="positive")
                output_label.set_text(f"Download: {output_path.name}")
                ui.download(str(output_path))
                # Add converted file to default playlist (id=1)
                add_to_playlist(1, str(output_path), output_path.name)
            except Exception as e:
                ui.notify(f"Conversion failed: {str(e)}", type="negative")
            finally:
                if input_path.exists():
                    input_path.unlink()

        input_file.on("upload", convert_file)
# Marketplace metadata
def marketplace_info():
    return {
        "name": "Media Converter",
        "description": "Convert media files between formats",
        "icon": "swap_horiz",
        "author": "nice-web",
        "author_url": "https://github.com/nice-web",
        "license": "MIT",
        "homepage": "https://example.com"
    }
