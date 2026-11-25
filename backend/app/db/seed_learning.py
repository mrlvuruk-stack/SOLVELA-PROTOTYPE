from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.learning import Roadmap, RoadmapNode, Skill, Assessment
import uuid

async def seed_learning_data(db: AsyncSession):
    """
    Seeds initial curated roadmaps, nodes, learning resources, and skills idempotently.
    """
    # 1. Seed Core Skills
    initial_skills = [
        {"name": "Python", "category": "Languages", "description": "Core programming language for backend & AI development."},
        {"name": "FastAPI", "category": "Backend", "description": "High-performance async web framework for building APIs."},
        {"name": "Next.js & React", "category": "Frontend", "description": "Server-rendered full-stack React framework."},
        {"name": "Vector Databases & Search", "category": "AI & ML", "description": "pgvector, embeddings, semantic retrieval, and hybrid search."},
        {"name": "Distributed Systems", "category": "Architecture", "description": "Consensus, partitioning, fault tolerance, and event-driven patterns."},
        {"name": "Algorithms & Optimization", "category": "Computer Science", "description": "Dynamic programming, graph theory, and greedy algorithms."}
    ]

    for s_data in initial_skills:
        existing = await db.execute(select(Skill).where(Skill.name == s_data["name"]))
        if not existing.scalar_one_or_none():
            skill = Skill(
                name=s_data["name"],
                category=s_data["category"],
                description=s_data["description"]
            )
            db.add(skill)

    # 2. Seed Official Roadmaps
    roadmaps_data = [
        {
            "slug": "full-stack-ai-engineering",
            "title": "Full-Stack AI Engineering & Agent Systems",
            "domain": "Artificial Intelligence",
            "description": "Master modern LLM architectures, vector databases, multi-agent swarms, Socratic mentoring engines, and low-latency API deployment.",
            "difficulty_level": "intermediate",
            "estimated_hours": 45,
            "nodes": [
                {
                    "title": "Module 1: LLM Foundations & Model Lifecycle",
                    "description": "Understand transformer mechanics, tokenization, context windows, and production model lifecycle management.",
                    "estimated_minutes": 60,
                    "order_index": 0,
                    "key_takeaways": [
                        "Differentiate between context length and effective memory",
                        "Evaluate model deprecation timelines and maintain zero-downtime fallback adapters",
                        "Optimize system prompts for deterministic structured output"
                    ],
                    "resources": [
                        {"title": "Attention Is All You Need (Vaswani et al.)", "url": "https://arxiv.org/abs/1706.03762", "type": "article", "est_minutes": 45},
                        {"title": "OpenAI / Anthropic Provider API Documentation", "url": "https://docs.anthropic.com", "type": "documentation", "est_minutes": 30}
                    ],
                    "assessment": {
                        "title": "LLM Foundations & Lifecycle Quiz",
                        "passing_score_pct": 75,
                        "questions": [
                            {
                                "id": 0,
                                "question": "What is the primary indicator of Time to First Byte (TTFB) in a streaming LLM response?",
                                "options": [
                                    "The time taken to close the TCP connection",
                                    "The duration until the first generated token/chunk arrives at the client",
                                    "The total time to render all generated paragraphs",
                                    "The database latency when storing user prompts"
                                ],
                                "correct_index": 1,
                                "explanation": "TTFB measures the duration from request transmission until the very first chunk arrives."
                            },
                            {
                                "id": 1,
                                "question": "Why should production AI applications implement automated model failover probes?",
                                "options": [
                                    "To prevent high GPU costs on self-hosted instances",
                                    "To prevent user-facing hangs if primary providers suffer latency spikes or retirement",
                                    "To convert text responses into audio files automatically",
                                    "To satisfy GDPR consent requirements"
                                ],
                                "correct_index": 1,
                                "explanation": "Failover probes prevent silent timeouts and ensure 99.99% user uptime."
                            }
                        ]
                    }
                },
                {
                    "title": "Module 2: Embeddings & Vector Retrieval (RAG)",
                    "description": "Implement vector indexing, cosine similarity, pgvector integration, and hybrid BM25 + dense search.",
                    "estimated_minutes": 75,
                    "order_index": 1,
                    "key_takeaways": [
                        "Construct multi-stage retrieval pipelines with semantic chunking",
                        "Deploy pgvector with HNSW / IVFFlat indexes in PostgreSQL 16",
                        "Mitigate hallucination via ground-truth citation verification"
                    ],
                    "resources": [
                        {"title": "pgvector Documentation & Benchmarks", "url": "https://github.com/pgvector/pgvector", "type": "repository", "est_minutes": 40},
                        {"title": "Retrieval Augmented Generation for Knowledge-Intensive NLP", "url": "https://arxiv.org/abs/2005.11401", "type": "article", "est_minutes": 50}
                    ],
                    "assessment": {
                        "title": "Vector Retrieval & Search Assessment",
                        "passing_score_pct": 70,
                        "questions": [
                            {
                                "id": 0,
                                "question": "Which index type in pgvector provides fast approximate nearest neighbor search with sub-linear query time?",
                                "options": ["B-Tree", "GIN", "HNSW", "BRIN"],
                                "correct_index": 2,
                                "explanation": "Hierarchical Navigable Small World (HNSW) graphs offer high recall and low search latency."
                            }
                        ]
                    }
                },
                {
                    "title": "Module 3: Autonomous Agents & Tool Orchestration",
                    "description": "Design deterministic agent loops, ReAct architectures, schema validation, and safe tool permissions.",
                    "estimated_minutes": 90,
                    "order_index": 2,
                    "key_takeaways": [
                        "Implement finite state machines for tool-calling agents",
                        "Enforce sandboxed command execution and permission boundaries",
                        "Measure multi-turn context drift and token consumption"
                    ],
                    "resources": [
                        {"title": "ReAct: Synergizing Reasoning and Acting in Language Models", "url": "https://arxiv.org/abs/2210.03629", "type": "article", "est_minutes": 45}
                    ]
                }
            ]
        },
        {
            "slug": "distributed-systems-cloud-architecture",
            "title": "Distributed Systems & Cloud Architecture",
            "domain": "Software Engineering",
            "description": "Deep-dive into consensus algorithms, partition tolerance, message streaming, load balancing, and fault-tolerant architectures.",
            "difficulty_level": "advanced",
            "estimated_hours": 50,
            "nodes": [
                {
                    "title": "Module 1: Consensus Protocols (Raft & Paxos)",
                    "description": "Leader election, log replication, safety invariants, and joint consensus reconfiguration.",
                    "estimated_minutes": 90,
                    "order_index": 0,
                    "key_takeaways": [
                        "Formalize leader heartbeat mechanisms and election timeouts",
                        "Verify quorum intersection across split-brain network partitions",
                        "Implement persistent state machines in memory and disk"
                    ],
                    "resources": [
                        {"title": "In Search of an Understandable Consensus Algorithm (Ongaro & Ousterhout)", "url": "https://raft.github.io/raft.pdf", "type": "article", "est_minutes": 60}
                    ],
                    "assessment": {
                        "title": "Raft Consensus Mastery",
                        "passing_score_pct": 75,
                        "questions": [
                            {
                                "id": 0,
                                "question": "In Raft, what ensures that only one leader can be elected per term?",
                                "options": [
                                    "A node can only vote for at most one candidate in a given term (First-come-first-served)",
                                    "The leader election is coordinated by a central master node",
                                    "Randomized delays ensure that elections never have ties",
                                    "Followers reject all votes if they have active client connections"
                                ],
                                "correct_index": 0,
                                "explanation": "Each server votes for at most one candidate per term on a first-come, first-served basis, ensuring a majority quorum is unique."
                            }
                        ]
                    }
                },
                {
                    "title": "Module 2: Eventual Consistency & Caching",
                    "description": "CAP theorem tradeoffs, read-your-writes consistency, CRDTs, and multi-region cache invalidation.",
                    "estimated_minutes": 60,
                    "order_index": 1,
                    "key_takeaways": [
                        "Balance latency vs consistency using tunables",
                        "Design idempotent event consumers with deduplication keys",
                        "Implement cache-aside and write-through patterns"
                    ],
                    "resources": [
                        {"title": "Designing Data-Intensive Applications (Kleppmann)", "url": "https://dataintensive.net", "type": "documentation", "est_minutes": 60}
                    ]
                }
            ]
        }
    ]

    for r_data in roadmaps_data:
        r_res = await db.execute(select(Roadmap).where(Roadmap.slug == r_data["slug"]))
        roadmap = r_res.scalar_one_or_none()
        if not roadmap:
            roadmap = Roadmap(
                slug=r_data["slug"],
                title=r_data["title"],
                domain=r_data["domain"],
                description=r_data["description"],
                difficulty_level=r_data["difficulty_level"],
                estimated_hours=r_data["estimated_hours"],
                is_official=True
            )
            db.add(roadmap)
            await db.flush()

            for n_data in r_data["nodes"]:
                node = RoadmapNode(
                    roadmap_id=roadmap.id,
                    title=n_data["title"],
                    description=n_data["description"],
                    estimated_minutes=n_data["estimated_minutes"],
                    order_index=n_data["order_index"],
                    key_takeaways_json=n_data.get("key_takeaways", []),
                    resources_json=n_data.get("resources", [])
                )
                db.add(node)
                await db.flush()

                if "assessment" in n_data:
                    a_data = n_data["assessment"]
                    assessment = Assessment(
                        node_id=node.id,
                        title=a_data["title"],
                        passing_score_pct=a_data["passing_score_pct"],
                        questions_json=a_data["questions"]
                    )
                    db.add(assessment)

    await db.commit()
