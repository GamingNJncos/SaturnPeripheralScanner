#!/usr/bin/env python3
"""
GNJ Saturn Peripheral Scanner
Scans Sega Saturn disc images (.iso, .bin) for peripheral compatibility codes.

The peripheral codes are located in the IP.BIN header at offset 0x50 (16 bytes).
This scanner extracts and reports all peripheral codes found in Saturn disc images.

Supported formats:
- ISO files (.iso) - 2048 bytes/sector
- BIN/CUE files (.bin) - 2352 bytes/sector (raw) or 2048 bytes/sector

Output Format:
Game_Title (0x60) | Version (0x2A) | Peripheral_Codes (0x50) | Supported Peripheral (Human Readable) | Source Filename

Author: GamingNJncos
#  ________             ____.
# /  _____/  ____      |    |
#/   \  ___ /    \     |    |
#\    \_\  \   |  \/\__|    |
# \______  /___|  /\________|
#        \/     \/           
"""


import os
import sys
import argparse
from pathlib import Path
from typing import Optional, Tuple, List
from datetime import datetime


# Known peripheral codes from official Sega documentation
PERIPHERAL_CODES = {
    'J': 'Control Pad',
    'A': 'Analog Controller',
    'E': '3D Controller',
    'M': 'Mouse',
    'K': 'Keyboard',
    'S': 'Steering Controller',
    'T': 'Multitap',
    'G': 'Virtua Gun',
    'W': 'RAM Cartridge',
    'C': 'Link Cable (JP)',
    'D': 'DirectLink (US)',
    'X': 'NetLink Modem',
    'Q': 'Pachinko Controller',
    'F': 'Floppy Drive',
    'R': 'ROM Cartridge',
    'P': 'Video CD Card',
}

# Saturn disc magic identifier
SATURN_MAGIC = b'SEGA SEGASATURN '

# Header offsets (from start of System ID at sector 0)
OFFSET_HARDWARE_ID = 0x00      # 16 bytes - "SEGA SEGASATURN "
OFFSET_MAKER_ID = 0x10         # 16 bytes
OFFSET_PRODUCT_NUM = 0x20      # 10 bytes
OFFSET_VERSION = 0x2A          # 6 bytes
OFFSET_RELEASE_DATE = 0x30     # 8 bytes
OFFSET_DEVICE_INFO = 0x38      # 8 bytes
OFFSET_AREA_CODES = 0x40       # 10 bytes (but often 16 used)
OFFSET_PERIPHERAL = 0x50       # 16 bytes
OFFSET_GAME_TITLE = 0x60       # 112 bytes

# Sector size for Mode 1 CD-ROM
SECTOR_SIZE_MODE1 = 2048
SECTOR_SIZE_RAW = 2352

# Raw sector header offset (sync + header = 16 bytes)
RAW_SECTOR_DATA_OFFSET = 16

# Column widths for aligned output
COL_TITLE = 50
COL_VERSION = 8
COL_PERIPH_CODES = 18
COL_PERIPH_DESC = 55
COL_FILENAME = 40


class ScanResult:
    """Represents the result of scanning a single file."""
    
    def __init__(self, filepath: str):
        self.filepath = filepath
        self.filename = os.path.basename(filepath)
        self.success = False
        self.skipped = False
        self.skip_reason = ""
        self.peripheral_raw = ""
        self.peripheral_codes = []
        self.game_title = ""
        self.version = ""
        self.product_number = ""
        self.area_codes = ""
        
    def get_human_readable_peripherals(self) -> str:
        """Return comma-separated human-readable peripheral descriptions."""
        descriptions = []
        for code in self.peripheral_codes:
            if code in PERIPHERAL_CODES:
                descriptions.append(PERIPHERAL_CODES[code])
            else:
                descriptions.append(f"Unknown({code})")
        return ", ".join(descriptions)


def read_sector_data(data: bytes, sector: int, raw_mode: bool = False) -> Optional[bytes]:
    """
    Read a single sector's user data from disc image data.
    """
    if raw_mode:
        offset = sector * SECTOR_SIZE_RAW + RAW_SECTOR_DATA_OFFSET
        if offset + SECTOR_SIZE_MODE1 > len(data):
            return None
        return data[offset:offset + SECTOR_SIZE_MODE1]
    else:
        offset = sector * SECTOR_SIZE_MODE1
        if offset + SECTOR_SIZE_MODE1 > len(data):
            return None
        return data[offset:offset + SECTOR_SIZE_MODE1]


def detect_raw_mode(data: bytes) -> bool:
    """
    Detect if the disc image is in raw (2352 bytes/sector) format.
    """
    if len(data) < 16:
        return False
    sync_pattern = bytes([0x00] + [0xFF] * 10 + [0x00])
    return data[:12] == sync_pattern


def find_saturn_header(data: bytes) -> Tuple[Optional[bytes], bool]:
    """
    Find and extract the Saturn System ID header from disc image data.
    """
    is_raw = detect_raw_mode(data)
    
    sector_data = read_sector_data(data, 0, is_raw)
    if sector_data and sector_data[:16] == SATURN_MAGIC:
        return sector_data[:256], is_raw
    
    for sector in range(16):
        sector_data = read_sector_data(data, sector, is_raw)
        if sector_data and sector_data[:16] == SATURN_MAGIC:
            return sector_data[:256], is_raw
    
    if is_raw:
        for sector in range(16):
            sector_data = read_sector_data(data, sector, False)
            if sector_data and sector_data[:16] == SATURN_MAGIC:
                return sector_data[:256], False
    
    return None, False


def extract_peripheral_codes(header: bytes) -> Tuple[str, List[str]]:
    """
    Extract peripheral codes from Saturn System ID header.
    """
    peripheral_bytes = header[OFFSET_PERIPHERAL:OFFSET_PERIPHERAL + 16]
    
    try:
        peripheral_raw = peripheral_bytes.decode('ascii', errors='replace')
    except:
        peripheral_raw = peripheral_bytes.hex()
    
    codes = []
    for char in peripheral_raw:
        if char != ' ' and char != '\x00' and char.isprintable():
            codes.append(char)
    
    return peripheral_raw, codes


def extract_game_info(header: bytes) -> Tuple[str, str, str, str]:
    """
    Extract additional game information from header.
    
    Returns:
        Tuple of (game_title, version, product_number, area_codes)
    """
    try:
        # Game title at 0x60, 112 bytes
        title_bytes = header[OFFSET_GAME_TITLE:OFFSET_GAME_TITLE + 112]
        game_title = title_bytes.decode('ascii', errors='replace').rstrip()
        
        # Version at 0x2A, 6 bytes
        version_bytes = header[OFFSET_VERSION:OFFSET_VERSION + 6]
        version = version_bytes.decode('ascii', errors='replace').rstrip()
        
        # Product number at 0x20, 10 bytes
        product_bytes = header[OFFSET_PRODUCT_NUM:OFFSET_PRODUCT_NUM + 10]
        product_number = product_bytes.decode('ascii', errors='replace').rstrip()
        
        # Area codes at 0x40, 16 bytes
        area_bytes = header[OFFSET_AREA_CODES:OFFSET_AREA_CODES + 16]
        area_codes = area_bytes.decode('ascii', errors='replace').rstrip()
        
        return game_title, version, product_number, area_codes
    except:
        return "", "", "", ""


def scan_file(filepath: str) -> ScanResult:
    """
    Scan a single file for Saturn peripheral codes.
    """
    result = ScanResult(filepath)
    
    ext = os.path.splitext(filepath)[1].lower()
    if ext not in ['.iso', '.bin']:
        result.skipped = True
        result.skip_reason = f"Unsupported file type: {ext}"
        return result
    
    if not os.path.isfile(filepath):
        result.skipped = True
        result.skip_reason = "File not found"
        return result
    
    file_size = os.path.getsize(filepath)
    if file_size < SECTOR_SIZE_MODE1:
        result.skipped = True
        result.skip_reason = "File too small to be valid Saturn image"
        return result
    
    try:
        read_size = min(file_size, 65536)
        with open(filepath, 'rb') as f:
            data = f.read(read_size)
        
        header, is_raw = find_saturn_header(data)
        
        if header is None:
            result.skipped = True
            result.skip_reason = "No Saturn header found"
            return result
        
        result.peripheral_raw, result.peripheral_codes = extract_peripheral_codes(header)
        result.game_title, result.version, result.product_number, result.area_codes = extract_game_info(header)
        
        result.success = True
        return result
        
    except PermissionError:
        result.skipped = True
        result.skip_reason = "Permission denied"
        return result
    except Exception as e:
        result.skipped = True
        result.skip_reason = f"Error: {str(e)}"
        return result


def scan_directory(directory: str, recursive: bool = True) -> List[ScanResult]:
    """
    Scan a directory for Saturn disc images.
    """
    results = []
    
    if recursive:
        for root, dirs, files in os.walk(directory):
            for filename in files:
                ext = os.path.splitext(filename)[1].lower()
                if ext in ['.iso', '.bin']:
                    filepath = os.path.join(root, filename)
                    results.append(scan_file(filepath))
    else:
        for filename in os.listdir(directory):
            ext = os.path.splitext(filename)[1].lower()
            if ext in ['.iso', '.bin']:
                filepath = os.path.join(directory, filename)
                results.append(scan_file(filepath))
    
    return results


def truncate_or_pad(text: str, width: int) -> str:
    """Truncate text with ellipsis if too long, or pad with spaces if too short."""
    if len(text) > width:
        return text[:width-3] + "..."
    return text.ljust(width)


def print_results(results: List[ScanResult], verbose: bool = False):
    """
    Print scan results to terminal with aligned columns.
    """
    print("\n" + "=" * 180)
    print(f"GNJ Saturn Peripheral Scanner v{__version__}")
    print("=" * 180)
    print(f"\nScanned: {len(results)} file(s)")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("\n" + "-" * 180)
    
    header = (
        f"{'Game_Title (0x60)':<{COL_TITLE}} | "
        f"{'Version':<{COL_VERSION}} | "
        f"{'Peripheral_Codes':<{COL_PERIPH_CODES}} | "
        f"{'Supported Peripherals':<{COL_PERIPH_DESC}} | "
        f"{'Source Filename'}"
    )
    print(header)
    print("-" * 180)
    
    successful = 0
    skipped = 0
    
    for result in results:
        if result.skipped:
            skipped += 1
            print(f"{truncate_or_pad('SKIPPED', COL_TITLE)} | "
                  f"{'':<{COL_VERSION}} | "
                  f"{'':<{COL_PERIPH_CODES}} | "
                  f"{truncate_or_pad(result.skip_reason, COL_PERIPH_DESC)} | "
                  f"{result.filename}")
        elif result.success:
            successful += 1
            title = truncate_or_pad(result.game_title, COL_TITLE)
            version = truncate_or_pad(result.version, COL_VERSION)
            codes_str = truncate_or_pad(result.peripheral_raw.rstrip(), COL_PERIPH_CODES)
            periph_desc = truncate_or_pad(result.get_human_readable_peripherals(), COL_PERIPH_DESC)
            
            print(f"{title} | {version} | {codes_str} | {periph_desc} | {result.filename}")
    
    print("-" * 180)
    print(f"Summary: {successful} successful, {skipped} skipped")
    print("=" * 180)


def write_results_to_file(results: List[ScanResult], output_path: str):
    """
    Write scan results to output file with aligned columns.
    
    Format: Game_Title (0x60) | Version (0x2A) | Peripheral_Codes (0x50) | Supported Peripheral | Source Filename
    """
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(f"# GNJ Saturn Peripheral Scanner v{__version__}\n")
        f.write(f"# Author: {__author__}\n")
        f.write(f"# Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"# Total files scanned: {len(results)}\n")
        f.write("#\n")
        f.write("# Peripheral Code Reference:\n")
        for code, desc in sorted(PERIPHERAL_CODES.items()):
            f.write(f"#   {code} = {desc}\n")
        f.write("#\n")
        f.write("# Format: Game_Title (0x60) | Version (0x2A) | Peripheral_Codes (0x50) | Supported Peripheral | Source Filename\n")
        f.write("#" + "=" * 179 + "\n\n")
        
        header = (
            f"{'Game_Title (0x60)':<{COL_TITLE}} | "
            f"{'Version':<{COL_VERSION}} | "
            f"{'Peripheral_Codes':<{COL_PERIPH_CODES}} | "
            f"{'Supported Peripherals':<{COL_PERIPH_DESC}} | "
            f"Source Filename"
        )
        f.write(header + "\n")
        f.write("-" * 180 + "\n")
        
        for result in results:
            if result.skipped:
                f.write(
                    f"{truncate_or_pad('SKIPPED', COL_TITLE)} | "
                    f"{'':<{COL_VERSION}} | "
                    f"{'':<{COL_PERIPH_CODES}} | "
                    f"{truncate_or_pad(result.skip_reason, COL_PERIPH_DESC)} | "
                    f"{result.filename}\n"
                )
            elif result.success:
                title = truncate_or_pad(result.game_title, COL_TITLE)
                version = truncate_or_pad(result.version, COL_VERSION)
                codes_str = truncate_or_pad(result.peripheral_raw.rstrip(), COL_PERIPH_CODES)
                periph_desc = truncate_or_pad(result.get_human_readable_peripherals(), COL_PERIPH_DESC)
                
                f.write(f"{title} | {version} | {codes_str} | {periph_desc} | {result.filename}\n")
            else:
                f.write(
                    f"{truncate_or_pad('ERROR', COL_TITLE)} | "
                    f"{'':<{COL_VERSION}} | "
                    f"{'':<{COL_PERIPH_CODES}} | "
                    f"{'Failed to read':<{COL_PERIPH_DESC}} | "
                    f"{result.filename}\n"
                )
    
    print(f"\nResults written to: {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description="GNJ Saturn Peripheral Scanner - Scan Sega Saturn disc images for peripheral codes",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Peripheral Code Reference:
  J = Control Pad                A = Analog Controller
  E = 3D Controller              M = Mouse
  K = Keyboard                   S = Steering Controller
  T = Multitap                   G = Virtua Gun
  W = RAM Cartridge              C = Link Cable (JP)
  D = DirectLink (US)            X = NetLink Modem
  Q = Pachinko Controller        F = Floppy Drive
  R = ROM Cartridge              P = Video CD Card

Output Format:
  Game_Title (0x60) | Version (0x2A) | Peripheral_Codes (0x50) | Supported Peripheral | Source Filename

Examples:
  %(prog)s game.iso
  %(prog)s game.bin
  %(prog)s /path/to/games/
        """
    )
    
    parser.add_argument('--version', action='version', 
                        version=f'%(prog)s v{__version__} ({__date__}) by {__author__}')
    parser.add_argument('path', nargs='+', help='File(s) or directory to scan')
    parser.add_argument('-r', '--recurse', action='store_true', default=True,
                        help='Recursively scan directories (default: True)')
    parser.add_argument('--no-recurse', action='store_true',
                        help='Do not recursively scan directories')
    parser.add_argument('-v', '--verbose', action='store_true',
                        help='Show verbose output')
    parser.add_argument('-o', '--output', default='GNJ_SaturnPeripheralScanner.txt',
                        help='Output filename (default: GNJ_SaturnPeripheralScanner.txt)')
    
    args = parser.parse_args()
    
    recursive = not args.no_recurse
    all_results = []
    
    for path in args.path:
        if os.path.isfile(path):
            all_results.append(scan_file(path))
        elif os.path.isdir(path):
            all_results.extend(scan_directory(path, recursive))
        else:
            result = ScanResult(path)
            result.skipped = True
            result.skip_reason = "Path does not exist"
            all_results.append(result)
    
    if not all_results:
        print("No files found to scan.")
        return
    
    print_results(all_results, args.verbose)
    
    output_path = os.path.join(os.getcwd(), args.output)
    write_results_to_file(all_results, output_path)


if __name__ == '__main__':
    main()
