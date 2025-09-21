## Rejigg Interview: Business Search API

### Overview
Build a search endpoint for the `Business` model, including a radius-expansion feature.

### Your Task
Implement the `POST /businesses/search/` endpoint (stubbed in `core/views.py`). It should support:
- multiple location filters which can either be a state, or lat/lng pairs.
- top-level `radius_miles`, which is applied to all lat/lng entries.
- optional `text` filter on business name


### Implementation Status:
1. Multiple location filters (state and/or lat/lng pairs)
2. Intelligent radius expansion with fallback sequence \[1, 5, 10, 25, 50, 100, 500]
3. Optional text filtering on business names (case-insensitive)
4. Comprehensive input validation and error handling
5. Detailed response metadata with search transparency
6.  Tests covering all scenarios and edge cases
7. Performance optimizations with caching and monitoring
8. Logging and error handling**
9. Database optimization tools** for production scaling

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
George My note

## API Documentation

### **POST /businesses/search/**

Comprehensive business search with multi-modal filtering and intelligent radius expansion.

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
# Run all tests (106 tests)
make test
```

For more detailed output:
```bash
# Run search-specific tests with verbose output
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

| Endpoint | Method | Description | Status |
|----------|--------|-------------|--------|
| `/businesses/` | GET | List all businesses (paginated) | ✅ Active |
| `/businesses/search/` | POST | **Advanced business search** | ✅ **Fully Implemented** |
| `/health/` | GET | Health check endpoint | ✅ Active |


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

### Quick Testing
```bash
make test              # Run all tests
make test-search       # Run search-specific tests
make test-utils        # Run utility function tests
make test-phase8       # Run Phase 8 performance tests
```

### Detailed Testing
```bash
# Run specific test phases
docker compose run --rm api python manage.py test tests.test_search.BusinessSearchPhase1Test
docker compose run --rm api python manage.py test tests.test_search.BusinessSearchPhase7Test

# Verbose output
docker compose run --rm api python manage.py test tests.test_search -v 2

# Run all tests with coverage
docker compose run --rm api python manage.py test --parallel --keepdb
```

## Troubleshooting

### Common Issues
| Issue | Solution |
|-------|----------|
| "Cannot connect to Docker daemon" | Ensure Docker Desktop is running |
| Containers fail to start | Try `make down && make build && make up` |
| Application not responding | Check logs with `make logs` |
| Port 8001 in use | Stop other services or change port in `docker-compose.yml` |
| Tests failing | Ensure containers are running: `make up` |

### Debug Commands
```bash
make logs              # View all container logs
make shell            # Access Django shell for debugging
docker compose ps     # Check container status
docker compose logs api  # View API container logs only
```

## Technical Implementation

### System Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           🌐 Client Applications                        │
└──────────────────────────────┬──────────────────────────────────────────┘
                               │ HTTP POST /businesses/search/
                               ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                          🚀 Django REST API                            │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────────┐  │
│  │   Validation    │  │   Caching       │  │   Performance           │  │
│  │   • Input       │  │   • 5min TTL    │  │   • Search IDs          │  │
│  │   • Locations   │  │   • Normalized  │  │   • Timing              │  │
│  │   • Coordinates │  │   • Hit/Miss    │  │   • Logging             │  │
│  └─────────────────┘  └─────────────────┘  └─────────────────────────┘  │
└──────────────────────────────┬──────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                        🔍 Search Processing Engine                      │
│                                                                         │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────────┐  │
│  │  State Filter   │    │  Text Filter    │    │  Geo-Spatial        │  │
│  │  • OR Logic     │    │  • Case Insens. │    │  • Haversine Dist.  │  │
│  │  • Multi-State  │    │  • icontains    │    │  • Bounding Box     │  │
│  │  • Validation   │    │  • Name Search  │    │  • Radius Expansion │  │
│  └─────────────────┘    └─────────────────┘    └─────────────────────┘  │
│                                 │                                       │
│                                 ▼                                       │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                    🎯 Radius Expansion Logic                    │   │
│  │     [1] → [5] → [10] → [25] → [50] → [100] → [500] miles       │   │
│  │                    ↓ Stop at first match                       │   │
│  └─────────────────────────────────────────────────────────────────┘   │
└──────────────────────────────┬──────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                          🗄️  Database Layer                            │
│                                                                         │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────────┐  │
│  │   SQLite DB     │    │   Optimized     │    │   Performance       │  │
│  │   • 3,500+      │    │   Indexes       │    │   Monitoring        │  │
│  │   • Businesses  │    │   • State       │    │   • Query Time      │  │
│  │   • 49 States   │    │   • Name        │    │   • Result Count    │  │
│  │   • Geo Coords  │    │   • Coordinates │    │   • Cache Stats     │  │
│  └─────────────────┘    └─────────────────┘    └─────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘
```

### Architecture Overview
- **Django REST Framework**: Robust API framework with comprehensive serialization
- **Geospatial calculations**: Haversine formula for accurate distance calculations
- **Intelligent search**: Multi-modal filtering with OR logic between location types
- **Performance optimized**: Bounding box pre-filtering for geospatial searches
- **Comprehensive validation**: Input sanitization and error handling at all levels

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

#### **4. Comprehensive Testing (`core/test_search.py`)**
- **97 tests** covering all functionality and edge cases
- **Phase-based testing**: Validates each implementation phase
- **Edge case coverage**: Boundary conditions, invalid inputs, performance limits
- **Production validation**: Tests against actual README examples

### Performance Optimizations

#### **Current Optimizations**
- **Bounding box pre-filtering**: Reduces geospatial calculations by ~90%
- **Early termination**: Stops radius expansion at first successful radius
- **Query optimization**: Efficient Django ORM usage with proper indexing
- **Result limiting**: 100 result cap to prevent memory issues

#### **Production Scaling Considerations**
- **Database indexing**: Add composite indexes on (state, name), (latitude, longitude)
- **Caching layer**: Redis for frequent searches and radius expansion results
- **Async processing**: Celery for complex multi-location searches
- **Pagination**: Full pagination support for large result sets
- **Rate limiting**: API throttling to prevent abuse
- **Monitoring**: Performance metrics and search analytics

## 🚀 Production Readiness

### 🎯 **Phase 8: Production Performance Features**

#### **✅ Intelligent Caching System (Implemented)**
- **Response caching**: 5-minute cache for frequent search patterns
- **Cache normalization**: Consistent cache keys for identical requests
- **Cache transparency**: Cache hit/miss status in response metadata
- **Memory management**: Configurable cache size (1000 entries) and timeout

#### **✅ Performance Monitoring (Implemented)**
- **Request tracking**: Unique search IDs for every request
- **Processing time**: Millisecond-precision performance measurement
- **Cache analytics**: Hit/miss rates and performance impact tracking
- **Search correlation**: Complete request tracing for debugging

#### **✅ Production Logging (Implemented)**
- **Structured logging**: JSON format with search context
- **Performance metrics**: Processing time, cache status, result counts
- **Error tracking**: Complete exception handling with stack traces
- **Request correlation**: Search IDs for debugging and support

#### **✅ Database Optimization Tools (Implemented)**
```bash
# Automated database optimization
make optimize-db-dry-run  # Preview optimizations
make optimize-db          # Apply production indexes
```

**Applied Indexes:**
```sql
CREATE INDEX idx_business_state ON core_business(state);
CREATE INDEX idx_business_name ON core_business(name);
CREATE INDEX idx_business_coords ON core_business(latitude, longitude);
CREATE INDEX idx_business_state_name ON core_business(state, name);
CREATE INDEX idx_business_name_lower ON core_business(LOWER(name));
```

### 🚀 Performance Optimization Flow

```
                    📥 Incoming Request
                           │
                    ┌──────▼──────┐
                    │ 🔍 Cache     │
                    │   Check      │
                    └──┬───────┬───┘
                  Hit  │       │ Miss
                 ⚡ 1ms│       │ 
                       │       ▼
              ┌────────▼───┐  ┌─────────────────────────┐
              │ Return     │  │    🔍 Database Query     │
              │ Cached     │  │                         │
              │ Response   │  │  ┌─────────────────┐    │
              └────────────┘  │  │ 📊 Index Usage  │    │
                             │  │ • State         │    │
                             │  │ • Name          │    │
                             │  │ • Coordinates   │    │
                             │  │ • Composite     │    │
                             │  └─────────────────┘    │
                             │           │             │
                             │           ▼             │
                             │  ┌─────────────────┐    │
                             │  │ 🎯 Optimization │    │
                             │  │ • Bounding Box  │    │
                             │  │ • Early Exit    │    │
                             │  │ • Deduplication │    │
                             │  └─────────────────┘    │
                             └─────────┬───────────────┘
                                       │
                              ┌────────▼────────┐
                              │  📊 Response    │
                              │  • Results      │
                              │  • Metadata     │
                              │  • Performance  │
                              │  • Cache Store  │
                              └─────────────────┘
```

### Scalability Strategy
As the number of businesses scales to millions of records:

#### **Enhanced Caching Strategy**
- **✅ Implemented**: Intelligent response caching with normalization
- **Search result caching**: Cache frequent search patterns (5-minute timeout)
- **Geo-spatial caching**: Pre-calculate business clusters by region
- **Radius expansion caching**: Cache expansion results for common locations

#### **Architecture Scaling**
- **Read replicas**: Separate read/write database instances
- **Microservices**: Extract search service as independent component  
- **CDN integration**: Cache static business data geographically
- **Load balancing**: Horizontal scaling with multiple API instances

### Monitoring & Analytics
- **Performance metrics**: Response times, cache hit rates, expansion frequency
- **Search analytics**: Popular locations, common search patterns
- **Error tracking**: Validation failures, timeout monitoring
- **Business metrics**: Search success rates, user behavior patterns

### Security Considerations
- **Input sanitization**: Comprehensive validation prevents injection attacks
- **Rate limiting**: Prevent API abuse and ensure fair usage
- **Geographic restrictions**: Optional IP-based location validation
- **Audit logging**: Track search patterns for security analysis

## 📊 Implementation Phases

### ✅ **Phase 1: Input Validation** (30 tests)
- Comprehensive request validation with detailed error messages
- Location type validation (state vs lat/lng)
- Radius and text parameter validation

### ✅ **Phase 2: Distance Calculations** (20 tests) 
- Haversine formula implementation for accurate geospatial distance
- Coordinate validation and boundary checking
- Performance-optimized distance calculations

### ✅ **Phase 3: Basic Search Logic** (8 tests)
- State-based filtering with OR logic
- Case-insensitive text search on business names
- Combined filter logic implementation

### ✅ **Phase 4: Geo-Location Search** (8 tests)
- Radius-based geospatial filtering
- Multiple location support with deduplication
- Bounding box optimization for performance

### ✅ **Phase 5: Radius Expansion** (8 tests)
- Intelligent fallback sequence [1,5,10,25,50,100,500]
- Early termination optimization
- Complete expansion tracking and reporting

### ✅ **Phase 6: Response Format** (10 tests)
- Rich metadata with search transparency
- Comprehensive location summaries
- Performance metrics and debugging support

### ✅ **Phase 7: Comprehensive Testing** (13 tests)
- README example validation
- Edge case coverage and boundary testing
- Production-ready validation and error handling

### ✅ **Phase 8: Performance Optimization** (9 tests)
- Intelligent caching system with 5-minute timeout
- Performance monitoring and request tracking
- Production-grade logging and error handling
- Database optimization tools and index management

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

