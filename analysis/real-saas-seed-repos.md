# Real Open-Source SaaS/Product Repos For A SaaSBench-Style Benchmark

These are candidate seed repositories for building a benchmark that targets full-stack SaaS/product engineering rather than library or CLI work.

The strongest candidates are real product applications with workspaces/users/auth, database-backed workflows, background jobs, integrations, deployment docs, and business-domain logic.

## Strongest Product-App Candidates

| Repo | Stars fetched | Main language | Why it is a good SaaSBench substrate | Caveat |
| --- | ---: | --- | --- | --- |
| `twentyhq/twenty` | 48,662 | TypeScript | Open-source CRM with React, NestJS, PostgreSQL, Redis, BullMQ, GraphQL, workspaces, objects, workflows, and AI features. | Large monorepo; setup may be non-trivial. |
| `makeplane/plane` | 49,943 | TypeScript | Project-management product with workspaces, issues, cycles, docs, triage, deployments, and real collaboration workflows. | Big surface area; many tasks may require frontend/backend coordination. |
| `chatwoot/chatwoot` | 29,827 | Ruby | Customer-support SaaS with inboxes, agents, contacts, conversations, automations, omni-channel integrations, and self-hosting. | Rails stack may be heavier if the benchmark targets mostly TS/Python agents. |
| `dubinc/dub` | 23,628 | TypeScript | Modern link attribution platform with short links, conversions, affiliate programs, open-core structure, and data-heavy integrations. | Some enterprise features are commercial/open-core. |
| `documenso/documenso` | 13,130 | TypeScript | Document-signing SaaS with auth, PostgreSQL, Prisma, PDF workflows, recipients, signing, emails, templates, and audit-like flows. | Smaller than the top projects but very product-shaped. |
| `formbricks/formbricks` | 12,324 | TypeScript | Survey and user-feedback SaaS with targeting, responses, analytics, integrations, and self-hosting. | Narrower product domain. |
| `calcom/cal.diy` | 44,836 | TypeScript | Scheduling product with Next.js, tRPC, Prisma, Postgres, auth, booking flows, calendars, app-store-style integrations. | Current repo is community edition; enterprise/commercial code was removed. |
| `PostHog/posthog` | 34,770 | Python | Full product analytics suite with events, session replay, feature flags, experiments, surveys, data warehouse, and workflows. | Very large and infra-heavy; setup is expensive for quick evals. |
| `getlago/lago` | 9,736 | Go | Billing/metering SaaS domain with subscriptions, usage tracking, pricing, payment orchestration, and revenue analytics. | More billing infrastructure than end-user product app. |
| `maybe-finance/maybe` | 54,148 | Ruby | Personal-finance app with real product workflows and financial domain complexity. | May be less enterprise/multi-tenant than CRM/support/project-management repos. |

## Platform / Infrastructure SaaS Candidates

These are excellent real systems, but they are closer to BaaS, platform, internal-tool, automation, CMS, or infra products than conventional enterprise SaaS applications.

| Repo | Stars fetched | Main language | Fit |
| --- | ---: | --- | --- |
| `appwrite/appwrite` | 56,184 | TypeScript | Auth, databases, storage, functions, realtime, hosting; great for cloud-platform tasks. |
| `supabase/supabase` | 103,235 | TypeScript | Postgres development platform; strong infra/product hybrid. |
| `directus/directus` | 36,024 | TypeScript | Turns a DB into CMS/admin/API; good auth/permissions/data-model substrate. |
| `nocodb/nocodb` | 63,156 | TypeScript | Airtable alternative; good spreadsheet/database/workspace workflows. |
| `ToolJet/ToolJet` | 37,956 | JavaScript | Internal tools and app-generation platform. |
| `n8n-io/n8n` | 190,347 | TypeScript | Workflow automation platform with integrations and execution semantics. |
| `activepieces/activepieces` | 22,480 | TypeScript | AI/workflow automation platform with integrations. |
| `Infisical/infisical` | 27,124 | TypeScript | Secrets, certificates, and privileged access management. |
| `getsentry/sentry` | 43,999 | Python | Error tracking and performance monitoring platform. |
| `grafana/grafana` | 74,046 | TypeScript | Observability/data visualization platform. |
| `hasura/graphql-engine` | 31,975 | TypeScript | Realtime GraphQL APIs, permissions, webhooks, DB integration. |
| `strapi/strapi` | 72,279 | TypeScript | Headless CMS product with admin UI, auth, plugins, content models. |
| `payloadcms/payload` | 42,700 | TypeScript | Full-stack Next.js framework/CMS with backend/admin panel. |
| `medusajs/medusa` | 34,057 | TypeScript | Commerce platform with products, carts, orders, payments, fulfillment. |
| `saleor/saleor` | 22,940 | Python | Headless commerce API. |
| `odoo/odoo` | 51,745 | Python | Massive ERP/business-app suite. |
| `frappe/erpnext` | 35,124 | Python | ERP with accounting, inventory, HR, manufacturing, CRM, etc. |

## Suggested Benchmark Seed Set

For a first custom benchmark, use a small set that covers different SaaS domains without making setup impossible:

1. `twentyhq/twenty` - CRM / multi-tenant business app.
2. `makeplane/plane` - project management / collaboration.
3. `chatwoot/chatwoot` - customer support / omni-channel messaging.
4. `documenso/documenso` - document signing / workflow/audit.
5. `dubinc/dub` - marketing attribution / analytics links.
6. `getlago/lago` - billing / usage metering.
7. `formbricks/formbricks` - survey/feedback product.
8. `calcom/cal.diy` - scheduling / integrations.

This set gives a benchmark real product surfaces: accounts, workspaces, roles, DB-backed workflows, jobs, integrations, emails, analytics, billing, and operational setup.
