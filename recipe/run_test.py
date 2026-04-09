#!/usr/bin/env python

"""
Smoke/integration test for the conda recipe of streamlit-image-coordinates.

What this test does
-------------------
This file verifies that the installed package `streamlit-image-coordinates`
can be imported and that its main public function,
`streamlit_image_coordinates(...)`, behaves as expected for the supported
input types.

Test cases covered
------------------
1. Import smoke test
   - Verifies that the package imports successfully.
   - Verifies that `streamlit_image_coordinates` exists and is callable.

2. Local file path input
   - Creates a temporary PNG image on disk.
   - Passes its Path to `streamlit_image_coordinates(...)`.
   - Verifies that width, key, and cursor are forwarded correctly.
   - Verifies that the image is converted to a base64 PNG data URL.

3. NumPy array input
   - Creates an in-memory NumPy image array.
   - Passes it to `streamlit_image_coordinates(...)`.
   - Verifies that the function accepts ndarray input.
   - Verifies that the image is converted to a base64 PNG data URL.

4. PIL image input with JPEG output
   - Creates an in-memory PIL Image.
   - Passes it to `streamlit_image_coordinates(...)` with JPEG settings.
   - Verifies that JPEG conversion works.
   - Verifies that the returned source is a base64 JPEG data URL.

5. Remote URL passthrough
   - Passes an HTTP image URL string.
   - Verifies that the URL is forwarded unchanged instead of being encoded.

6. Invalid image format
   - Passes an unsupported format such as GIF.
   - Verifies that the function raises ValueError.

7. Invalid source type
   - Passes an unsupported object such as an integer.
   - Verifies that the function raises ValueError.

Notes
-----
- This is intentionally not a frontend/UI test.
- This is sufficient for a conda recipe test because it validates package
  installation and core Python behavior.
- The internal `_component_func` is replaced with a fake function so the test
  can inspect what would be sent to the Streamlit component backend.
"""

from pathlib import Path
import tempfile

import numpy as np
from PIL import Image

import streamlit_image_coordinates as sic


def main() -> None:
    print("Starting smoke tests for streamlit-image-coordinates...")

    # 1) Import smoke test
    assert hasattr(sic, "streamlit_image_coordinates")
    assert callable(sic.streamlit_image_coordinates)
    print("Test 1 passed: package import and public API are available.")

    # Replace internal Streamlit component bridge with a fake function.
    captured: dict = {}

    def fake_component_func(**kwargs):
        captured.clear()
        captured.update(kwargs)
        return kwargs

    sic._component_func = fake_component_func
    print("Patched internal component function for headless testing.")

    # 2) Local file path input
    with tempfile.TemporaryDirectory() as tmpdir:
        img_path = Path(tmpdir) / "test.png"
        Image.new("RGB", (8, 6), color=(255, 0, 0)).save(img_path)

        result = sic.streamlit_image_coordinates(
            img_path,
            width=123,
            key="file-test",
            cursor="crosshair",
        )

        assert result["width"] == 123
        assert result["key"] == "file-test"
        assert result["cursor"] == "crosshair"
        assert result["src"].startswith("data:image/png;base64,")
        print("Test 2 passed: local file path input is accepted and encoded as PNG data URL.")

    # 3) NumPy array input
    arr = np.zeros((5, 7, 3), dtype=np.uint8)
    result = sic.streamlit_image_coordinates(
        arr,
        image_format="PNG",
        key="array-test",
    )
    assert result["key"] == "array-test"
    assert result["src"].startswith("data:image/png;base64,")
    print("Test 3 passed: NumPy array input is accepted and encoded as PNG data URL.")

    # 4) PIL image input with JPEG output
    img = Image.new("RGB", (4, 4), color=(0, 255, 0))
    result = sic.streamlit_image_coordinates(
        img,
        image_format="JPEG",
        jpeg_quality=70,
        key="jpeg-test",
    )
    assert result["key"] == "jpeg-test"
    assert result["src"].startswith("data:image/jpeg;base64,")
    print("Test 4 passed: PIL image input is accepted and encoded as JPEG data URL.")

    # 5) Remote URL passthrough
    url = "https://placekitten.com/200/300"
    result = sic.streamlit_image_coordinates(url, key="url-test")
    assert result["src"] == url
    assert result["key"] == "url-test"
    print("Test 5 passed: remote image URL is passed through unchanged.")

    # 6) Invalid image format
    try:
        sic.streamlit_image_coordinates(arr, image_format="GIF")
    except ValueError as e:
        assert "Only 'PNG' and 'JPEG' image formats are supported" in str(e)
        print("Test 6 passed: unsupported image format correctly raises ValueError.")
    else:
        raise AssertionError("Expected ValueError for unsupported image_format")

    # 7) Invalid source type
    try:
        sic.streamlit_image_coordinates(12345)
    except ValueError as e:
        assert "Must pass a string, Path, numpy array or object with a save method" in str(e)
        print("Test 7 passed: unsupported source type correctly raises ValueError.")
    else:
        raise AssertionError("Expected ValueError for unsupported source type")

    print("All streamlit-image-coordinates tests passed successfully.")


if __name__ == "__main__":
    main()
