# Repos To Study For A Custom SaaSBench

## Best Starting Points

### UniPat-AI/SaaS-Bench

URL: https://github.com/UniPat-AI/SaaS-Bench

This is the most practical starting point if the goal is a benchmark around real, locally deployable SaaS workflows. The repo includes `docker/`, `docs/`, `saas_bench/`, `scripts/`, `tasks/`, and documentation for adding tasks and verification protocols.

Use it for: task format, local SaaS deployment model, browser/GUI-agent workflows, reproducible verification.

### snowmountainAi/webdevbench

URL: https://github.com/snowmountainAi/webdevbench

This is the SWE-WebDevBench repo. It focuses on evaluating app-building platforms as virtual software agencies across product, engineering, and ops dimensions. It is useful for rubrics and evaluation structure, especially around business requirements, architecture, deployment, security, scalability, and reliability.

Use it for: evaluation dimensions, rubric design, app creation vs app modification split, SaaS/AI-native task framing.

### bytedance/web-bench

URL: https://github.com/bytedance/web-bench

This is a more mature runnable web-development benchmark with Docker-based quickstart. It contains 50 projects, each with 20 sequential tasks, designed to simulate real web development workflows.

Use it for: benchmark harness, project/task sequencing, Dockerized runner, reporting.

## Useful But Less Direct

### ShadeCloak/SaaSBench

URL: https://github.com/ShadeCloak/SaaSbench

This is the repo linked from the enterprise SaaSBench paper, but as of the checked snapshot it is mostly a placeholder with the code and dataset marked "Coming Soon."

Use it for: paper framing and taxonomy, not implementation yet.

### mnluzimu/FullStack-Agent

URL: https://github.com/mnluzimu/FullStack-Agent

This repo links FullStack-Dev, FullStack-Learn, and FullStack-Bench. It is useful if you care about generated full-stack sites and evaluation of frontend, backend, and database functionality.

Use it for: full-stack generation pipeline ideas, backend/database test breakdowns.

### bytedance/FullStackBench

URL: https://github.com/bytedance/FullStackBench

This is a broader multilingual full-stack programming benchmark with SandboxFusion support and Hugging Face dataset links. It is less SaaS-product-shaped than UniPat/SWE-WebDevBench, but good for sandbox/evaluation infrastructure.

Use it for: multilingual sandbox execution, model evaluation harness ideas.

### alt-research/vibe-coding-benchmark-public

URL: https://github.com/alt-research/vibe-coding-benchmark-public

This appears to be a public vibe-coding benchmark repo with tasks, templates, scripts, Docker Compose, and agent-specific configuration folders.

Use it for: prompt-to-app benchmark structure and agent/tool-specific setup patterns.
