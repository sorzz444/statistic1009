"""Utilities for checking Spark-related package versions and creating a local SparkSession."""
from __future__ import annotations

import logging
from typing import Mapping, Optional

import pyspark
from pkg_resources import DistributionNotFound, get_distribution
from pyspark.sql import SparkSession

LOGGER = logging.getLogger(__name__)


def _get_package_version(package_name: str) -> str:
    """Return the installed version of ``package_name`` or ``"unknown"``."""
    try:
        return get_distribution(package_name).version
    except DistributionNotFound:
        return "unknown"


def log_environment_versions() -> None:
    """Log the versions of PySpark and SynapseML that are currently installed."""
    LOGGER.info("PySpark version: %s", pyspark.__version__)
    LOGGER.info("SynapseML version: %s", _get_package_version("synapseml"))


DEFAULT_SPARK_CONFIG: Mapping[str, str] = {
    # Force the default filesystem to the local filesystem so accidental HDFS
    # access (e.g. ``hdfs://test2024``) is avoided.
    "spark.hadoop.fs.defaultFS": "file:///",
    # Persist Spark SQL tables to a local path instead of HDFS.
    "spark.sql.warehouse.dir": "file:///tmp/spark-warehouse",
}


def create_local_spark_session(
    app_name: str = "LocalApp",
    *,
    log_level: str = "WARN",
    extra_configs: Optional[Mapping[str, str]] = None,
) -> SparkSession:
    """Create (or reuse) a ``SparkSession`` configured for local filesystem access.

    Parameters
    ----------
    app_name:
        Name of the Spark application.
    log_level:
        Desired Spark log level. ``"WARN"`` keeps output concise for notebooks.
    extra_configs:
        Additional Spark configuration entries to apply.
    """

    builder = SparkSession.builder.appName(app_name).master("local[*]")

    # Apply baseline configuration that keeps Spark on the local filesystem.
    for key, value in DEFAULT_SPARK_CONFIG.items():
        builder = builder.config(key, value)

    if extra_configs:
        for key, value in extra_configs.items():
            builder = builder.config(key, value)

    spark = builder.getOrCreate()
    spark.sparkContext.setLogLevel(log_level)
    return spark


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    log_environment_versions()
    spark_session = create_local_spark_session()
    LOGGER.info("SparkSession started with app name '%s'", spark_session.sparkContext.appName)
