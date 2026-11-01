"""Bounded, versioned Parquet encoding for normalized daily climate rows."""

from __future__ import annotations

from datetime import date
import io
import math

import pyarrow as pa
import pyarrow.parquet as pq

from app.contracts.challenge.v1 import DailyClimateObservation

CACHE_FORMAT = "fieldshift-climate-parquet-v1"
MAX_DAILY_ROWS = 20_000
MAX_PARQUET_BYTES = 64 * 1024 * 1024
MAX_DECODED_TABLE_BYTES = 128 * 1024 * 1024
MAX_ROW_GROUPS = 20

_SCHEMA_METADATA = {
    b"fieldshift.cache_format": CACHE_FORMAT.encode("ascii"),
    b"fieldshift.rainfall_mm": b"mm/day",
    b"fieldshift.temperature_c": b"degC",
    b"fieldshift.solar_mj_m2_day": b"MJ/m^2/day",
}


class ParquetClimateCacheError(ValueError):
    """The bounded Parquet payload does not match the climate cache contract."""


def _schema() -> pa.Schema:
    return pa.schema(
        [
            pa.field("date", pa.date32(), nullable=False),
            pa.field("rainfall_mm", pa.float64(), nullable=False),
            pa.field("temperature_c", pa.float64(), nullable=False),
            pa.field("solar_mj_m2_day", pa.float64(), nullable=False),
            pa.field("quality_flags", pa.list_(pa.string()), nullable=False),
        ],
        metadata=_SCHEMA_METADATA,
    )


def encode_daily_series(rows: list[DailyClimateObservation]) -> bytes:
    if not rows or len(rows) > MAX_DAILY_ROWS:
        raise ParquetClimateCacheError("daily-series row count is outside the supported bounds")
    for row in rows:
        if not all(
            math.isfinite(value)
            for value in (row.rainfall_mm, row.temperature_c, row.solar_mj_m2_day)
        ):
            raise ParquetClimateCacheError("daily-series contains a non-finite value")
    table = pa.Table.from_pylist(
        [row.model_dump(mode="python") for row in rows], schema=_schema()
    )
    if table.nbytes > MAX_DECODED_TABLE_BYTES:
        raise ParquetClimateCacheError("daily-series table exceeds the decoded byte limit")
    output = pa.BufferOutputStream()
    pq.write_table(
        table,
        output,
        compression="zstd",
        version="2.6",
        row_group_size=5_000,
        write_statistics=True,
    )
    payload = output.getvalue().to_pybytes()
    if len(payload) > MAX_PARQUET_BYTES:
        raise ParquetClimateCacheError("daily-series Parquet exceeds the byte limit")
    return payload


def decode_daily_series(payload: bytes, *, expected_rows: int) -> list[DailyClimateObservation]:
    if not payload or len(payload) > MAX_PARQUET_BYTES:
        raise ParquetClimateCacheError("daily-series Parquet exceeds the byte limit")
    if payload[:4] != b"PAR1" or payload[-4:] != b"PAR1":
        raise ParquetClimateCacheError("daily-series Parquet framing is invalid")
    if not 1 <= expected_rows <= MAX_DAILY_ROWS:
        raise ParquetClimateCacheError("daily-series row count is outside the supported bounds")

    try:
        reader = pq.ParquetFile(
            io.BytesIO(payload),
            thrift_string_size_limit=MAX_PARQUET_BYTES,
            thrift_container_size_limit=MAX_DAILY_ROWS * 16,
        )
        metadata = reader.metadata
        if metadata.num_rows != expected_rows:
            raise ParquetClimateCacheError("daily-series row count does not match the index")
        if metadata.num_row_groups < 1 or metadata.num_row_groups > MAX_ROW_GROUPS:
            raise ParquetClimateCacheError("daily-series row-group count is outside the supported bounds")
        if metadata.serialized_size > MAX_PARQUET_BYTES:
            raise ParquetClimateCacheError("daily-series Parquet metadata exceeds the byte limit")
        if sum(metadata.row_group(index).total_byte_size for index in range(metadata.num_row_groups)) > MAX_DECODED_TABLE_BYTES:
            raise ParquetClimateCacheError("daily-series decoded size exceeds the byte limit")

        schema = reader.schema_arrow
        expected = _schema()
        if schema.names != expected.names or schema.types != expected.types:
            raise ParquetClimateCacheError("daily-series Parquet schema is unsupported")
        if schema.metadata != _SCHEMA_METADATA:
            raise ParquetClimateCacheError("daily-series Parquet units or format metadata are invalid")

        table = reader.read()
    except ParquetClimateCacheError:
        raise
    except Exception as error:
        raise ParquetClimateCacheError("daily-series Parquet could not be decoded") from error

    if table.num_rows != expected_rows or table.nbytes > MAX_DECODED_TABLE_BYTES:
        raise ParquetClimateCacheError("daily-series decoded table exceeds its bounds")
    if any(column.null_count for column in table.columns):
        raise ParquetClimateCacheError("daily-series Parquet contains null values")

    observations: list[DailyClimateObservation] = []
    for item in table.to_pylist():
        if not isinstance(item["date"], date):
            raise ParquetClimateCacheError("daily-series Parquet date is invalid")
        if not all(
            math.isfinite(item[field])
            for field in ("rainfall_mm", "temperature_c", "solar_mj_m2_day")
        ):
            raise ParquetClimateCacheError("daily-series Parquet contains a non-finite value")
        try:
            observations.append(DailyClimateObservation.model_validate(item))
        except Exception as error:
            raise ParquetClimateCacheError("daily-series Parquet contains an invalid observation") from error
    return observations
