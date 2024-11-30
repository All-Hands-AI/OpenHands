from collections import Counter
from copy import deepcopy
from difflib import SequenceMatcher
from io import BytesIO

from bs4 import BeautifulSoup, Comment, NavigableString, Tag
import cv2
import numpy as np
import torch
from colormath.color_conversions import convert_color
from colormath.color_diff import delta_e_cie2000
from colormath.color_objects import LabColor, sRGBColor
from PIL import Image, ImageChops, ImageColor
from scipy.optimize import linear_sum_assignment
from transformers import CLIPModel, CLIPProcessor

from openhands.core.logger import openhands_logger as logger


def calculate_similarity(block1, block2):
    """Calculate text similarity between two blocks using SequenceMatcher."""
    text_similarity = SequenceMatcher(None, block1['text'], block2['text']).ratio()
    return text_similarity


def adjust_cost_for_context(cost_matrix, consecutive_bonus=1.0, window_size=20):
    """Adjust cost matrix by considering context similarity."""
    if window_size <= 0:
        return cost_matrix

    n, m = cost_matrix.shape
    adjusted_cost_matrix = np.copy(cost_matrix)

    for i in range(n):
        for j in range(m):
            if adjusted_cost_matrix[i][j] >= -0.5:
                continue
            nearby_matrix = cost_matrix[
                max(0, i - window_size) : min(n, i + window_size + 1),
                max(0, j - window_size) : min(m, j + window_size + 1),
            ]
            flattened_array = nearby_matrix.flatten()
            sorted_array = np.sort(flattened_array)[::-1]
            sorted_array = np.delete(
                sorted_array, np.where(sorted_array == cost_matrix[i, j])[0][0]
            )
            top_k_elements = sorted_array[-window_size * 2 :]
            bonus = consecutive_bonus * np.sum(top_k_elements)
            adjusted_cost_matrix[i][j] += bonus
    return adjusted_cost_matrix


def create_cost_matrix(A, B):
    """Create cost matrix for block matching."""
    n = len(A)
    m = len(B)
    cost_matrix = np.zeros((n, m))
    for i in range(n):
        for j in range(m):
            cost_matrix[i, j] = -calculate_similarity(A[i], B[j])
    return cost_matrix


def calculate_distance_max_1d(x1, y1, x2, y2):
    """Calculate maximum 1D distance between points."""
    return max(abs(x2 - x1), abs(y2 - y1))


def calculate_ratio(h1, h2):
    """Calculate ratio between two heights."""
    return max(h1, h2) / min(h1, h2)


def rgb_to_lab(rgb):
    """Convert RGB color to Lab color space."""
    rgb_color = sRGBColor(rgb[0], rgb[1], rgb[2], is_upscaled=True)
    lab_color = convert_color(rgb_color, LabColor)
    return lab_color


def color_similarity_ciede2000(rgb1, rgb2):
    """Calculate color similarity using CIEDE2000 formula."""
    lab1 = rgb_to_lab(rgb1)
    lab2 = rgb_to_lab(rgb2)
    delta_e = delta_e_cie2000(lab1, lab2)
    similarity = max(0, 1 - (delta_e / 100))
    return similarity


def merge_blocks_wo_check(block1, block2):
    """Merge two blocks without additional checks."""
    merged_text = block1['text'] + ' ' + block2['text']
    x_min = min(block1['bbox'][0], block2['bbox'][0])
    y_min = min(block1['bbox'][1], block2['bbox'][1])
    x_max = max(
        block1['bbox'][0] + block1['bbox'][2], block2['bbox'][0] + block2['bbox'][2]
    )
    y_max = max(
        block1['bbox'][1] + block1['bbox'][3], block2['bbox'][1] + block2['bbox'][3]
    )
    merged_bbox = (x_min, y_min, x_max - x_min, y_max - y_min)
    merged_color = tuple(
        (color1 + color2) // 2
        for color1, color2 in zip(block1['color'], block2['color'])
    )
    return {'text': merged_text, 'bbox': merged_bbox, 'color': merged_color}


def find_maximum_matching(A, B, consecutive_bonus, window_size):
    """Find maximum matching between two sets of blocks."""
    cost_matrix = create_cost_matrix(A, B)
    cost_matrix = adjust_cost_for_context(cost_matrix, consecutive_bonus, window_size)
    row_ind, col_ind = linear_sum_assignment(cost_matrix)
    current_cost = cost_matrix[row_ind, col_ind].tolist()
    return list(zip(row_ind, col_ind)), current_cost, cost_matrix


def remove_indices(lst, indices):
    """Remove indices from list in reverse order."""
    for index in sorted(indices, reverse=True):
        if index < len(lst):
            lst.pop(index)
    return lst


def merge_blocks_by_list(blocks, merge_list):
    """Merge blocks according to merge list."""
    pop_list = []
    while merge_list:
        i = merge_list[0][0]
        j = merge_list[0][1]
        blocks[i] = merge_blocks_wo_check(blocks[i], blocks[j])
        pop_list.append(j)
        merge_list.pop(0)
        if merge_list:
            new_merge_list = []
            for k in range(len(merge_list)):
                if (
                    merge_list[k][0] != i
                    and merge_list[k][1] != i
                    and merge_list[k][0] != j
                    and merge_list[k][1] != j
                ):
                    new_merge_list.append(merge_list[k])
            merge_list = new_merge_list
    remove_indices(blocks, pop_list)
    return blocks


def difference_of_means(list1, list2):
    """Calculate difference of means between two lists."""
    counter1 = Counter(list1)
    counter2 = Counter(list2)

    for element in set(list1) & set(list2):
        common_count = min(counter1[element], counter2[element])
        counter1[element] -= common_count
        counter2[element] -= common_count

    unique_list1 = [item for item in counter1.elements()]
    unique_list2 = [item for item in counter2.elements()]

    mean_list1 = sum(unique_list1) / len(unique_list1) if unique_list1 else 0
    mean_list2 = sum(unique_list2) / len(unique_list2) if unique_list2 else 0

    if mean_list1 - mean_list2 > 0:
        if min(unique_list1) > min(unique_list2):
            return mean_list1 - mean_list2
        return 0.0
    return mean_list1 - mean_list2


def find_possible_merge(A, B, consecutive_bonus, window_size, debug=False):
    """Find possible merges between blocks."""
    merge_bonus = 0.0
    merge_windows = 1

    def sortFn(value):
        return value[2]

    while True:
        A_changed = False
        B_changed = False

        matching, current_cost, cost_matrix = find_maximum_matching(
            A, B, merge_bonus, merge_windows
        )

        if len(A) >= 2:
            merge_list = []
            for i in range(len(A) - 1):
                new_A = deepcopy(A)
                new_A[i] = merge_blocks_wo_check(new_A[i], new_A[i + 1])
                new_A.pop(i + 1)
                updated_matching, updated_cost, _ = find_maximum_matching(
                    new_A, B, merge_bonus, merge_windows
                )
                diff = difference_of_means(current_cost, updated_cost)
                if diff > 0.05:
                    merge_list.append([i, i + 1, diff])

            merge_list.sort(key=sortFn, reverse=True)
            if merge_list:
                A_changed = True
                A = merge_blocks_by_list(A, merge_list)
                matching, current_cost, cost_matrix = find_maximum_matching(
                    A, B, merge_bonus, merge_windows
                )

        if len(B) >= 2:
            merge_list = []
            for i in range(len(B) - 1):
                new_B = deepcopy(B)
                new_B[i] = merge_blocks_wo_check(new_B[i], new_B[i + 1])
                new_B.pop(i + 1)
                updated_matching, updated_cost, _ = find_maximum_matching(
                    A, new_B, merge_bonus, merge_windows
                )
                diff = difference_of_means(current_cost, updated_cost)
                if diff > 0.05:
                    merge_list.append([i, i + 1, diff])

            merge_list.sort(key=sortFn, reverse=True)
            if merge_list:
                B_changed = True
                B = merge_blocks_by_list(B, merge_list)
                matching, current_cost, cost_matrix = find_maximum_matching(
                    A, B, merge_bonus, merge_windows
                )

        if not A_changed and not B_changed:
            break

    matching, _, _ = find_maximum_matching(A, B, consecutive_bonus, window_size)
    return A, B, matching


def merge_blocks_by_bbox(blocks):
    """Merge blocks with same bounding box."""
    merged_blocks = {}
    for block in blocks:
        bbox = tuple(block['bbox'])
        if bbox in merged_blocks:
            existing_block = merged_blocks[bbox]
            existing_block['text'] += ' ' + block['text']
            existing_block['color'] = [
                (ec + c) / 2 for ec, c in zip(existing_block['color'], block['color'])
            ]
        else:
            merged_blocks[bbox] = block
    return list(merged_blocks.values())


def mask_bounding_boxes_with_inpainting(image, bounding_boxes):
    """Mask bounding boxes in image using inpainting."""
    image_cv = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
    mask = np.zeros(image_cv.shape[:2], dtype=np.uint8)
    height, width = image_cv.shape[:2]

    for bbox in bounding_boxes:
        x_ratio, y_ratio, w_ratio, h_ratio = bbox
        x = int(x_ratio * width)
        y = int(y_ratio * height)
        w = int(w_ratio * width)
        h = int(h_ratio * height)
        mask[y : y + h, x : x + w] = 255

    inpainted_image = cv2.inpaint(image_cv, mask, 3, cv2.INPAINT_TELEA)
    return Image.fromarray(cv2.cvtColor(inpainted_image, cv2.COLOR_BGR2RGB))


def rescale_and_mask(image, blocks):
    """Rescale image and mask blocks."""
    if blocks:
        image = mask_bounding_boxes_with_inpainting(image, blocks)

    width, height = image.size
    if width < height:
        new_size = (width, width)
    else:
        new_size = (height, height)

    return image.resize(new_size, Image.LANCZOS)


def calculate_clip_similarity(image1, image2, blocks1, blocks2):
    """Calculate CLIP similarity between two images."""
    model = CLIPModel.from_pretrained('openai/clip-vit-base-patch32')
    processor = CLIPProcessor.from_pretrained('openai/clip-vit-base-patch32')
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    model = model.to(device)

    # Mask and preprocess images
    image1_masked = rescale_and_mask(image1, [block['bbox'] for block in blocks1])
    image2_masked = rescale_and_mask(image2, [block['bbox'] for block in blocks2])
    inputs = processor(
        images=[image1_masked, image2_masked], return_tensors='pt', padding=True
    )
    inputs = {k: v.to(device) for k, v in inputs.items()}

    # Calculate features and similarity
    with torch.no_grad():
        image_features = model.get_image_features(**inputs)
        image_features1 = image_features[0].unsqueeze(0)
        image_features2 = image_features[1].unsqueeze(0)
        image_features1 /= image_features1.norm(dim=-1, keepdim=True)
        image_features2 /= image_features2.norm(dim=-1, keepdim=True)
        similarity = (image_features1 @ image_features2.T).item()

    return similarity


def rgb_to_hex(rgb):
    """Convert an RGB tuple to hexadecimal format."""
    return '{:02X}{:02X}{:02X}'.format(*rgb)


class ColorPool:
    def __init__(self, offset=0):
        color_values = list(range(10, 251, 16))
        color_list = [((r + offset) % 256, (g + offset) % 256, (b + offset) % 256) 
                     for r in color_values for g in color_values for b in color_values]
        self.color_pool = [rgb_to_hex(color) for color in color_list]

    def pop_color(self):
        if self.color_pool:
            return self.color_pool.pop()
        else:
            raise NotImplementedError


def process_html_str(html_str, offset=0):
    """Process HTML string to assign unique colors to text elements."""
    soup = BeautifulSoup(html_str, 'html.parser')

    def update_style(element, property_name, value):
        important_value = f"{value} !important"
        styles = element.attrs.get('style', '').split(';')
        updated_styles = [s for s in styles if not s.strip().startswith(property_name) and len(s.strip()) > 0]
        updated_styles.append(f"{property_name}: {important_value}")
        element['style'] = '; '.join(updated_styles).strip()

    # Set background color of all elements to transparent white
    for element in soup.find_all(True):
        update_style(element, 'background-color', 'rgba(255, 255, 255, 0.0)')

    color_pool = ColorPool(offset)
    text_tags = ['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'div', 'span', 'a', 'b', 'li', 
                 'table', 'td', 'th', 'button', 'footer', 'header', 'figcaption']

    for tag in soup.find_all(text_tags):
        color = f"#{color_pool.pop_color()}"
        update_style(tag, 'color', color)
        update_style(tag, 'opacity', '1.0')

    return str(soup)


def similar(n1, n2):
    """Check if two numbers are similar within a threshold."""
    return abs(n1 - n2) <= 8


def find_different_pixels(image1, image2):
    """Find pixels that differ between two images."""
    if image1.size != image2.size:
        logger.warning("Images are not the same size")
        return None

    image1 = image1.convert('RGB')
    image2 = image2.convert('RGB')
    pixels1 = image1.load()
    pixels2 = image2.load()
    different_pixels = []

    for x in range(image1.size[0]):
        for y in range(image1.size[1]):
            r1, g1, b1 = pixels1[x, y]
            r2, g2, b2 = pixels2[x, y]
            if similar((r1 + 50) % 256, r2) and similar((g1 + 50) % 256, g2) and similar((b1 + 50) % 256, b2):
                different_pixels.append((y, x))

    return np.stack(different_pixels) if different_pixels else None


def extract_text_with_color(html_str):
    """Extract text and color information from HTML string."""
    def get_color(tag):
        if 'style' in tag.attrs:
            styles = tag['style'].split(';')
            color_style = [s for s in styles if 'color' in s and 'background-color' not in s]
            if color_style:
                color = color_style[-1].split(':')[1].strip().replace(" !important", "")
                if color[0] == "#":
                    return color
                else:
                    try:
                        if color.startswith('rgb'):
                            color = tuple(map(int, color[4:-1].split(',')))
                        else:
                            color = ImageColor.getrgb(color)
                        return '#{:02x}{:02x}{:02x}'.format(*color)
                    except ValueError:
                        logger.warning(f"Unable to identify or convert color: {color}")
                        return None
        return None

    def extract_text_recursive(element, parent_color='#000000'):
        if isinstance(element, Comment):
            return None
        elif isinstance(element, NavigableString):
            text = element.strip()
            return (text, parent_color) if text else None
        elif isinstance(element, Tag):
            current_color = get_color(element) or parent_color
            children_texts = filter(None, [extract_text_recursive(child, current_color) 
                                        for child in element.children])
            return list(children_texts)

    soup = BeautifulSoup(html_str, 'html.parser')
    body = soup.body
    return extract_text_recursive(body) if body else []


def flatten_tree(tree):
    """Flatten a nested tree structure into a list."""
    flat_list = []
    def flatten(node):
        if isinstance(node, list):
            for item in node:
                flatten(item)
        else:
            flat_list.append(node)
    flatten(tree)
    return flat_list


def get_blocks_from_image_diff_pixels(image, html_text_color_tree, different_pixels):
    """Extract text blocks from image using color differences."""
    image_cv = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
    x_w = image_cv.shape[0]
    y_w = image_cv.shape[1]

    def hex_to_bgr(hex_color):
        hex_color = hex_color.lstrip('#')
        rgb = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        return rgb[::-1]

    def get_intersect(arr1, arr2):
        arr1_reshaped = arr1.view([('', arr1.dtype)] * arr1.shape[1])
        arr2_reshaped = arr2.view([('', arr2.dtype)] * arr2.shape[1])
        common_rows = np.intersect1d(arr1_reshaped, arr2_reshaped)
        return common_rows.view(arr1.dtype).reshape(-1, arr1.shape[1])

    blocks = []
    for item in html_text_color_tree:
        try:
            color = np.array(hex_to_bgr(item[1]), dtype="uint8")
        except:
            continue

        lower = color - 4
        upper = color + 4
        mask = cv2.inRange(image_cv, lower, upper)
        coords = np.column_stack(np.where(mask > 0))
        coords = get_intersect(coords, different_pixels)

        if coords.size == 0:
            continue

        x_min, y_min = np.min(coords, axis=0)
        x_max, y_max = np.max(coords, axis=0)
        
        # Get average color from original image
        color_coords = coords.copy()
        color_coords = color_coords[color_coords[:, 0] <= x_max]
        color_coords = color_coords[color_coords[:, 1] <= y_max]
        colors = [image_cv[x, y] for x, y in color_coords]
        avg_color = tuple(map(int, np.mean(colors, axis=0)))[::-1]  # Convert BGR to RGB

        blocks.append({
            'text': item[0].lower(),
            'bbox': (y_min / y_w, x_min / x_w, (y_max - y_min + 1) / y_w, (x_max - x_min + 1) / x_w),
            'color': avg_color
        })

    return blocks


def get_blocks_from_html(html_str, image1):
    """Extract text blocks from HTML and image."""
    # Process HTML with two different color offsets
    html_str_1 = process_html_str(html_str, offset=0)
    html_str_2 = process_html_str(html_str, offset=50)

    # Render both HTML versions to images
    # TODO: Screenshot html_str_2
    filter_color = (255, 0, 0)  
    image2 = Image.new("RGB", image1.size, filter_color)


    # Find pixels that differ between the two rendered images
    different_pixels = find_different_pixels(image1, image2)
    if different_pixels is None:
        logger.warning("Unable to get pixels with different colors")
        return []

    # Extract text and color information from HTML
    html_text_color_tree = flatten_tree(extract_text_with_color(html_str_1))
    try:
        blocks = get_blocks_from_image_diff_pixels(image1, html_text_color_tree, different_pixels)
    except Exception as e:
        logger.warning(f"Unable to get blocks: {e}")
        return []

    return blocks


def evaluate(task, generated_img):
    """Evaluate generated image against reference image using multiple metrics."""
    # Load reference image
    post_image = task['post_image']

    # Extract blocks from HTML and images
    post_blocks = get_blocks_from_html(task['post_html'], post_image)
    gen_blocks = get_blocks_from_html(task['gen_html'], generated_img)

    print("block details", post_blocks, gen_blocks)
    if not post_blocks or not gen_blocks:
        # Fallback to basic CLIP and pixel comparison if no blocks available
        clip_score = calculate_clip_similarity(post_image, generated_img, [], [])
        logger.info(f'CLIP similarity score: {clip_score}')

        # Pixel comparison
        diff = ImageChops.difference(generated_img, post_image)
        pixel_match = not diff.getbbox()
        logger.info(
            f"Pixel difference analysis: {'No difference' if pixel_match else 'Differences found'}"
        )

        return clip_score > 0.95 or pixel_match

    # Merge blocks with same bounding boxes
    post_blocks = merge_blocks_by_bbox(post_blocks)
    gen_blocks = merge_blocks_by_bbox(gen_blocks)

    # Find optimal block matching
    consecutive_bonus, window_size = 0.1, 1
    gen_blocks_m, post_blocks_m, matching = find_possible_merge(
        gen_blocks, deepcopy(post_blocks), consecutive_bonus, window_size
    )

    # Filter matches with low similarity
    filtered_matching = []
    for i, j in matching:
        text_similarity = calculate_similarity(gen_blocks_m[i], post_blocks_m[j])
        if text_similarity >= 0.5:
            filtered_matching.append([i, j, text_similarity])
    matching = filtered_matching

    if not matching:
        logger.warning('No matching blocks found')
        clip_score = calculate_clip_similarity(
            post_image, generated_img, gen_blocks, post_blocks
        )
        return clip_score > 0.95

    # Calculate metrics for matched blocks
    indices1 = [item[0] for item in matching]
    indices2 = [item[1] for item in matching]

    # Calculate unmatched areas
    unmatched_area_1 = sum(
        block['bbox'][2] * block['bbox'][3]
        for i, block in enumerate(gen_blocks_m)
        if i not in indices1
    )
    unmatched_area_2 = sum(
        block['bbox'][2] * block['bbox'][3]
        for j, block in enumerate(post_blocks_m)
        if j not in indices2
    )
    total_unmatched_area = unmatched_area_1 + unmatched_area_2

    # Calculate metrics for matched blocks
    matched_areas = []
    text_scores = []
    position_scores = []
    color_scores = []

    for i, j, text_similarity in matching:
        # Area
        block_area = (
            gen_blocks_m[i]['bbox'][2] * gen_blocks_m[i]['bbox'][3]
            + post_blocks_m[j]['bbox'][2] * post_blocks_m[j]['bbox'][3]
        )
        matched_areas.append(block_area)

        # Position similarity
        position_similarity = 1 - calculate_distance_max_1d(
            gen_blocks_m[i]['bbox'][0] + gen_blocks_m[i]['bbox'][2] / 2,
            gen_blocks_m[i]['bbox'][1] + gen_blocks_m[i]['bbox'][3] / 2,
            post_blocks_m[j]['bbox'][0] + post_blocks_m[j]['bbox'][2] / 2,
            post_blocks_m[j]['bbox'][1] + post_blocks_m[j]['bbox'][3] / 2,
        )

        # Color similarity
        color_similarity = color_similarity_ciede2000(
            gen_blocks_m[i]['color'], post_blocks_m[j]['color']
        )

        text_scores.append(text_similarity)
        position_scores.append(position_similarity)
        color_scores.append(color_similarity)

    # Calculate final scores
    total_area = sum(matched_areas) + total_unmatched_area
    size_score = sum(matched_areas) / total_area if total_area > 0 else 0
    text_score = np.mean(text_scores) if text_scores else 0
    position_score = np.mean(position_scores) if position_scores else 0
    color_score = np.mean(color_scores) if color_scores else 0
    clip_score = calculate_clip_similarity(
        post_image, generated_img, gen_blocks, post_blocks
    )

    # Combine scores with equal weights
    final_score = 0.2 * (
        size_score + text_score + position_score + color_score + clip_score
    )

    logger.info('Evaluation scores:')
    logger.info(f'- Size score: {size_score:.3f}')
    logger.info(f'- Text score: {text_score:.3f}')
    logger.info(f'- Position score: {position_score:.3f}')
    logger.info(f'- Color score: {color_score:.3f}')
    logger.info(f'- CLIP score: {clip_score:.3f}')
    logger.info(f'- Final score: {final_score:.3f}')

    return final_score > 0.8  # Consider it a match if final score > 80%


def png_to_bytes(png):
    buffer = BytesIO()
    png.save(buffer, format='PNG')
    image_bytes = buffer.getvalue()
    return image_bytes


def bytes_to_image(image_bytes):
    """Convert bytes to a Pillow Image object."""
    return Image.open(BytesIO(image_bytes))


if __name__ == '__main__':
    first_image = Image.open('./evaluation/visualcodebench/data/1/post.png')
    image = Image.open('./evaluation/visualcodebench/data/1/prev.png')
    
    
    html_file = open('./evaluation/visualcodebench/data/1/post/index.html', 'r')
    first_html = html_file.read()
    html_file.close()

    html_file = open('./evaluation/visualcodebench/data/1/prev/index.html', 'r')
    gen_html = html_file.read()
    html_file.close()



    sample = {'post_image': first_image, "post_html": first_html, "gen_html": gen_html}



    evaluate(sample, image)

