# src/kube_ai_proxy/mcp/__init__.py

import logging

# 1) FastMCP core
from fastmcp import FastMCP


from mcp.server.fastmcp import FastMCP, Context
from mcp.types import CallToolRequest


# 2) Project imports
from kube_ai_proxy.config import (
    INSTRUCTIONS,
    SUPPORTED_CLI_TOOLS,
    DEFAULT_TIMEOUT,
    K8S_CONTEXT,
    K8S_NAMESPACE,
)
from kube_ai_proxy.cli_executor import run_startup_checks
from kube_ai_proxy.prompts import register_prompts

# 3) Executor functions (plain async funcs, defined in their modules)
from kube_ai_proxy.executor.kubectl import describe_kubectl, execute_kubectl
from kube_ai_proxy.executor.helm    import describe_helm,    execute_helm
from kube_ai_proxy.executor.istioctl import describe_istioctl, execute_istioctl
from kube_ai_proxy.executor.argocd  import describe_argocd,  execute_argocd

# 4) (Optional) RBACChecker for middleware
from kube_ai_proxy.security.rbac_checker import RBACChecker

logger = logging.getLogger("kube-ai-proxy.mcp")

#
# 5) Run your startup checks synchronously and capture status map
#
cli_status = run_startup_checks(SUPPORTED_CLI_TOOLS)
logger.info(f"CLI tools installed status: {cli_status}")

#
# 6) Instantiate one global FastMCP server
#
mcp = FastMCP(
    name=INSTRUCTIONS.splitlines()[0],
    instructions=INSTRUCTIONS,
)

#
# 7) Middleware: inject defaults into each request’s Context.locals
#


#
# 10) Register prompt templates
#
register_prompts(mcp)

mcp.tool(description="Get kubectl help text")(    describe_kubectl)
mcp.tool(description="Execute kubectl commands")( execute_kubectl)
mcp.tool(description="Get Helm help text")(       describe_helm)
mcp.tool(description="Execute Helm commands")(    execute_helm)
mcp.tool(description="Get istioctl help text")(   describe_istioctl)
mcp.tool(description="Execute istioctl commands")(execute_istioctl)
mcp.tool(description="Get ArgoCD help text")(     describe_argocd)
mcp.tool(description="Execute ArgoCD commands")(  execute_argocd)
