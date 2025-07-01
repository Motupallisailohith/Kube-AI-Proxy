# src/kube_ai_proxy/executor/argocd.py

"""
Executor module for ArgoCD commands.
Defines describe_argocd and execute_argocd functions, decorated as MCP tools.
"""
import shlex
import asyncio
from asyncio.subprocess import PIPE
from mcp.server.fastmcp import Context

from kube_ai_proxy.config import SUPPORTED_CLI_TOOLS, DEFAULT_TIMEOUT

from kube_ai_proxy.security.rbac_checker import RBACChecker
from kube_ai_proxy.tools import CommandResult, CommandHelpResult



async def describe_argocd(
    command: str | None = None,
    ctx: Context | None = None,
) -> CommandHelpResult:
    """
    Return argocd help output for the given subcommand.
    """
    tool_cfg = SUPPORTED_CLI_TOOLS["argocd"]
    help_flag = tool_cfg["help_flag"]
    cmd = ["argocd"]
    if command:
        cmd.extend(shlex.split(command))
    cmd.append(help_flag)

    proc = await asyncio.create_subprocess_exec(*cmd, stdout=PIPE, stderr=PIPE)
    out, err = await proc.communicate()
    text = out.decode(errors="replace") or err.decode(errors="replace")

    return CommandHelpResult(help_text=text, status="success")



async def execute_argocd(
    command: str,
    timeout: int | None = None,
    ctx: Context | None = None,
) -> CommandResult:
    """
    Execute an argocd command, enforcing RBAC policies before execution.
    """
    parts = shlex.split(command)
    # RBAC check
    if len(parts) > 1:
        verb = parts[1]
        target = parts[2] if len(parts) > 2 else ""
        checker = RBACChecker()
        allowed = await checker.can_i_argocd(verb, target)
        if not allowed:
            return CommandResult(
                status="error",
                output=f"RBAC: permission denied for {verb} {target}",
                exit_code=1,
            )

    # Determine timeout
    exec_timeout = float(timeout or DEFAULT_TIMEOUT)

    # Launch process
    proc = await asyncio.create_subprocess_exec(
        *shlex.split(command), stdout=PIPE, stderr=PIPE
    )

    try:
        out, err = await asyncio.wait_for(proc.communicate(), exec_timeout)
        exit_code = proc.returncode if proc.returncode is not None else 0
        output = out.decode("utf-8", errors="replace") or err.decode("utf-8", "replace")
        status = "success" if exit_code == 0 else "error"
    except asyncio.TimeoutError:
        proc.kill()
        exit_code = -1
        output = f"Command timed out after {exec_timeout}s"
        status = "error"

    return CommandResult(
        status=status,
        output=output,
        exit_code=exit_code,
    )