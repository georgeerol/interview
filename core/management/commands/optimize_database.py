"""Django management command to optimize database for production performance.

Create indexes and optimize the database for business search operations.
Supports dry-run mode to preview changes before applying them.
"""

from django.core.management.base import BaseCommand
from django.db import connection
from django.conf import settings


class Command(BaseCommand):
    """Django management command to create production database indexes for business search."""
    
    help = 'Optimize database for production business search performance'

    def add_arguments(self, parser):
        """Add command line arguments."""
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be done without executing',
        )

    def handle(self, *args, **options):
        """Execute the database optimization command."""
        dry_run = options['dry_run']
        
        # Production database optimizations
        optimizations = [
            {
                'name': 'Business state index',
                'sql': 'CREATE INDEX IF NOT EXISTS idx_business_state ON core_business(state);',
                'description': 'Speeds up state-based filtering'
            },
            {
                'name': 'Business name index',
                'sql': 'CREATE INDEX IF NOT EXISTS idx_business_name ON core_business(name);',
                'description': 'Speeds up text search on business names'
            },
            {
                'name': 'Business coordinates index',
                'sql': 'CREATE INDEX IF NOT EXISTS idx_business_coords ON core_business(latitude, longitude);',
                'description': 'Speeds up geospatial bounding box queries'
            },
            {
                'name': 'Business state-name composite index',
                'sql': 'CREATE INDEX IF NOT EXISTS idx_business_state_name ON core_business(state, name);',
                'description': 'Speeds up combined state and text filtering'
            },
            {
                'name': 'Business name case-insensitive index',
                'sql': 'CREATE INDEX IF NOT EXISTS idx_business_name_lower ON core_business(LOWER(name));',
                'description': 'Speeds up case-insensitive text search'
            }
        ]
        
        self.stdout.write(
            self.style.SUCCESS('Database Optimization for Business Search API')
        )
        self.stdout.write('=' * 60)
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING('DRY RUN MODE - No changes will be made')
            )
            
        for optimization in optimizations:
            self.stdout.write(f"\n{optimization['name']}")
            self.stdout.write(f"   Description: {optimization['description']}")
            self.stdout.write(f"   SQL: {optimization['sql']}")
            
            if not dry_run:
                try:
                    with connection.cursor() as cursor:
                        cursor.execute(optimization['sql'])
                    self.stdout.write(
                        self.style.SUCCESS('   Applied successfully')
                    )
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f'   Failed: {e}')
                    )
            else:
                self.stdout.write(
                    self.style.WARNING('   Would be applied (dry run)')
                )
        
        # Database statistics
        self.stdout.write('\n' + '=' * 60)
        self.stdout.write('Database Statistics:')
        
        try:
            with connection.cursor() as cursor:
                cursor.execute('SELECT COUNT(*) FROM core_business;')
                business_count = cursor.fetchone()[0]
                
                cursor.execute('SELECT COUNT(DISTINCT state) FROM core_business;')
                state_count = cursor.fetchone()[0]
                
                self.stdout.write(f"   Total businesses: {business_count:,}")
                self.stdout.write(f"   States covered: {state_count}")
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'   Could not retrieve statistics: {e}')
            )
        
        # Performance recommendations
        self.stdout.write('\n' + '=' * 60)
        self.stdout.write('Additional Production Recommendations:')
        
        recommendations = [
            "Enable query logging to monitor slow queries",
            "Consider PostgreSQL with PostGIS for advanced geospatial features",
            "Implement Redis caching for frequent search patterns",
            "Add database connection pooling for high concurrency",
            "Monitor cache hit rates and adjust cache timeout accordingly",
            "Consider read replicas for scaling read operations",
            "Implement API rate limiting to prevent abuse",
            "Add monitoring and alerting for search performance metrics"
        ]
        
        for i, rec in enumerate(recommendations, 1):
            self.stdout.write(f"   {i}. {rec}")
        
        self.stdout.write('\n' + '=' * 60)
        if dry_run:
            self.stdout.write(
                self.style.SUCCESS('Dry run completed. Use --dry-run=false to apply changes.')
            )
        else:
            self.stdout.write(
                self.style.SUCCESS('Database optimization completed!')
            )
