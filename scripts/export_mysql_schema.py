"""Export SQLAlchemy schema to MySQL DDL.

Usage:
    python scripts/export_mysql_schema.py > mysql_schema.sql
"""

from sqlalchemy.schema import CreateTable
from sqlalchemy.dialects import mysql

# Importing the database manager loads all models into SQLAlchemy metadata.
import ayanna_erp.database.database_manager  # noqa: F401
from ayanna_erp.database.base import Base


if __name__ == "__main__":
    tables = list(Base.metadata.sorted_tables)
    print("-- AUTO-GENERATED MySQL DDL FROM SQLAlchemy MODELS")
    print("-- Tables:", len(tables))
    print()

    for table in tables:
        ddl = str(CreateTable(table).compile(dialect=mysql.dialect()))
        print(ddl)
        print(";")
        print()
