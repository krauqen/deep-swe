# Benchmarks Targeting Full-Stack / SaaS Coding Agent Gaps

DeepSWE is mostly library, framework, CLI, SDK, parser, and infra-tool work. It does not strongly cover full SaaS application engineering with product UI, backend services, auth, database schemas, migrations, queues, deployment, or multi-component integration.

## Closest Matches

### SaaSBench

SaaSBench is the closest match to the missing category. It was introduced as a benchmark for enterprise SaaS engineering, explicitly targeting heterogeneous full-stack systems, multi-component orchestration, databases, frameworks, and long-horizon setup/integration complexity.

Paper: https://arxiv.org/abs/2605.17526

### SWE-WebDevBench

SWE-WebDevBench evaluates coding-agent application platforms as "virtual software agencies." It focuses on app creation and app modification requests across product, engineering, and ops dimensions, with higher tiers including multi-role SaaS and AI-native applications.

Paper: https://arxiv.org/abs/2605.04637

### App-Bench

App-Bench evaluates one-shot generation of full-stack web apps from natural-language prompts. Its tasks include real-time sync, multi-role logic, authentication flows, payments/media upload-style features, and domain apps such as finance, healthcare, legal, pharmacy, games, and rentals.

Website: https://appbench.ai/

### FullStack-Bench

FullStack-Bench appears in the FullStack-Agent paper. It evaluates generated websites across frontend, backend, and database functionality, specifically motivated by the problem that many agents produce polished frontends without real backend/data behavior.

Paper: https://arxiv.org/abs/2602.03798

## Caveat

These benchmarks are closer to full-stack SaaS than DeepSWE, but they are not all equivalent to "maintain an existing production SaaS codebase." Some focus on from-scratch app generation or platform evaluation rather than realistic ongoing maintenance in a mature repo with production infrastructure.
