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

----
# George Interview Response: Business Search API

| # | Implementation Item                                                               | Status |
| - | --------------------------------------------------------------------------------- | ------ |
| 1 | Multiple location filters (state and/or lat/lng pairs)                            | Done   |
| 2 | Intelligent radius expansion with fallback sequence \[1, 5, 10, 25, 50, 100, 500] | Done   |
| 3 | Optional text filtering on business names (case-insensitive)                      | Done   |
| 4 | Comprehensive input validation and error handling                                 | Done   |
| 5 | Detailed response metadata with search transparency                               | Done   |
| 6 | Comprehensive testing with unit + integration architecture (215 tests)            | Done   |
| 7 | Performance optimizations with caching and monitoring                             | Done   |
| 8 | Logging and error handling                                                        | Done   |
| 9 | Database optimization tools for production scaling                                | Done   |


## System Architecture

![Business Search API Architecture](imgs/BusinessSearchAPI.png)

### Key Components

#### **1. Input Validation (`core/serializers.py`)**
- **LocationSerializer**: Validates individual location objects (state OR lat/lng)
- **BusinessSearchRequestSerializer**: Validates complete search payload
- **Conditional validation**: Different rules for state vs geo locations
- **Error handling**: Detailed error messages for debugging

#### **2. Geospatial Engine (`core/utils.py`)**
- **Haversine distance**: Accurate earth-surface distance calculations
- **Bounding box optimization**: Pre-filter by rectangular bounds for performance
- **Radius expansion**: Intelligent fallback through [1,5,10,25,50,100,500] sequence
- **Multi-location support**: Handles multiple geo points with deduplication

#### **3. Search Logic (`core/views.py`)**
- **Multi-modal filtering**: Combines state, geo, and text filters
- **OR logic**: Results from any matching filter type
- **Performance limits**: 100 result limit with pagination support
- **Rich metadata**: Complete search transparency and debugging info

#### **4. Comprehensive Testing (Unit + Integration Architecture)**
- **215 tests** covering all functionality and edge cases (`tests/`)
- **Unit tests (69)**: Individual component validation in isolation (`tests/unit/`)
- **Integration tests (60)**: Complete API workflow validation (`tests/integration/`)
- **Legacy tests (86)**: Original phase-based comprehensive suite (`tests/test_search.py`)
- **Edge case coverage**: Boundary conditions, invalid inputs, performance limits
- **Production validation**: Tests against actual README examples

## API Documentation

### **POST /businesses/search/**

Business search with multi-modal filtering and intelligent radius expansion.

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


### **Example 1: Multi-Filter Search**

**Request:**
```bash
curl -X POST http://localhost:8001/businesses/search/ \
  -H "Content-Type: application/json" \
  -d '{
    "locations": [
      { "state": "CA" },
      { "state": "NY" },
      { "lat": 34.052235, "lng": -118.243683 }
    ],
    "radius_miles": 50,
    "text": "coffee"
  }'
```

**Response:** Returns all businesses containing "coffee" within CA state, NY state, OR within 50 miles of Los Angeles coordinates.

### **Example 2: Radius Expansion**

**Request:**
```bash
curl -X POST http://localhost:8001/businesses/search/ \
  -H "Content-Type: application/json" \
  -d '{
    "locations": [{ "lat": 37.9290, "lng": -116.7510 }],
    "radius_miles": 5
  }'
```

**Response:** Demonstrates automatic radius expansion from 5 → 10 → 25 → 50 → 100 → 500 miles until businesses are found in the Nevada desert location.

## Getting Started

### Prerequisites
- **Docker Desktop** must be installed and running
- **curl** or **Postman** for API testing (optional)

### Quick Start
```bash
# 1. Build and start the application
make build && make up

# 2. Verify it's working
make health

# 3. Test the search API
curl -X POST http://localhost:8001/businesses/search/ \
  -H "Content-Type: application/json" \
  -d '{"locations": [{"state": "CA"}], "text": "coffee"}'
```

## **Step-by-Step Setup Guide**

### **Step 1: Start the Application**

First, let's build and start the Docker containers:

```bash
# Build the Docker containers
make build

# Start the application in detached mode
make up
```

If you don't have `make`, you can use the Docker commands directly:
```bash
docker compose build
docker compose up -d
```

### **Step 2: Health Check**

Let's verify the application is running:

```bash
make health
```

Or manually:
```bash
curl -fsS http://localhost:8001/health/
```

You should see: `{"status": "ok"}`

### **Step 3: Database Setup**

Make sure the database is migrated and seeded with business data:

```bash
make migrate
```

Or:
```bash
docker compose run --rm api python manage.py migrate --noinput
```

### **Step 4: Run Tests**

Let's run the comprehensive test suite to verify everything works:

```bash
# Run all tests (215 tests)
make test

# Or run fast unit + integration tests (129 tests in ~0.08s)
make test-fast
```

For more detailed output:
```bash
# Run unit tests for fast feedback (69 tests in ~0.04s)
make test-unit

# Run integration tests for API validation (60 tests)
make test-integration

# Run legacy comprehensive test suite with verbose output
make test-search
```

### **Step 5: Test the API Endpoints**

#### **Test 1: Basic Health Check**
```bash
curl http://localhost:8001/health/
```

#### **Test 2: List Businesses**
```bash
curl http://localhost:8001/businesses/
```

#### **Test 3: Search by State**
```bash
curl -X POST http://localhost:8001/businesses/search/ \
  -H "Content-Type: application/json" \
  -d '{
    "locations": [{"state": "CA"}],
    "text": "coffee"
  }'
```

#### **Test 4: Geospatial Search with Radius**
```bash
curl -X POST http://localhost:8001/businesses/search/ \
  -H "Content-Type: application/json" \
  -d '{
    "locations": [{"lat": 34.052235, "lng": -118.243683}],
    "radius_miles": 50
  }'
```

#### **Test 5: Multi-Location Search (README Example)**
```bash
curl -X POST http://localhost:8001/businesses/search/ \
  -H "Content-Type: application/json" \
  -d '{
    "locations": [
      {"state": "CA"},
      {"state": "NY"},
      {"lat": 34.052235, "lng": -118.243683}
    ],
    "radius_miles": 50,
    "text": "coffee"
  }'
```

### **Step 6: Check Logs**

If anything isn't working, check the logs:

```bash
make logs
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
make test-phase8          # Run Phase 8 performance tests
```

## Testing


###  **Quick Testing Commands**

```bash
# Fast development feedback (unit tests only)
make test-unit                     

# Full API validation (integration tests)
make test-integration              

# Combined fast testing (recommended for CI/CD)
make test-fast                     

# Complete test suite
make test                          # All tests
```

### **Test Organization**

#### **Unit Tests** (`tests/unit/`)
```bash
make test-serializers              # Input validation
make test-distance                 # Geospatial calculations
make test-utils                    # Utility functions
```

#### **Integration Tests** (`tests/integration/` - 60 tests)
```bash
make test-api-validation          # API input validation
make test-search-logic            # Search endpoints
make test-advanced                # Advanced features
make test-production              # Production workflows
```

### **Detailed Testing**
```bash
# Run specific test files with verbose output
docker compose run --rm api python manage.py test tests.unit.test_serializers -v 2
docker compose run --rm api python manage.py test tests.integration.test_search_logic -v 2

# Legacy phase-based testing (maintained for compatibility)
make test-search                   # Original comprehensive test suite
make test-phase8                   # Phase 8 performance tests

# Parallel execution for faster CI/CD
docker compose run --rm api python manage.py test tests.unit tests.integration --parallel
```


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
make shell            # Access Django shell for debugging
docker compose ps     # Check container status
docker compose logs api  # View API container logs only
```


##  **Future Enhancements**

*The following improvements would be considered for a production system at scale:*

### **🏗️ Architecture & Design Patterns**
- **SOLID Principles Implementation**
  - Extract `SearchService` class for business logic (Single Responsibility)
  - Implement Repository pattern for data access abstraction (Dependency Inversion)
  - Create Strategy pattern for different search types (Open/Closed Principle)
  - Add dependency injection container for better testability

### **🔧 Advanced Features**
- **Search Enhancements**
  - Fuzzy text matching with similarity scoring
  - Auto-complete/suggestions for business names
  - Search result ranking and relevance scoring
  - Saved searches and search history
  
- **Performance & Scalability**
  - Redis caching layer for distributed systems
  - Elasticsearch integration for advanced text search
  - Database read replicas and connection pooling
  - API rate limiting and request throttling
  
- **Monitoring & Observability**
  - Distributed tracing with OpenTelemetry
  - Metrics dashboard (Grafana/Prometheus)
  - Real-time alerting for performance degradation
  - A/B testing framework for search algorithms

### **🛡️ Production Hardening**
- **Security**
  - API authentication and authorization
  - Input sanitization and SQL injection prevention
  - CORS configuration and security headers
  
- **DevOps & Infrastructure**
  - CI/CD pipeline with automated testing
  - Blue-green deployment strategy
  - Infrastructure as Code (Terraform/CloudFormation)
  - Container orchestration (Kubernetes)

### **📊 Business Intelligence**
- Search analytics and user behavior tracking
- Business discovery insights and recommendations
- Geographic search pattern analysis
- Performance benchmarking and optimization reports

*These enhancements would be prioritized based on business requirements, user feedback, and system load characteristics.*

---

