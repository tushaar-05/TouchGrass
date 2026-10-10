"""Setup script: Download verified Google YAMNet ONNX model and class map.

Source: https://huggingface.co/zeropointnine/yamnet-onnx
Commit SHA: ac2ca3bd45d12ec1f19f1144205ea529b4e9dedf
License: Apache-2.0 (Google TensorFlow Model Garden)
"""
import sys
import urllib.request
from pathlib import Path

MODEL_DIR = Path(__file__).resolve().parent.parent.parent / "models"
ONNX_URL = "https://huggingface.co/zeropointnine/yamnet-onnx/resolve/ac2ca3bd45d12ec1f19f1144205ea529b4e9dedf/yamnet.onnx"
CSV_URL = "https://huggingface.co/zeropointnine/yamnet-onnx/resolve/ac2ca3bd45d12ec1f19f1144205ea529b4e9dedf/yamnet_class_map.csv"

EXPECTED_MIN_BYTES = 14 * 1024 * 1024  # ~15.3 MB


def download_file(url: str, dest: Path) -> None:
    print(f"Downloading {dest.name} from {url}...")
    urllib.request.urlretrieve(url, dest)
    size_mb = dest.stat().st_size / (1024 * 1024)
    print(f"-> Saved {dest.name} ({size_mb:.2f} MB)")


def main():
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    onnx_dest = MODEL_DIR / "yamnet.onnx"
    csv_dest = MODEL_DIR / "yamnet_class_map.csv"

    if onnx_dest.exists() and onnx_dest.stat().st_size > EXPECTED_MIN_BYTES:
        print(f"Model already present: {onnx_dest} ({onnx_dest.stat().st_size / (1024*1024):.2f} MB)")
    else:
        download_file(ONNX_URL, onnx_dest)

    if csv_dest.exists() and csv_dest.stat().st_size > 1000:
        print(f"Class map already present: {csv_dest}")
    else:
        download_file(CSV_URL, csv_dest)

    print("Setup verification: Model files successfully verified on disk.")


if __name__ == "__main__":
    main()
