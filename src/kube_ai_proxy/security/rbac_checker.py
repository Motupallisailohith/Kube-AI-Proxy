# src/kube_ai_proxy/security/rbac_checker.py

"""
RBACChecker: Enforces Role-Based Access Control by invoking Kubernetes 'auth can-i' and stubbing for other tools.
"""
import shlex
import asyncio
from asyncio.subprocess import PIPE

from kube_ai_proxy.config import K8S_CONTEXT, K8S_NAMESPACE


class RBACChecker:
    """
    Provides methods to check if a user can perform specific actions on resources.
    For Kubernetes, uses `kubectl auth can-i`. For other tools, extend as needed.
    """

    def __init__(self, context: str | None = None, namespace: str | None = None):
        self.context = context or K8S_CONTEXT
        self.namespace = namespace or K8S_NAMESPACE

    async def can_i(self, verb: str, resource: str) -> bool:
        """
        Check Kubernetes RBAC: `kubectl auth can-i <verb> <resource>`.
        """
        cmd = ["kubectl", "auth", "can-i", verb, resource]
        if self.context:
            cmd += ["--context", self.context]
        if self.namespace:
            cmd += ["--namespace", self.namespace]

        proc = await asyncio.create_subprocess_exec(*cmd, stdout=PIPE, stderr=PIPE)
        out, _ = await proc.communicate()
        result = out.decode().strip().lower()
        return result == "yes"

    async def can_i_helm(self, verb: str, release: str) -> bool:
        """
        Helm RBAC stub: always allow by default or implement Helm chart-specific checks.
        """
        # TODO: Implement real Helm RBAC if needed
        return True

    async def can_i_istio(self, verb: str, resource: str) -> bool:
        """
        Istio RBAC stub: always allow by default or integrate with Istio policies.
        """
        # TODO: Implement real Istio RBAC checks
        return True

    async def can_i_argocd(self, verb: str, app: str) -> bool:
        """
        ArgoCD RBAC stub: always allow by default or query ArgoCD API.
        """
        # TODO: Implement real ArgoCD RBAC checks
        return True
