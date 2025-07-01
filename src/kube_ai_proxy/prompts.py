# src/kube_ai_proxy/prompts.py

"""
Kubernetes CLI prompt definitions for the Kube AI Proxy MCP Server.

This module provides a collection of useful prompt templates for common Kubernetes,
Istio, Helm, and ArgoCD operations. These prompts help ensure consistent best practices
and efficient resource management when driving Kubernetes via AI.
"""

import logging

logger = logging.getLogger(__name__)


def register_prompts(mcp):
    """Register all prompt templates with the MCP server."""
    logger.info("Registering custom prompt templates")

    @mcp.prompt()
    def k8s_resource_status(resource_type: str, namespace: str = "default") -> str:
        """Generate kubectl commands to check the status of Kubernetes resources."""
        return f"""Generate kubectl commands to check the status of {resource_type}
in the {namespace} namespace.

Include commands to:
1. List all {resource_type} with basic information
2. Show detailed status and conditions
3. Check recent events related to these resources
4. Identify any issues or potential problems
5. Retrieve logs if applicable

Structure the commands so they're easily executed and parsed."""

    @mcp.prompt()
    def k8s_deploy_application(app_name: str, image: str, namespace: str = "default", replicas: int = 1) -> str:
        """Generate commands to deploy an application with kubectl and/or Helm."""
        return f"""Generate commands to deploy an application named '{app_name}'
using image '{image}' with {replicas} replicas in the {namespace} namespace.

Include commands to:
1. Create or apply a Deployment (kubectl apply or helm install)
2. Set appropriate resource requests and limits
3. Configure readiness and liveness probes
4. Apply labels and annotations
5. Verify rollout status
6. Test connectivity to the deployed application

Follow Kubernetes best practices for security and reliability."""

    @mcp.prompt()
    def k8s_troubleshoot(resource_type: str, resource_name: str, namespace: str = "default") -> str:
        """Generate troubleshooting commands for a specific Kubernetes resource."""
        return f"""Generate kubectl commands to troubleshoot the {resource_type}
named '{resource_name}' in the {namespace} namespace.

Include commands to:
1. Describe the resource and inspect its spec/status
2. View recent events related to this resource
3. Tail and grep logs for errors
4. Check related resources (e.g., pods for a Deployment)
5. Verify network policies and service endpoints
6. Suggest remediation steps based on common failure patterns"""

    @mcp.prompt()
    def k8s_resource_inventory(namespace: str = "") -> str:
        """Generate a comprehensive inventory of cluster resources."""
        scope = f"in the {namespace} namespace" if namespace else "across all namespaces"
        return f"""Generate kubectl commands to inventory Kubernetes resources {scope}.

Include commands to:
1. List all resource types and count by type
2. Show resource usage (CPU/memory) if available
3. Identify system components and critical namespaces
4. Highlight resources without labels or with misconfigurations
5. Export the inventory in JSON or YAML"""

    @mcp.prompt()
    def k8s_security_check(namespace: str = "") -> str:
        """Generate kubectl commands for security analysis."""
        scope = f"in the {namespace} namespace" if namespace else "across the entire cluster"
        return f"""Generate kubectl commands to perform a security assessment {scope}.

Include checks for:
1. Pods running as root or with privileged contexts
2. ServiceAccount and RBAC permissions
3. Exposed Secrets or ConfigMaps
4. NetworkPolicies and insecure ingress
5. Image vulnerability scanning (if possible)
6. Compliance with CIS Kubernetes benchmarks"""

    @mcp.prompt()
    def k8s_resource_scaling(resource_type: str, resource_name: str, namespace: str = "default") -> str:
        """Generate commands to scale a Kubernetes resource up or down."""
        return f"""Generate kubectl commands to scale the {resource_type}
named '{resource_name}' in the {namespace} namespace.

Include commands to:
1. Check current replica count and resource usage
2. Scale the resource manually
3. Configure HorizontalPodAutoscaler if needed
4. Monitor rollout progress
5. Roll back if scaling causes issues"""

    @mcp.prompt()
    def k8s_logs_analysis(pod_name: str, namespace: str = "default", container: str = "") -> str:
        """Generate commands to analyze logs from a pod (and container)."""
        container_clause = f" from container '{container}'" if container else ""
        return f"""Generate kubectl commands to analyze logs{container_clause}
of pod '{pod_name}' in the {namespace} namespace.

Include commands to:
1. Retrieve recent logs with timestamps
2. Filter logs for warnings and errors
3. Search for specific patterns
4. Follow logs in real time
5. Extract relevant segments for offline analysis"""

    @mcp.prompt()
    def istio_service_mesh(namespace: str = "default") -> str:
        """Generate istioctl commands to manage Istio service mesh."""
        return f"""Generate istioctl commands to manage the Istio service mesh
in the {namespace} namespace.

Include commands to:
1. Analyze mesh configuration for errors
2. Inspect traffic routing and VirtualServices
3. Check mTLS and security policies
4. Monitor mesh health and metrics
5. Debug common Istio issues"""

    @mcp.prompt()
    def helm_chart_management(release_name: str = "", namespace: str = "default") -> str:
        """Generate helm commands to manage chart releases."""
        target = f"for release '{release_name}'" if release_name else "for all releases"
        return f"""Generate helm commands to manage chart releases {target}
in the {namespace} namespace.

Include commands to:
1. List installed releases
2. Inspect release history and status
3. Install, upgrade, and rollback charts
4. Validate chart templates and values
5. Manage Helm repositories"""

    @mcp.prompt()
    def argocd_application(app_name: str = "", namespace: str = "argocd") -> str:
        """Generate argocd commands to manage ArgoCD applications."""
        target = f"for application '{app_name}'" if app_name else "for all applications"
        return f"""Generate argocd commands to manage GitOps deployments {target}
in the {namespace} namespace.

Include commands to:
1. List and get application details
2. Sync applications to Git
3. Roll back to previous revisions
4. Monitor sync and health status"""

    logger.info("Successfully registered custom prompt templates")
