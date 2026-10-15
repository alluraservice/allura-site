"""
Photo uploads for the admin item pages.

Uploaded photos are stored in the `uploaded_images` table (not in the project folder, because on
Render the project folder is wiped on every deploy) and served by the Flask route  /media/<id>.
An item's image_url is simply set to '/media/<id>', so every page that already does
src=f"/{image_url}" keeps working without changes.
"""
import base64
import io

from flask import Response, abort, request

from database.db_handler import get_uploaded_image

MAX_UPLOAD_BYTES = 8 * 1024 * 1024          # what the admin may upload
MAX_DIMENSION = 1600                         # longest side after processing
ALLOWED_MIME = {'image/jpeg', 'image/png', 'image/webp', 'image/gif', 'image/avif'}


def decode_upload(contents):
    """dcc.Upload contents ('data:<mime>;base64,<data>') -> (mime, bytes)."""
    if not contents or ',' not in contents:
        raise ValueError("No file received.")
    header, b64 = contents.split(',', 1)
    mime = header.split(':', 1)[-1].split(';', 1)[0].lower()
    return mime, base64.b64decode(b64)


def validate_upload(contents, filename):
    """Returns an error message, or None if the file is an acceptable photo."""
    try:
        mime, data = decode_upload(contents)
    except Exception:
        return "That file couldn't be read. Please try another photo."
    if mime not in ALLOWED_MIME:
        return f"“{filename}” isn't a supported photo. Use JPG, PNG, WEBP or GIF."
    if len(data) > MAX_UPLOAD_BYTES:
        return f"“{filename}” is {len(data) / 1048576:.1f} MB. The limit is {MAX_UPLOAD_BYTES // 1048576} MB."
    try:
        from PIL import Image
        Image.open(io.BytesIO(data)).verify()
    except ImportError:
        pass
    except Exception:
        return f"“{filename}” doesn't look like a valid image file."
    return None


def process_upload(contents):
    """
    Shrinks large photos to MAX_DIMENSION and re-encodes them as WEBP (keeps transparency,
    much smaller than PNG). Returns (mime, bytes, width, height).
    Falls back to the original file if Pillow isn't installed.
    """
    mime, data = decode_upload(contents)
    try:
        from PIL import Image, ImageOps
    except ImportError:
        return mime, data, None, None

    img = Image.open(io.BytesIO(data))
    img = ImageOps.exif_transpose(img)            # respect phone camera rotation
    if img.mode not in ('RGB', 'RGBA'):
        img = img.convert('RGBA' if 'A' in img.getbands() or img.mode == 'P' else 'RGB')
    img.thumbnail((MAX_DIMENSION, MAX_DIMENSION))
    out = io.BytesIO()
    img.save(out, format='WEBP', quality=88, method=4)
    return 'image/webp', out.getvalue(), img.width, img.height


def register_media_routes(server):
    """Call once with the Flask server (index.py)."""

    @server.route('/media/<int:image_id>')
    def serve_uploaded_image(image_id):
        etag = f'"img-{image_id}"'
        if request.headers.get('If-None-Match') == etag:
            return Response(status=304)
        img = get_uploaded_image(image_id)
        if not img:
            abort(404)
        resp = Response(bytes(img['data']), mimetype=img['mime_type'])
        # An id never changes content (a new upload gets a new id), so browsers can cache it forever
        resp.headers['Cache-Control'] = 'public, max-age=31536000, immutable'
        resp.headers['ETag'] = etag
        return resp
