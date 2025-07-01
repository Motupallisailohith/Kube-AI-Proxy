# src/kube_ai_proxy/security/security.py

import logging
import re
import shlex
from dataclasses import dataclass, field
from pathlib import Path
import yaml

from kube_ai_proxy.config import SECURITY_CONFIG_PATH, SECURITY_MODE
from kube_ai_proxy.tools import (
    ALLOWED_K8S_TOOLS,
    is_pipe_command,
    split_pipe_command,
    validate_unix_command,
)

logger = logging.getLogger("kube_ai_proxy.security")

# Default dictionary of potentially dangerous commands for each CLI tool
DEFAULT_DANGEROUS_COMMANDS: dict[str, list[str]] = {
    "kubectl": [
        "kubectl delete",
        "kubectl drain",
        "kubectl replace --force",
        "kubectl exec",
        "kubectl port-forward",
        "kubectl cp",
        "kubectl delete pods --all",
    ],
    "istioctl": [
        "istioctl experimental",
        "istioctl proxy-config",
        "istioctl dashboard",
    ],
    "helm": [
        "helm delete",
        "helm uninstall",
        "helm rollback",
        "helm upgrade",
    ],
    "argocd": [
        "argocd app delete",
        "argocd cluster rm",
        "argocd repo rm",
        "argocd app set",
    ],
}

# Default safe patterns to override dangerous ones
DEFAULT_SAFE_PATTERNS: dict[str, list[str]] = {
    "kubectl": [
        "kubectl delete pod",
        "kubectl delete deployment",
        "kubectl delete service",
        "kubectl delete configmap",
        "kubectl delete secret",
        "kubectl exec --help",
        "kubectl exec -it",
        "kubectl exec pod",
        "kubectl exec deployment",
        "kubectl port-forward --help",
        "kubectl cp --help",
    ],
    "istioctl": [
        "istioctl experimental -h",
        "istioctl experimental --help",
        "istioctl proxy-config --help",
        "istioctl dashboard --help",
    ],
    "helm": [
        "helm delete --help",
        "helm uninstall --help",
        "helm rollback --help",
        "helm upgrade --help",
    ],
    "argocd": [
        "argocd app delete --help",
        "argocd cluster rm --help",
        "argocd repo rm --help",
        "argocd app set --help",
    ],
}


@dataclass
class ValidationRule:
    pattern: str
    description: str
    error_message: str
    regex: bool = False


@dataclass
class SecurityConfig:
    dangerous_commands: dict[str, list[str]]
    safe_patterns: dict[str, list[str]]
    regex_rules: dict[str, list[ValidationRule]] = field(default_factory=dict)

    def __post_init__(self):
        if self.regex_rules is None:
            self.regex_rules = {}


def load_security_config() -> SecurityConfig:
    """Load custom security config if provided, otherwise use defaults."""
    dangerous = DEFAULT_DANGEROUS_COMMANDS.copy()
    safe = DEFAULT_SAFE_PATTERNS.copy()
    regex_rules: dict[str, list[ValidationRule]] = {}

    if SECURITY_CONFIG_PATH:
        path = Path(SECURITY_CONFIG_PATH)
        if path.exists():
            try:
                data = yaml.safe_load(path.read_text())
                # override dangerous
                for tool, cmds in data.get("dangerous_commands", {}).items():
                    dangerous[tool] = cmds
                # override safe
                for tool, pats in data.get("safe_patterns", {}).items():
                    safe[tool] = pats
                # load regex_rules
                for tool, rules in data.get("regex_rules", {}).items():
                    regex_rules[tool] = [
                        ValidationRule(
                            pattern=r["pattern"],
                            description=r["description"],
                            error_message=r.get(
                                "error_message",
                                f"Command matches restricted pattern: {r['pattern']}"
                            ),
                            regex=True,
                        )
                        for r in rules
                    ]
                logger.info(f"Loaded security config from {path}")
            except Exception as e:
                logger.error(f"Error loading security_config.yaml: {e}")
                logger.warning("Falling back to defaults")

    return SecurityConfig(dangerous_commands=dangerous,
                          safe_patterns=safe,
                          regex_rules=regex_rules)


# Initialize once
SECURITY_CONFIG = load_security_config()


def is_safe_exec_command(command: str) -> bool:
    """Special handling for `kubectl exec` to avoid blind shells."""
    if not command.startswith("kubectl exec"):
        return True
    # allow help/version
    if " --help" in command or " -h " in command or " version" in command:
        return True

    interactive_flags = [" -i ", " --stdin ", " -t ", " --tty ", " -it ", " -ti "]
    has_int = any(f in command for f in interactive_flags)

    # detect raw shell patterns
    shell_patterns = [
        " -- sh", " -- bash", " -- /bin/sh", " -- /bin/bash", " -- zsh",
        " -- /usr/bin/bash", " -- ksh", " -- csh",
    ]
    for pat in shell_patterns:
        if pat in command + " ":
            # if using -c, allow
            if f"{pat} -c " in command:
                return True
            return has_int

    return True


def validate_k8s_command(command: str) -> None:
    """Validate a single kubectl/helm/istioctl/argocd command."""
    parts = shlex.split(command)
    if not parts or parts[0] not in ALLOWED_K8S_TOOLS:
        raise ValueError(f"Unsupported CLI tool: {parts[0] if parts else command}")

    # exec special case
    if parts[0] == "kubectl" and "exec" in parts:
        if not is_safe_exec_command(command):
            raise ValueError(
                "Unsafe kubectl exec usage: use explicit flags (-it or -c) or avoid raw shells."
            )

    # regex-based rules
    for rule in SECURITY_CONFIG.regex_rules.get(parts[0], []):
        if re.search(rule.pattern, command):
            raise ValueError(rule.error_message)

    # prefix-based dangerous check
    for bad in SECURITY_CONFIG.dangerous_commands.get(parts[0], []):
        if command.startswith(bad):
            # see if an allowed safe pattern matches
            for good in SECURITY_CONFIG.safe_patterns.get(parts[0], []):
                if command.startswith(good):
                    return
            raise ValueError(f"Command '{bad}' is restricted. Specify more precise resources.")


def validate_pipe_command(pipe_command: str) -> None:
    """
    Split on pipes and validate each stage:
     - first must be a K8s tool
     - the rest must be allowed Unix commands
    """
    cmds = split_pipe_command(pipe_command)
    if not cmds:
        raise ValueError("Empty piped command")

    # first command is kubectl/helm/…
    validate_k8s_command(cmds[0])

    # subsequent commands must be allowed Unix utilities
    for idx, c in enumerate(cmds[1:], start=1):
        parts = shlex.split(c)
        if not parts or not validate_unix_command(c):
            raise ValueError(f"Invalid pipe stage #{idx}: '{parts[0] if parts else c}'")


def reload_security_config() -> None:
    """Reload the YAML security config at runtime."""
    global SECURITY_CONFIG
    SECURITY_CONFIG = load_security_config()
    logger.info("Security configuration reloaded")


def validate_command(command: str) -> None:
    """
    Central entrypoint for validating ANY command string.
    Raises ValueError if it fails.
    """
    if SECURITY_MODE.lower() == "permissive":
        return
    if is_pipe_command(command):
        validate_pipe_command(command)
    else:
        validate_k8s_command(command)
