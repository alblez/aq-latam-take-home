-- Idempotent seed data for AI Interviewer Platform.
--
-- Contains: 6 jobs, 37 competencies, 111 question pack items.
-- Uses ON CONFLICT (id) DO UPDATE for safe reruns.
-- Stable UUIDs for dev reproducibility. No gen_random_uuid() calls.
--
-- Run via: just backend-seed
-- Order: jobs -> competencies -> question_pack_items (FK constraints)

-- ============================================================
-- JOBS (6 rows)
-- ============================================================

INSERT INTO jobs (id, title, description, sort_order)
VALUES (
  '10000001-0000-4000-8000-000000000001',
  'Frontend Engineer',
  'Builds performant, accessible user interfaces with modern component frameworks. Probes depth in rendering optimization, state architecture, design system integration, and cross-browser reliability.',
  0
)
ON CONFLICT (id) DO UPDATE SET
  title = EXCLUDED.title,
  description = EXCLUDED.description,
  sort_order = EXCLUDED.sort_order;

INSERT INTO jobs (id, title, description, sort_order)
VALUES (
  '10000001-0000-4000-8000-000000000002',
  'Backend Engineer',
  'Designs and operates server-side systems handling data persistence, API contracts, and service reliability. Probes depth in schema design, concurrency control, observability, and failure-mode thinking.',
  1
)
ON CONFLICT (id) DO UPDATE SET
  title = EXCLUDED.title,
  description = EXCLUDED.description,
  sort_order = EXCLUDED.sort_order;

INSERT INTO jobs (id, title, description, sort_order)
VALUES (
  '10000001-0000-4000-8000-000000000003',
  'Fullstack Engineer',
  'Delivers end-to-end features spanning browser and server, owning the full request lifecycle. Probes depth in integration patterns, deployment pipelines, pragmatic trade-offs, and cross-layer debugging.',
  2
)
ON CONFLICT (id) DO UPDATE SET
  title = EXCLUDED.title,
  description = EXCLUDED.description,
  sort_order = EXCLUDED.sort_order;

INSERT INTO jobs (id, title, description, sort_order)
VALUES (
  '10000001-0000-4000-8000-000000000004',
  'Staff Engineer',
  'Drives technical strategy across teams, sets architecture direction, and multiplies engineering effectiveness. Probes depth in decision-making under ambiguity, organizational influence, and long-term system evolution.',
  3
)
ON CONFLICT (id) DO UPDATE SET
  title = EXCLUDED.title,
  description = EXCLUDED.description,
  sort_order = EXCLUDED.sort_order;

INSERT INTO jobs (id, title, description, sort_order)
VALUES (
  '10000001-0000-4000-8000-000000000005',
  'ML Engineer',
  'Ships machine learning models into production with robust pipelines, monitoring, and iterative improvement cycles. Probes depth in model serving, data quality, experiment rigor, and production failure recovery.',
  4
)
ON CONFLICT (id) DO UPDATE SET
  title = EXCLUDED.title,
  description = EXCLUDED.description,
  sort_order = EXCLUDED.sort_order;

INSERT INTO jobs (id, title, description, sort_order)
VALUES (
  '10000001-0000-4000-8000-000000000006',
  'Platform Engineer',
  'Builds and maintains the infrastructure, tooling, and automation that engineering teams depend on daily. Probes depth in IaC practices, container orchestration, developer experience, and production reliability.',
  5
)
ON CONFLICT (id) DO UPDATE SET
  title = EXCLUDED.title,
  description = EXCLUDED.description,
  sort_order = EXCLUDED.sort_order;

-- ============================================================
-- COMPETENCIES (37 rows)
-- Frontend Engineer: 6 (4 technical, 2 behavioral)
-- ============================================================

INSERT INTO competencies (id, job_id, name, category, description, sort_order)
VALUES (
  '20000001-0000-4000-8000-000000000001',
  '10000001-0000-4000-8000-000000000001',
  'Component Architecture',
  'technical',
  'Ability to decompose UI into reusable, composable components with clear boundaries, prop contracts, and predictable rendering behavior.',
  0
)
ON CONFLICT (id) DO UPDATE SET
  job_id = EXCLUDED.job_id,
  name = EXCLUDED.name,
  category = EXCLUDED.category,
  description = EXCLUDED.description,
  sort_order = EXCLUDED.sort_order;

INSERT INTO competencies (id, job_id, name, category, description, sort_order)
VALUES (
  '20000001-0000-4000-8000-000000000002',
  '10000001-0000-4000-8000-000000000001',
  'Performance Optimization',
  'technical',
  'Skill in identifying and resolving rendering bottlenecks, bundle size issues, and runtime inefficiencies in browser applications.',
  1
)
ON CONFLICT (id) DO UPDATE SET
  job_id = EXCLUDED.job_id,
  name = EXCLUDED.name,
  category = EXCLUDED.category,
  description = EXCLUDED.description,
  sort_order = EXCLUDED.sort_order;

INSERT INTO competencies (id, job_id, name, category, description, sort_order)
VALUES (
  '20000001-0000-4000-8000-000000000003',
  '10000001-0000-4000-8000-000000000001',
  'State Management Patterns',
  'technical',
  'Understanding of when and how to apply local state, context, reducers, or external stores based on data scope and update frequency.',
  2
)
ON CONFLICT (id) DO UPDATE SET
  job_id = EXCLUDED.job_id,
  name = EXCLUDED.name,
  category = EXCLUDED.category,
  description = EXCLUDED.description,
  sort_order = EXCLUDED.sort_order;

INSERT INTO competencies (id, job_id, name, category, description, sort_order)
VALUES (
  '20000001-0000-4000-8000-000000000004',
  '10000001-0000-4000-8000-000000000001',
  'Accessibility and Inclusive Design',
  'technical',
  'Knowledge of WCAG standards, semantic markup, ARIA patterns, and keyboard navigation to ensure interfaces work for all users.',
  3
)
ON CONFLICT (id) DO UPDATE SET
  job_id = EXCLUDED.job_id,
  name = EXCLUDED.name,
  category = EXCLUDED.category,
  description = EXCLUDED.description,
  sort_order = EXCLUDED.sort_order;

INSERT INTO competencies (id, job_id, name, category, description, sort_order)
VALUES (
  '20000001-0000-4000-8000-000000000005',
  '10000001-0000-4000-8000-000000000001',
  'Cross-functional Collaboration',
  'behavioral',
  'Effectiveness in partnering with designers, product managers, and backend engineers to translate requirements into polished user experiences.',
  4
)
ON CONFLICT (id) DO UPDATE SET
  job_id = EXCLUDED.job_id,
  name = EXCLUDED.name,
  category = EXCLUDED.category,
  description = EXCLUDED.description,
  sort_order = EXCLUDED.sort_order;

INSERT INTO competencies (id, job_id, name, category, description, sort_order)
VALUES (
  '20000001-0000-4000-8000-000000000006',
  '10000001-0000-4000-8000-000000000001',
  'Technical Communication',
  'behavioral',
  'Ability to articulate technical decisions, trade-offs, and component design rationale to both technical and non-technical audiences.',
  5
)
ON CONFLICT (id) DO UPDATE SET
  job_id = EXCLUDED.job_id,
  name = EXCLUDED.name,
  category = EXCLUDED.category,
  description = EXCLUDED.description,
  sort_order = EXCLUDED.sort_order;

-- ============================================================
-- Backend Engineer: 5 (3 technical, 2 behavioral)
-- ============================================================

INSERT INTO competencies (id, job_id, name, category, description, sort_order)
VALUES (
  '20000001-0000-4000-8000-000000000007',
  '10000001-0000-4000-8000-000000000002',
  'API Design Patterns',
  'technical',
  'Skill in designing clear, evolvable HTTP interfaces with proper resource modeling, versioning strategy, and error semantics.',
  0
)
ON CONFLICT (id) DO UPDATE SET
  job_id = EXCLUDED.job_id,
  name = EXCLUDED.name,
  category = EXCLUDED.category,
  description = EXCLUDED.description,
  sort_order = EXCLUDED.sort_order;

INSERT INTO competencies (id, job_id, name, category, description, sort_order)
VALUES (
  '20000001-0000-4000-8000-000000000008',
  '10000001-0000-4000-8000-000000000002',
  'Database Modeling',
  'technical',
  'Ability to design normalized schemas, choose appropriate index strategies, and reason about query performance under production load.',
  1
)
ON CONFLICT (id) DO UPDATE SET
  job_id = EXCLUDED.job_id,
  name = EXCLUDED.name,
  category = EXCLUDED.category,
  description = EXCLUDED.description,
  sort_order = EXCLUDED.sort_order;

INSERT INTO competencies (id, job_id, name, category, description, sort_order)
VALUES (
  '20000001-0000-4000-8000-000000000009',
  '10000001-0000-4000-8000-000000000002',
  'Distributed Systems Thinking',
  'technical',
  'Understanding of consistency models, failure domains, retry strategies, and the trade-offs inherent in multi-service architectures.',
  2
)
ON CONFLICT (id) DO UPDATE SET
  job_id = EXCLUDED.job_id,
  name = EXCLUDED.name,
  category = EXCLUDED.category,
  description = EXCLUDED.description,
  sort_order = EXCLUDED.sort_order;

INSERT INTO competencies (id, job_id, name, category, description, sort_order)
VALUES (
  '20000001-0000-4000-8000-000000000010',
  '10000001-0000-4000-8000-000000000002',
  'Problem Decomposition',
  'behavioral',
  'Approach to breaking down ambiguous requirements into concrete implementation steps with clear milestones and validation points.',
  3
)
ON CONFLICT (id) DO UPDATE SET
  job_id = EXCLUDED.job_id,
  name = EXCLUDED.name,
  category = EXCLUDED.category,
  description = EXCLUDED.description,
  sort_order = EXCLUDED.sort_order;

INSERT INTO competencies (id, job_id, name, category, description, sort_order)
VALUES (
  '20000001-0000-4000-8000-000000000011',
  '10000001-0000-4000-8000-000000000002',
  'Operational Awareness',
  'behavioral',
  'Mindset of anticipating production failure modes, planning monitoring, and designing systems that surface problems before users notice.',
  4
)
ON CONFLICT (id) DO UPDATE SET
  job_id = EXCLUDED.job_id,
  name = EXCLUDED.name,
  category = EXCLUDED.category,
  description = EXCLUDED.description,
  sort_order = EXCLUDED.sort_order;

-- ============================================================
-- Fullstack Engineer: 7 (5 technical, 2 behavioral)
-- ============================================================

INSERT INTO competencies (id, job_id, name, category, description, sort_order)
VALUES (
  '20000001-0000-4000-8000-000000000012',
  '10000001-0000-4000-8000-000000000003',
  'End-to-End System Design',
  'technical',
  'Ability to architect features spanning client and server with coherent data flow, caching strategy, and failure boundaries.',
  0
)
ON CONFLICT (id) DO UPDATE SET
  job_id = EXCLUDED.job_id,
  name = EXCLUDED.name,
  category = EXCLUDED.category,
  description = EXCLUDED.description,
  sort_order = EXCLUDED.sort_order;

INSERT INTO competencies (id, job_id, name, category, description, sort_order)
VALUES (
  '20000001-0000-4000-8000-000000000013',
  '10000001-0000-4000-8000-000000000003',
  'Frontend-Backend Integration',
  'technical',
  'Skill in connecting UI components to API endpoints with proper loading states, error handling, and optimistic updates.',
  1
)
ON CONFLICT (id) DO UPDATE SET
  job_id = EXCLUDED.job_id,
  name = EXCLUDED.name,
  category = EXCLUDED.category,
  description = EXCLUDED.description,
  sort_order = EXCLUDED.sort_order;

INSERT INTO competencies (id, job_id, name, category, description, sort_order)
VALUES (
  '20000001-0000-4000-8000-000000000014',
  '10000001-0000-4000-8000-000000000003',
  'CI/CD and Deployment Strategy',
  'technical',
  'Understanding of build pipelines, deployment automation, rollback strategies, and environment management for continuous delivery.',
  2
)
ON CONFLICT (id) DO UPDATE SET
  job_id = EXCLUDED.job_id,
  name = EXCLUDED.name,
  category = EXCLUDED.category,
  description = EXCLUDED.description,
  sort_order = EXCLUDED.sort_order;

INSERT INTO competencies (id, job_id, name, category, description, sort_order)
VALUES (
  '20000001-0000-4000-8000-000000000015',
  '10000001-0000-4000-8000-000000000003',
  'Cross-Stack Debugging',
  'technical',
  'Skill in tracing issues across network boundaries, correlating frontend errors with backend logs, and isolating root causes efficiently.',
  3
)
ON CONFLICT (id) DO UPDATE SET
  job_id = EXCLUDED.job_id,
  name = EXCLUDED.name,
  category = EXCLUDED.category,
  description = EXCLUDED.description,
  sort_order = EXCLUDED.sort_order;

INSERT INTO competencies (id, job_id, name, category, description, sort_order)
VALUES (
  '20000001-0000-4000-8000-000000000016',
  '10000001-0000-4000-8000-000000000003',
  'Data Flow Architecture',
  'technical',
  'Ability to design how data moves between client cache, server state, and persistence layers with clear ownership and consistency guarantees.',
  4
)
ON CONFLICT (id) DO UPDATE SET
  job_id = EXCLUDED.job_id,
  name = EXCLUDED.name,
  category = EXCLUDED.category,
  description = EXCLUDED.description,
  sort_order = EXCLUDED.sort_order;

INSERT INTO competencies (id, job_id, name, category, description, sort_order)
VALUES (
  '20000001-0000-4000-8000-000000000017',
  '10000001-0000-4000-8000-000000000003',
  'Pragmatic Trade-off Decisions',
  'behavioral',
  'Judgment in choosing when to optimize, when to ship, and how to communicate scope decisions to stakeholders with clear reasoning.',
  5
)
ON CONFLICT (id) DO UPDATE SET
  job_id = EXCLUDED.job_id,
  name = EXCLUDED.name,
  category = EXCLUDED.category,
  description = EXCLUDED.description,
  sort_order = EXCLUDED.sort_order;

INSERT INTO competencies (id, job_id, name, category, description, sort_order)
VALUES (
  '20000001-0000-4000-8000-000000000018',
  '10000001-0000-4000-8000-000000000003',
  'Ownership and Delivery',
  'behavioral',
  'Track record of driving features from concept to production without requiring constant direction, handling ambiguity independently.',
  6
)
ON CONFLICT (id) DO UPDATE SET
  job_id = EXCLUDED.job_id,
  name = EXCLUDED.name,
  category = EXCLUDED.category,
  description = EXCLUDED.description,
  sort_order = EXCLUDED.sort_order;

-- ============================================================
-- Staff Engineer: 8 (3 technical, 5 behavioral)
-- ============================================================

INSERT INTO competencies (id, job_id, name, category, description, sort_order)
VALUES (
  '20000001-0000-4000-8000-000000000019',
  '10000001-0000-4000-8000-000000000004',
  'Technical Strategy and Vision',
  'behavioral',
  'Ability to define multi-quarter technical direction, align it with business goals, and communicate it in ways that teams can act on.',
  0
)
ON CONFLICT (id) DO UPDATE SET
  job_id = EXCLUDED.job_id,
  name = EXCLUDED.name,
  category = EXCLUDED.category,
  description = EXCLUDED.description,
  sort_order = EXCLUDED.sort_order;

INSERT INTO competencies (id, job_id, name, category, description, sort_order)
VALUES (
  '20000001-0000-4000-8000-000000000020',
  '10000001-0000-4000-8000-000000000004',
  'Architecture Decision-Making',
  'technical',
  'Skill in evaluating architectural options under uncertainty, documenting decisions with ADRs, and evolving systems without rewrites.',
  1
)
ON CONFLICT (id) DO UPDATE SET
  job_id = EXCLUDED.job_id,
  name = EXCLUDED.name,
  category = EXCLUDED.category,
  description = EXCLUDED.description,
  sort_order = EXCLUDED.sort_order;

INSERT INTO competencies (id, job_id, name, category, description, sort_order)
VALUES (
  '20000001-0000-4000-8000-000000000021',
  '10000001-0000-4000-8000-000000000004',
  'Cross-Team Influence',
  'behavioral',
  'Effectiveness in driving alignment across multiple teams without direct authority, using technical credibility and relationship building.',
  2
)
ON CONFLICT (id) DO UPDATE SET
  job_id = EXCLUDED.job_id,
  name = EXCLUDED.name,
  category = EXCLUDED.category,
  description = EXCLUDED.description,
  sort_order = EXCLUDED.sort_order;

INSERT INTO competencies (id, job_id, name, category, description, sort_order)
VALUES (
  '20000001-0000-4000-8000-000000000022',
  '10000001-0000-4000-8000-000000000004',
  'Mentorship and Growth',
  'behavioral',
  'Practice of developing other engineers through code review, pairing, design discussions, and creating learning opportunities within delivery work.',
  3
)
ON CONFLICT (id) DO UPDATE SET
  job_id = EXCLUDED.job_id,
  name = EXCLUDED.name,
  category = EXCLUDED.category,
  description = EXCLUDED.description,
  sort_order = EXCLUDED.sort_order;

INSERT INTO competencies (id, job_id, name, category, description, sort_order)
VALUES (
  '20000001-0000-4000-8000-000000000023',
  '10000001-0000-4000-8000-000000000004',
  'System Design at Scale',
  'technical',
  'Ability to design systems handling significant load with appropriate scaling strategies, data partitioning, and graceful degradation.',
  4
)
ON CONFLICT (id) DO UPDATE SET
  job_id = EXCLUDED.job_id,
  name = EXCLUDED.name,
  category = EXCLUDED.category,
  description = EXCLUDED.description,
  sort_order = EXCLUDED.sort_order;

INSERT INTO competencies (id, job_id, name, category, description, sort_order)
VALUES (
  '20000001-0000-4000-8000-000000000024',
  '10000001-0000-4000-8000-000000000004',
  'Risk Assessment and Mitigation',
  'behavioral',
  'Judgment in identifying technical risks early, quantifying their impact, and proposing proportional mitigation without over-engineering.',
  5
)
ON CONFLICT (id) DO UPDATE SET
  job_id = EXCLUDED.job_id,
  name = EXCLUDED.name,
  category = EXCLUDED.category,
  description = EXCLUDED.description,
  sort_order = EXCLUDED.sort_order;

INSERT INTO competencies (id, job_id, name, category, description, sort_order)
VALUES (
  '20000001-0000-4000-8000-000000000025',
  '10000001-0000-4000-8000-000000000004',
  'Code Quality Standards',
  'technical',
  'Skill in establishing and evolving code quality practices including review culture, testing strategy, and linting/formatting standards across teams.',
  6
)
ON CONFLICT (id) DO UPDATE SET
  job_id = EXCLUDED.job_id,
  name = EXCLUDED.name,
  category = EXCLUDED.category,
  description = EXCLUDED.description,
  sort_order = EXCLUDED.sort_order;

INSERT INTO competencies (id, job_id, name, category, description, sort_order)
VALUES (
  '20000001-0000-4000-8000-000000000026',
  '10000001-0000-4000-8000-000000000004',
  'Organizational Impact',
  'behavioral',
  'Track record of identifying and executing improvements that benefit the broader engineering organization beyond immediate team scope.',
  7
)
ON CONFLICT (id) DO UPDATE SET
  job_id = EXCLUDED.job_id,
  name = EXCLUDED.name,
  category = EXCLUDED.category,
  description = EXCLUDED.description,
  sort_order = EXCLUDED.sort_order;

-- ============================================================
-- ML Engineer: 5 (3 technical, 2 behavioral)
-- ============================================================

INSERT INTO competencies (id, job_id, name, category, description, sort_order)
VALUES (
  '20000001-0000-4000-8000-000000000027',
  '10000001-0000-4000-8000-000000000005',
  'Model Deployment and Serving',
  'technical',
  'Ability to package, deploy, and serve ML models in production with appropriate latency, throughput, and resource constraints.',
  0
)
ON CONFLICT (id) DO UPDATE SET
  job_id = EXCLUDED.job_id,
  name = EXCLUDED.name,
  category = EXCLUDED.category,
  description = EXCLUDED.description,
  sort_order = EXCLUDED.sort_order;

INSERT INTO competencies (id, job_id, name, category, description, sort_order)
VALUES (
  '20000001-0000-4000-8000-000000000028',
  '10000001-0000-4000-8000-000000000005',
  'Data Pipeline Design',
  'technical',
  'Skill in building reliable data ingestion, transformation, and validation pipelines that maintain quality guarantees at scale.',
  1
)
ON CONFLICT (id) DO UPDATE SET
  job_id = EXCLUDED.job_id,
  name = EXCLUDED.name,
  category = EXCLUDED.category,
  description = EXCLUDED.description,
  sort_order = EXCLUDED.sort_order;

INSERT INTO competencies (id, job_id, name, category, description, sort_order)
VALUES (
  '20000001-0000-4000-8000-000000000029',
  '10000001-0000-4000-8000-000000000005',
  'Experiment Design and Tracking',
  'technical',
  'Understanding of hypothesis formulation, A/B testing methodology, metric selection, and reproducible experiment infrastructure.',
  2
)
ON CONFLICT (id) DO UPDATE SET
  job_id = EXCLUDED.job_id,
  name = EXCLUDED.name,
  category = EXCLUDED.category,
  description = EXCLUDED.description,
  sort_order = EXCLUDED.sort_order;

INSERT INTO competencies (id, job_id, name, category, description, sort_order)
VALUES (
  '20000001-0000-4000-8000-000000000030',
  '10000001-0000-4000-8000-000000000005',
  'Stakeholder Communication',
  'behavioral',
  'Ability to translate model performance metrics and limitations into business terms that product and leadership teams can act on.',
  3
)
ON CONFLICT (id) DO UPDATE SET
  job_id = EXCLUDED.job_id,
  name = EXCLUDED.name,
  category = EXCLUDED.category,
  description = EXCLUDED.description,
  sort_order = EXCLUDED.sort_order;

INSERT INTO competencies (id, job_id, name, category, description, sort_order)
VALUES (
  '20000001-0000-4000-8000-000000000031',
  '10000001-0000-4000-8000-000000000005',
  'Production Reliability',
  'behavioral',
  'Mindset of building ML systems that degrade gracefully, monitoring model drift, and maintaining fallback paths when predictions fail.',
  4
)
ON CONFLICT (id) DO UPDATE SET
  job_id = EXCLUDED.job_id,
  name = EXCLUDED.name,
  category = EXCLUDED.category,
  description = EXCLUDED.description,
  sort_order = EXCLUDED.sort_order;

-- ============================================================
-- Platform Engineer: 6 (4 technical, 2 behavioral)
-- ============================================================

INSERT INTO competencies (id, job_id, name, category, description, sort_order)
VALUES (
  '20000001-0000-4000-8000-000000000032',
  '10000001-0000-4000-8000-000000000006',
  'Infrastructure as Code',
  'technical',
  'Skill in defining, versioning, and managing infrastructure through declarative configuration with drift detection and plan-apply workflows.',
  0
)
ON CONFLICT (id) DO UPDATE SET
  job_id = EXCLUDED.job_id,
  name = EXCLUDED.name,
  category = EXCLUDED.category,
  description = EXCLUDED.description,
  sort_order = EXCLUDED.sort_order;

INSERT INTO competencies (id, job_id, name, category, description, sort_order)
VALUES (
  '20000001-0000-4000-8000-000000000033',
  '10000001-0000-4000-8000-000000000006',
  'Container Orchestration',
  'technical',
  'Understanding of container lifecycle management, scheduling, networking, and resource allocation in orchestrated environments.',
  1
)
ON CONFLICT (id) DO UPDATE SET
  job_id = EXCLUDED.job_id,
  name = EXCLUDED.name,
  category = EXCLUDED.category,
  description = EXCLUDED.description,
  sort_order = EXCLUDED.sort_order;

INSERT INTO competencies (id, job_id, name, category, description, sort_order)
VALUES (
  '20000001-0000-4000-8000-000000000034',
  '10000001-0000-4000-8000-000000000006',
  'Developer Experience Design',
  'technical',
  'Ability to build internal tooling, documentation, and self-service platforms that reduce friction for product engineering teams.',
  2
)
ON CONFLICT (id) DO UPDATE SET
  job_id = EXCLUDED.job_id,
  name = EXCLUDED.name,
  category = EXCLUDED.category,
  description = EXCLUDED.description,
  sort_order = EXCLUDED.sort_order;

INSERT INTO competencies (id, job_id, name, category, description, sort_order)
VALUES (
  '20000001-0000-4000-8000-000000000035',
  '10000001-0000-4000-8000-000000000006',
  'Observability and Monitoring',
  'technical',
  'Skill in designing logging, metrics, tracing, and alerting systems that give operators actionable signals during incidents.',
  3
)
ON CONFLICT (id) DO UPDATE SET
  job_id = EXCLUDED.job_id,
  name = EXCLUDED.name,
  category = EXCLUDED.category,
  description = EXCLUDED.description,
  sort_order = EXCLUDED.sort_order;

INSERT INTO competencies (id, job_id, name, category, description, sort_order)
VALUES (
  '20000001-0000-4000-8000-000000000036',
  '10000001-0000-4000-8000-000000000006',
  'Incident Response and Reliability',
  'behavioral',
  'Practice of structured incident management including triage, communication, mitigation, and blameless post-mortems that drive systemic improvement.',
  4
)
ON CONFLICT (id) DO UPDATE SET
  job_id = EXCLUDED.job_id,
  name = EXCLUDED.name,
  category = EXCLUDED.category,
  description = EXCLUDED.description,
  sort_order = EXCLUDED.sort_order;

INSERT INTO competencies (id, job_id, name, category, description, sort_order)
VALUES (
  '20000001-0000-4000-8000-000000000037',
  '10000001-0000-4000-8000-000000000006',
  'Security-First Thinking',
  'behavioral',
  'Mindset of integrating security considerations into infrastructure decisions from the start rather than treating them as an afterthought.',
  5
)
ON CONFLICT (id) DO UPDATE SET
  job_id = EXCLUDED.job_id,
  name = EXCLUDED.name,
  category = EXCLUDED.category,
  description = EXCLUDED.description,
  sort_order = EXCLUDED.sort_order;

-- ============================================================
-- QUESTION PACK ITEMS (111 rows, 3 per competency)
-- Frontend Engineer competencies
-- ============================================================

-- Component Architecture (technical)
INSERT INTO question_pack_items (id, competency_id, prompt_text, sort_order)
VALUES (
  '30000001-0000-4000-8000-000000000001',
  '20000001-0000-4000-8000-000000000001',
  'Walk me through how you would decompose a complex page layout into a component tree, explaining your decisions about component boundaries and data flow.',
  0
)
ON CONFLICT (id) DO UPDATE SET
  competency_id = EXCLUDED.competency_id,
  prompt_text = EXCLUDED.prompt_text,
  sort_order = EXCLUDED.sort_order;

INSERT INTO question_pack_items (id, competency_id, prompt_text, sort_order)
VALUES (
  '30000001-0000-4000-8000-000000000002',
  '20000001-0000-4000-8000-000000000001',
  'Describe a time you inherited a component with unclear responsibilities. How did you identify the boundaries and refactor it?',
  1
)
ON CONFLICT (id) DO UPDATE SET
  competency_id = EXCLUDED.competency_id,
  prompt_text = EXCLUDED.prompt_text,
  sort_order = EXCLUDED.sort_order;

INSERT INTO question_pack_items (id, competency_id, prompt_text, sort_order)
VALUES (
  '30000001-0000-4000-8000-000000000003',
  '20000001-0000-4000-8000-000000000001',
  'How would you design a component API that needs to support both simple and advanced use cases without becoming unwieldy?',
  2
)
ON CONFLICT (id) DO UPDATE SET
  competency_id = EXCLUDED.competency_id,
  prompt_text = EXCLUDED.prompt_text,
  sort_order = EXCLUDED.sort_order;

-- Performance Optimization (technical)
INSERT INTO question_pack_items (id, competency_id, prompt_text, sort_order)
VALUES (
  '30000001-0000-4000-8000-000000000004',
  '20000001-0000-4000-8000-000000000002',
  'Walk me through your process for diagnosing a slow-rendering page. What tools do you reach for first and what patterns do you look for?',
  0
)
ON CONFLICT (id) DO UPDATE SET
  competency_id = EXCLUDED.competency_id,
  prompt_text = EXCLUDED.prompt_text,
  sort_order = EXCLUDED.sort_order;

INSERT INTO question_pack_items (id, competency_id, prompt_text, sort_order)
VALUES (
  '30000001-0000-4000-8000-000000000005',
  '20000001-0000-4000-8000-000000000002',
  'Tell me about a time you significantly reduced bundle size or improved load time. What was the bottleneck and what trade-offs did you accept?',
  1
)
ON CONFLICT (id) DO UPDATE SET
  competency_id = EXCLUDED.competency_id,
  prompt_text = EXCLUDED.prompt_text,
  sort_order = EXCLUDED.sort_order;

INSERT INTO question_pack_items (id, competency_id, prompt_text, sort_order)
VALUES (
  '30000001-0000-4000-8000-000000000006',
  '20000001-0000-4000-8000-000000000002',
  'How do you decide between memoization, virtualization, and lazy loading when optimizing a list-heavy interface?',
  2
)
ON CONFLICT (id) DO UPDATE SET
  competency_id = EXCLUDED.competency_id,
  prompt_text = EXCLUDED.prompt_text,
  sort_order = EXCLUDED.sort_order;

-- State Management Patterns (technical)
INSERT INTO question_pack_items (id, competency_id, prompt_text, sort_order)
VALUES (
  '30000001-0000-4000-8000-000000000007',
  '20000001-0000-4000-8000-000000000003',
  'Describe how you decide whether a piece of state belongs in a component, a context provider, or an external store.',
  0
)
ON CONFLICT (id) DO UPDATE SET
  competency_id = EXCLUDED.competency_id,
  prompt_text = EXCLUDED.prompt_text,
  sort_order = EXCLUDED.sort_order;

INSERT INTO question_pack_items (id, competency_id, prompt_text, sort_order)
VALUES (
  '30000001-0000-4000-8000-000000000008',
  '20000001-0000-4000-8000-000000000003',
  'Walk me through a situation where state synchronization between components became complex. How did you simplify it?',
  1
)
ON CONFLICT (id) DO UPDATE SET
  competency_id = EXCLUDED.competency_id,
  prompt_text = EXCLUDED.prompt_text,
  sort_order = EXCLUDED.sort_order;

INSERT INTO question_pack_items (id, competency_id, prompt_text, sort_order)
VALUES (
  '30000001-0000-4000-8000-000000000009',
  '20000001-0000-4000-8000-000000000003',
  'How would you approach managing server state versus client state in an application with frequent real-time updates?',
  2
)
ON CONFLICT (id) DO UPDATE SET
  competency_id = EXCLUDED.competency_id,
  prompt_text = EXCLUDED.prompt_text,
  sort_order = EXCLUDED.sort_order;

-- Accessibility and Inclusive Design (technical)
INSERT INTO question_pack_items (id, competency_id, prompt_text, sort_order)
VALUES (
  '30000001-0000-4000-8000-000000000010',
  '20000001-0000-4000-8000-000000000004',
  'Walk me through how you would audit an existing form component for accessibility issues and prioritize the fixes.',
  0
)
ON CONFLICT (id) DO UPDATE SET
  competency_id = EXCLUDED.competency_id,
  prompt_text = EXCLUDED.prompt_text,
  sort_order = EXCLUDED.sort_order;

INSERT INTO question_pack_items (id, competency_id, prompt_text, sort_order)
VALUES (
  '30000001-0000-4000-8000-000000000011',
  '20000001-0000-4000-8000-000000000004',
  'Describe a situation where you had to balance visual design requirements with accessibility standards. What was your approach?',
  1
)
ON CONFLICT (id) DO UPDATE SET
  competency_id = EXCLUDED.competency_id,
  prompt_text = EXCLUDED.prompt_text,
  sort_order = EXCLUDED.sort_order;

INSERT INTO question_pack_items (id, competency_id, prompt_text, sort_order)
VALUES (
  '30000001-0000-4000-8000-000000000012',
  '20000001-0000-4000-8000-000000000004',
  'How do you ensure keyboard navigation works correctly in a complex interactive widget like a data grid or drag-and-drop interface?',
  2
)
ON CONFLICT (id) DO UPDATE SET
  competency_id = EXCLUDED.competency_id,
  prompt_text = EXCLUDED.prompt_text,
  sort_order = EXCLUDED.sort_order;

-- Cross-functional Collaboration (behavioral)
INSERT INTO question_pack_items (id, competency_id, prompt_text, sort_order)
VALUES (
  '30000001-0000-4000-8000-000000000013',
  '20000001-0000-4000-8000-000000000005',
  'Tell me about a time you disagreed with a designer about an interaction pattern. How did you reach a resolution that served users?',
  0
)
ON CONFLICT (id) DO UPDATE SET
  competency_id = EXCLUDED.competency_id,
  prompt_text = EXCLUDED.prompt_text,
  sort_order = EXCLUDED.sort_order;

INSERT INTO question_pack_items (id, competency_id, prompt_text, sort_order)
VALUES (
  '30000001-0000-4000-8000-000000000014',
  '20000001-0000-4000-8000-000000000005',
  'Describe how you work with backend engineers to shape an API contract that serves both frontend and backend constraints.',
  1
)
ON CONFLICT (id) DO UPDATE SET
  competency_id = EXCLUDED.competency_id,
  prompt_text = EXCLUDED.prompt_text,
  sort_order = EXCLUDED.sort_order;

INSERT INTO question_pack_items (id, competency_id, prompt_text, sort_order)
VALUES (
  '30000001-0000-4000-8000-000000000015',
  '20000001-0000-4000-8000-000000000005',
  'Walk me through how you communicate technical constraints to a product manager pushing for a tight deadline.',
  2
)
ON CONFLICT (id) DO UPDATE SET
  competency_id = EXCLUDED.competency_id,
  prompt_text = EXCLUDED.prompt_text,
  sort_order = EXCLUDED.sort_order;

-- Technical Communication (behavioral)
INSERT INTO question_pack_items (id, competency_id, prompt_text, sort_order)
VALUES (
  '30000001-0000-4000-8000-000000000016',
  '20000001-0000-4000-8000-000000000006',
  'Describe how you documented a complex architectural decision so that future team members could understand the reasoning.',
  0
)
ON CONFLICT (id) DO UPDATE SET
  competency_id = EXCLUDED.competency_id,
  prompt_text = EXCLUDED.prompt_text,
  sort_order = EXCLUDED.sort_order;

INSERT INTO question_pack_items (id, competency_id, prompt_text, sort_order)
VALUES (
  '30000001-0000-4000-8000-000000000017',
  '20000001-0000-4000-8000-000000000006',
  'Tell me about a time you had to explain a performance trade-off to stakeholders who lacked deep frontend knowledge.',
  1
)
ON CONFLICT (id) DO UPDATE SET
  competency_id = EXCLUDED.competency_id,
  prompt_text = EXCLUDED.prompt_text,
  sort_order = EXCLUDED.sort_order;

INSERT INTO question_pack_items (id, competency_id, prompt_text, sort_order)
VALUES (
  '30000001-0000-4000-8000-000000000018',
  '20000001-0000-4000-8000-000000000006',
  'How do you approach writing a technical RFC or proposal that needs buy-in from engineers with different specializations?',
  2
)
ON CONFLICT (id) DO UPDATE SET
  competency_id = EXCLUDED.competency_id,
  prompt_text = EXCLUDED.prompt_text,
  sort_order = EXCLUDED.sort_order;

-- ============================================================
-- Backend Engineer question pack items
-- ============================================================

-- API Design Patterns (technical)
INSERT INTO question_pack_items (id, competency_id, prompt_text, sort_order)
VALUES (
  '30000001-0000-4000-8000-000000000019',
  '20000001-0000-4000-8000-000000000007',
  'Walk me through how you design error responses for a public API, including status codes, error codes, and what information to expose versus hide.',
  0
)
ON CONFLICT (id) DO UPDATE SET
  competency_id = EXCLUDED.competency_id,
  prompt_text = EXCLUDED.prompt_text,
  sort_order = EXCLUDED.sort_order;

INSERT INTO question_pack_items (id, competency_id, prompt_text, sort_order)
VALUES (
  '30000001-0000-4000-8000-000000000020',
  '20000001-0000-4000-8000-000000000007',
  'Describe a situation where you had to evolve an API without breaking existing consumers. What strategy did you use?',
  1
)
ON CONFLICT (id) DO UPDATE SET
  competency_id = EXCLUDED.competency_id,
  prompt_text = EXCLUDED.prompt_text,
  sort_order = EXCLUDED.sort_order;

INSERT INTO question_pack_items (id, competency_id, prompt_text, sort_order)
VALUES (
  '30000001-0000-4000-8000-000000000021',
  '20000001-0000-4000-8000-000000000007',
  'How would you approach designing pagination for an endpoint where the underlying data changes frequently between requests?',
  2
)
ON CONFLICT (id) DO UPDATE SET
  competency_id = EXCLUDED.competency_id,
  prompt_text = EXCLUDED.prompt_text,
  sort_order = EXCLUDED.sort_order;

-- Database Modeling (technical)
INSERT INTO question_pack_items (id, competency_id, prompt_text, sort_order)
VALUES (
  '30000001-0000-4000-8000-000000000022',
  '20000001-0000-4000-8000-000000000008',
  'Walk me through your approach to modeling a many-to-many relationship where the join entity has its own lifecycle and attributes.',
  0
)
ON CONFLICT (id) DO UPDATE SET
  competency_id = EXCLUDED.competency_id,
  prompt_text = EXCLUDED.prompt_text,
  sort_order = EXCLUDED.sort_order;

INSERT INTO question_pack_items (id, competency_id, prompt_text, sort_order)
VALUES (
  '30000001-0000-4000-8000-000000000023',
  '20000001-0000-4000-8000-000000000008',
  'Describe a time when you chose between normalization and denormalization. What drove the decision and how did it perform?',
  1
)
ON CONFLICT (id) DO UPDATE SET
  competency_id = EXCLUDED.competency_id,
  prompt_text = EXCLUDED.prompt_text,
  sort_order = EXCLUDED.sort_order;

INSERT INTO question_pack_items (id, competency_id, prompt_text, sort_order)
VALUES (
  '30000001-0000-4000-8000-000000000024',
  '20000001-0000-4000-8000-000000000008',
  'How do you decide which columns to index and how do you validate that your indexes are actually being used by the query planner?',
  2
)
ON CONFLICT (id) DO UPDATE SET
  competency_id = EXCLUDED.competency_id,
  prompt_text = EXCLUDED.prompt_text,
  sort_order = EXCLUDED.sort_order;

-- Distributed Systems Thinking (technical)
INSERT INTO question_pack_items (id, competency_id, prompt_text, sort_order)
VALUES (
  '30000001-0000-4000-8000-000000000025',
  '20000001-0000-4000-8000-000000000009',
  'Describe how you would handle a scenario where two services need to maintain consistency without distributed transactions.',
  0
)
ON CONFLICT (id) DO UPDATE SET
  competency_id = EXCLUDED.competency_id,
  prompt_text = EXCLUDED.prompt_text,
  sort_order = EXCLUDED.sort_order;

INSERT INTO question_pack_items (id, competency_id, prompt_text, sort_order)
VALUES (
  '30000001-0000-4000-8000-000000000026',
  '20000001-0000-4000-8000-000000000009',
  'Tell me about a time a network partition or service failure exposed a gap in your system design. What did you learn?',
  1
)
ON CONFLICT (id) DO UPDATE SET
  competency_id = EXCLUDED.competency_id,
  prompt_text = EXCLUDED.prompt_text,
  sort_order = EXCLUDED.sort_order;

INSERT INTO question_pack_items (id, competency_id, prompt_text, sort_order)
VALUES (
  '30000001-0000-4000-8000-000000000027',
  '20000001-0000-4000-8000-000000000009',
  'How would you design a retry strategy for an idempotent write operation that must eventually succeed without duplicating side effects?',
  2
)
ON CONFLICT (id) DO UPDATE SET
  competency_id = EXCLUDED.competency_id,
  prompt_text = EXCLUDED.prompt_text,
  sort_order = EXCLUDED.sort_order;

-- Problem Decomposition (behavioral)
INSERT INTO question_pack_items (id, competency_id, prompt_text, sort_order)
VALUES (
  '30000001-0000-4000-8000-000000000028',
  '20000001-0000-4000-8000-000000000010',
  'Describe how you broke down an ambiguous feature request into concrete implementation milestones with clear success criteria.',
  0
)
ON CONFLICT (id) DO UPDATE SET
  competency_id = EXCLUDED.competency_id,
  prompt_text = EXCLUDED.prompt_text,
  sort_order = EXCLUDED.sort_order;

INSERT INTO question_pack_items (id, competency_id, prompt_text, sort_order)
VALUES (
  '30000001-0000-4000-8000-000000000029',
  '20000001-0000-4000-8000-000000000010',
  'Tell me about a time the initial decomposition of a problem turned out to be wrong. How did you recognize it and adapt?',
  1
)
ON CONFLICT (id) DO UPDATE SET
  competency_id = EXCLUDED.competency_id,
  prompt_text = EXCLUDED.prompt_text,
  sort_order = EXCLUDED.sort_order;

INSERT INTO question_pack_items (id, competency_id, prompt_text, sort_order)
VALUES (
  '30000001-0000-4000-8000-000000000030',
  '20000001-0000-4000-8000-000000000010',
  'Walk me through how you decide which parts of a complex system to build first when dependencies are unclear.',
  2
)
ON CONFLICT (id) DO UPDATE SET
  competency_id = EXCLUDED.competency_id,
  prompt_text = EXCLUDED.prompt_text,
  sort_order = EXCLUDED.sort_order;

-- Operational Awareness (behavioral)
INSERT INTO question_pack_items (id, competency_id, prompt_text, sort_order)
VALUES (
  '30000001-0000-4000-8000-000000000031',
  '20000001-0000-4000-8000-000000000011',
  'Describe how you build observability into a new service from the start. What signals do you prioritize and why?',
  0
)
ON CONFLICT (id) DO UPDATE SET
  competency_id = EXCLUDED.competency_id,
  prompt_text = EXCLUDED.prompt_text,
  sort_order = EXCLUDED.sort_order;

INSERT INTO question_pack_items (id, competency_id, prompt_text, sort_order)
VALUES (
  '30000001-0000-4000-8000-000000000032',
  '20000001-0000-4000-8000-000000000011',
  'Tell me about a production incident you were involved in. How did you triage it and what changes did you make afterward?',
  1
)
ON CONFLICT (id) DO UPDATE SET
  competency_id = EXCLUDED.competency_id,
  prompt_text = EXCLUDED.prompt_text,
  sort_order = EXCLUDED.sort_order;

INSERT INTO question_pack_items (id, competency_id, prompt_text, sort_order)
VALUES (
  '30000001-0000-4000-8000-000000000033',
  '20000001-0000-4000-8000-000000000011',
  'How do you decide what level of redundancy and failover a system needs versus accepting some downtime risk?',
  2
)
ON CONFLICT (id) DO UPDATE SET
  competency_id = EXCLUDED.competency_id,
  prompt_text = EXCLUDED.prompt_text,
  sort_order = EXCLUDED.sort_order;

-- ============================================================
-- Fullstack Engineer question pack items
-- ============================================================

-- End-to-End System Design (technical)
INSERT INTO question_pack_items (id, competency_id, prompt_text, sort_order)
VALUES (
  '30000001-0000-4000-8000-000000000034',
  '20000001-0000-4000-8000-000000000012',
  'Walk me through how you would design a feature that requires real-time updates from server to multiple connected clients.',
  0
)
ON CONFLICT (id) DO UPDATE SET
  competency_id = EXCLUDED.competency_id,
  prompt_text = EXCLUDED.prompt_text,
  sort_order = EXCLUDED.sort_order;

INSERT INTO question_pack_items (id, competency_id, prompt_text, sort_order)
VALUES (
  '30000001-0000-4000-8000-000000000035',
  '20000001-0000-4000-8000-000000000012',
  'Describe a system you built where the caching strategy was critical to user experience. How did you handle invalidation?',
  1
)
ON CONFLICT (id) DO UPDATE SET
  competency_id = EXCLUDED.competency_id,
  prompt_text = EXCLUDED.prompt_text,
  sort_order = EXCLUDED.sort_order;

INSERT INTO question_pack_items (id, competency_id, prompt_text, sort_order)
VALUES (
  '30000001-0000-4000-8000-000000000036',
  '20000001-0000-4000-8000-000000000012',
  'How do you decide where to place validation logic when building a feature that spans client forms, API handlers, and database constraints?',
  2
)
ON CONFLICT (id) DO UPDATE SET
  competency_id = EXCLUDED.competency_id,
  prompt_text = EXCLUDED.prompt_text,
  sort_order = EXCLUDED.sort_order;

-- Frontend-Backend Integration (technical)
INSERT INTO question_pack_items (id, competency_id, prompt_text, sort_order)
VALUES (
  '30000001-0000-4000-8000-000000000037',
  '20000001-0000-4000-8000-000000000013',
  'Describe how you handle optimistic UI updates that might be rejected by the server. What rollback strategy do you use?',
  0
)
ON CONFLICT (id) DO UPDATE SET
  competency_id = EXCLUDED.competency_id,
  prompt_text = EXCLUDED.prompt_text,
  sort_order = EXCLUDED.sort_order;

INSERT INTO question_pack_items (id, competency_id, prompt_text, sort_order)
VALUES (
  '30000001-0000-4000-8000-000000000038',
  '20000001-0000-4000-8000-000000000013',
  'Walk me through how you design loading and error states for a page that fetches from multiple independent API endpoints.',
  1
)
ON CONFLICT (id) DO UPDATE SET
  competency_id = EXCLUDED.competency_id,
  prompt_text = EXCLUDED.prompt_text,
  sort_order = EXCLUDED.sort_order;

INSERT INTO question_pack_items (id, competency_id, prompt_text, sort_order)
VALUES (
  '30000001-0000-4000-8000-000000000039',
  '20000001-0000-4000-8000-000000000013',
  'Tell me about a time an API contract changed and broke the frontend. How did you prevent it from happening again?',
  2
)
ON CONFLICT (id) DO UPDATE SET
  competency_id = EXCLUDED.competency_id,
  prompt_text = EXCLUDED.prompt_text,
  sort_order = EXCLUDED.sort_order;

-- CI/CD and Deployment Strategy (technical)
INSERT INTO question_pack_items (id, competency_id, prompt_text, sort_order)
VALUES (
  '30000001-0000-4000-8000-000000000040',
  '20000001-0000-4000-8000-000000000014',
  'Describe your approach to designing a deployment pipeline that gives confidence without slowing iteration speed.',
  0
)
ON CONFLICT (id) DO UPDATE SET
  competency_id = EXCLUDED.competency_id,
  prompt_text = EXCLUDED.prompt_text,
  sort_order = EXCLUDED.sort_order;

INSERT INTO question_pack_items (id, competency_id, prompt_text, sort_order)
VALUES (
  '30000001-0000-4000-8000-000000000041',
  '20000001-0000-4000-8000-000000000014',
  'Tell me about a time a deployment went wrong. What was your rollback process and what did you change afterward?',
  1
)
ON CONFLICT (id) DO UPDATE SET
  competency_id = EXCLUDED.competency_id,
  prompt_text = EXCLUDED.prompt_text,
  sort_order = EXCLUDED.sort_order;

INSERT INTO question_pack_items (id, competency_id, prompt_text, sort_order)
VALUES (
  '30000001-0000-4000-8000-000000000042',
  '20000001-0000-4000-8000-000000000014',
  'How do you manage environment-specific configuration across development, staging, and production without secrets leaking?',
  2
)
ON CONFLICT (id) DO UPDATE SET
  competency_id = EXCLUDED.competency_id,
  prompt_text = EXCLUDED.prompt_text,
  sort_order = EXCLUDED.sort_order;

-- Cross-Stack Debugging (technical)
INSERT INTO question_pack_items (id, competency_id, prompt_text, sort_order)
VALUES (
  '30000001-0000-4000-8000-000000000043',
  '20000001-0000-4000-8000-000000000015',
  'Walk me through how you trace a user-reported bug that could originate in the browser, the API layer, or the database.',
  0
)
ON CONFLICT (id) DO UPDATE SET
  competency_id = EXCLUDED.competency_id,
  prompt_text = EXCLUDED.prompt_text,
  sort_order = EXCLUDED.sort_order;

INSERT INTO question_pack_items (id, competency_id, prompt_text, sort_order)
VALUES (
  '30000001-0000-4000-8000-000000000044',
  '20000001-0000-4000-8000-000000000015',
  'Describe a time you used correlation IDs or distributed tracing to identify a failure across service boundaries.',
  1
)
ON CONFLICT (id) DO UPDATE SET
  competency_id = EXCLUDED.competency_id,
  prompt_text = EXCLUDED.prompt_text,
  sort_order = EXCLUDED.sort_order;

INSERT INTO question_pack_items (id, competency_id, prompt_text, sort_order)
VALUES (
  '30000001-0000-4000-8000-000000000045',
  '20000001-0000-4000-8000-000000000015',
  'How do you reproduce and isolate an intermittent issue that only appears under production traffic patterns?',
  2
)
ON CONFLICT (id) DO UPDATE SET
  competency_id = EXCLUDED.competency_id,
  prompt_text = EXCLUDED.prompt_text,
  sort_order = EXCLUDED.sort_order;

-- Data Flow Architecture (technical)
INSERT INTO question_pack_items (id, competency_id, prompt_text, sort_order)
VALUES (
  '30000001-0000-4000-8000-000000000046',
  '20000001-0000-4000-8000-000000000016',
  'Describe how you design the data flow for a feature where both the client and server can initiate state changes.',
  0
)
ON CONFLICT (id) DO UPDATE SET
  competency_id = EXCLUDED.competency_id,
  prompt_text = EXCLUDED.prompt_text,
  sort_order = EXCLUDED.sort_order;

INSERT INTO question_pack_items (id, competency_id, prompt_text, sort_order)
VALUES (
  '30000001-0000-4000-8000-000000000047',
  '20000001-0000-4000-8000-000000000016',
  'Walk me through how you handle stale data in a client cache when the server state has moved ahead.',
  1
)
ON CONFLICT (id) DO UPDATE SET
  competency_id = EXCLUDED.competency_id,
  prompt_text = EXCLUDED.prompt_text,
  sort_order = EXCLUDED.sort_order;

INSERT INTO question_pack_items (id, competency_id, prompt_text, sort_order)
VALUES (
  '30000001-0000-4000-8000-000000000048',
  '20000001-0000-4000-8000-000000000016',
  'How would you architect data ownership boundaries between a frontend state layer and a backend persistence layer?',
  2
)
ON CONFLICT (id) DO UPDATE SET
  competency_id = EXCLUDED.competency_id,
  prompt_text = EXCLUDED.prompt_text,
  sort_order = EXCLUDED.sort_order;

-- Pragmatic Trade-off Decisions (behavioral)
INSERT INTO question_pack_items (id, competency_id, prompt_text, sort_order)
VALUES (
  '30000001-0000-4000-8000-000000000049',
  '20000001-0000-4000-8000-000000000017',
  'Tell me about a time you shipped something you knew was imperfect. How did you decide what to cut and what to keep?',
  0
)
ON CONFLICT (id) DO UPDATE SET
  competency_id = EXCLUDED.competency_id,
  prompt_text = EXCLUDED.prompt_text,
  sort_order = EXCLUDED.sort_order;

INSERT INTO question_pack_items (id, competency_id, prompt_text, sort_order)
VALUES (
  '30000001-0000-4000-8000-000000000050',
  '20000001-0000-4000-8000-000000000017',
  'Describe how you communicate technical debt to non-technical stakeholders and negotiate time to address it.',
  1
)
ON CONFLICT (id) DO UPDATE SET
  competency_id = EXCLUDED.competency_id,
  prompt_text = EXCLUDED.prompt_text,
  sort_order = EXCLUDED.sort_order;

INSERT INTO question_pack_items (id, competency_id, prompt_text, sort_order)
VALUES (
  '30000001-0000-4000-8000-000000000051',
  '20000001-0000-4000-8000-000000000017',
  'Walk me through a decision where you chose a simpler solution over a more elegant one. What made simplicity the right call?',
  2
)
ON CONFLICT (id) DO UPDATE SET
  competency_id = EXCLUDED.competency_id,
  prompt_text = EXCLUDED.prompt_text,
  sort_order = EXCLUDED.sort_order;

-- Ownership and Delivery (behavioral)
INSERT INTO question_pack_items (id, competency_id, prompt_text, sort_order)
VALUES (
  '30000001-0000-4000-8000-000000000052',
  '20000001-0000-4000-8000-000000000018',
  'Describe a project where you owned the full lifecycle from proposal to production. How did you handle unexpected blockers?',
  0
)
ON CONFLICT (id) DO UPDATE SET
  competency_id = EXCLUDED.competency_id,
  prompt_text = EXCLUDED.prompt_text,
  sort_order = EXCLUDED.sort_order;

INSERT INTO question_pack_items (id, competency_id, prompt_text, sort_order)
VALUES (
  '30000001-0000-4000-8000-000000000053',
  '20000001-0000-4000-8000-000000000018',
  'Tell me about a time you identified a gap that nobody was responsible for and took ownership of filling it.',
  1
)
ON CONFLICT (id) DO UPDATE SET
  competency_id = EXCLUDED.competency_id,
  prompt_text = EXCLUDED.prompt_text,
  sort_order = EXCLUDED.sort_order;

INSERT INTO question_pack_items (id, competency_id, prompt_text, sort_order)
VALUES (
  '30000001-0000-4000-8000-000000000054',
  '20000001-0000-4000-8000-000000000018',
  'How do you maintain momentum on a feature when requirements shift mid-implementation?',
  2
)
ON CONFLICT (id) DO UPDATE SET
  competency_id = EXCLUDED.competency_id,
  prompt_text = EXCLUDED.prompt_text,
  sort_order = EXCLUDED.sort_order;

-- ============================================================
-- Staff Engineer question pack items
-- ============================================================

-- Technical Strategy and Vision (behavioral)
INSERT INTO question_pack_items (id, competency_id, prompt_text, sort_order)
VALUES (
  '30000001-0000-4000-8000-000000000055',
  '20000001-0000-4000-8000-000000000019',
  'Describe how you developed a technical strategy that influenced multiple teams. How did you get alignment?',
  0
)
ON CONFLICT (id) DO UPDATE SET
  competency_id = EXCLUDED.competency_id,
  prompt_text = EXCLUDED.prompt_text,
  sort_order = EXCLUDED.sort_order;

INSERT INTO question_pack_items (id, competency_id, prompt_text, sort_order)
VALUES (
  '30000001-0000-4000-8000-000000000056',
  '20000001-0000-4000-8000-000000000019',
  'Tell me about a time your proposed technical direction was challenged by a peer. How did you handle the disagreement?',
  1
)
ON CONFLICT (id) DO UPDATE SET
  competency_id = EXCLUDED.competency_id,
  prompt_text = EXCLUDED.prompt_text,
  sort_order = EXCLUDED.sort_order;

INSERT INTO question_pack_items (id, competency_id, prompt_text, sort_order)
VALUES (
  '30000001-0000-4000-8000-000000000057',
  '20000001-0000-4000-8000-000000000019',
  'Walk me through how you connect business objectives to specific technical investments when proposing a roadmap.',
  2
)
ON CONFLICT (id) DO UPDATE SET
  competency_id = EXCLUDED.competency_id,
  prompt_text = EXCLUDED.prompt_text,
  sort_order = EXCLUDED.sort_order;

-- Architecture Decision-Making (technical)
INSERT INTO question_pack_items (id, competency_id, prompt_text, sort_order)
VALUES (
  '30000001-0000-4000-8000-000000000058',
  '20000001-0000-4000-8000-000000000020',
  'Describe an architectural decision you made that you later realized was wrong. How did you course-correct?',
  0
)
ON CONFLICT (id) DO UPDATE SET
  competency_id = EXCLUDED.competency_id,
  prompt_text = EXCLUDED.prompt_text,
  sort_order = EXCLUDED.sort_order;

INSERT INTO question_pack_items (id, competency_id, prompt_text, sort_order)
VALUES (
  '30000001-0000-4000-8000-000000000059',
  '20000001-0000-4000-8000-000000000020',
  'Walk me through how you evaluate build-versus-buy decisions for infrastructure components.',
  1
)
ON CONFLICT (id) DO UPDATE SET
  competency_id = EXCLUDED.competency_id,
  prompt_text = EXCLUDED.prompt_text,
  sort_order = EXCLUDED.sort_order;

INSERT INTO question_pack_items (id, competency_id, prompt_text, sort_order)
VALUES (
  '30000001-0000-4000-8000-000000000060',
  '20000001-0000-4000-8000-000000000020',
  'How do you document and communicate architecture decisions so they remain useful as the team grows?',
  2
)
ON CONFLICT (id) DO UPDATE SET
  competency_id = EXCLUDED.competency_id,
  prompt_text = EXCLUDED.prompt_text,
  sort_order = EXCLUDED.sort_order;

-- Cross-Team Influence (behavioral)
INSERT INTO question_pack_items (id, competency_id, prompt_text, sort_order)
VALUES (
  '30000001-0000-4000-8000-000000000061',
  '20000001-0000-4000-8000-000000000021',
  'Tell me about a time you needed to change how another team built something. How did you influence without authority?',
  0
)
ON CONFLICT (id) DO UPDATE SET
  competency_id = EXCLUDED.competency_id,
  prompt_text = EXCLUDED.prompt_text,
  sort_order = EXCLUDED.sort_order;

INSERT INTO question_pack_items (id, competency_id, prompt_text, sort_order)
VALUES (
  '30000001-0000-4000-8000-000000000062',
  '20000001-0000-4000-8000-000000000021',
  'Describe how you built consensus across teams with conflicting priorities on a shared technical dependency.',
  1
)
ON CONFLICT (id) DO UPDATE SET
  competency_id = EXCLUDED.competency_id,
  prompt_text = EXCLUDED.prompt_text,
  sort_order = EXCLUDED.sort_order;

INSERT INTO question_pack_items (id, competency_id, prompt_text, sort_order)
VALUES (
  '30000001-0000-4000-8000-000000000063',
  '20000001-0000-4000-8000-000000000021',
  'Walk me through how you identify which cross-team initiatives are worth your time versus better delegated.',
  2
)
ON CONFLICT (id) DO UPDATE SET
  competency_id = EXCLUDED.competency_id,
  prompt_text = EXCLUDED.prompt_text,
  sort_order = EXCLUDED.sort_order;

-- Mentorship and Growth (behavioral)
INSERT INTO question_pack_items (id, competency_id, prompt_text, sort_order)
VALUES (
  '30000001-0000-4000-8000-000000000064',
  '20000001-0000-4000-8000-000000000022',
  'Describe how you helped a mid-level engineer grow into a senior role. What specific actions did you take?',
  0
)
ON CONFLICT (id) DO UPDATE SET
  competency_id = EXCLUDED.competency_id,
  prompt_text = EXCLUDED.prompt_text,
  sort_order = EXCLUDED.sort_order;

INSERT INTO question_pack_items (id, competency_id, prompt_text, sort_order)
VALUES (
  '30000001-0000-4000-8000-000000000065',
  '20000001-0000-4000-8000-000000000022',
  'Tell me about a code review or design discussion where you turned a correction into a learning opportunity.',
  1
)
ON CONFLICT (id) DO UPDATE SET
  competency_id = EXCLUDED.competency_id,
  prompt_text = EXCLUDED.prompt_text,
  sort_order = EXCLUDED.sort_order;

INSERT INTO question_pack_items (id, competency_id, prompt_text, sort_order)
VALUES (
  '30000001-0000-4000-8000-000000000066',
  '20000001-0000-4000-8000-000000000022',
  'How do you balance giving direct answers versus guiding someone to discover the solution themselves?',
  2
)
ON CONFLICT (id) DO UPDATE SET
  competency_id = EXCLUDED.competency_id,
  prompt_text = EXCLUDED.prompt_text,
  sort_order = EXCLUDED.sort_order;

-- System Design at Scale (technical)
INSERT INTO question_pack_items (id, competency_id, prompt_text, sort_order)
VALUES (
  '30000001-0000-4000-8000-000000000067',
  '20000001-0000-4000-8000-000000000023',
  'Walk me through how you would design a system to handle a 10x traffic increase with minimal architectural changes.',
  0
)
ON CONFLICT (id) DO UPDATE SET
  competency_id = EXCLUDED.competency_id,
  prompt_text = EXCLUDED.prompt_text,
  sort_order = EXCLUDED.sort_order;

INSERT INTO question_pack_items (id, competency_id, prompt_text, sort_order)
VALUES (
  '30000001-0000-4000-8000-000000000068',
  '20000001-0000-4000-8000-000000000023',
  'Describe a data partitioning strategy you implemented. How did you choose the partition key and handle cross-partition queries?',
  1
)
ON CONFLICT (id) DO UPDATE SET
  competency_id = EXCLUDED.competency_id,
  prompt_text = EXCLUDED.prompt_text,
  sort_order = EXCLUDED.sort_order;

INSERT INTO question_pack_items (id, competency_id, prompt_text, sort_order)
VALUES (
  '30000001-0000-4000-8000-000000000069',
  '20000001-0000-4000-8000-000000000023',
  'How do you design graceful degradation so that partial failures do not cascade into total system unavailability?',
  2
)
ON CONFLICT (id) DO UPDATE SET
  competency_id = EXCLUDED.competency_id,
  prompt_text = EXCLUDED.prompt_text,
  sort_order = EXCLUDED.sort_order;

-- Risk Assessment and Mitigation (behavioral)
INSERT INTO question_pack_items (id, competency_id, prompt_text, sort_order)
VALUES (
  '30000001-0000-4000-8000-000000000070',
  '20000001-0000-4000-8000-000000000024',
  'Describe how you identify and communicate technical risks at the start of a project. What framework do you use?',
  0
)
ON CONFLICT (id) DO UPDATE SET
  competency_id = EXCLUDED.competency_id,
  prompt_text = EXCLUDED.prompt_text,
  sort_order = EXCLUDED.sort_order;

INSERT INTO question_pack_items (id, competency_id, prompt_text, sort_order)
VALUES (
  '30000001-0000-4000-8000-000000000071',
  '20000001-0000-4000-8000-000000000024',
  'Tell me about a time you advocated against a risky approach that others were enthusiastic about. How did you make the case?',
  1
)
ON CONFLICT (id) DO UPDATE SET
  competency_id = EXCLUDED.competency_id,
  prompt_text = EXCLUDED.prompt_text,
  sort_order = EXCLUDED.sort_order;

INSERT INTO question_pack_items (id, competency_id, prompt_text, sort_order)
VALUES (
  '30000001-0000-4000-8000-000000000072',
  '20000001-0000-4000-8000-000000000024',
  'How do you decide when a risk is acceptable versus when it needs mitigation before proceeding?',
  2
)
ON CONFLICT (id) DO UPDATE SET
  competency_id = EXCLUDED.competency_id,
  prompt_text = EXCLUDED.prompt_text,
  sort_order = EXCLUDED.sort_order;

-- Code Quality Standards (technical)
INSERT INTO question_pack_items (id, competency_id, prompt_text, sort_order)
VALUES (
  '30000001-0000-4000-8000-000000000073',
  '20000001-0000-4000-8000-000000000025',
  'Walk me through how you introduced or improved a code review culture on a team that previously lacked one.',
  0
)
ON CONFLICT (id) DO UPDATE SET
  competency_id = EXCLUDED.competency_id,
  prompt_text = EXCLUDED.prompt_text,
  sort_order = EXCLUDED.sort_order;

INSERT INTO question_pack_items (id, competency_id, prompt_text, sort_order)
VALUES (
  '30000001-0000-4000-8000-000000000074',
  '20000001-0000-4000-8000-000000000025',
  'Describe how you decide which testing strategies to enforce versus which to leave as team guidance.',
  1
)
ON CONFLICT (id) DO UPDATE SET
  competency_id = EXCLUDED.competency_id,
  prompt_text = EXCLUDED.prompt_text,
  sort_order = EXCLUDED.sort_order;

INSERT INTO question_pack_items (id, competency_id, prompt_text, sort_order)
VALUES (
  '30000001-0000-4000-8000-000000000075',
  '20000001-0000-4000-8000-000000000025',
  'How do you evolve coding standards as a codebase grows without creating churn on existing code?',
  2
)
ON CONFLICT (id) DO UPDATE SET
  competency_id = EXCLUDED.competency_id,
  prompt_text = EXCLUDED.prompt_text,
  sort_order = EXCLUDED.sort_order;

-- Organizational Impact (behavioral)
INSERT INTO question_pack_items (id, competency_id, prompt_text, sort_order)
VALUES (
  '30000001-0000-4000-8000-000000000076',
  '20000001-0000-4000-8000-000000000026',
  'Describe an initiative you drove that improved engineering effectiveness beyond your immediate team.',
  0
)
ON CONFLICT (id) DO UPDATE SET
  competency_id = EXCLUDED.competency_id,
  prompt_text = EXCLUDED.prompt_text,
  sort_order = EXCLUDED.sort_order;

INSERT INTO question_pack_items (id, competency_id, prompt_text, sort_order)
VALUES (
  '30000001-0000-4000-8000-000000000077',
  '20000001-0000-4000-8000-000000000026',
  'Tell me about a time you identified a systemic problem and proposed a solution that required organizational change.',
  1
)
ON CONFLICT (id) DO UPDATE SET
  competency_id = EXCLUDED.competency_id,
  prompt_text = EXCLUDED.prompt_text,
  sort_order = EXCLUDED.sort_order;

INSERT INTO question_pack_items (id, competency_id, prompt_text, sort_order)
VALUES (
  '30000001-0000-4000-8000-000000000078',
  '20000001-0000-4000-8000-000000000026',
  'How do you measure the impact of platform or tooling investments that benefit many teams indirectly?',
  2
)
ON CONFLICT (id) DO UPDATE SET
  competency_id = EXCLUDED.competency_id,
  prompt_text = EXCLUDED.prompt_text,
  sort_order = EXCLUDED.sort_order;

-- ============================================================
-- ML Engineer question pack items
-- ============================================================

-- Model Deployment and Serving (technical)
INSERT INTO question_pack_items (id, competency_id, prompt_text, sort_order)
VALUES (
  '30000001-0000-4000-8000-000000000079',
  '20000001-0000-4000-8000-000000000027',
  'Walk me through how you deploy a new model version to production with confidence that it performs at least as well as the previous one.',
  0
)
ON CONFLICT (id) DO UPDATE SET
  competency_id = EXCLUDED.competency_id,
  prompt_text = EXCLUDED.prompt_text,
  sort_order = EXCLUDED.sort_order;

INSERT INTO question_pack_items (id, competency_id, prompt_text, sort_order)
VALUES (
  '30000001-0000-4000-8000-000000000080',
  '20000001-0000-4000-8000-000000000027',
  'Describe how you handle latency requirements when serving predictions in real-time versus batch scenarios.',
  1
)
ON CONFLICT (id) DO UPDATE SET
  competency_id = EXCLUDED.competency_id,
  prompt_text = EXCLUDED.prompt_text,
  sort_order = EXCLUDED.sort_order;

INSERT INTO question_pack_items (id, competency_id, prompt_text, sort_order)
VALUES (
  '30000001-0000-4000-8000-000000000081',
  '20000001-0000-4000-8000-000000000027',
  'How do you decide between embedding a model in the application versus serving it as a separate microservice?',
  2
)
ON CONFLICT (id) DO UPDATE SET
  competency_id = EXCLUDED.competency_id,
  prompt_text = EXCLUDED.prompt_text,
  sort_order = EXCLUDED.sort_order;

-- Data Pipeline Design (technical)
INSERT INTO question_pack_items (id, competency_id, prompt_text, sort_order)
VALUES (
  '30000001-0000-4000-8000-000000000082',
  '20000001-0000-4000-8000-000000000028',
  'Describe how you ensure data quality at each stage of a pipeline that feeds into model training.',
  0
)
ON CONFLICT (id) DO UPDATE SET
  competency_id = EXCLUDED.competency_id,
  prompt_text = EXCLUDED.prompt_text,
  sort_order = EXCLUDED.sort_order;

INSERT INTO question_pack_items (id, competency_id, prompt_text, sort_order)
VALUES (
  '30000001-0000-4000-8000-000000000083',
  '20000001-0000-4000-8000-000000000028',
  'Walk me through how you handle schema evolution in a data pipeline without breaking downstream consumers.',
  1
)
ON CONFLICT (id) DO UPDATE SET
  competency_id = EXCLUDED.competency_id,
  prompt_text = EXCLUDED.prompt_text,
  sort_order = EXCLUDED.sort_order;

INSERT INTO question_pack_items (id, competency_id, prompt_text, sort_order)
VALUES (
  '30000001-0000-4000-8000-000000000084',
  '20000001-0000-4000-8000-000000000028',
  'How do you design pipeline monitoring to catch silent data corruption before it affects model performance?',
  2
)
ON CONFLICT (id) DO UPDATE SET
  competency_id = EXCLUDED.competency_id,
  prompt_text = EXCLUDED.prompt_text,
  sort_order = EXCLUDED.sort_order;

-- Experiment Design and Tracking (technical)
INSERT INTO question_pack_items (id, competency_id, prompt_text, sort_order)
VALUES (
  '30000001-0000-4000-8000-000000000085',
  '20000001-0000-4000-8000-000000000029',
  'Describe your approach to designing an A/B test for a model change. How do you choose metrics and determine sample size?',
  0
)
ON CONFLICT (id) DO UPDATE SET
  competency_id = EXCLUDED.competency_id,
  prompt_text = EXCLUDED.prompt_text,
  sort_order = EXCLUDED.sort_order;

INSERT INTO question_pack_items (id, competency_id, prompt_text, sort_order)
VALUES (
  '30000001-0000-4000-8000-000000000086',
  '20000001-0000-4000-8000-000000000029',
  'Walk me through how you ensure experiment reproducibility when the training environment has many moving parts.',
  1
)
ON CONFLICT (id) DO UPDATE SET
  competency_id = EXCLUDED.competency_id,
  prompt_text = EXCLUDED.prompt_text,
  sort_order = EXCLUDED.sort_order;

INSERT INTO question_pack_items (id, competency_id, prompt_text, sort_order)
VALUES (
  '30000001-0000-4000-8000-000000000087',
  '20000001-0000-4000-8000-000000000029',
  'How do you decide when an experiment has generated enough signal to ship versus when it needs more data?',
  2
)
ON CONFLICT (id) DO UPDATE SET
  competency_id = EXCLUDED.competency_id,
  prompt_text = EXCLUDED.prompt_text,
  sort_order = EXCLUDED.sort_order;

-- Stakeholder Communication (behavioral)
INSERT INTO question_pack_items (id, competency_id, prompt_text, sort_order)
VALUES (
  '30000001-0000-4000-8000-000000000088',
  '20000001-0000-4000-8000-000000000030',
  'Tell me about a time you had to explain why a model was not ready for production despite good offline metrics.',
  0
)
ON CONFLICT (id) DO UPDATE SET
  competency_id = EXCLUDED.competency_id,
  prompt_text = EXCLUDED.prompt_text,
  sort_order = EXCLUDED.sort_order;

INSERT INTO question_pack_items (id, competency_id, prompt_text, sort_order)
VALUES (
  '30000001-0000-4000-8000-000000000089',
  '20000001-0000-4000-8000-000000000030',
  'Describe how you communicate model uncertainty and limitations to product stakeholders who want deterministic answers.',
  1
)
ON CONFLICT (id) DO UPDATE SET
  competency_id = EXCLUDED.competency_id,
  prompt_text = EXCLUDED.prompt_text,
  sort_order = EXCLUDED.sort_order;

INSERT INTO question_pack_items (id, competency_id, prompt_text, sort_order)
VALUES (
  '30000001-0000-4000-8000-000000000090',
  '20000001-0000-4000-8000-000000000030',
  'How do you set expectations around model performance timelines when improvement is uncertain and non-linear?',
  2
)
ON CONFLICT (id) DO UPDATE SET
  competency_id = EXCLUDED.competency_id,
  prompt_text = EXCLUDED.prompt_text,
  sort_order = EXCLUDED.sort_order;

-- Production Reliability (behavioral)
INSERT INTO question_pack_items (id, competency_id, prompt_text, sort_order)
VALUES (
  '30000001-0000-4000-8000-000000000091',
  '20000001-0000-4000-8000-000000000031',
  'Describe how you design fallback behavior when a model prediction service becomes unavailable.',
  0
)
ON CONFLICT (id) DO UPDATE SET
  competency_id = EXCLUDED.competency_id,
  prompt_text = EXCLUDED.prompt_text,
  sort_order = EXCLUDED.sort_order;

INSERT INTO question_pack_items (id, competency_id, prompt_text, sort_order)
VALUES (
  '30000001-0000-4000-8000-000000000092',
  '20000001-0000-4000-8000-000000000031',
  'Walk me through how you monitor for model drift in production and what actions you take when drift is detected.',
  1
)
ON CONFLICT (id) DO UPDATE SET
  competency_id = EXCLUDED.competency_id,
  prompt_text = EXCLUDED.prompt_text,
  sort_order = EXCLUDED.sort_order;

INSERT INTO question_pack_items (id, competency_id, prompt_text, sort_order)
VALUES (
  '30000001-0000-4000-8000-000000000093',
  '20000001-0000-4000-8000-000000000031',
  'Tell me about a time an ML system failed silently in production. How did you detect and resolve it?',
  2
)
ON CONFLICT (id) DO UPDATE SET
  competency_id = EXCLUDED.competency_id,
  prompt_text = EXCLUDED.prompt_text,
  sort_order = EXCLUDED.sort_order;

-- ============================================================
-- Platform Engineer question pack items
-- ============================================================

-- Infrastructure as Code (technical)
INSERT INTO question_pack_items (id, competency_id, prompt_text, sort_order)
VALUES (
  '30000001-0000-4000-8000-000000000094',
  '20000001-0000-4000-8000-000000000032',
  'Walk me through how you structure IaC modules to balance reusability across environments with environment-specific overrides.',
  0
)
ON CONFLICT (id) DO UPDATE SET
  competency_id = EXCLUDED.competency_id,
  prompt_text = EXCLUDED.prompt_text,
  sort_order = EXCLUDED.sort_order;

INSERT INTO question_pack_items (id, competency_id, prompt_text, sort_order)
VALUES (
  '30000001-0000-4000-8000-000000000095',
  '20000001-0000-4000-8000-000000000032',
  'Describe how you handle infrastructure drift detection and remediation in a team where manual changes sometimes happen.',
  1
)
ON CONFLICT (id) DO UPDATE SET
  competency_id = EXCLUDED.competency_id,
  prompt_text = EXCLUDED.prompt_text,
  sort_order = EXCLUDED.sort_order;

INSERT INTO question_pack_items (id, competency_id, prompt_text, sort_order)
VALUES (
  '30000001-0000-4000-8000-000000000096',
  '20000001-0000-4000-8000-000000000032',
  'How do you test infrastructure changes before applying them to production environments?',
  2
)
ON CONFLICT (id) DO UPDATE SET
  competency_id = EXCLUDED.competency_id,
  prompt_text = EXCLUDED.prompt_text,
  sort_order = EXCLUDED.sort_order;

-- Container Orchestration (technical)
INSERT INTO question_pack_items (id, competency_id, prompt_text, sort_order)
VALUES (
  '30000001-0000-4000-8000-000000000097',
  '20000001-0000-4000-8000-000000000033',
  'Describe how you configure resource limits and requests for containers to balance cost and reliability.',
  0
)
ON CONFLICT (id) DO UPDATE SET
  competency_id = EXCLUDED.competency_id,
  prompt_text = EXCLUDED.prompt_text,
  sort_order = EXCLUDED.sort_order;

INSERT INTO question_pack_items (id, competency_id, prompt_text, sort_order)
VALUES (
  '30000001-0000-4000-8000-000000000098',
  '20000001-0000-4000-8000-000000000033',
  'Walk me through how you handle rolling deployments with zero-downtime guarantees in an orchestrated environment.',
  1
)
ON CONFLICT (id) DO UPDATE SET
  competency_id = EXCLUDED.competency_id,
  prompt_text = EXCLUDED.prompt_text,
  sort_order = EXCLUDED.sort_order;

INSERT INTO question_pack_items (id, competency_id, prompt_text, sort_order)
VALUES (
  '30000001-0000-4000-8000-000000000099',
  '20000001-0000-4000-8000-000000000033',
  'How do you debug networking issues between containers that work locally but fail in orchestration?',
  2
)
ON CONFLICT (id) DO UPDATE SET
  competency_id = EXCLUDED.competency_id,
  prompt_text = EXCLUDED.prompt_text,
  sort_order = EXCLUDED.sort_order;

-- Developer Experience Design (technical)
INSERT INTO question_pack_items (id, competency_id, prompt_text, sort_order)
VALUES (
  '30000001-0000-4000-8000-000000000100',
  '20000001-0000-4000-8000-000000000034',
  'Describe how you measure whether internal tooling is actually improving developer productivity versus adding friction.',
  0
)
ON CONFLICT (id) DO UPDATE SET
  competency_id = EXCLUDED.competency_id,
  prompt_text = EXCLUDED.prompt_text,
  sort_order = EXCLUDED.sort_order;

INSERT INTO question_pack_items (id, competency_id, prompt_text, sort_order)
VALUES (
  '30000001-0000-4000-8000-000000000101',
  '20000001-0000-4000-8000-000000000034',
  'Walk me through how you designed a self-service platform feature that reduced support requests from product teams.',
  1
)
ON CONFLICT (id) DO UPDATE SET
  competency_id = EXCLUDED.competency_id,
  prompt_text = EXCLUDED.prompt_text,
  sort_order = EXCLUDED.sort_order;

INSERT INTO question_pack_items (id, competency_id, prompt_text, sort_order)
VALUES (
  '30000001-0000-4000-8000-000000000102',
  '20000001-0000-4000-8000-000000000034',
  'How do you balance building reusable platform abstractions versus just solving the immediate problem a team brings you?',
  2
)
ON CONFLICT (id) DO UPDATE SET
  competency_id = EXCLUDED.competency_id,
  prompt_text = EXCLUDED.prompt_text,
  sort_order = EXCLUDED.sort_order;

-- Observability and Monitoring (technical)
INSERT INTO question_pack_items (id, competency_id, prompt_text, sort_order)
VALUES (
  '30000001-0000-4000-8000-000000000103',
  '20000001-0000-4000-8000-000000000035',
  'Describe how you design an alerting strategy that minimizes noise while catching real incidents quickly.',
  0
)
ON CONFLICT (id) DO UPDATE SET
  competency_id = EXCLUDED.competency_id,
  prompt_text = EXCLUDED.prompt_text,
  sort_order = EXCLUDED.sort_order;

INSERT INTO question_pack_items (id, competency_id, prompt_text, sort_order)
VALUES (
  '30000001-0000-4000-8000-000000000104',
  '20000001-0000-4000-8000-000000000035',
  'Walk me through how you implement distributed tracing across services with different tech stacks.',
  1
)
ON CONFLICT (id) DO UPDATE SET
  competency_id = EXCLUDED.competency_id,
  prompt_text = EXCLUDED.prompt_text,
  sort_order = EXCLUDED.sort_order;

INSERT INTO question_pack_items (id, competency_id, prompt_text, sort_order)
VALUES (
  '30000001-0000-4000-8000-000000000105',
  '20000001-0000-4000-8000-000000000035',
  'How do you decide which metrics to instrument versus which to derive from logs or traces after the fact?',
  2
)
ON CONFLICT (id) DO UPDATE SET
  competency_id = EXCLUDED.competency_id,
  prompt_text = EXCLUDED.prompt_text,
  sort_order = EXCLUDED.sort_order;

-- Incident Response and Reliability (behavioral)
INSERT INTO question_pack_items (id, competency_id, prompt_text, sort_order)
VALUES (
  '30000001-0000-4000-8000-000000000106',
  '20000001-0000-4000-8000-000000000036',
  'Describe your approach to running a blameless post-mortem that produces actionable improvements.',
  0
)
ON CONFLICT (id) DO UPDATE SET
  competency_id = EXCLUDED.competency_id,
  prompt_text = EXCLUDED.prompt_text,
  sort_order = EXCLUDED.sort_order;

INSERT INTO question_pack_items (id, competency_id, prompt_text, sort_order)
VALUES (
  '30000001-0000-4000-8000-000000000107',
  '20000001-0000-4000-8000-000000000036',
  'Tell me about a time you had to make a mitigation decision during an active incident with incomplete information.',
  1
)
ON CONFLICT (id) DO UPDATE SET
  competency_id = EXCLUDED.competency_id,
  prompt_text = EXCLUDED.prompt_text,
  sort_order = EXCLUDED.sort_order;

INSERT INTO question_pack_items (id, competency_id, prompt_text, sort_order)
VALUES (
  '30000001-0000-4000-8000-000000000108',
  '20000001-0000-4000-8000-000000000036',
  'How do you establish SLOs and error budgets that balance reliability investment with feature velocity?',
  2
)
ON CONFLICT (id) DO UPDATE SET
  competency_id = EXCLUDED.competency_id,
  prompt_text = EXCLUDED.prompt_text,
  sort_order = EXCLUDED.sort_order;

-- Security-First Thinking (behavioral)
INSERT INTO question_pack_items (id, competency_id, prompt_text, sort_order)
VALUES (
  '30000001-0000-4000-8000-000000000109',
  '20000001-0000-4000-8000-000000000037',
  'Walk me through how you integrate security reviews into infrastructure change workflows without creating bottlenecks.',
  0
)
ON CONFLICT (id) DO UPDATE SET
  competency_id = EXCLUDED.competency_id,
  prompt_text = EXCLUDED.prompt_text,
  sort_order = EXCLUDED.sort_order;

INSERT INTO question_pack_items (id, competency_id, prompt_text, sort_order)
VALUES (
  '30000001-0000-4000-8000-000000000110',
  '20000001-0000-4000-8000-000000000037',
  'Describe a time you discovered a security misconfiguration in production infrastructure. How did you respond and prevent recurrence?',
  1
)
ON CONFLICT (id) DO UPDATE SET
  competency_id = EXCLUDED.competency_id,
  prompt_text = EXCLUDED.prompt_text,
  sort_order = EXCLUDED.sort_order;

INSERT INTO question_pack_items (id, competency_id, prompt_text, sort_order)
VALUES (
  '30000001-0000-4000-8000-000000000111',
  '20000001-0000-4000-8000-000000000037',
  'How do you approach least-privilege access patterns when teams push back on the friction they introduce?',
  2
)
ON CONFLICT (id) DO UPDATE SET
  competency_id = EXCLUDED.competency_id,
  prompt_text = EXCLUDED.prompt_text,
  sort_order = EXCLUDED.sort_order;
