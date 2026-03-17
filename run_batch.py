"""CLI for batch processing without GUI."""

from __future__ import annotations

import argparse
from pathlib import Path

from src.io import list_images, match_pairs_by_lower
from src.pipeline import PipelineParams, process_batch
from src.spot_detection import SpotParams


def main() -> None:
    parser = argparse.ArgumentParser(description="TIRF liposome analysis (batch)")
    parser.add_argument("--mode", choices=["single", "dual"], default="single", help="Analysis mode")
    parser.add_argument("--input", type=Path, required=True, help="Input file or folder (single); or lower-channel folder (dual)")
    parser.add_argument("--input-upper", type=Path, default=None, help="Upper-channel folder (dual mode only)")
    parser.add_argument("--output", type=Path, required=True, help="Output folder")
    parser.add_argument("--diameter", type=int, default=7, help="Spot diameter (odd)")
    parser.add_argument("--minmass", type=float, default=0, help="Minimum integrated brightness")
    parser.add_argument("--separation", type=float, default=None, help="Min separation between spots")
    parser.add_argument("--sub-mask-radius", type=float, default=None, help="Dual: radius around each lower spot (px)")
    parser.add_argument("--preprocess-sigma", type=float, default=1.0, help="Gaussian preprocess sigma")
    args = parser.parse_args()

    args.output.mkdir(parents=True, exist_ok=True)
    spot_params = SpotParams(
        diameter=args.diameter,
        minmass=args.minmass,
        separation=args.separation,
    )
    params = PipelineParams(
        spot_params=spot_params,
        preprocess_sigma=args.preprocess_sigma,
        sub_mask_radius_pixels=args.sub_mask_radius,
    )

    if args.mode == "single":
        if args.input.is_file():
            paths = [(args.input, None)]
        else:
            paths = [(p, None) for p in list_images(args.input)]
    else:
        if args.input_upper is None:
            raise SystemExit("Dual mode requires --input-upper (folder or file)")
        if args.input.is_file() and args.input_upper.is_file():
            paths = [(args.input, args.input_upper)]
        else:
            pairs, missing = match_pairs_by_lower(args.input, args.input_upper)
            if missing:
                print(f"Warning: {len(missing)} lower images have no matching upper; they will be skipped.")
                for m in missing[:10]:
                    print(f"  missing upper for: {m.name}")
                if len(missing) > 10:
                    print("  ... more missing not shown")
            paths = pairs

    def progress(i: int, n: int, msg: str) -> None:
        print(f"[{i+1}/{n}] {msg}")

    process_batch(paths, args.output, params, args.mode, progress_callback=progress)
    print("Done.")


if __name__ == "__main__":
    main()
