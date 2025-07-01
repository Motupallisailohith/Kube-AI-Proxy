# Choose a slim Python base
FROM python:3.13-slim

RUN apt-get update \
 && apt-get install -y --no-install-recommends \
    curl \
    tar \
 && apt-get clean \
 && rm -rf /var/lib/apt/lists/*

# Install kubectl
ARG KUBECTL_VERSION=v1.33.0
RUN curl -LO "https://dl.k8s.io/release/${KUBECTL_VERSION}/bin/linux/amd64/kubectl" \
 && chmod +x kubectl \
 && mv kubectl /usr/local/bin/

# Install Helm
ARG HELM_VERSION=v3.17.3
RUN curl -LO "https://get.helm.sh/helm-${HELM_VERSION}-linux-amd64.tar.gz" \
 && tar -zxvf helm-${HELM_VERSION}-linux-amd64.tar.gz \
 && mv linux-amd64/helm /usr/local/bin/helm \
 && rm -rf linux-amd64 helm-${HELM_VERSION}-linux-amd64.tar.gz

ARG ISTIO_VERSION=1.25.2
RUN curl -L https://istio.io/downloadIstio | ISTIO_VERSION=${ISTIO_VERSION} TARGET_ARCH=amd64 sh - \
 && mv istio-*/bin/istioctl /usr/local/bin/ \
 && rm -rf istio-*

# Install ArgoCD
ARG ARGOCD_VERSION=v2.14.11
RUN curl -sSL -o argocd https://github.com/argoproj/argo-cd/releases/download/${ARGOCD_VERSION}/argocd-linux-amd64 \
 && chmod +x argocd \
 && mv argocd /usr/local/bin/




# Create an unprivileged user (similar to upstream)
RUN groupadd -g 10001 appgroup \
 && useradd -m -s /bin/bash -u 10001 -g appgroup appuser

# Set workdir and copy in your code
WORKDIR /app
COPY pyproject.toml README.md LICENSE ./
RUN pip install --no-cache-dir fastmcp mcp pydantic PyYAML
# Adjust permissions
RUN chown -R appuser:appgroup /app
COPY src/ ./src/
RUN pip install --no-cache-dir .

# Switch to non-root user
USER appuser

# Expose nothing by default – we're using stdio transport
# ENV K8S_MCP_TRANSPORT=stdio     # optional, your code already reads MCP_TRANSPORT

ENTRYPOINT ["python", "-m", "kube_ai_proxy.main"]
