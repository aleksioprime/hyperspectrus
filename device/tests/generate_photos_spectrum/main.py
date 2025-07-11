import argparse
import os
import cv2
import numpy as np
from datetime import datetime

SPECTRAL_PRESETS = {
    # "имя_спектра": (коэф_R, коэф_G, коэф_B)
    "450nm": (0.5, 0.7, 1.6),
    "550nm": (0.8, 1.5, 0.6),
    "650nm": (1.7, 0.7, 0.5)
}

def color_tint(img: np.ndarray, factor_r: float, factor_g: float, factor_b: float) -> np.ndarray:
    """Усиление определённых каналов для имитации спектра"""
    img_tint = img.astype(np.float32)
    img_tint[..., 0] *= factor_r
    img_tint[..., 1] *= factor_g
    img_tint[..., 2] *= factor_b
    img_tint = np.clip(img_tint, 0, 255).astype(np.uint8)
    return img_tint

def generate_spectral_images(
    input_file: str,
    output_root: str,
    spectra: dict = SPECTRAL_PRESETS
):
    """Генерирует цветные псевдоспектральные снимки"""
    img = cv2.imread(input_file)
    if img is None:
        raise FileNotFoundError(f"Не удалось открыть файл {input_file}")
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

    basename = os.path.splitext(os.path.basename(input_file))[0]
    dt_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = os.path.join(output_root, f"{basename}_{dt_str}")
    os.makedirs(output_dir, exist_ok=True)

    for name, (r, g, b) in spectra.items():
        img_out = color_tint(img, r, g, b)
        out_path = os.path.join(output_dir, f"spectrum_{name}.png")
        cv2.imwrite(out_path, cv2.cvtColor(img_out, cv2.COLOR_RGB2BGR))
        print(f"Сохранено: {out_path}")

def main():
    parser = argparse.ArgumentParser(
        description="Генерация набора цветных спектральных снимков из одного фото"
    )
    parser.add_argument("input", help="Путь к исходному изображению (jpg/png)")
    parser.add_argument("-o", "--output", default="spectral_outputs", help="Папка для сохранения")

    args = parser.parse_args()

    generate_spectral_images(args.input, args.output, SPECTRAL_PRESETS)

if __name__ == "__main__":
    main()

# python main.py ./photo_inputs/test.png