# src/kube_ai_proxy/tools.py

"""
Core utilities and type definitions for Kube AI Proxy.
Includes command parsing, validation helpers, and result types.
"""

import shlex
from dataclasses import dataclass
from typing import Literal, NotRequired, TypedDict


# -------------------------------------------------------------------
# Allowed command lists
# -------------------------------------------------------------------

# List of allowed Unix commands that can be used in a pipe
ALLOWED_UNIX_COMMANDS = [
    # File operations
    "cat", "ls", "cd", "pwd", "cp", "mv", "rm", "mkdir", "touch", "chmod", "chown",
    # Text processing
    "grep", "sed", "awk", "cut", "sort", "uniq", "wc", "head", "tail", "tr", "find",
    # System information
    "ps", "top", "df", "du", "uname", "whoami", "date", "which", "echo",
    # Networking
    "ping", "ifconfig", "netstat", "curl", "wget", "dig", "nslookup", "ssh", "scp",
    # Other utilities
    "man", "less", "tar", "gzip", "gunzip", "zip", "unzip", "xargs", "jq", "yq", "tee", "column", "watch"
]

# List of allowed Kubernetes CLI tools
ALLOWED_K8S_TOOLS = [
    "kubectl",
    "istioctl",
    "helm",
    "argocd",
]


# -------------------------------------------------------------------
# TypedDicts for structured results
# -------------------------------------------------------------------

class ErrorDetailsNested(TypedDict, total=False):
    """Nested error details (e.g., command, exit_code, stderr)."""
    command: str
    exit_code: int
    stderr: str


class ErrorDetails(TypedDict, total=False):
    """Structured error information."""
    message: str
    code: str
    details: ErrorDetailsNested


class CommandResult(TypedDict):
    """
    Command execution result.

    - status: "success" or "error"
    - output: the stdout (or error text)
    - exit_code: optional integer exit code
    - execution_time: optional float seconds
    - error: optional ErrorDetails
    """
    status: Literal["success", "error"]
    output: str
    exit_code: NotRequired[int]
    execution_time: NotRequired[float]
    error: NotRequired[ErrorDetails]


@dataclass
class CommandHelpResult:
    """
    Result for help/documentation commands.

    - help_text: help output
    - status: "success" or "error"
    - error: optional ErrorDetails
    """
    help_text: str
    status: str = "success"
    error: ErrorDetails | None = None


# -------------------------------------------------------------------
# Validation helpers
# -------------------------------------------------------------------

def is_valid_k8s_tool(command: str) -> bool:
    """
    Check if a command starts with a supported Kubernetes CLI tool.
    """
    parts = shlex.split(command)
    if not parts:
        return False
    return parts[0] in ALLOWED_K8S_TOOLS


def validate_unix_command(command: str) -> bool:
    """
    Validate that the given command is an allowed Unix utility.
    """
    parts = shlex.split(command)
    if not parts:
        return False
    return parts[0] in ALLOWED_UNIX_COMMANDS


def is_pipe_command(command: str) -> bool:
    """
    Determine whether a command string contains a pipe ('|') outside quotes.
    """
    in_single = False
    in_double = False
    for i, ch in enumerate(command):
        if ch == "'" and (i == 0 or command[i-1] != "\\"):
            in_single = not in_single
        elif ch == '"' and (i == 0 or command[i-1] != "\\"):
            in_double = not in_double
        elif ch == "|" and not in_single and not in_double:
            return True
    return False


def split_pipe_command(pipe_command: str) -> list[str]:
    """
    Split a piped command string into its component commands.
    Respects quoted substrings so that '|' inside quotes is ignored.
    """
    if not pipe_command:
        return []
    commands: list[str] = []
    buf = ""
    in_single = False
    in_double = False

    for i, ch in enumerate(pipe_command):
        if ch == "'" and (i == 0 or pipe_command[i-1] != "\\"):
            in_single = not in_single
            buf += ch
        elif ch == '"' and (i == 0 or pipe_command[i-1] != "\\"):
            in_double = not in_double
            buf += ch
        elif ch == "|" and not in_single and not in_double:
            commands.append(buf.strip())
            buf = ""
        else:
            buf += ch

    if buf.strip():
        commands.append(buf.strip())

    return commands
