def valid_boundary(boundary: str) -> bool:
    """Return True if the boundary string is a valid RFC 2046 boundary.

    Django 2.2 expects the stdlib ``cgi`` module to provide ``valid_boundary``.
    In Python 3.13+ the module was removed, so we supply a minimal compatible
    implementation here. The logic mirrors Django's original implementation:
    a boundary must not be empty, must not consist solely of whitespace, and
    must not contain any control characters (ASCII < 32) or the space character.
    """
    if not boundary:
        return False
    # Disallow whitespace and control characters
    for ch in boundary:
        # Handle both str and bytes characters (Python 3.14 compatibility)
        ch_val = ord(ch) if isinstance(ch, str) else ch
        if ch_val <= 32:  # ASCII 32 is space, everything below is control char
            return False
    return True
