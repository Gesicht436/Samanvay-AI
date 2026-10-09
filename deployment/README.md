# Deployment

Start local infrastructure with:

```powershell
docker compose -f deployment/docker-compose.yml up -d
```

The compose file provides Qdrant, Neo4j, and PostgreSQL. The API and frontend can run from source during development or be containerized independently.