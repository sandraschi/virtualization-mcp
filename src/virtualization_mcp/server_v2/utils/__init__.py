"""Utility functions for the virtualization-mcp server."""

import asyncio
import inspect
import logging
import os
import platform
import shutil
import subprocess
import sys
from collections.abc import Callable, Coroutine
from functools import wraps
from pathlib import Path
from typing import Any, Dict, List, Optional, TypeVar, Union

import psutil

logger = logging.getLogger(__name__)

T = TypeVar("T")

# Type aliases
PathLike = Union[str, Path]


def ensure_path(path: PathLike) -> Path:
    """Ensure the path is a Path object and convert if necessary."""
    return path if isinstance(path, Path) else Path(path)


def run_command(
    command: list[str],
    cwd: PathLike | None = None,
    env: dict[str, str] | None = None,
    check: bool = True,
    capture_output: bool = True,
    **kwargs,
) -> subprocess.CompletedProcess:
    """Run a command and return the result.

    Args:
        command: Command to run as a list of strings
        cwd: Working directory for the command
        env: Environment variables to use
        check: If True, raise CalledProcessError on non-zero exit code
        capture_output: If True, capture stdout and stderr
        **kwargs: Additional arguments to subprocess.run()

    Returns:
        subprocess.CompletedProcess: The result of the command

    Raises:
        subprocess.CalledProcessError: If check=True and the command fails
    """
    if cwd is not None:
        cwd = str(ensure_path(cwd))

    # Ensure command is a list of strings
    command = [str(arg) for arg in command]

    logger.debug(f"Running command: {' '.join(command)}")

    try:
        return subprocess.run(
            command,
            cwd=cwd,
            env=env or os.environ,
            check=check,
            capture_output=capture_output,
            text=True,
            **kwargs,
        )
    except subprocess.CalledProcessError as e:
        logger.error(f"Command failed with code {e.returncode}: {e.cmd}")
        if e.stdout:
            logger.debug(f"stdout: {e.stdout}")
        if e.stderr:
            logger.error(f"stderr: {e.stderr}")
        raise


def ensure_dir(path: PathLike) -> Path:
    """Ensure a directory exists, creating it if necessary."""
    path = ensure_path(path)
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_platform() -> str:
    """Get the current platform name."""
    system = platform.system().lower()
    if system == "windows":
        return "windows"
    elif system == "darwin":
        return "macos"
    elif system == "linux":
        return "linux"
    return "unknown"


def is_process_running(process_name: str) -> bool:
    """Check if a process is running by name."""
    return any(process_name.lower() in p.name().lower() for p in psutil.process_iter())


def async_retry(
    max_attempts: int = 3, delay: float = 1.0, exceptions: tuple = (Exception,)
) -> Callable:
    """Decorator for retrying async functions with exponential backoff.

    Args:
        max_attempts: Maximum number of attempts
        delay: Initial delay between attempts in seconds
        exceptions: Tuple of exceptions to catch and retry on

    Returns:
        Decorated async function with retry logic
    """

    def decorator(
        func: Callable[..., Coroutine[Any, Any, T]],
    ) -> Callable[..., Coroutine[Any, Any, T]]:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> T:
            last_exception = None
            current_delay = delay

            for attempt in range(1, max_attempts + 1):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt == max_attempts:
                        break

                    logger.warning(
                        f"Attempt {attempt} failed: {e}. Retrying in {current_delay:.1f}s..."
                    )
                    await asyncio.sleep(current_delay)
                    current_delay *= 2  # Exponential backoff

            # If we get here, all attempts failed
            raise last_exception  # type: ignore

        return wrapper

    return decorator


def get_caller_info(levels_up: int = 1) -> dict[str, Any]:
    """Get information about the calling function.

    Args:
        levels_up: Number of stack frames to go up (1 = caller of this function)

    Returns:
        Dictionary with information about the calling function
    """
    frame = inspect.currentframe()
    try:
        # Go up the specified number of frames
        for _ in range(levels_up + 1):
            if frame is None:
                break
            frame = frame.f_back

        if frame is None:
            return {"function": "<unknown>", "file": "<unknown>", "line": 0}

        return {
            "function": frame.f_code.co_name,
            "file": frame.f_code.co_filename,
            "line": frame.f_lineno,
        }
    finally:
        # Avoid reference cycles
        del frame


def format_size(size_bytes: int, binary: bool = True) -> str:
    """Format a size in bytes to a human-readable string.

    Args:
        size_bytes: Size in bytes
        binary: If True, use binary (1024) base, otherwise use decimal (1000)

    Returns:
        Formatted size string (e.g., "1.5 MB" or "1.4 MiB")
    """
    if binary:
        base = 1024
        suffixes = ["B", "KiB", "MiB", "GiB", "TiB", "PiB", "EiB", "ZiB", "YiB"]
    else:
        base = 1000
        suffixes = ["B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB"]

    if size_bytes == 0:
        return f"0 {suffixes[0]}"

    size = float(size_bytes)
    for suffix in suffixes[:-1]:
        if abs(size) < base:
            return f"{size:.1f} {suffix}"
        size /= base

    return f"{size:.1f} {suffixes[-1]}"
