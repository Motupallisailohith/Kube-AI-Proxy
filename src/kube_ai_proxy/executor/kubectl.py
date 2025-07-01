# src/kube_ai_proxy/executor/kubectl.py

"""
Executor module for Kubernetes 'kubectl' commands.
Defines functions for describe_kubectl and execute_kubectl, then wires them
into your MCP server at import-time *after* mcp is fully initialized.
"""

import shlex
import asyncio
from asyncio.subprocess import PIPE

from kube_ai_proxy.config import (
    K8S_CONTEXT,
    K8S_NAMESPACE,
    SUPPORTED_CLI_TOOLS,
    DEFAULT_TIMEOUT,
)
from kube_ai_proxy.security.rbac_checker import RBACChecker
from kube_ai_proxy.tools import CommandResult, CommandHelpResult


async def describe_kubectl(
    command: str | None = None,
) -> CommandHelpResult:
    """
    Return kubectl help output for the given subcommand.
    """
    tool_cfg = SUPPORTED_CLI_TOOLS["kubectl"]
    help_flag = tool_cfg["help_flag"]

    cmd = ["kubectl"]
    if command:
        cmd.extend(shlex.split(command))
    cmd.append(help_flag)

    proc = await asyncio.create_subprocess_exec(*cmd, stdout=PIPE, stderr=PIPE)
    out, err = await proc.communicate()
    text = out.decode(errors="replace") or err.decode(errors="replace")

    return CommandHelpResult(help_text=text, status="success")


async def execute_kubectl(
    command: str,
    timeout: int | None = None,
) -> CommandResult:
    """
    Execute a kubectl command, enforcing RBAC policies before execution.
    """
    # RBAC check: parse verb and resource
    parts = shlex.split(command)
    if len(parts) > 1:
        verb = parts[1]
        resource = parts[2] if len(parts) > 2 else ""
        checker = RBACChecker(context=K8S_CONTEXT, namespace=K8S_NAMESPACE)
        allowed = await checker.can_i(verb, resource)
        if not allowed:
            return CommandResult(
                status="error",
                output=f"RBAC: permission denied for {verb} {resource}",
                exit_code=1,
            )

    # Execute the command
    exec_timeout = timeout or DEFAULT_TIMEOUT
    proc = await asyncio.create_subprocess_exec(
        *shlex.split(command), stdout=PIPE, stderr=PIPE
    )
    try:
        out, err = await asyncio.wait_for(proc.communicate(), exec_timeout)
        exit_code = proc.returncode if proc.returncode is not None else -1
        output = out.decode("utf-8", errors="replace") or err.decode("utf-8", errors="replace")
        status = "success" if exit_code == 0 else "error"

    except asyncio.TimeoutError:
        proc.kill()
        # Treat timeout as error with a distinct non-zero code
        return CommandResult(
            status="error",
            output=f"Command timed out after {exec_timeout}s",
            exit_code=-1,
        )


    return CommandResult(
        status=status,
        output=output,
        exit_code=exit_code,
    )


# ───────────────────────────────────────────────────────────────────────────────
# Now that your mcp server has been fully initialized (in mcp/__init__.py),
# import and register these functions as MCP tools.
# ───────────────────────────────────────────────────────────────────────────────

