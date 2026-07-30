#!/usr/bin/env python3
"""
Database Reset & Wiping Script Template

Purpose:
    Safely resets the PostgreSQL database environment by dropping all tables,
    re-applying Alembic migrations, and optionally re-seeding test data.

Usage:
    python scripts/reset_database.py [--force]
"""

import argparse
import sys
import logging

logging.basicConfig(level=logging.INFO, format="[%(asctime)s] [%(levelname)s]: %(message)s")
logger = logging.getLogger("reset_database")


def parse_args():
    parser = argparse.ArgumentParser(description="Reset database schema and re-run migrations.")
    parser.add_argument(
        "--force",
        action="store_true",
        help="Skip safety confirmation prompt",
    )
    return parser.parse_args()


def main():
    args = parse_args()

    if not args.force:
        logger.warning("ATTENTION: This operation will drop all database tables and erase data!")
        confirm = input("Are you sure you want to reset the database? [y/N]: ").strip().lower()
        if confirm != "y":
            logger.info("Database reset canceled by user.")
            sys.exit(0)

    # TODO: In Phase 2, implement database wipe & migration reset:
    # from backend.app import create_app
    # from backend.app.database import db
    # db.drop_all()
    # db.create_all()

    logger.info("TODO: Reset database logic will be executed here when models are defined.")
    print("Reset database placeholder script initialized successfully.")


if __name__ == "__main__":
    main()
