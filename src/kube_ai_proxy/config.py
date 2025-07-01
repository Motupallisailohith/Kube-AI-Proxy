# src/kube_ai_proxy/config.py

"""Configuration settings for Kube AI Proxy MCP Server.

Environment variables:
  - K8S_MCP_TIMEOUT: custom timeout in seconds (default: 300)
  - K8S_MCP_MAX_OUTPUT: max output size in characters (default: 100000)
  - K8S_MCP_TRANSPORT: transport protocol ("stdio" or "sse", default: "stdio")
  - K8S_CONTEXT: Kubernetes context to use (default: current context)
  - K8S_NAMESPACE: Kubernetes namespace to use (default: "default")
  - K8S_MCP_SECURITY_MODE: security mode ("strict" or "permissive", default: "strict")
  - K8S_MCP_SECURITY_CONFIG: path to custom security rules YAML (default: None)

"""
import os
from pathlib import Path

# Command execution settings
DEFAULT_TIMEOUT = int(os.environ.get("K8S_MCP_TIMEOUT", "300"))
MAX_OUTPUT_SIZE = int(os.environ.get("K8S_MCP_MAX_OUTPUT", "100000"))

# MCP transport protocol: stdio or sse
MCP_TRANSPORT = os.environ.get("K8S_MCP_TRANSPORT", "stdio")

# Kubernetes context and namespace
K8S_CONTEXT = os.environ.get("K8S_CONTEXT", "")
K8S_NAMESPACE = os.environ.get("K8S_NAMESPACE", "default")

# Security settings
SECURITY_MODE = os.environ.get("K8S_MCP_SECURITY_MODE", "strict")
SECURITY_CONFIG_PATH = os.environ.get("K8S_MCP_SECURITY_CONFIG", None)

# Supported CLI tools with their check and help commands
SUPPORTED_CLI_TOOLS = {
    "kubectl": {
        "check_cmd": "kubectl version --client",
        "help_flag": "--help",
    },
    "helm": {
        "check_cmd": "helm version --short",
        "help_flag": "--help",
    },
    "istioctl": {
        "check_cmd": "istioctl version --remote=false",
        "help_flag": "--help",
    },
    "argocd": {
        "check_cmd": "argocd version --client",
        "help_flag": "--help",
    },
}

# Instructions shown to clients connecting to the MCP server
INSTRUCTIONS = """
Kube AI Proxy MCP Server — a simple interface to Kubernetes CLI tools.

Supported tools:
- kubectl: Kubernetes control
- helm: Helm chart manager
- istioctl: Istio service mesh CLI
- argocd: ArgoCD GitOps CLI

Use describe_<tool> to fetch help text.
Use execute_<tool> to run commands (supports pipes, timeouts, and RBAC checks).
"""

# Base directory for loading additional resources or templates
BASE_DIR = Path(__file__).parent.parent
