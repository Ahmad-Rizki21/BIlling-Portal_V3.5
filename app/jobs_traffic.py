# ====================================================================
# TRAFFIC MONITORING JOBS - AUTOMATED DATA COLLECTION
# ====================================================================
# File ini berisi job-job terjadwal untuk traffic monitoring system.
# Menggunakan APScheduler untuk menjalankan task secara periodik.
#
# Jobs yang tersedia:
# - job_collect_traffic_data: Collect traffic data dari semua Mikrotik servers
# - job_cleanup_old_traffic_data: Clean up old traffic data
# - job_generate_traffic_reports: Generate daily/weekly traffic reports
#
# Schedule:
# - Traffic collection: Setiap 5 menit
# - Data cleanup: Setiap hari jam 2 pagi
# - Report generation: Setiap hari jam 1 pagi
# ====================================================================

import logging
from datetime import datetime, timezone, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from contextlib import asynccontextmanager

from .database import AsyncSessionLocal
from .services.traffic_monitoring_service import traffic_monitoring_service

@asynccontextmanager
async def get_async_db():
    async with AsyncSessionLocal() as session:
        yield session

logger = logging.getLogger(__name__)


async def job_collect_traffic_data():
    """
    Job terjadwal untuk mengumpulkan traffic data dari semua Mikrotik servers.
    Dijalankan setiap 5 menit untuk data real-time.
    """
    job_name = "Traffic Data Collection"
    start_time = datetime.now(timezone.utc)

    logger.info(f"=== {job_name} Started at {start_time} ===")

    async with get_async_db() as db:
        try:
            # Collect traffic data dari semua servers
            result = await traffic_monitoring_service.collect_traffic_data(db)

            # Log results
            end_time = datetime.now(timezone.utc)
            duration = (end_time - start_time).total_seconds()

            logger.info(f"✅ {job_name} Completed in {duration:.2f}s")
            logger.info(f"📊 Collection Summary:")
            logger.info(f"   - Servers processed: {result.get('servers_processed', 0)}")
            logger.info(f"   - Total users: {result.get('total_users', 0)}")
            logger.info(f"   - Errors: {len(result.get('errors', []))}")

            if result.get('errors'):
                logger.warning(f"⚠️ Collection errors occurred:")
                for error in result.get('errors', []):
                    logger.warning(f"   - {error}")

        except Exception as e:
            logger.error(f"❌ {job_name} Failed: {str(e)}")
            logger.error(f"Error details:", exc_info=True)


async def job_cleanup_old_traffic_data():
    """
    Job terjadwal untuk membersihkan traffic data yang sudah lama.
    Dijalankan setiap hari jam 2 pagi untuk maintain database performance.
    """
    job_name = "Traffic Data Cleanup"
    start_time = datetime.now(timezone.utc)

    logger.info(f"=== {job_name} Started at {start_time} ===")

    async with get_async_db() as db:
        try:
            # Cleanup old data using service
            retention_days = traffic_monitoring_service.retention_days
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=retention_days)

            # Query old records
            from .models.traffic_history import TrafficHistory
            from sqlalchemy import select

            query = select(TrafficHistory).where(TrafficHistory.timestamp < cutoff_date)
            result = await db.execute(query)
            old_records = result.scalars().all()

            # Delete old records
            deleted_count = 0
            for record in old_records:
                await db.delete(record)
                deleted_count += 1

            await db.commit()

            # Log results
            end_time = datetime.now(timezone.utc)
            duration = (end_time - start_time).total_seconds()

            logger.info(f"✅ {job_name} Completed in {duration:.2f}s")
            logger.info(f"🗑️ Deleted {deleted_count} old traffic records (older than {cutoff_date})")

        except Exception as e:
            logger.error(f"❌ {job_name} Failed: {str(e)}")
            logger.error(f"Error details:", exc_info=True)


async def job_generate_traffic_reports():
    """
    Job terjadwal untuk generate traffic reports.
    Dijalankan setiap hari jam 1 pagi untuk daily reports.
    """
    job_name = "Traffic Reports Generation"
    start_time = datetime.now(timezone.utc)

    logger.info(f"=== {job_name} Started at {start_time} ===")

    async with get_async_db() as db:
        try:
            # Generate daily traffic summary
            yesterday = datetime.now(timezone.utc) - timedelta(days=1)
            start_of_day = yesterday.replace(hour=0, minute=0, second=0, microsecond=0)
            end_of_day = yesterday.replace(hour=23, minute=59, second=59, microsecond=999999)

            # Get traffic statistics for yesterday
            stats = await traffic_monitoring_service.get_server_traffic_summary(
                db,
                hours=24
            )

            # Log summary
            total_users = sum(row.get('active_users', 0) for row in stats) if stats else 0
            total_bandwidth = sum(row.get('total_mbps', 0) for row in stats) if stats else 0

            logger.info(f"📈 Daily Traffic Report for {yesterday.date()}:")
            logger.info(f"   - Active servers: {len(stats) if stats else 0}")
            logger.info(f"   - Total active users: {total_users}")
            logger.info(f"   - Total bandwidth usage: {total_bandwidth:.2f} Mbps")

            if stats:
                logger.info(f"   - Top performing server:")
                top_server = max(stats, key=lambda x: x.get('total_mbps', 0)) if stats else None
                if top_server:
                    logger.info(f"     * {top_server.get('server_name', 'Unknown')}: {top_server.get('total_mbps', 0):.2f} Mbps ({top_server.get('active_users', 0)} users)")

            # TODO: Save reports to database or send notifications

            # Log completion
            end_time = datetime.now(timezone.utc)
            duration = (end_time - start_time).total_seconds()

            logger.info(f"✅ {job_name} Completed in {duration:.2f}s")

        except Exception as e:
            logger.error(f"❌ {job_name} Failed: {str(e)}")
            logger.error(f"Error details:", exc_info=True)


async def job_health_check_traffic_monitoring():
    """
    Job untuk health check traffic monitoring system.
    Memeriksa apakah collection masih berjalan normal.
    """
    job_name = "Traffic Monitoring Health Check"
    start_time = datetime.now(timezone.utc)

    logger.info(f"=== {job_name} Started at {start_time} ===")

    async with get_async_db() as db:
        try:
            # Check latest collection time
            from .models.traffic_history import TrafficHistory
            from sqlalchemy import select, desc

            query = select(TrafficHistory).order_by(desc(TrafficHistory.timestamp)).limit(1)
            result = await db.execute(query)
            latest_record = result.scalar_one_or_none()

            if latest_record:
                time_diff = datetime.now(timezone.utc) - latest_record.timestamp

                if time_diff.total_seconds() > 600:  # 10 minutes
                    logger.warning(f"⚠️ Traffic data is stale! Latest: {latest_record.timestamp} ({time_diff.total_seconds():.0f}s ago)")

                    # TODO: Send alert notification
                else:
                    logger.info(f"✅ Traffic data is fresh. Latest: {latest_record.timestamp} ({time_diff.total_seconds():.0f}s ago)")

                # Check active servers status
                server_stats = await traffic_monitoring_service.get_server_traffic_summary(db, hours=1)

                if server_stats:
                    active_servers = len(server_stats)
                    total_users = sum(server.get('active_users', 0) for server in server_stats)

                    logger.info(f"📊 System Status (last hour):")
                    logger.info(f"   - Active servers: {active_servers}")
                    logger.info(f"   - Active users: {total_users}")

                    # Check for inactive servers
                    for server in server_stats:
                        if server.get('active_users', 0) == 0:
                            logger.warning(f"⚠️ Server {server.get('server_name', 'Unknown')} has no active users")
                else:
                    logger.warning("⚠️ No server statistics available")

            else:
                logger.error("❌ No traffic data found! System may not be collecting data.")
                # TODO: Send critical alert

            # Log completion
            end_time = datetime.now(timezone.utc)
            duration = (end_time - start_time).total_seconds()

            logger.info(f"✅ {job_name} Completed in {duration:.2f}s")

        except Exception as e:
            logger.error(f"❌ {job_name} Failed: {str(e)}")
            logger.error(f"Error details:", exc_info=True)


# ====================================================================
# SCHEDULER CONFIGURATION
# ====================================================================

def setup_traffic_monitoring_jobs(scheduler):
    """
    Setup semua traffic monitoring jobs ke scheduler.
    Dipanggil dari main.py saat aplikasi start.
    """

    # Traffic collection job - Setiap 5 menit
    scheduler.add_job(
        job_collect_traffic_data,
        'interval',
        minutes=5,
        id='traffic_collection',
        name='Traffic Data Collection',
        max_instances=1,  # Cegah overlapping
        misfire_grace_time=60,  # Allow 1 minute delay
        replace_existing=True
    )

    # Data cleanup job - Setiap hari jam 2 pagi
    scheduler.add_job(
        job_cleanup_old_traffic_data,
        'cron',
        hour=2,
        minute=0,
        id='traffic_cleanup',
        name='Traffic Data Cleanup',
        max_instances=1,
        misfire_grace_time=300,  # Allow 5 minute delay
        replace_existing=True
    )

    # Report generation job - Setiap hari jam 1 pagi
    scheduler.add_job(
        job_generate_traffic_reports,
        'cron',
        hour=1,
        minute=0,
        id='traffic_reports',
        name='Traffic Reports Generation',
        max_instances=1,
        misfire_grace_time=300,  # Allow 5 minute delay
        replace_existing=True
    )

    # Health check job - Setiap 15 menit
    scheduler.add_job(
        job_health_check_traffic_monitoring,
        'interval',
        minutes=15,
        id='traffic_health_check',
        name='Traffic Monitoring Health Check',
        max_instances=1,
        misfire_grace_time=120,  # Allow 2 minute delay
        replace_existing=True
    )

    logger.info("🕐 Traffic monitoring jobs scheduled:")
    logger.info("   - Traffic Collection: Every 5 minutes")
    logger.info("   - Data Cleanup: Daily at 2:00 AM")
    logger.info("   - Report Generation: Daily at 1:00 AM")
    logger.info("   - Health Check: Every 15 minutes")