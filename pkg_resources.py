# Minimal shim for pkg_resources to satisfy Razorpay client

class DistributionNotFound(Exception):
    """Raised when a distribution cannot be found."""
    pass

def require(package_name):
    """Return a list with a single object having a .version attribute.
    Mimics the subset of ``pkg_resources.require`` used by razorpay.
    """
    try:
        # Use importlib.metadata (built-in in Python 3.8+)
        try:
            from importlib import metadata as importlib_metadata
        except ImportError:
            import importlib_metadata
        version = importlib_metadata.version(package_name)
        class _Dist:
            def __init__(self, version):
                self.version = version
        return [_Dist(version)]
    except Exception:
        raise DistributionNotFound(f"Distribution '{package_name}' not found")

__all__ = ["DistributionNotFound", "require"]
