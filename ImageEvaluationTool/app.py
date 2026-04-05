"""
Image Generation Evaluation Tool
MSc Thesis: Understanding and Comparing Generative AI Models
Domain: Image Generation
"""

from flask import Flask, render_template, request, jsonify, send_file
import os
import json
import base64
import io
import math
import hashlib
import re
import csv
import traceback
from datetime import datetime
from collections import Counter

import numpy as np
import cv2
from PIL import Image, ImageFilter, ImageStat, ImageDraw, ImageFont
from scipy import ndimage, signal
from sklearn.cluster import KMeans

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB
app.config['SECRET_KEY'] = 'image-eval-tool-thesis'


class NumpyJSONEncoder(json.JSONEncoder):
    """Custom JSON encoder that handles NumPy types."""
    def default(self, obj):
        if isinstance(obj, np.bool_):
            return bool(obj)
        if isinstance(obj, np.integer):
            return int(obj)
        if isinstance(obj, np.floating):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return super().default(obj)


app.json_encoder = NumpyJSONEncoder  # Flask < 2.3 compat
app.json.encoder = NumpyJSONEncoder  # Flask >= 2.3

UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'uploads')
EXPORT_FOLDER = os.path.join(os.path.dirname(__file__), 'exports')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(EXPORT_FOLDER, exist_ok=True)

# ──────────────────────────────────────────────
# UTILITY FUNCTIONS
# ──────────────────────────────────────────────

def pil_to_cv2(pil_img):
    """Convert PIL Image to OpenCV format (BGR)."""
    rgb = np.array(pil_img.convert('RGB'))
    return cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)

def sanitize_for_json(obj):
    """Recursively convert all NumPy types to native Python types for JSON serialization."""
    if isinstance(obj, dict):
        return {k: sanitize_for_json(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [sanitize_for_json(item) for item in obj]
    elif isinstance(obj, np.bool_):
        return bool(obj)
    elif isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, float) and (math.isnan(obj) or math.isinf(obj)):
        return str(obj)
    return obj

def cv2_to_pil(cv2_img):
    """Convert OpenCV image (BGR) to PIL Image."""
    rgb = cv2.cvtColor(cv2_img, cv2.COLOR_BGR2RGB)
    return Image.fromarray(rgb)

def resize_to_match(img, target_shape):
    """Resize image to match target dimensions."""
    return cv2.resize(img, (target_shape[1], target_shape[0]), interpolation=cv2.INTER_AREA)

def img_to_base64_thumbnail(pil_img, max_size=200):
    """Create a small base64 thumbnail for display."""
    img_copy = pil_img.copy()
    img_copy.thumbnail((max_size, max_size), Image.LANCZOS)
    buf = io.BytesIO()
    img_copy.save(buf, format='PNG')
    return base64.b64encode(buf.getvalue()).decode('utf-8')

# ──────────────────────────────────────────────
# METRIC 1: Resolution & Aspect Ratio
# ──────────────────────────────────────────────

def compute_resolution_metrics(pil_img, prompt_text=""):
    """Analyze resolution, aspect ratio, and megapixels."""
    w, h = pil_img.size
    aspect_ratio = w / h
    megapixels = (w * h) / 1_000_000
    is_landscape = w > h
    is_portrait = h > w
    is_square = abs(w - h) < 10

    common_ratios = {
        '1:1': 1.0, '4:3': 4/3, '3:2': 3/2, '16:9': 16/9,
        '3:4': 3/4, '2:3': 2/3, '9:16': 9/16, '21:9': 21/9
    }
    closest_ratio = min(common_ratios.items(), key=lambda x: abs(x[1] - aspect_ratio))

    # Score: higher resolution = better, max at 4K+
    res_score = min(100, (megapixels / 8.3) * 100)  # 4K ~ 8.3MP

    return {
        'width': w,
        'height': h,
        'aspect_ratio': round(aspect_ratio, 3),
        'closest_standard_ratio': closest_ratio[0],
        'ratio_deviation': round(abs(closest_ratio[1] - aspect_ratio), 4),
        'megapixels': round(megapixels, 2),
        'orientation': 'square' if is_square else ('landscape' if is_landscape else 'portrait'),
        'resolution_score': round(res_score, 1)
    }

# ──────────────────────────────────────────────
# METRIC 2: Color Histogram Analysis
# ──────────────────────────────────────────────

def compute_color_histogram(pil_img):
    """Analyze color distribution across RGB channels."""
    img_arr = np.array(pil_img.convert('RGB'))
    histograms = {}
    channel_stats = {}

    for i, ch_name in enumerate(['red', 'green', 'blue']):
        channel = img_arr[:, :, i].flatten()
        hist, _ = np.histogram(channel, bins=256, range=(0, 256))
        hist_normalized = hist / hist.sum()
        histograms[ch_name] = hist_normalized.tolist()

        channel_stats[ch_name] = {
            'mean': float(np.mean(channel)),
            'std': float(np.std(channel)),
            'median': float(np.median(channel)),
            'skewness': float(((channel - np.mean(channel)) ** 3).mean() / (np.std(channel) ** 3 + 1e-10)),
        }

    # Color diversity via histogram entropy
    combined = img_arr.reshape(-1, 3)
    # Quantize to reduce bins
    quantized = (combined // 32).astype(np.uint8)
    color_codes = quantized[:, 0] * 64 + quantized[:, 1] * 8 + quantized[:, 2]
    hist_all, _ = np.histogram(color_codes, bins=512, range=(0, 512))
    hist_all = hist_all / hist_all.sum()
    entropy = -np.sum(hist_all[hist_all > 0] * np.log2(hist_all[hist_all > 0]))

    # Histogram uniformity score (0=all one color, 100=very diverse)
    diversity_score = min(100, (entropy / 9.0) * 100)

    return {
        'channel_stats': channel_stats,
        'color_entropy': round(entropy, 3),
        'color_diversity_score': round(diversity_score, 1),
        'histograms': {k: [round(v, 6) for v in vals[::4]] for k, vals in histograms.items()}  # downsampled for JSON
    }

# ──────────────────────────────────────────────
# METRIC 3: Brightness, Contrast, Saturation
# ──────────────────────────────────────────────

def compute_brightness_contrast_saturation(pil_img):
    """Compute brightness, contrast (RMS), and saturation statistics."""
    rgb = np.array(pil_img.convert('RGB')).astype(np.float64)
    hsv = cv2.cvtColor(rgb.astype(np.uint8), cv2.COLOR_RGB2HSV).astype(np.float64)

    # Brightness (V channel of HSV)
    brightness = hsv[:, :, 2]
    mean_brightness = np.mean(brightness)
    std_brightness = np.std(brightness)

    # Luminance (weighted)
    luminance = 0.299 * rgb[:, :, 0] + 0.587 * rgb[:, :, 1] + 0.114 * rgb[:, :, 2]
    mean_luminance = np.mean(luminance)

    # Contrast: RMS contrast
    rms_contrast = np.std(luminance)

    # Michelson contrast
    lum_min, lum_max = np.min(luminance), np.max(luminance)
    michelson = (lum_max - lum_min) / (lum_max + lum_min + 1e-10)

    # Saturation
    saturation = hsv[:, :, 1]
    mean_saturation = np.mean(saturation)
    std_saturation = np.std(saturation)

    # Dynamic range
    dynamic_range = lum_max - lum_min

    # Score brightness (ideal around 120-140 for most photos)
    brightness_score = max(0, 100 - abs(mean_brightness - 130) * 1.2)
    contrast_score = min(100, (rms_contrast / 80) * 100)
    saturation_score = min(100, (mean_saturation / 128) * 100)

    return {
        'mean_brightness': round(mean_brightness, 2),
        'std_brightness': round(std_brightness, 2),
        'mean_luminance': round(mean_luminance, 2),
        'rms_contrast': round(rms_contrast, 2),
        'michelson_contrast': round(michelson, 4),
        'dynamic_range': round(dynamic_range, 2),
        'mean_saturation': round(mean_saturation, 2),
        'std_saturation': round(std_saturation, 2),
        'brightness_score': round(brightness_score, 1),
        'contrast_score': round(contrast_score, 1),
        'saturation_score': round(saturation_score, 1)
    }

# ──────────────────────────────────────────────
# METRIC 4: Edge Density & Detail Complexity
# ──────────────────────────────────────────────

def compute_edge_density(pil_img):
    """Analyze edge density using Canny and Sobel operators."""
    gray = cv2.cvtColor(pil_to_cv2(pil_img), cv2.COLOR_BGR2GRAY)

    # Canny edge detection
    edges_canny = cv2.Canny(gray, 50, 150)
    edge_density_canny = np.sum(edges_canny > 0) / edges_canny.size

    # Sobel gradients
    sobel_x = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
    sobel_y = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
    gradient_magnitude = np.sqrt(sobel_x ** 2 + sobel_y ** 2)
    mean_gradient = np.mean(gradient_magnitude)

    # Texture complexity via local standard deviation
    local_std = ndimage.generic_filter(gray.astype(np.float64), np.std, size=7)
    texture_complexity = np.mean(local_std)

    # Detail regions (high gradient areas)
    detail_mask = gradient_magnitude > np.percentile(gradient_magnitude, 75)
    detail_ratio = np.sum(detail_mask) / detail_mask.size

    # Score
    detail_score = min(100, (edge_density_canny / 0.15) * 100)

    return {
        'edge_density_canny': round(edge_density_canny, 4),
        'mean_gradient_magnitude': round(mean_gradient, 2),
        'texture_complexity': round(texture_complexity, 2),
        'detail_ratio': round(detail_ratio, 4),
        'detail_score': round(detail_score, 1)
    }

# ──────────────────────────────────────────────
# METRIC 5: Sharpness / Blur Detection
# ──────────────────────────────────────────────

def compute_sharpness(pil_img):
    """Assess image sharpness using Laplacian variance and other methods."""
    gray = cv2.cvtColor(pil_to_cv2(pil_img), cv2.COLOR_BGR2GRAY)

    # Laplacian variance (higher = sharper)
    laplacian = cv2.Laplacian(gray, cv2.CV_64F)
    laplacian_var = laplacian.var()
    laplacian_mean = np.mean(np.abs(laplacian))

    # Tenengrad (Sobel-based focus measure)
    gx = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
    gy = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
    tenengrad = np.mean(gx ** 2 + gy ** 2)

    # Brenner focus measure
    shifted = np.roll(gray.astype(np.float64), -2, axis=1)
    brenner = np.mean((gray.astype(np.float64) - shifted) ** 2)

    # Frequency domain analysis
    f_transform = np.fft.fft2(gray.astype(np.float64))
    f_shift = np.fft.fftshift(f_transform)
    magnitude_spectrum = np.abs(f_shift)
    # High frequency ratio
    h, w = gray.shape
    center_h, center_w = h // 2, w // 2
    radius = min(h, w) // 4
    mask = np.zeros_like(gray, dtype=bool)
    Y, X = np.ogrid[:h, :w]
    mask_area = (X - center_w) ** 2 + (Y - center_h) ** 2 > radius ** 2
    high_freq_energy = np.sum(magnitude_spectrum[mask_area])
    total_energy = np.sum(magnitude_spectrum) + 1e-10
    high_freq_ratio = high_freq_energy / total_energy

    # Sharpness score (normalized)
    sharpness_score = min(100, (laplacian_var / 1500) * 100)

    return {
        'laplacian_variance': round(laplacian_var, 2),
        'laplacian_mean': round(laplacian_mean, 2),
        'tenengrad': round(tenengrad, 2),
        'brenner_focus': round(brenner, 2),
        'high_freq_ratio': round(high_freq_ratio, 4),
        'sharpness_score': round(sharpness_score, 1),
        'blur_detected': bool(laplacian_var < 100)
    }

# ──────────────────────────────────────────────
# METRIC 6: Composition Analysis
# ──────────────────────────────────────────────

def compute_composition(pil_img):
    """Analyze composition: rule of thirds, symmetry, visual weight distribution."""
    gray = cv2.cvtColor(pil_to_cv2(pil_img), cv2.COLOR_BGR2GRAY).astype(np.float64)
    h, w = gray.shape

    # Rule of thirds: check if high-interest areas align with thirds lines
    edges = cv2.Canny(gray.astype(np.uint8), 50, 150)
    third_h1, third_h2 = h // 3, 2 * h // 3
    third_w1, third_w2 = w // 3, 2 * w // 3

    # Energy near thirds intersections (4 points)
    roi_size_h = h // 10
    roi_size_w = w // 10
    thirds_points = [
        (third_h1, third_w1), (third_h1, third_w2),
        (third_h2, third_w1), (third_h2, third_w2)
    ]
    thirds_energy = 0
    for py, px in thirds_points:
        y1, y2 = max(0, py - roi_size_h), min(h, py + roi_size_h)
        x1, x2 = max(0, px - roi_size_w), min(w, px + roi_size_w)
        roi = edges[y1:y2, x1:x2]
        thirds_energy += np.sum(roi > 0)

    total_edge_energy = np.sum(edges > 0) + 1e-10
    thirds_adherence = min(1.0, thirds_energy / (total_edge_energy * 0.3))

    # Horizontal symmetry
    left_half = gray[:, :w // 2]
    right_half = np.fliplr(gray[:, w // 2:w // 2 * 2])
    if left_half.shape == right_half.shape:
        h_symmetry = 1.0 - np.mean(np.abs(left_half - right_half)) / 255.0
    else:
        min_w2 = min(left_half.shape[1], right_half.shape[1])
        h_symmetry = 1.0 - np.mean(np.abs(left_half[:, :min_w2] - right_half[:, :min_w2])) / 255.0

    # Vertical symmetry
    top_half = gray[:h // 2, :]
    bot_half = np.flipud(gray[h // 2:h // 2 * 2, :])
    if top_half.shape == bot_half.shape:
        v_symmetry = 1.0 - np.mean(np.abs(top_half - bot_half)) / 255.0
    else:
        min_h2 = min(top_half.shape[0], bot_half.shape[0])
        v_symmetry = 1.0 - np.mean(np.abs(top_half[:min_h2] - bot_half[:min_h2])) / 255.0

    # Visual weight distribution (center of mass)
    total_intensity = np.sum(gray) + 1e-10
    y_indices, x_indices = np.meshgrid(np.arange(h), np.arange(w), indexing='ij')
    center_y = np.sum(y_indices * gray) / total_intensity / h
    center_x = np.sum(x_indices * gray) / total_intensity / w
    # Distance from geometric center (0.5, 0.5)
    center_deviation = math.sqrt((center_x - 0.5) ** 2 + (center_y - 0.5) ** 2)

    # Quadrant balance
    q1 = np.mean(gray[:h // 2, :w // 2])
    q2 = np.mean(gray[:h // 2, w // 2:])
    q3 = np.mean(gray[h // 2:, :w // 2])
    q4 = np.mean(gray[h // 2:, w // 2:])
    quadrant_balance = 1.0 - np.std([q1, q2, q3, q4]) / 128.0

    composition_score = min(100, max(0, thirds_adherence * 30 + h_symmetry * 20 + quadrant_balance * 25 + (1 - center_deviation) * 25))

    return {
        'rule_of_thirds_adherence': round(thirds_adherence, 3),
        'horizontal_symmetry': round(h_symmetry, 3),
        'vertical_symmetry': round(v_symmetry, 3),
        'visual_center_x': round(center_x, 3),
        'visual_center_y': round(center_y, 3),
        'center_deviation': round(center_deviation, 4),
        'quadrant_balance': round(quadrant_balance, 3),
        'composition_score': round(composition_score, 1)
    }

# ──────────────────────────────────────────────
# METRIC 7: Color Palette Extraction
# ──────────────────────────────────────────────

def compute_color_palette(pil_img, n_colors=6):
    """Extract dominant colors using K-Means clustering."""
    img_arr = np.array(pil_img.convert('RGB'))
    pixels = img_arr.reshape(-1, 3).astype(np.float64)

    # Subsample for speed
    if len(pixels) > 50000:
        indices = np.random.choice(len(pixels), 50000, replace=False)
        pixels = pixels[indices]

    kmeans = KMeans(n_clusters=n_colors, n_init=10, max_iter=100, random_state=42)
    kmeans.fit(pixels)

    colors = kmeans.cluster_centers_.astype(int)
    labels = kmeans.labels_
    counts = np.bincount(labels)
    percentages = counts / counts.sum()

    # Sort by dominance
    sorted_idx = np.argsort(-percentages)
    palette = []
    for idx in sorted_idx:
        r, g, b = colors[idx]
        hex_color = '#{:02x}{:02x}{:02x}'.format(int(r), int(g), int(b))
        # Name the color approximately
        color_name = _approximate_color_name(int(r), int(g), int(b))
        palette.append({
            'rgb': [int(r), int(g), int(b)],
            'hex': hex_color,
            'percentage': round(float(percentages[idx]) * 100, 1),
            'name': color_name
        })

    # Color harmony score (based on hue distribution)
    hsv_colors = []
    for c in colors:
        r, g, b = c / 255.0
        pixel_hsv = cv2.cvtColor(np.array([[[r * 255, g * 255, b * 255]]], dtype=np.uint8), cv2.COLOR_RGB2HSV)
        hsv_colors.append(pixel_hsv[0, 0])

    hues = [c[0] for c in hsv_colors if c[1] > 20]  # Only consider saturated colors
    if len(hues) >= 2:
        hue_std = np.std(hues)
        harmony_score = max(0, min(100, 100 - hue_std * 0.8))
    else:
        harmony_score = 80.0  # Monochromatic is fine

    return {
        'palette': palette,
        'num_dominant_colors': n_colors,
        'color_harmony_score': round(harmony_score, 1)
    }


def _approximate_color_name(r, g, b):
    """Approximate a human-readable color name."""
    color_map = {
        'white': (255, 255, 255), 'black': (0, 0, 0),
        'red': (255, 0, 0), 'green': (0, 128, 0), 'blue': (0, 0, 255),
        'yellow': (255, 255, 0), 'cyan': (0, 255, 255), 'magenta': (255, 0, 255),
        'orange': (255, 165, 0), 'purple': (128, 0, 128), 'pink': (255, 192, 203),
        'brown': (139, 69, 19), 'gray': (128, 128, 128), 'navy': (0, 0, 128),
        'teal': (0, 128, 128), 'olive': (128, 128, 0), 'maroon': (128, 0, 0),
        'beige': (245, 245, 220), 'ivory': (255, 255, 240), 'silver': (192, 192, 192),
        'gold': (255, 215, 0), 'coral': (255, 127, 80), 'salmon': (250, 128, 114),
        'lime': (0, 255, 0), 'indigo': (75, 0, 130), 'violet': (238, 130, 238),
        'turquoise': (64, 224, 208), 'tan': (210, 180, 140), 'khaki': (240, 230, 140),
    }
    min_dist = float('inf')
    closest = 'unknown'
    for name, (cr, cg, cb) in color_map.items():
        dist = math.sqrt((r - cr) ** 2 + (g - cg) ** 2 + (b - cb) ** 2)
        if dist < min_dist:
            min_dist = dist
            closest = name
    return closest

# ──────────────────────────────────────────────
# METRIC 8: Perceptual Hashing
# ──────────────────────────────────────────────

def compute_perceptual_hash(pil_img):
    """Compute multiple perceptual hashes for image comparison."""
    gray = pil_img.convert('L')

    # Average Hash (aHash)
    resized = gray.resize((8, 8), Image.LANCZOS)
    arr = np.array(resized)
    mean_val = arr.mean()
    ahash = ''.join(['1' if px > mean_val else '0' for px in arr.flatten()])
    ahash_hex = hex(int(ahash, 2))[2:].zfill(16)

    # Difference Hash (dHash)
    resized_d = gray.resize((9, 8), Image.LANCZOS)
    arr_d = np.array(resized_d)
    dhash = ''
    for row in range(8):
        for col in range(8):
            dhash += '1' if arr_d[row, col] > arr_d[row, col + 1] else '0'
    dhash_hex = hex(int(dhash, 2))[2:].zfill(16)

    # Perceptual Hash (pHash) using DCT
    resized_p = gray.resize((32, 32), Image.LANCZOS)
    arr_p = np.array(resized_p, dtype=np.float64)
    dct = cv2.dct(arr_p)
    dct_low = dct[:8, :8]
    median_val = np.median(dct_low)
    phash = ''.join(['1' if v > median_val else '0' for v in dct_low.flatten()])
    phash_hex = hex(int(phash, 2))[2:].zfill(16)

    return {
        'average_hash': ahash_hex,
        'difference_hash': dhash_hex,
        'perceptual_hash': phash_hex
    }

# ──────────────────────────────────────────────
# METRIC 9: Noise Estimation
# ──────────────────────────────────────────────

def compute_noise_metrics(pil_img):
    """Estimate image noise level."""
    gray = cv2.cvtColor(pil_to_cv2(pil_img), cv2.COLOR_BGR2GRAY).astype(np.float64)
    h, w = gray.shape

    # Noise estimation using Laplacian (Immerkaer method)
    M = np.array([[1, -2, 1], [-2, 4, -2], [1, -2, 1]])
    sigma = np.sum(np.abs(signal.convolve2d(gray, M, mode='valid')))
    sigma = sigma * math.sqrt(0.5 * math.pi) / (6 * (w - 2) * (h - 2))

    # SNR estimate
    signal_power = np.std(gray)
    snr = signal_power / (sigma + 1e-10)

    # Noise score (lower noise = better)
    noise_score = max(0, min(100, 100 - sigma * 5))

    return {
        'estimated_noise_sigma': round(sigma, 3),
        'signal_to_noise_ratio': round(snr, 2),
        'noise_score': round(noise_score, 1)
    }

# ──────────────────────────────────────────────
# METRIC 10: Structural Similarity (SSIM)
# ──────────────────────────────────────────────

def compute_ssim(img1_cv, img2_cv):
    """Compute SSIM between two images (custom implementation)."""
    # Resize to match
    if img1_cv.shape != img2_cv.shape:
        img2_cv = resize_to_match(img2_cv, img1_cv.shape)

    gray1 = cv2.cvtColor(img1_cv, cv2.COLOR_BGR2GRAY).astype(np.float64)
    gray2 = cv2.cvtColor(img2_cv, cv2.COLOR_BGR2GRAY).astype(np.float64)

    C1 = (0.01 * 255) ** 2
    C2 = (0.03 * 255) ** 2

    mu1 = cv2.GaussianBlur(gray1, (11, 11), 1.5)
    mu2 = cv2.GaussianBlur(gray2, (11, 11), 1.5)

    mu1_sq = mu1 ** 2
    mu2_sq = mu2 ** 2
    mu1_mu2 = mu1 * mu2

    sigma1_sq = cv2.GaussianBlur(gray1 ** 2, (11, 11), 1.5) - mu1_sq
    sigma2_sq = cv2.GaussianBlur(gray2 ** 2, (11, 11), 1.5) - mu2_sq
    sigma12 = cv2.GaussianBlur(gray1 * gray2, (11, 11), 1.5) - mu1_mu2

    numerator = (2 * mu1_mu2 + C1) * (2 * sigma12 + C2)
    denominator = (mu1_sq + mu2_sq + C1) * (sigma1_sq + sigma2_sq + C2)

    ssim_map = numerator / denominator
    return float(np.mean(ssim_map))

# ──────────────────────────────────────────────
# METRIC 11: Reference-Based Metrics
# ──────────────────────────────────────────────

def compute_reference_metrics(pil_img, pil_ref):
    """Compute all reference-based comparison metrics."""
    img_cv = pil_to_cv2(pil_img)
    ref_cv = pil_to_cv2(pil_ref)

    if img_cv.shape != ref_cv.shape:
        ref_cv = resize_to_match(ref_cv, img_cv.shape)

    # SSIM
    ssim_val = compute_ssim(img_cv, ref_cv)

    # MSE & PSNR
    mse = np.mean((img_cv.astype(np.float64) - ref_cv.astype(np.float64)) ** 2)
    if mse == 0:
        psnr = float('inf')
    else:
        psnr = 10 * math.log10(255.0 ** 2 / mse)

    # Histogram correlation per channel
    hist_corr = []
    for i in range(3):
        h1 = cv2.calcHist([img_cv], [i], None, [256], [0, 256]).flatten()
        h2 = cv2.calcHist([ref_cv], [i], None, [256], [0, 256]).flatten()
        corr = cv2.compareHist(h1.astype(np.float32), h2.astype(np.float32), cv2.HISTCMP_CORREL)
        hist_corr.append(float(corr))

    # Perceptual hash distance
    hash1 = compute_perceptual_hash(pil_img)
    hash2 = compute_perceptual_hash(pil_ref)

    def hamming_hex(h1, h2):
        b1 = bin(int(h1, 16))[2:].zfill(64)
        b2 = bin(int(h2, 16))[2:].zfill(64)
        return sum(c1 != c2 for c1, c2 in zip(b1, b2))

    phash_dist = hamming_hex(hash1['perceptual_hash'], hash2['perceptual_hash'])
    phash_similarity = 1.0 - phash_dist / 64.0

    # Feature matching using ORB
    orb = cv2.ORB_create(nfeatures=500)
    gray1 = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
    gray2 = cv2.cvtColor(ref_cv, cv2.COLOR_BGR2GRAY)
    kp1, des1 = orb.detectAndCompute(gray1, None)
    kp2, des2 = orb.detectAndCompute(gray2, None)

    feature_match_score = 0.0
    if des1 is not None and des2 is not None and len(des1) > 0 and len(des2) > 0:
        bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
        matches = bf.match(des1, des2)
        good_matches = [m for m in matches if m.distance < 50]
        feature_match_score = len(good_matches) / max(len(kp1), len(kp2), 1)

    # Overall reference similarity score (weighted average, all components 0-1)
    ref_score = min(100, (ssim_val * 0.35 + np.mean(hist_corr) * 0.25 + phash_similarity * 0.20 + feature_match_score * 0.20) * 100)

    return {
        'ssim': round(ssim_val, 4),
        'mse': round(mse, 2),
        'psnr': round(psnr, 2) if psnr != float('inf') else 'inf',
        'histogram_correlation': {
            'blue': round(hist_corr[0], 4),
            'green': round(hist_corr[1], 4),
            'red': round(hist_corr[2], 4),
            'mean': round(np.mean(hist_corr), 4)
        },
        'perceptual_hash_distance': phash_dist,
        'perceptual_hash_similarity': round(phash_similarity, 4),
        'feature_match_score': round(feature_match_score, 4),
        'reference_similarity_score': round(ref_score, 1)
    }

# ──────────────────────────────────────────────
# METRIC 12: Prompt Constraint Parsing & Checking
# ──────────────────────────────────────────────

def parse_prompt_constraints(prompt_text):
    """Parse structured constraints from the prompt text."""
    constraints = {
        'background_colors': [],
        'required_colors': [],
        'forbidden_elements': [],
        'required_objects': [],
        'style_keywords': [],
        'composition_type': None,
        'text_content': [],
        'count_requirements': [],
        'lighting_type': None,
        'aspect_ratio': None,
    }

    text_lower = prompt_text.lower()

    # Background color detection
    bg_patterns = [
        r'(?:plain|seamless)?\s*(white|black|gray|grey|blue|red|green|light[\s-]?gray|light[\s-]?grey|deep blue)\s*background',
        r'background\s*(?:must\s+)?(?:be(?:come)?|:)\s*(?:a\s+)?([\w\s-]+?)(?:\s*[,;.]|\s+with)',
    ]
    for pat in bg_patterns:
        matches = re.findall(pat, text_lower)
        constraints['background_colors'].extend([m.strip() for m in matches])

    # Required colors
    color_keywords = ['matte-black', 'matte black', 'stainless-steel', 'silver', 'blue', 'red',
                      'white', 'yellow', 'green', 'pink', 'black', 'cyan', 'gold', 'orange',
                      'purple', 'brown', 'gray', 'grey', 'pastel', 'deep blue', 'light cyan']
    for ck in color_keywords:
        if ck in text_lower:
            constraints['required_colors'].append(ck)

    # Required objects
    object_patterns = [
        r'must include[:\s]+(.+?)(?:\.|$)',
        r'include\s+(?:exactly\s+)?(?:these\s+)?objects?\s*[:\s]+(.+?)(?:\.|$)',
        r'place\s+(?:exactly\s+)?(\d+\s+\w+)',
    ]
    for pat in object_patterns:
        matches = re.findall(pat, text_lower)
        for m in matches:
            items = re.split(r'[,;]', m)
            constraints['required_objects'].extend([i.strip() for i in items if i.strip()])

    # Specific objects by keyword
    obj_keywords = ['laptop', 'notebook', 'pen', 'coffee mug', 'plant', 'smartphone', 'phone',
                    'sticky note', 'paperclip', 'bottle', 'water bottle', 'arrow', 'callout']
    for ok in obj_keywords:
        if ok in text_lower and ok not in [o.lower() for o in constraints['required_objects']]:
            constraints['required_objects'].append(ok)

    # Forbidden elements
    forbidden_patterns = [
        r'no\s+([\w\s,]+?)(?:\.|$)',
        r'do\s+not\s+add\s+([\w\s,]+?)(?:\.|$)',
        r'without\s+([\w\s,]+?)(?:\.|$)',
    ]
    for pat in forbidden_patterns:
        matches = re.findall(pat, text_lower)
        for m in matches:
            items = re.split(r'[,;]', m)
            constraints['forbidden_elements'].extend([i.strip() for i in items if len(i.strip()) > 2])

    # Style keywords
    styles = ['photorealistic', 'realistic', 'oil painting', 'watercolor', 'minimalist',
              'cyberpunk', 'blueprint', 'clay animation', 'stop-motion', 'flat lay',
              'product photo', 'studio', 'overhead', 'top-down', 'technical', 'line art',
              'cartoon', 'illustration', 'sketch', 'vintage', 'retro', '3d render']
    for s in styles:
        if s in text_lower:
            constraints['style_keywords'].append(s)

    # Composition type
    if any(k in text_lower for k in ['centered', 'center']):
        constraints['composition_type'] = 'centered'
    elif any(k in text_lower for k in ['flat lay', 'top-down', 'overhead']):
        constraints['composition_type'] = 'overhead'
    elif '3/4 angle' in text_lower:
        constraints['composition_type'] = '3/4 angle'

    # Text content requirements
    text_patterns = [
        r'write\s+(?:exactly\s+)?(?:this\s+)?text[:\s]+"?([^"]+?)"?\s*$',
        r'text\s+in\s+uppercase:\s+(.+?)(?:\s*$|\s*\n)',
        r'containing\s+only\s+(?:a\s+)?(?:single\s+)?letter:\s*([A-Z](?:,\s*[A-Z])*)',
    ]
    for pat in text_patterns:
        matches = re.findall(pat, text_lower if 'uppercase' not in pat else prompt_text, re.MULTILINE)
        constraints['text_content'].extend(matches)

    # Count requirements
    count_patterns = [
        r'exactly\s+(\d+)\s+([\w\s]+?)(?:\s*[,;.]|\s+visible|\s+on)',
        r'(\d+)\s+(callout\s+arrows?|sticky\s+notes?|paperclips?|objects?)',
    ]
    for pat in count_patterns:
        matches = re.findall(pat, text_lower)
        for count, obj in matches:
            constraints['count_requirements'].append({'object': obj.strip(), 'count': int(count)})

    # Lighting
    if 'softbox' in text_lower or 'studio light' in text_lower:
        constraints['lighting_type'] = 'studio'
    elif 'daylight' in text_lower or 'natural' in text_lower:
        constraints['lighting_type'] = 'natural'
    elif 'soft' in text_lower and 'light' in text_lower:
        constraints['lighting_type'] = 'soft'

    return constraints


def check_constraint_adherence(pil_img, constraints):
    """Check how well the image adheres to parsed constraints."""
    results = {}
    scores = []
    img_arr = np.array(pil_img.convert('RGB'))
    hsv_arr = cv2.cvtColor(img_arr, cv2.COLOR_RGB2HSV)

    # 1. Background color check
    if constraints.get('background_colors'):
        bg_target = constraints['background_colors'][0]
        # Sample corners and edges for background color
        h, w = img_arr.shape[:2]
        border = max(5, min(h, w) // 20)
        bg_pixels = np.concatenate([
            img_arr[:border, :, :].reshape(-1, 3),
            img_arr[-border:, :, :].reshape(-1, 3),
            img_arr[:, :border, :].reshape(-1, 3),
            img_arr[:, -border:, :].reshape(-1, 3),
        ])
        bg_mean = bg_pixels.mean(axis=0)

        color_targets = {
            'white': [255, 255, 255], 'black': [0, 0, 0],
            'light gray': [200, 200, 200], 'light-gray': [200, 200, 200],
            'light grey': [200, 200, 200], 'gray': [128, 128, 128],
            'grey': [128, 128, 128], 'blue': [0, 0, 200],
            'deep blue': [0, 0, 139], 'red': [200, 0, 0],
            'green': [0, 128, 0],
        }
        target_rgb = color_targets.get(bg_target, [128, 128, 128])
        bg_distance = np.sqrt(np.sum((bg_mean - np.array(target_rgb)) ** 2))
        bg_score = max(0, 100 - bg_distance * 0.5)
        results['background_color'] = {
            'expected': bg_target,
            'detected_rgb': bg_mean.astype(int).tolist(),
            'distance': round(bg_distance, 1),
            'score': round(bg_score, 1)
        }
        scores.append(bg_score)

    # 2. Color presence check
    if constraints.get('required_colors'):
        color_checks = []
        palette_data = compute_color_palette(pil_img, n_colors=8)
        detected_names = [c['name'] for c in palette_data['palette']]

        for req_color in constraints['required_colors']:
            # Normalize color name
            normalized = req_color.replace('-', ' ').replace('matte ', '').replace('stainless steel', 'silver')
            found = any(normalized in dn or dn in normalized for dn in detected_names)
            color_checks.append({
                'color': req_color,
                'found': found,
                'score': 100 if found else 0
            })

        if color_checks:
            avg_color_score = np.mean([c['score'] for c in color_checks])
            results['color_presence'] = {
                'checks': color_checks,
                'score': round(avg_color_score, 1)
            }
            scores.append(avg_color_score)

    # 3. Style analysis
    if constraints.get('style_keywords'):
        style_scores = []
        bcs = compute_brightness_contrast_saturation(pil_img)
        edge = compute_edge_density(pil_img)
        sharp = compute_sharpness(pil_img)

        for style in constraints['style_keywords']:
            style_score = 50  # Default neutral
            if style in ['photorealistic', 'realistic', 'product photo', 'studio']:
                # Expect high detail, moderate contrast, good sharpness
                style_score = min(100, (sharp['sharpness_score'] * 0.4 + edge['detail_score'] * 0.3 + bcs['contrast_score'] * 0.3))
            elif style in ['blueprint', 'technical', 'line art']:
                # Expect high edge density, low color diversity
                color_div = compute_color_histogram(pil_img)['color_diversity_score']
                style_score = min(100, edge['detail_score'] * 0.5 + (100 - color_div) * 0.5)
            elif style in ['watercolor', 'oil painting']:
                # Expect softer edges, higher saturation
                style_score = min(100, bcs['saturation_score'] * 0.5 + (100 - sharp['sharpness_score']) * 0.3 + 20)
            elif style in ['flat lay', 'overhead', 'top-down']:
                # Check composition suggests top-down view
                comp = compute_composition(pil_img)
                style_score = min(100, comp['quadrant_balance'] * 80 + 20)

            style_scores.append({'style': style, 'score': round(style_score, 1)})

        results['style_adherence'] = {
            'checks': style_scores,
            'score': round(np.mean([s['score'] for s in style_scores]), 1)
        }
        scores.append(results['style_adherence']['score'])

    # 4. Composition type check
    if constraints.get('composition_type'):
        comp = compute_composition(pil_img)
        comp_type = constraints['composition_type']
        if comp_type == 'centered':
            comp_score = max(0, 100 - comp['center_deviation'] * 300)
        elif comp_type == 'overhead':
            comp_score = comp['quadrant_balance'] * 100
        else:
            comp_score = comp['composition_score']
        results['composition_adherence'] = {
            'expected': comp_type,
            'center_deviation': comp['center_deviation'],
            'score': round(comp_score, 1)
        }
        scores.append(comp_score)

    # 5. Lighting check
    if constraints.get('lighting_type'):
        bcs = compute_brightness_contrast_saturation(pil_img)
        lt = constraints['lighting_type']
        if lt == 'studio':
            light_score = min(100, bcs['contrast_score'] * 0.6 + bcs['brightness_score'] * 0.4)
        elif lt == 'natural':
            light_score = bcs['brightness_score']
        else:
            light_score = max(0, 100 - bcs['rms_contrast'] * 0.5)  # soft = low contrast
        results['lighting_adherence'] = {
            'expected': lt,
            'brightness': bcs['mean_brightness'],
            'contrast': bcs['rms_contrast'],
            'score': round(light_score, 1)
        }
        scores.append(light_score)

    # Overall constraint adherence score
    overall = round(np.mean(scores), 1) if scores else 50.0
    results['overall_constraint_score'] = overall

    return results

# ──────────────────────────────────────────────
# MASTER EVALUATION FUNCTION
# ──────────────────────────────────────────────

def evaluate_image(pil_img, prompt_text, pil_ref=None):
    """Run all metrics on a single image."""
    results = {}

    # Reference-free metrics
    results['resolution'] = compute_resolution_metrics(pil_img, prompt_text)
    results['color_histogram'] = compute_color_histogram(pil_img)
    results['brightness_contrast_saturation'] = compute_brightness_contrast_saturation(pil_img)
    results['edge_density'] = compute_edge_density(pil_img)
    results['sharpness'] = compute_sharpness(pil_img)
    results['composition'] = compute_composition(pil_img)
    results['color_palette'] = compute_color_palette(pil_img)
    results['perceptual_hash'] = compute_perceptual_hash(pil_img)
    results['noise'] = compute_noise_metrics(pil_img)

    # Constraint adherence
    constraints = parse_prompt_constraints(prompt_text)
    results['constraints_parsed'] = constraints
    results['constraint_adherence'] = check_constraint_adherence(pil_img, constraints)

    # Reference-based metrics
    if pil_ref is not None:
        results['reference_comparison'] = compute_reference_metrics(pil_img, pil_ref)

    # Compute composite scores
    category_scores = {
        'Technical Quality': round(np.mean([
            results['resolution']['resolution_score'],
            results['sharpness']['sharpness_score'],
            results['noise']['noise_score'],
        ]), 1),
        'Color & Tone': round(np.mean([
            results['brightness_contrast_saturation']['brightness_score'],
            results['brightness_contrast_saturation']['contrast_score'],
            results['brightness_contrast_saturation']['saturation_score'],
            results['color_histogram']['color_diversity_score'],
            results['color_palette']['color_harmony_score'],
        ]), 1),
        'Detail & Texture': round(np.mean([
            results['edge_density']['detail_score'],
            results['sharpness']['sharpness_score'],
        ]), 1),
        'Composition': results['composition']['composition_score'],
        'Constraint Adherence': results['constraint_adherence'].get('overall_constraint_score', 50.0),
    }

    if pil_ref is not None:
        category_scores['Reference Similarity'] = results['reference_comparison']['reference_similarity_score']

    results['category_scores'] = category_scores
    results['overall_score'] = round(np.mean(list(category_scores.values())), 1)

    return results

# ──────────────────────────────────────────────
# FLASK ROUTES
# ──────────────────────────────────────────────

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/evaluate', methods=['POST'])
def evaluate():
    """Main evaluation endpoint."""
    try:
        prompt_text = request.form.get('prompt', '')
        if not prompt_text.strip():
            return jsonify({'error': 'Prompt text is required'}), 400

        # Parse reference image if provided
        ref_file = request.files.get('reference_image')
        pil_ref = None
        if ref_file and ref_file.filename:
            pil_ref = Image.open(ref_file.stream).convert('RGB')

        # Parse model images
        model_results = {}
        model_names = request.form.getlist('model_names[]')
        model_images = request.files.getlist('model_images[]')

        if not model_images or not model_names:
            return jsonify({'error': 'At least one model image is required'}), 400

        for i, (name, img_file) in enumerate(zip(model_names, model_images)):
            if not img_file or not img_file.filename:
                continue
            model_name = name.strip() or f'Model {i+1}'
            pil_img = Image.open(img_file.stream).convert('RGB')

            # Generate thumbnail
            thumbnail = img_to_base64_thumbnail(pil_img, 150)

            # Run evaluation
            metrics = evaluate_image(pil_img, prompt_text, pil_ref)
            metrics['thumbnail'] = thumbnail
            metrics['model_name'] = model_name

            model_results[model_name] = metrics

        if not model_results:
            return jsonify({'error': 'No valid images were uploaded'}), 400

        # Build leaderboard
        leaderboard = sorted(
            [{'model': name, 'overall_score': data['overall_score'],
              'category_scores': data['category_scores']}
             for name, data in model_results.items()],
            key=lambda x: x['overall_score'], reverse=True
        )

        # Parse constraints for display
        constraints = parse_prompt_constraints(prompt_text)

        response = {
            'success': True,
            'prompt': prompt_text,
            'constraints': constraints,
            'models': model_results,
            'leaderboard': leaderboard,
            'timestamp': datetime.now().isoformat(),
            'num_models': len(model_results),
            'has_reference': pil_ref is not None
        }

        return jsonify(sanitize_for_json(response))

    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/llm-judge', methods=['POST'])
def llm_judge():
    """LLM-as-Judge endpoint using Groq API.
    
    Supports two modes:
    - Vision mode (default): Uses Llama 4 Scout which can see images directly
    - Text mode (fallback): Sends programmatic image description to Llama 3.3 70B
    """
    try:
        import requests as http_requests  # avoid name clash with flask.request

        api_key = request.form.get('groq_api_key', '').strip()
        if not api_key or not api_key.startswith('gsk_'):
            return jsonify({'error': 'Valid Groq API key required (starts with gsk_)'}), 400

        prompt_text = request.form.get('prompt', '')
        if not prompt_text.strip():
            return jsonify({'error': 'Prompt text is required'}), 400

        use_vision = request.form.get('use_vision', 'true').lower() == 'true'

        model_names = request.form.getlist('model_names[]')
        model_images = request.files.getlist('model_images[]')

        judge_results = {}

        GROQ_URL = 'https://api.groq.com/openai/v1/chat/completions'
        HEADERS = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {api_key}'
        }

        JUDGE_INSTRUCTIONS = """You are an expert image generation evaluator for an academic thesis benchmark.
Score each category from 0-100 based on how well the AI-generated image matches the original prompt.

Respond ONLY with valid JSON in this exact format (no markdown, no backticks):
{
  "prompt_adherence": <score>,
  "technical_quality": <score>,
  "style_accuracy": <score>,
  "composition": <score>,
  "color_accuracy": <score>,
  "detail_realism": <score>,
  "overall_quality": <score>,
  "strengths": ["<strength1>", "<strength2>"],
  "weaknesses": ["<weakness1>", "<weakness2>"],
  "summary": "<2-3 sentence evaluation summary>"
}"""

        for i, (name, img_file) in enumerate(zip(model_names, model_images)):
            if not img_file or not img_file.filename:
                continue
            model_name = name.strip() or f'Model {i+1}'
            pil_img = Image.open(img_file.stream).convert('RGB')

            try:
                if use_vision:
                    # === VISION MODE: Send actual image to Llama 4 Scout ===
                    buf = io.BytesIO()
                    # Resize large images to reduce base64 payload
                    img_for_api = pil_img.copy()
                    img_for_api.thumbnail((1024, 1024), Image.LANCZOS)
                    img_for_api.save(buf, format='JPEG', quality=85)
                    img_b64 = base64.b64encode(buf.getvalue()).decode('utf-8')

                    user_content = [
                        {
                            "type": "text",
                            "text": f"ORIGINAL PROMPT given to the AI image generator:\n\"\"\"\n{prompt_text}\n\"\"\"\n\nThe image attached is what the AI model generated. Evaluate how well it follows the prompt."
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{img_b64}"
                            }
                        }
                    ]

                    payload = {
                        "model": "meta-llama/llama-4-scout-17b-16e-instruct",
                        "messages": [
                            {"role": "system", "content": JUDGE_INSTRUCTIONS},
                            {"role": "user", "content": user_content}
                        ],
                        "temperature": 0.3,
                        "max_tokens": 1000
                    }
                else:
                    # === TEXT MODE: Send programmatic description to Llama 3.3 ===
                    description = _generate_image_description(pil_img)

                    user_content = f"""ORIGINAL PROMPT (given to the AI model):
\"\"\"{prompt_text}\"\"\"

GENERATED IMAGE ANALYSIS (computed programmatically from the output image):
{description}

Evaluate how well the AI model followed the prompt instructions."""

                    payload = {
                        "model": "llama-3.3-70b-versatile",
                        "messages": [
                            {"role": "system", "content": JUDGE_INSTRUCTIONS},
                            {"role": "user", "content": user_content}
                        ],
                        "temperature": 0.3,
                        "max_tokens": 1000
                    }

                # Make the API call using requests library
                resp = http_requests.post(
                    GROQ_URL,
                    headers=HEADERS,
                    json=payload,
                    timeout=60
                )

                if resp.status_code != 200:
                    error_detail = resp.text[:500]
                    judge_results[model_name] = {
                        'error': f'Groq API returned {resp.status_code}: {error_detail}',
                        'success': False
                    }
                    continue

                result = resp.json()
                llm_response = result['choices'][0]['message']['content']

                # Parse JSON from response (handle markdown fences)
                llm_response_clean = llm_response.strip()
                if llm_response_clean.startswith('```'):
                    llm_response_clean = re.sub(r'^```(?:json)?\s*', '', llm_response_clean)
                    llm_response_clean = re.sub(r'\s*```$', '', llm_response_clean)

                judge_data = json.loads(llm_response_clean)
                judge_results[model_name] = {
                    'scores': judge_data,
                    'success': True
                }

            except json.JSONDecodeError as json_err:
                judge_results[model_name] = {
                    'error': f'Failed to parse LLM response as JSON: {str(json_err)}. Raw: {llm_response[:300]}',
                    'success': False
                }
            except http_requests.exceptions.Timeout:
                judge_results[model_name] = {
                    'error': 'Request timed out (60s). The image may be too large or Groq is overloaded.',
                    'success': False
                }
            except http_requests.exceptions.ConnectionError as conn_err:
                judge_results[model_name] = {
                    'error': f'Connection error: {str(conn_err)}. Check your internet connection.',
                    'success': False
                }
            except Exception as api_err:
                judge_results[model_name] = {
                    'error': str(api_err),
                    'success': False
                }

        return jsonify(sanitize_for_json({
            'success': True,
            'judge_results': judge_results
        }))

    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


def _generate_image_description(pil_img):
    """Generate a detailed textual description of image properties for LLM judge."""
    res = compute_resolution_metrics(pil_img)
    bcs = compute_brightness_contrast_saturation(pil_img)
    palette = compute_color_palette(pil_img, n_colors=6)
    edge = compute_edge_density(pil_img)
    sharp = compute_sharpness(pil_img)
    comp = compute_composition(pil_img)
    noise = compute_noise_metrics(pil_img)

    palette_desc = ", ".join([f"{c['name']} ({c['hex']}, {c['percentage']}%)" for c in palette['palette']])

    desc = f"""IMAGE PROPERTIES:
- Resolution: {res['width']}x{res['height']} ({res['megapixels']} MP, {res['orientation']})
- Aspect Ratio: {res['aspect_ratio']} (closest standard: {res['closest_standard_ratio']})
- Mean Brightness: {bcs['mean_brightness']:.1f}/255
- RMS Contrast: {bcs['rms_contrast']:.1f}
- Mean Saturation: {bcs['mean_saturation']:.1f}/255
- Dynamic Range: {bcs['dynamic_range']:.1f}
- Dominant Colors (by area): {palette_desc}
- Color Harmony Score: {palette['color_harmony_score']}/100
- Edge Density: {edge['edge_density_canny']:.4f} (detail ratio: {edge['detail_ratio']:.4f})
- Sharpness (Laplacian variance): {sharp['laplacian_variance']:.1f} ({'sharp' if not sharp['blur_detected'] else 'potentially blurry'})
- Composition: rule-of-thirds adherence {comp['rule_of_thirds_adherence']:.2f}, H-symmetry {comp['horizontal_symmetry']:.2f}, V-symmetry {comp['vertical_symmetry']:.2f}
- Visual center of mass: ({comp['visual_center_x']:.2f}, {comp['visual_center_y']:.2f})
- Noise level: sigma={noise['estimated_noise_sigma']:.2f}, SNR={noise['signal_to_noise_ratio']:.1f}
- Texture complexity: {edge['texture_complexity']:.1f}"""

    return desc


@app.route('/export', methods=['POST'])
def export_results():
    """Export evaluation results as CSV or JSON."""
    try:
        data = request.get_json()
        export_format = data.get('format', 'json')
        results = data.get('results', {})

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        if export_format == 'json':
            filename = f'image_eval_results_{timestamp}.json'
            filepath = os.path.join(EXPORT_FOLDER, filename)
            with open(filepath, 'w') as f:
                json.dump(results, f, indent=2, default=str)
            return send_file(filepath, as_attachment=True, download_name=filename)

        elif export_format == 'csv':
            filename = f'image_eval_results_{timestamp}.csv'
            filepath = os.path.join(EXPORT_FOLDER, filename)

            models = results.get('models', {})
            if not models:
                return jsonify({'error': 'No results to export'}), 400

            # Flatten metrics for CSV
            rows = []
            for model_name, model_data in models.items():
                row = {'Model': model_name, 'Overall Score': model_data.get('overall_score', '')}
                # Category scores
                for cat, score in model_data.get('category_scores', {}).items():
                    row[f'Category: {cat}'] = score
                # Detailed metrics
                for metric_group, metrics in model_data.items():
                    if isinstance(metrics, dict) and metric_group not in ['category_scores', 'constraints_parsed', 'thumbnail', 'perceptual_hash']:
                        for key, val in metrics.items():
                            if not isinstance(val, (dict, list)):
                                row[f'{metric_group}.{key}'] = val
                rows.append(row)

            if rows:
                fieldnames = list(rows[0].keys())
                # Ensure all rows have same keys
                for r in rows:
                    for k in r:
                        if k not in fieldnames:
                            fieldnames.append(k)

                with open(filepath, 'w', newline='') as f:
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writeheader()
                    writer.writerows(rows)

                return send_file(filepath, as_attachment=True, download_name=filename)

        return jsonify({'error': 'Invalid format'}), 400

    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True, port=5000)