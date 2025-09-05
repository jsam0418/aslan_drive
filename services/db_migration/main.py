"""
Database Migration Service - Main Entry Point

Handles Alembic database migrations for Aslan Drive.
"""
import logging
import os
import sys
from pathlib import Path

from alembic import command
from alembic.config import Config

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def get_alembic_config() -> Config:
    """Get Alembic configuration."""
    alembic_cfg_path = project_root / "alembic.ini"
    if not alembic_cfg_path.exists():
        raise FileNotFoundError(f"Alembic configuration not found: {alembic_cfg_path}")

    config = Config(str(alembic_cfg_path))

    # Override database URL from environment
    database_url = os.getenv("DATABASE_URL")
    if database_url:
        config.set_main_option("sqlalchemy.url", database_url)
        logger.info("Using database URL from environment")
    else:
        logger.warning("DATABASE_URL not set, using default from alembic.ini")

    return config


def migrate_to_head() -> bool:
    """Run Alembic upgrade to head."""
    try:
        logger.info("Starting database migration to head...")
        config = get_alembic_config()

        # Run upgrade to head
        command.upgrade(config, "head")

        logger.info("Database migration completed successfully")
        return True

    except Exception as e:
        logger.error(f"Database migration failed: {e}")
        return False


def check_current_revision() -> str:
    """Check current database revision."""
    try:
        config = get_alembic_config()

        # Get current revision
        from sqlalchemy import create_engine

        from alembic.runtime.migration import MigrationContext

        database_url = os.getenv("DATABASE_URL")
        if not database_url:
            raise ValueError("DATABASE_URL environment variable is required")

        engine = create_engine(database_url)

        with engine.connect() as connection:
            context = MigrationContext.configure(connection)
            current_rev = context.get_current_revision()

        logger.info(f"Current database revision: {current_rev}")
        return current_rev or "None"

    except Exception as e:
        logger.error(f"Failed to check current revision: {e}")
        return "Error"


def stamp_database(revision: str = "head") -> bool:
    """Stamp database with a revision (without running migrations)."""
    try:
        logger.info(f"Stamping database with revision: {revision}")
        config = get_alembic_config()

        command.stamp(config, revision)

        logger.info("Database stamped successfully")
        return True

    except Exception as e:
        logger.error(f"Database stamping failed: {e}")
        return False


def main():
    """Main entry point for migration service."""
    logger.info("Starting Database Migration Service...")

    # Get command from environment or default to upgrade
    migration_command = os.getenv("MIGRATION_COMMAND", "upgrade").lower()

    try:
        if migration_command == "upgrade":
            success = migrate_to_head()
        elif migration_command == "check":
            current_rev = check_current_revision()
            print(f"Current revision: {current_rev}")
            success = True
        elif migration_command == "stamp":
            revision = os.getenv("STAMP_REVISION", "head")
            success = stamp_database(revision)
        else:
            logger.error(f"Unknown migration command: {migration_command}")
            success = False

        if success:
            logger.info("Migration service completed successfully")
            sys.exit(0)
        else:
            logger.error("Migration service failed")
            sys.exit(1)

    except KeyboardInterrupt:
        logger.info("Migration service interrupted")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Migration service failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
