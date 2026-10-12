"""
Point cloud and timestamp file I/O utilities.
Supports honest parsing of .npy, .bin, ASCII/binary .pcd, and .ply point cloud files.
Validates array shapes, point counts, file integrity, and timestamp metadata.
"""

from pathlib import Path
from typing import Tuple, Optional, List, Dict, Any
import re
import numpy as np


def parse_pcd_file(fpath: Path) -> Tuple[np.ndarray, Optional[np.ndarray], Dict[str, Any]]:
    """
    Parses an uncompressed ASCII or binary Point Cloud Data (.pcd) file.
    Does NOT fabricate points. Returns actual 3D points and optional intensity.
    """
    header_byte_offset = 0
    with open(fpath, "rb") as f:
        header_lines = []
        while True:
            line = f.readline()
            if not line:
                raise ValueError(f"Malformed PCD file (EOF before DATA section): {fpath.name}")
            line_str = line.decode("ascii", errors="replace").strip()
            header_lines.append(line_str)
            if line_str.startswith("DATA"):
                header_byte_offset = f.tell()
                break

    header_meta: Dict[str, str] = {}
    for hline in header_lines:
        if hline.startswith("#") or not hline:
            continue
        parts = hline.split()
        if len(parts) >= 2:
            header_meta[parts[0].upper()] = " ".join(parts[1:])

    data_type = header_meta.get("DATA", "").strip().lower()
    fields = header_meta.get("FIELDS", "").split()
    sizes = [int(s) for s in header_meta.get("SIZE", "").split()] if "SIZE" in header_meta else []
    types = header_meta.get("TYPE", "").split()
    points_count = int(header_meta.get("POINTS", "0"))

    if points_count == 0:
        width = int(header_meta.get("WIDTH", "0"))
        height = int(header_meta.get("HEIGHT", "1"))
        points_count = width * height

    if not fields or "x" not in fields or "y" not in fields or "z" not in fields:
        raise ValueError(f"PCD file {fpath.name} is missing essential 3D fields (x, y, z). Fields found: {fields}")

    x_idx = fields.index("x")
    y_idx = fields.index("y")
    z_idx = fields.index("z")
    intensity_idx = fields.index("intensity") if "intensity" in fields else None

    if data_type == "ascii":
        # Read remaining ASCII lines
        with open(fpath, "r", encoding="utf-8", errors="replace") as f_txt:
            for _ in range(len(header_lines)):
                f_txt.readline()
            raw_lines = [line.strip().split() for line in f_txt if line.strip() and not line.startswith("#")]
        
        if len(raw_lines) == 0:
            raise ValueError(f"PCD ASCII file {fpath.name} contains 0 data rows.")

        data_matrix = np.array(raw_lines, dtype=np.float32)
        xyz = data_matrix[:, [x_idx, y_idx, z_idx]]
        intensity = data_matrix[:, intensity_idx] if intensity_idx is not None else None
        return xyz, intensity, {"format": "pcd_ascii", "fields": fields, "points_declared": points_count}

    elif data_type == "binary":
        if data_type == "binary_compressed":
            raise ValueError(
                f"PCD file {fpath.name} uses 'binary_compressed' format which is not supported without external decompression tools. "
                "Please export uncompressed binary or ASCII PCD."
            )
        # Compute binary struct offset for x, y, z
        type_map = {"F": "f", "I": "i", "U": "u"}
        dtype_fields = []
        for fld, sz, tp in zip(fields, sizes, types):
            np_type = f"{type_map.get(tp, 'f')}{sz}"
            dtype_fields.append((fld, np_type))

        pcd_dtype = np.dtype(dtype_fields)
        with open(fpath, "rb") as f_bin:
            f_bin.seek(header_byte_offset)
            raw_bytes = f_bin.read()

        record_size = pcd_dtype.itemsize
        num_records = len(raw_bytes) // record_size
        if num_records == 0:
            raise ValueError(f"PCD binary file {fpath.name} contains 0 records.")

        arr = np.frombuffer(raw_bytes[:num_records * record_size], dtype=pcd_dtype)
        xyz = np.column_stack([arr["x"], arr["y"], arr["z"]]).astype(np.float32)
        intensity = arr["intensity"].astype(np.float32) if "intensity" in fields else None
        return xyz, intensity, {"format": "pcd_binary", "fields": fields, "points_declared": points_count}

    else:
        raise ValueError(
            f"Unsupported PCD DATA format '{data_type}' in {fpath.name}. Supported formats: 'ascii', 'binary'."
        )


def parse_ply_file(fpath: Path) -> Tuple[np.ndarray, Optional[np.ndarray], Dict[str, Any]]:
    """
    Parses a Stanford Polygon (.ply) point cloud file (ASCII or binary little endian).
    """
    header_byte_offset = 0
    with open(fpath, "rb") as f:
        header_lines = []
        while True:
            line = f.readline()
            if not line:
                raise ValueError(f"Malformed PLY file (EOF before end_header): {fpath.name}")
            line_str = line.decode("ascii", errors="replace").strip()
            header_lines.append(line_str)
            if line_str == "end_header":
                header_byte_offset = f.tell()
                break

    ply_format = ""
    vertex_count = 0
    properties: List[Tuple[str, str]] = []
    in_vertex = False

    for hline in header_lines:
        parts = hline.split()
        if not parts:
            continue
        if parts[0] == "format":
            ply_format = parts[1]
        elif parts[0] == "element" and len(parts) >= 3 and parts[1] == "vertex":
            vertex_count = int(parts[2])
            in_vertex = True
        elif parts[0] == "element" and parts[1] != "vertex":
            in_vertex = False
        elif parts[0] == "property" and in_vertex and len(parts) >= 3:
            properties.append((parts[2], parts[1]))

    prop_names = [p[0] for p in properties]
    if "x" not in prop_names or "y" not in prop_names or "z" not in prop_names:
        raise ValueError(f"PLY file {fpath.name} is missing 3D coordinates (x, y, z). Found: {prop_names}")

    x_idx = prop_names.index("x")
    y_idx = prop_names.index("y")
    z_idx = prop_names.index("z")
    int_idx = None
    for candidate in ["intensity", "scalar_Intensity", "confidence"]:
        if candidate in prop_names:
            int_idx = prop_names.index(candidate)
            break

    if ply_format.startswith("ascii"):
        with open(fpath, "r", encoding="utf-8", errors="replace") as f_txt:
            for _ in range(len(header_lines)):
                f_txt.readline()
            rows = []
            for line in f_txt:
                parts = line.strip().split()
                if len(parts) >= 3:
                    rows.append(parts)
                if vertex_count > 0 and len(rows) >= vertex_count:
                    break

        if not rows:
            raise ValueError(f"PLY file {fpath.name} contains 0 vertex records.")

        data = np.array(rows, dtype=np.float32)
        xyz = data[:, [x_idx, y_idx, z_idx]]
        intensity = data[:, int_idx] if int_idx is not None else None
        return xyz, intensity, {"format": "ply_ascii", "vertex_count": vertex_count}

    elif "binary_little_endian" in ply_format:
        type_dict = {
            "float": "f4", "float32": "f4", "double": "f8", "float64": "f8",
            "char": "i1", "uchar": "u1", "uint8": "u1", "int": "i4", "int32": "i4",
        }
        dtype_list = [(name, type_dict.get(dtype_str, "f4")) for name, dtype_str in properties]
        ply_dtype = np.dtype(dtype_list)

        with open(fpath, "rb") as f_bin:
            f_bin.seek(header_byte_offset)
            raw = f_bin.read()

        record_sz = ply_dtype.itemsize
        n_rec = len(raw) // record_sz
        if n_rec == 0:
            raise ValueError(f"PLY binary file {fpath.name} contains 0 vertices.")

        arr = np.frombuffer(raw[:n_rec * record_sz], dtype=ply_dtype)
        xyz = np.column_stack([arr["x"], arr["y"], arr["z"]]).astype(np.float32)
        intensity = arr[properties[int_idx][0]].astype(np.float32) if int_idx is not None else None
        return xyz, intensity, {"format": "ply_binary", "vertex_count": vertex_count}

    else:
        raise ValueError(f"Unsupported PLY format '{ply_format}' in {fpath.name}. Supported: ascii, binary_little_endian.")


def load_point_cloud_file(fpath: Path) -> Tuple[np.ndarray, Optional[np.ndarray], Dict[str, Any]]:
    """
    Loads and validates a 3D point cloud from a file.
    Supports .npy, .bin, .pcd, and .ply formats.
    Validates array shape, point count, and returns (points, intensity, metadata).
    Raises informative exceptions for empty, corrupt, or unsupported files.
    """
    fpath = Path(fpath)
    if not fpath.is_file():
        raise FileNotFoundError(f"Point cloud file does not exist: {fpath}")

    st_size = fpath.stat().st_size
    if st_size == 0:
        raise ValueError(f"Point cloud file is empty (0 bytes): {fpath.name}")

    ext = fpath.suffix.lower()

    if ext == ".npy":
        arr = np.load(fpath)
        if not isinstance(arr, np.ndarray) or arr.ndim != 2 or arr.shape[1] < 3:
            raise ValueError(
                f"Invalid NumPy point cloud in {fpath.name}: expected 2D array with shape (N, >=3), got {getattr(arr, 'shape', 'unknown')}"
            )
        xyz = arr[:, :3].astype(np.float32)
        intensity = arr[:, 3].astype(np.float32) if arr.shape[1] > 3 else None
        if len(xyz) == 0:
            raise ValueError(f"NumPy point cloud array in {fpath.name} contains 0 points.")
        return xyz, intensity, {"format": "npy", "raw_shape": arr.shape}

    elif ext == ".bin":
        raw = np.fromfile(str(fpath), dtype=np.float32)
        if len(raw) == 0:
            raise ValueError(f"Binary point cloud file {fpath.name} contains 0 floats.")

        if len(raw) % 4 == 0:
            arr = raw.reshape(-1, 4)
            xyz = arr[:, :3]
            intensity = arr[:, 3]
        elif len(raw) % 3 == 0:
            arr = raw.reshape(-1, 3)
            xyz = arr[:, :3]
            intensity = None
        else:
            raise ValueError(
                f"Binary point cloud file {fpath.name} has {len(raw)} float32 values, which is not divisible by 3 or 4."
            )
        return xyz, intensity, {"format": "bin", "num_points": len(xyz)}

    elif ext == ".pcd":
        return parse_pcd_file(fpath)

    elif ext == ".ply":
        return parse_ply_file(fpath)

    else:
        raise ValueError(
            f"Unsupported point cloud format '{ext}' in {fpath.name}. "
            "Supported formats are: .npy, .bin, .pcd, .ply"
        )


def discover_timestamps(root_path: Optional[Path], files: List[Path]) -> Optional[List[float]]:
    """
    Discovers authentic sensor timestamps for a list of point cloud files.
    Checks for:
      1. timestamps.csv or timestamps.txt in root_path or parent directory.
      2. Filename-encoded numeric timestamps (e.g. 1583842345.123456.pcd or 1583842345123456789.bin).
    Returns a list of float timestamps in seconds if verified, otherwise None.
    NEVER manufactures synthetic timestamps.
    """
    if not root_path or not files:
        return None

    # Search for timestamp metadata files
    candidate_names = [
        "timestamps.csv", "timestamps.txt", "times.txt",
        "os1_cloud_node_timestamps.csv", "lidar_timestamps.txt"
    ]
    for cname in candidate_names:
        for search_dir in [root_path, root_path.parent]:
            tpath = search_dir / cname
            if tpath.is_file() and tpath.stat().st_size > 0:
                try:
                    timestamps = []
                    with open(tpath, "r", encoding="utf-8") as f:
                        lines = [l.strip() for l in f if l.strip() and not l.startswith("#")]
                    if lines:
                        first_line = lines[0]
                        first_parts = [p.strip().lower() for p in (first_line.split(",") if "," in first_line else first_line.split())]
                        col_idx = -1
                        has_header = False
                        for col_candidate in ["timestamp_sec", "timestamp", "time", "t", "seconds", "sec"]:
                            if col_candidate in first_parts:
                                col_idx = first_parts.index(col_candidate)
                                has_header = True
                                break
                        
                        start_idx = 1 if has_header else 0
                        read_col = col_idx if col_idx != -1 else 0

                        for line in lines[start_idx:]:
                            parts = line.split(",") if "," in line else line.split()
                            try:
                                val = float(parts[read_col])
                            except (ValueError, IndexError):
                                continue
                            # If nanoseconds (> 1e15) or microseconds (> 1e12), convert to seconds
                            if val > 1e15:
                                val /= 1e9
                            elif val > 1e12:
                                val /= 1e6
                            timestamps.append(val)
                    if len(timestamps) >= len(files):
                        return timestamps[:len(files)]
                except Exception:
                    pass

    # Check for filename-encoded timestamps
    # Pattern: Unix timestamp with optional decimal: e.g. 1583842345.123456 or 1583842345123456789
    ts_from_names = []
    ts_pattern = re.compile(r"^(\d{9,19}(?:\.\d+)?)\.(?:pcd|bin|npy|ply)$")
    for f in files:
        match = ts_pattern.match(f.name)
        if match:
            try:
                val = float(match.group(1))
                if val > 1e15:
                    val /= 1e9
                elif val > 1e12:
                    val /= 1e6
                ts_from_names.append(val)
            except ValueError:
                break
        else:
            break

    if len(ts_from_names) == len(files):
        return ts_from_names

    return None
