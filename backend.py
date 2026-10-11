"""
AeroCraft AI - sketch analysis prototype

Takes a rocket side-profile sketch (a NumPy image) and works out the same
things the browser app reads from its canvas: the outline, where the nose ends,
the body width, and any fins sticking out past the body. It then turns those
into the slider values the app uses (nose height, body length, diameter, fin span).

This script is standalone. aerocraft.html does its own sketch reading in JavaScript
and doesn't call this file.

Usage:
    python backend.py              # runs a built-in test sketch
    python backend.py sketch.png   # analyzes your own image
"""

import sys

import cv2
import numpy as np


def extract_outline(sketch):
    """
    Turn a sketch into a filled silhouette mask.

    Blurs the image, runs Canny edge detection, takes the largest outside
    contour and fills it in. Works for both filled shapes and thin outlines.
    Returns the mask, or None if nothing was found.
    """
    if sketch.ndim == 3:
        sketch = cv2.cvtColor(sketch, cv2.COLOR_BGR2GRAY)

    # Dark-on-light drawings (like a photo of paper) get flipped so the lines are bright
    if sketch.mean() > 127:
        sketch = 255 - sketch

    blurred = cv2.GaussianBlur(sketch, (5, 5), 0)
    edges = cv2.Canny(blurred, 50, 150)
    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return None

    # Pick by bounding-box size, since an unfilled outline has almost no enclosed area
    def bbox_area(c):
        _, _, w, h = cv2.boundingRect(c)
        return w * h

    main = max(contours, key=bbox_area)
    mask = np.zeros(sketch.shape[:2], dtype=np.uint8)
    cv2.drawContours(mask, [main], -1, 255, thickness=cv2.FILLED)
    return mask


def width_profile(mask):
    """
    Measure the half-width of the silhouette at every row, top to bottom.
    Returns (half_widths, top_row), or (None, None) if the mask is empty.
    """
    rows = np.where(mask.any(axis=1))[0]
    if len(rows) < 12:
        return None, None
    top, bottom = rows[0], rows[-1]
    half = []
    for y in range(top, bottom + 1):
        xs = np.where(mask[y] > 0)[0]
        half.append((xs[-1] - xs[0] + 1) / 2 if len(xs) else 0.0)
    return np.array(half), top


def extract_rocket_features(sketch):
    """
    Split a sketch into nose, body and fins.

    Same approach as the browser version:
      - body half-width = median width through the middle 40% of the drawing
      - nose ends at the first row that reaches 90% of the body width
      - how curved the nose is picks conical, parabolic or ogive
      - rows wider than the body (by more than 4%) are fins
    All measurements are in pixels.
    """
    mask = extract_outline(sketch)
    if mask is None:
        return {"status": "No valid geometry detected"}

    half, top = width_profile(mask)
    if half is None:
        return {"status": "No valid geometry detected"}

    n = len(half)
    middle = np.sort(half[int(n * 0.3):int(np.ceil(n * 0.7))])
    body_half = max(1.0, float(middle[len(middle) // 2]))

    reached = np.where(half >= body_half * 0.9)[0]
    nose_end = max(1, int(reached[0]) if len(reached) else 1)

    mid_ratio = half[nose_end // 2] / body_half
    if mid_ratio < 0.58:
        nose_shape = "conical"
    elif mid_ratio < 0.8:
        nose_shape = "parabolic"
    else:
        nose_shape = "ogive"

    # Rows that stick out past the body, grouped into separate fins
    wide = half > body_half * 1.04 + 0.5
    fin_runs, start = [], None
    for i, flag in enumerate(wide):
        if flag and start is None:
            start = i
        elif not flag and start is not None:
            if i - start > 1:
                fin_runs.append((start, i - 1))
            start = None
    if start is not None and n - start > 1:
        fin_runs.append((start, n - 1))

    return {
        "top_row": int(top),
        "height_px": n,
        "width_px": int(round(half.max() * 2)),
        "aspect_ratio": round(float(n / (half.max() * 2)), 2),
        "body_diameter_px": round(body_half * 2, 1),
        "nose_height_px": nose_end,
        "body_length_px": n - nose_end,
        "nose_shape": nose_shape,
        "fin_span_px": round(max(0.0, float(half.max()) - body_half), 1),
        "fin_sections": len(fin_runs),
        "profile": [round(float(v), 1) for v in half],
    }


def to_rocket_params(features, length_m=9.8):
    """
    Convert pixel measurements to the values the app's sliders use.

    One scale for both axes (length_m spread over the drawing's height), so the
    proportions match the sketch. Also gives a rough drag coefficient using the
    same formula as the app (nose type plus a small term for four fins).
    """
    if "status" in features:
        return features

    scale = length_m / features["height_px"]          # metres per pixel
    diameter = features["body_diameter_px"] * scale
    fin_span = features["fin_span_px"] * scale

    nose_cd = {"ogive": 0.12, "conical": 0.18, "parabolic": 0.15}[features["nose_shape"]]
    fin_drag = 4 * 0.02 * (fin_span / diameter)

    return {
        "noseShape": features["nose_shape"],
        "noseHeight": round(features["nose_height_px"] * scale, 2),
        "bodyLength": round(features["body_length_px"] * scale, 2),
        "bodyDiameter": round(diameter, 2),
        "finSpan": round(fin_span, 2),
        "estimated_drag_cd": round(nose_cd + fin_drag, 2),
    }


def _test_sketch():
    """A pencil-shaped rocket outline on a blank 512x512 canvas."""
    img = np.zeros((512, 512), dtype=np.uint8)
    cx = 256
    pts = [(cx, 40), (cx - 18, 110), (cx - 18, 400), (cx - 55, 450),
           (cx + 55, 450), (cx + 18, 400), (cx + 18, 110)]
    cv2.polylines(img, [np.array(pts, dtype=np.int32)], True, 255, thickness=4)
    return img


if __name__ == "__main__":
    if len(sys.argv) > 1:
        image = cv2.imread(sys.argv[1], cv2.IMREAD_UNCHANGED)
        if image is None:
            sys.exit(f"Couldn't read image: {sys.argv[1]}")
        if image.ndim == 3 and image.shape[2] == 4:      # PNG with transparency
            alpha = image[:, :, 3]
            image = np.where(alpha > 0, 255, 0).astype(np.uint8)
    else:
        image = _test_sketch()

    features = extract_rocket_features(image)
    features.pop("profile", None)                         # long list, skip when printing
    print("Features (pixels):", features)
    print("Rocket parameters:", to_rocket_params(extract_rocket_features(image)))
