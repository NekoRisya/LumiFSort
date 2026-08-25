def format_bytes(n: int) -> str:
    """
    Convert an integer number of bytes into a human-readable string,
    scaling to the closest binary unit (1024-based).

    Examples:
        format_bytes(0)          -> "0 B"
        format_bytes(512)        -> "512 B"
        format_bytes(1024)       -> "1 KB"
        format_bytes(1536)       -> "1.5 KB"
        format_bytes(1073741824) -> "1 GB"
    """
    if not isinstance(n, int):
        raise TypeError(f"expected int, got {type(n).__name__}")
    if n < 0:
        raise ValueError("size cannot be negative")

    units = ["B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB"]
    size = float(n)
    unit_index = 0

    while size >= 1024 and unit_index < len(units) - 1:
        size /= 1024
        unit_index += 1

    unit = units[unit_index]

    # No unit -> no decimals; otherwise trim trailing .0
    if unit_index == 0:
        return f"{int(size)} {unit}"

    rounded = round(size, 2)
    if rounded == int(rounded):
        return f"{int(rounded)} {unit}"
    return f"{rounded} {unit}"
