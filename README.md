## Rejigg Interview: Business Search API

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
