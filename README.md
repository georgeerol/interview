# Rejigg Interview: Business Search API

### Overview
Build a search endpoint for the `Business` model, including a radius-expansion feature.

### Your Task
Implement the `POST /businesses/search/` endpoint (stubbed in `core/views.py`). It should support:
- multiple location filters which can either be a state, or lat/lng pairs.
- top-level `radius_miles`, which is applied to all lat/lng entries.
- optional `text` filter on business name

### Requirements
- Users can search by (lat/lng + radius) and/or (state). If multiple lat/lng pairs are used, apply a single radius to all lat/lng pairs.
- Radius expansion and fallback:
  - If no results are found within the provided `radius_miles`, expand the radius incrementally to [1, 5, 10, 25, 50, 100, 500], in order, until matches are found; if there are still no matches at max radius, return an empty result.  Your response should also communicate back to the client how the search was expanded so it can be explained to the user.

### Assumptions
- Inputs are well-formed:
  - no address geocoding is required
  - lat/lng coordinates will be provided for geo queries
- Only US cities/states need to be considered
- You don't need to handle auth

### Examples

**Input 1**:

_(You can change the shape of the input payload if you'd like)_

```json
{
  "locations": [
    { "state": "CA" },
    { "state": "NY" },
    { "lat": 34.052235, "lng": -118.243683 }
  ],
  "radius_miles": 50,
  "text": "coffee"
}
```

**Output 1**:

All businesses containing "coffee" within the states of, NY, CA, or within 50 miles of lat 34.052235, lng: -118.243683

**Input 2**

```json
{
    "locations": [
        { "lat": 37.9290, "lng": -116.7510 }
    ],
    "radius_miles": 5
}
```

**Output 2**:

There are no businesses within 5 miles of this point, so we should expand the search radius 5->10->25->50->100->500 until a match is found.  The response should also explain the radius at which a match was found.


**Example GEO Search UI (illustrative only; you don't need to implement this)**

![GEO search UI example](example_ui.png)

### Getting Started
- Build and start:
  - `make build && make up`
- Apply migrations:
  - `make migrate`
- Access the site:
  - macOS: `open http://localhost:8001`
  - Linux: `xdg-open http://localhost:8001`
  - Windows (PowerShell): `start http://localhost:8001`
- Health check:
  - `make health` (hits `http://localhost:8001/health/`)

### Submission

- Email your submisson to `barrett@rejigg.com`.  It should include:
  - A link to a repository with your code (or you can include it as an attachment if you prefer)
  - Include brief notes or comments if you made tradeoffs or assumptions (as if you were writing a pull request).
  - Discuss how you would productionize your submission (including how you would think about performance as the number of businesses scales)

---

# Implementation Response: Business Search API

## 📋 Quick Overview

| Component | Description | Status |
|-----------|-------------|--------|
| **API Endpoint** | `POST /businesses/search/` | Complete |
| **Multi-Modal Search** | State + Geo + Text filtering | Complete |
| **Radius Expansion** | Auto-expand [1,5,10,25,50,100,500] | Complete |
| **Performance** | Caching + Monitoring + Optimization | Complete |
| **Testing** | 158 tests (98 unit + 60 integration) | Complete |
| **Database** | 500 businesses across 49 US states | Complete |

## Implementation Summary

| # | Implementation Item | Status |
| - | ------------------ | ------ |
| 1 | Multiple location filters (state and/or lat/lng pairs) | Done |
| 2 | Intelligent radius expansion with fallback sequence [1, 5, 10, 25, 50, 100, 500] | Done |
| 3 | Optional text filtering on business names (case-insensitive) | Done |
| 4 | Comprehensive input validation and error handling | Done |
| 5 | Detailed response metadata with search transparency | Done |
| 6 | Comprehensive testing with unit + integration architecture (158 tests) | Done |
| 7 | Performance optimizations with caching and monitoring | Done |
| 8 | Logging and error handling | Done |
| 9 | Database optimization tools for production scaling | Done |


## System Architecture

![Business Search API Architecture](imgs/BusinessSearchAPI.png)
Excalidraw: [Business Search API Architecture](imgs/SearchFlowArchitecture.excalidraw)

### Search Flow Architecture

![Search Flow Architecture](imgs/SearchFlowArchitecture.png)
Excalidraw: [Search Flow Architecture](imgs/SearchFlowArchitecture.excalidraw)

### Radius Expansion Logic

![Radius Expansion Logic](imgs/RadiusExpansionLogic.png)
Excalidraw: [Radius Expansion Logic](imgs/RadiusExpansionLogic.excalidraw)


### Key Components

#### **1. Input Validation (`core/api/serializers.py`)**
- **LocationSerializer**: Validates individual location objects (state OR lat/lng)
- **BusinessSearchRequestSerializer**: Validates complete search payload
- **Conditional validation**: Different rules for state vs geo locations
- **Error handling**: Detailed error messages for debugging

#### **2. Geospatial Engine (`core/infrastructure/utils.py`)**
- **Haversine distance**: Accurate earth-surface distance calculations
- **Bounding box optimization**: Pre-filter by rectangular bounds for performance
- **Radius expansion**: Intelligent fallback through [1,5,10,25,50,100,500] sequence
- **Multi-location support**: Handles multiple geo points with deduplication

#### **3. Search Logic (`core/api/views.py`)**
- **Multi-modal filtering**: Combines state, geo, and text filters
- **OR logic**: Results from any matching filter type
- **Performance limits**: 100 result limit with pagination support
- **Rich metadata**: Complete search transparency and debugging info

#### **4. Comprehensive Testing (Unit + Integration Architecture)**
- **158 tests** covering all functionality and edge cases (`tests/`)
- **Unit tests (98)**: Individual component validation in isolation (`tests/unit/`)
- **Integration tests (60)**: Complete API workflow validation (`tests/integration/`)
- **Edge case coverage**: Boundary conditions, invalid inputs, performance limits
- **Production validation**: Tests against actual README examples

## API Documentation

### **POST /businesses/search/**

Business search with multi-modal filtering and intelligent radius expansion.

#### **Search Types**

| Type | Example | Logic |
|------|---------|-------|
| **State** | `{"state": "CA"}` | Filter by US state code |
| **Geo** | `{"lat": 34.05, "lng": -118.24}` | Haversine distance + radius |
| **Text** | `"text": "coffee"` | Case-insensitive name search |
| **Combined** | State + Geo + Text | **OR logic** between location types |

#### **Request Format**

```json
{
  "locations": [
    { "state": "CA" },
    { "state": "NY" },
    { "lat": 34.052235, "lng": -118.243683 }
  ],
  "radius_miles": 50,
  "text": "coffee"
}
```

#### **Request Parameters**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `locations` | Array | Yes      | Array of location filters (1-20 items) |
| `locations[].state` | String | Cond*    | US state code (e.g., "CA", "NY") |
| `locations[].lat` | Number | Cond*    | Latitude (-90 to 90) |
| `locations[].lng` | Number | Cond*    | Longitude (-180 to 180) |
| `radius_miles` | Number | Optional | Radius in miles (0.1-1000, default: 50 for geo searches) |
| `text` | String | Optional | Case-insensitive business name filter |

*Conditional(Cond): Each location must have either `state` OR `lat`+`lng`, not both.

#### **Response Format**

```json
{
  "results": [
    {
      "id": 18,
      "name": "Acme Coffee & Co",
      "city": "Los Angeles", 
      "state": "CA",
      "latitude": "34.052235",
      "longitude": "-118.243683"
    }
  ],
  "search_metadata": {
    "total_count": 11,
    "total_found": 12,
    "radius_used": 50.0,
    "radius_expanded": false,
    "radius_requested": 50.0,
    "radius_expansion_sequence": [50.0],
    "filters_applied": ["text", "state", "geo"],
    "search_locations": [
      {"type": "state", "state": "CA"},
      {"type": "state", "state": "NY"},
      {"type": "geo", "lat": 34.052235, "lng": -118.243683}
    ],
    "performance": {
      "processing_time_ms": 12.34,
      "search_id": "search_1758307715935",
      "cached": false
    },
    "cache_key": "business_search:a1b2c3d4e5f6..."
  }
}
```

#### **Response Metadata Fields**

| Field | Type | Description |
|-------|------|-------------|
| `total_count` | Integer | Number of businesses returned (≤100) |
| `total_found` | Integer | Total businesses found before pagination |
| `radius_used` | Number | Actual radius used in miles |
| `radius_expanded` | Boolean | Whether radius was expanded from request |
| `radius_requested` | Number | Originally requested radius (geo searches only) |
| `radius_expansion_sequence` | Array | All radii tried during expansion |
| `filters_applied` | Array | List of filters used: `["text", "state", "geo"]` |
| `search_locations` | Array | Summary of all search locations by type |
| `performance` | Object | Performance metrics and monitoring |
| `performance.processing_time_ms` | Number | Request processing time in milliseconds |
| `performance.search_id` | String | Unique identifier for request tracking |
| `performance.cached` | Boolean | Whether response was served from cache |
| `cache_key` | String | Cache key for debugging (when cached) |


### **API Examples**

See the original requirements section above for detailed input/output examples.

## Getting Started

### Prerequisites
- **Docker Desktop** must be installed and running
- **curl** or **Postman** for API testing (optional)

### Quick Start
```bash
# 1. Build and start the application
make build && make up

# 2. Apply database migrations
make migrate

# 3. Verify it's working
make health

# 4. Test the search API
curl -X POST http://localhost:8001/businesses/search/ \
  -H "Content-Type: application/json" \
  -d '{"locations": [{"state": "CA"}], "text": "coffee"}'
```

### API Testing Examples
```bash
# Health check
curl http://localhost:8001/health/

# List all businesses
curl http://localhost:8001/businesses/

# Search by state
curl -X POST http://localhost:8001/businesses/search/ \
  -H "Content-Type: application/json" \
  -d '{"locations": [{"state": "CA"}], "text": "coffee"}'

# Geospatial search with radius
curl -X POST http://localhost:8001/businesses/search/ \
  -H "Content-Type: application/json" \
  -d '{"locations": [{"lat": 34.052235, "lng": -118.243683}], "radius_miles": 50}'
```

### Available Endpoints

| Endpoint              | Method | Description                     |
| --------------------- | ------ | ------------------------------- |
| `/businesses/`        | GET    | List all businesses (paginated) |
| `/businesses/search/` | POST   | **Advanced business search**    |
| `/health/`            | GET    | Health check endpoint           |

## Development Commands

### Essential Commands
```bash
make build          # Build Docker containers
make up            # Start all services  
make down          # Stop all services
make health        # Check application health
make logs          # View container logs
```

### Database Commands
```bash
make migrate           # Apply database migrations
make makemigrations   # Create new migrations
```

###  Production Commands 
```bash
make optimize-db          # Apply database optimizations for production
make optimize-db-dry-run  # Preview database optimizations (safe)
make test-performance     # Run performance optimization tests
```

## Testing

### **Test Commands**
```bash
make test              # Run all 158 tests
make test-fast         # Run unit + integration tests (recommended)
make test-unit         # Run unit tests only (fast feedback)
make test-integration  # Run integration tests only
```

### **Test Architecture**
- **158 total tests** across unit and integration suites
- **Unit tests (98):** Serializers, distance calculations, utilities
- **Integration tests (60):** API validation, search logic, production features
- **Coverage:** All functionality, edge cases, and production scenarios


## Troubleshooting

### Common Issues
| Issue | Solution |
|-------|----------|
| "Cannot connect to Docker daemon" | Ensure Docker Desktop is running |
| Containers fail to start | Try `make down && make build && make up` |
| Application not responding | Check logs with `make logs` |
| Port 8001 in use | Stop other services or change port in `docker-compose.yml` |
| Tests failing | Ensure containers are running: `make up`. Try `make test-unit` for fast feedback |

### Debug Commands
```bash
make logs              # View all container logs
docker compose ps     # Check container status
docker compose logs api  # View API container logs only
```



## Technical Decisions & Trade-offs

### Key Architectural Decisions

| Decision | Approach                                                        | Pros | Cons                                                   | Rationale                          |
|----------|-----------------------------------------------------------------|------|--------------------------------------------------------|------------------------------------|
| **Architecture** | Layered architecture with dependency injection                  | Testable, maintainable, follows SOLID principles | More complex than single-file solution                 | Modular, maintainable and scalable |
| **Geospatial** | Custom Haversine distance calculation                           | No external dependencies, works with SQLite| Less efficient than database-native geospatial queries | Keeps setup simple                 |
| **Validation** | Detailed serializer input validation with custom error messages | Robust error handling, clear user feedback | More code than basic validation. Can use a library     | Good Validation                    |
| **Caching** | In-memory Django cache (5min TTL)                               | Simple setup, immediate performance boost | Doesn't scale across servers                           | Project Simplicity                 |


### Production Scaling Strategy

#### Current State vs Production Target
| Aspect | Current                | Production Target                   |
|--------|------------------------|-------------------------------------|
| **Database** | SQLite (500 records)   | PostgreSQL + PostGIS (10M+ records) |
| **Caching** | In-memory (1K entries) | Redis Cluster                       |
| **Performance** | ~12ms response         | <50ms at scale                      |
| **Capacity** | Hundreds req/sec       | 1000+ req/sec                       |

#### Next Steps
1. **PostgreSQL + PostGIS** for native geospatial support
2. **Redis Cluster** for distributed caching
3. **Elasticsearch** for advanced text search
4. **Kubernetes** for container orchestration
5. **Monitoring** with Grafana/Prometheus
6.  **Read replicas:** Separate read/write operations

### Performance Optimization Strategy

| What We're Optimizing | What We Do Now (Simple) | What We'd Do in Production (Advanced) |
|----------------------|--------------------------|---------------------------------------|
| **Geospatial** | Calculate exact distance for all businesses using Haversine formula | Use PostgreSQL's built-in geospatial features that are much faster than custom calculations |
| **Search Logic** | Stop radius expansion as soon as we find any businesses | Handle complex searches in background so users don't wait |
| **Result Management** | Never return more than 100 businesses to avoid overwhelming user/system | Cache common search results so we don't recalculate them every time |
| **Caching** | Store search results in memory for 5 minutes for instant repeated searches | Use shared cache system that works across multiple servers |
| **Database** | Use Django's built-in database tools efficiently | Use advanced database features like connection pools and query optimization |

### Security & Monitoring

| Security Area | Current Implementation | Production Enhancement |
|---------------|------------------------|------------------------|
| **Input Protection** | Comprehensive parameter validation | JWT tokens with rate limiting |
| **Data Security** | Django ORM parameterized queries prevent SQL injection | HTTPS enforcement with TLS 1.3 certificates |
| **Performance Tracking** | Assign unique IDs to each search request and measure how long they take | APM, metrics dashboards, alerting |


### Alternative Approaches Considered

| Alternative | What We Considered | Pros | Cons | Why We Didn't Choose It                                |
|-------------|-------------------|------|------|--------------------------------------------------------|
| **Geospatial Services** | Google Maps API, Mapbox for distance calculations | More accurate, handles edge cases | External dependencies, API costs | Simple Custom implementation  |
| **NoSQL Database** | MongoDB with geospatial indexes | Native geospatial support, horizontal scaling | Different from existing Django setup | Stayed with relational model for consistency           |
| **GraphQL API** | GraphQL instead of REST | Flexible queries, better for complex data fetching | More complex setup, learning curve | REST is simpler and meets requirements                 |

### What I'd Do Differently

#### With More Time
| Feature | Description |
|---------|-------------|
| API Versioning | Implement v1/ prefix for future compatibility |
| Rate Limiting | Add request throttling per client |
| Authentication | JWT-based API authentication |
| Pagination | Full pagination for large result sets |

#### With Different Requirements
| Feature | Description |
|---------|-------------|
| Real-time Updates | WebSocket for live business updates |
| Analytics | Search pattern analysis and recommendations |
| Mobile Optimization | Simplified response format for mobile apps |

#### Advanced Features for Enterprise Scale

##### Search Enhancements
| Feature | Description |
|---------|-------------|
| Auto-complete | Suggestions for business names |
| Search Ranking | Result ranking and relevance scoring |
| Saved Searches | Search history and saved queries |

##### Monitoring & Observability
| Feature | Description |
|---------|-------------|
| Distributed Tracing | OpenTelemetry for request tracking |
| Metrics Dashboard | Grafana/Prometheus monitoring |
| Real-time Alerting | Performance degradation alerts |
| A/B Testing | Framework for search algorithm testing |

##### DevOps & Infrastructure
| Feature | Description |
|---------|-------------|
| CI/CD Pipeline | Automated testing and deployment |
| Container Orchestration | Kubernetes deployment |

---

