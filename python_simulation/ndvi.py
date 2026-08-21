"""Small, reusable NDVI helpers used by the Phase 2 satellite module.

Sentinel-2 Band 4 is red light and Band 8 is near-infrared (NIR).  Healthy
leaves usually absorb red light for photosynthesis and reflect NIR, which
makes their NDVI higher.
"""


def calculate_ndvi(red, nir):
    """Return NDVI = (NIR - Red) / (NIR + Red), safely limited to [-1, 1]."""
    denominator = nir + red
    if denominator == 0:
        return 0.0
    return round(max(-1.0, min(1.0, (nir - red) / denominator)), 3)


def classify_ndvi(ndvi):
    """Translate an NDVI number into a farmer-friendly vegetation status."""
    if ndvi >= 0.60:
        return "Healthy", "Dense, active vegetation"
    if ndvi >= 0.30:
        return "Watch", "Moderate vegetation or early stress"
    return "Critical", "Sparse vegetation or significant stress"
