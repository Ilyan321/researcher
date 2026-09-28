-- =============================================================================
-- Migration: 20260928000001_initial_rag_schema.sql
-- Description: Agentic RAG Memory, Sessions, Reports, and Vector Search
-- =============================================================================

-- 1. Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- 2. Sessions Table (Tracks individual research topics / chat threads)
CREATE TABLE IF NOT EXISTS sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 3. Reports Table (Stores generated dossiers and versions per session)
CREATE TABLE IF NOT EXISTS reports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    markdown_content TEXT NOT NULL,
    version INT DEFAULT 1,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 4. Chat Messages Table (Stores user queries, agent replies, and iterative turns)
CREATE TABLE IF NOT EXISTS chat_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    role TEXT NOT NULL,
    content TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 5. Evidence Nodes Table (Vector store for verified facts, papers, and findings)
CREATE TABLE IF NOT EXISTS evidence_nodes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID REFERENCES sessions(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    embedding VECTOR(1536),
    metadata JSONB DEFAULT '{}'::JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 6. Vector Index (HNSW for fast cosine similarity search)
CREATE INDEX IF NOT EXISTS evidence_nodes_embedding_idx 
ON evidence_nodes 
USING hnsw (embedding vector_cosine_ops);

-- 7. RPC Function for Cosine Similarity Search & Scoped RAG
CREATE OR REPLACE FUNCTION match_evidence (
    query_embedding VECTOR(1536),
    match_threshold FLOAT DEFAULT 0.2,
    match_count INT DEFAULT 5,
    p_session_id UUID DEFAULT NULL
)
RETURNS TABLE (
    id UUID,
    session_id UUID,
    content TEXT,
    metadata JSONB,
    similarity FLOAT
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        e.id,
        e.session_id,
        e.content,
        e.metadata,
        (1 - (e.embedding <=> query_embedding))::FLOAT AS similarity
    FROM evidence_nodes e
    WHERE (p_session_id IS NULL OR e.session_id = p_session_id)
      AND (1 - (e.embedding <=> query_embedding)) > match_threshold
    ORDER BY e.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;

-- 8. Row Level Security (RLS) & Permissive Policies for Client Key Access
ALTER TABLE sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE reports ENABLE ROW LEVEL SECURITY;
ALTER TABLE chat_messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE evidence_nodes ENABLE ROW LEVEL SECURITY;

DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE policyname = 'Allow all access to sessions') THEN
        CREATE POLICY "Allow all access to sessions" ON sessions FOR ALL USING (true) WITH CHECK (true);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE policyname = 'Allow all access to reports') THEN
        CREATE POLICY "Allow all access to reports" ON reports FOR ALL USING (true) WITH CHECK (true);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE policyname = 'Allow all access to chat_messages') THEN
        CREATE POLICY "Allow all access to chat_messages" ON chat_messages FOR ALL USING (true) WITH CHECK (true);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE policyname = 'Allow all access to evidence_nodes') THEN
        CREATE POLICY "Allow all access to evidence_nodes" ON evidence_nodes FOR ALL USING (true) CHECK (true);
    END IF;
END $$;
