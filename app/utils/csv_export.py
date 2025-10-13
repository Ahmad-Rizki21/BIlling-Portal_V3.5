"""
Centralized CSV export utilities untuk menghilangkan duplikasi export logic
"""

import csv
import io
import logging
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Union

from fastapi.responses import StreamingResponse

logger = logging.getLogger(__name__)


class CSVExporter:
    """
    Centralized CSV export utility untuk menghilangkan duplikasi
    export logic di pelanggan.py, data_teknis.py, dan file lainnya
    """

    @staticmethod
    def create_csv_response(
        data: List[Dict[str, Any]], filename_prefix: str, headers: Optional[Collection[str]] = None, include_bom: bool = True
    ) -> StreamingResponse:
        """
        Create CSV response dengan format yang konsisten
        Menghilangkan duplikasi CSV export logic di semua routers
        """
        try:
            # Create StringIO untuk menampung CSV data
            output = io.StringIO()

            # Add BOM untuk Excel compatibility jika required
            if include_bom:
                output.write("\ufeff")

            # Determine headers
            if headers is None and data:
                headers = list(data[0].keys())
            elif headers is None:
                headers = []

            # Create CSV writer
            writer = csv.DictWriter(output, fieldnames=headers)
            writer.writeheader()

            # Write data rows
            if data:
                writer.writerows(data)

            # Reset string position
            output.seek(0)

            # Generate filename dengan timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{filename_prefix}_{timestamp}.csv"

            # Create response headers
            response_headers = {"Content-Disposition": f'attachment; filename="{filename}"'}

            # Return StreamingResponse
            return StreamingResponse(
                io.BytesIO(output.getvalue().encode("utf-8")),
                headers=response_headers,
                media_type="text/csv; charset=utf-8",
            )

        except Exception as e:
            logger.error(f"Failed to create CSV response for {filename_prefix}: {e}")
            raise

    @staticmethod
    def create_csv_template(headers: Collection[str], sample_data: List[Dict[str, Any]], filename_prefix: str) -> StreamingResponse:
        """
        Create CSV template untuk import dengan sample data
        Menghilangkan duplikasi template creation logic
        """
        try:
            output = io.StringIO()
            output.write("\ufeff")  # BOM untuk Excel

            writer = csv.DictWriter(output, fieldnames=headers)
            writer.writeheader()

            # Write sample data jika ada
            if sample_data:
                writer.writerows(sample_data)

            output.seek(0)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"template_{filename_prefix}_{timestamp}.csv"

            response_headers = {"Content-Disposition": f'attachment; filename="{filename}"'}

            return StreamingResponse(
                io.BytesIO(output.getvalue().encode("utf-8")),
                headers=response_headers,
                media_type="text/csv; charset=utf-8",
            )

        except Exception as e:
            logger.error(f"Failed to create CSV template for {filename_prefix}: {e}")
            raise

    @staticmethod
    def prepare_export_data(
        raw_data: List[Any],
        field_mapping: Optional[Dict[str, str]] = None,
        exclude_fields: Optional[Collection[str]] = None,
        transform_functions: Optional[Dict[str, Callable[..., Any]]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Prepare data untuk export dengan field mapping dan transformations
        Menghilangkan duplikasi data preparation logic
        """
        processed_data = []

        for item in raw_data:
            # Convert object to dict
            if hasattr(item, "__dict__"):
                item_dict = item.__dict__.copy()
                # Remove SQLAlchemy internal attributes
                item_dict = {k: v for k, v in item_dict.items() if not k.startswith("_")}
            elif isinstance(item, dict):
                item_dict = item.copy()
            else:
                # For simple types or other objects
                item_dict = {"value": item}

            # Apply field mapping
            if field_mapping:
                mapped_dict = {}
                for export_field, source_field in field_mapping.items():
                    mapped_dict[export_field] = item_dict.get(source_field, "")
                item_dict = mapped_dict

            # Exclude fields
            if exclude_fields:
                item_dict = {k: v for k, v in item_dict.items() if k not in exclude_fields}

            # Apply transformation functions
            if transform_functions:
                for field, transform_func in transform_functions.items():
                    if field in item_dict:
                        try:
                            item_dict[field] = transform_func(item_dict[field])
                        except Exception as e:
                            logger.warning(f"Failed to transform field {field}: {e}")
                            item_dict[field] = str(item_dict[field]) if item_dict[field] else ""

            # Handle None values
            for key, value in item_dict.items():
                if value is None:
                    item_dict[key] = ""

            processed_data.append(item_dict)

        return processed_data


class CSVImportHelper:
    """
    Helper utilities untuk CSV import operations
    """

    @staticmethod
    def validate_csv_headers(
        expected_headers: Collection[str], actual_headers: Collection[str], case_sensitive: bool = False
    ) -> tuple[bool, List[str]]:
        """
        Validate CSV headers terhadap expected headers
        Returns: (is_valid, missing_headers)
        """
        if not case_sensitive:
            expected_headers = [h.lower() for h in expected_headers]
            actual_headers = [h.lower() for h in actual_headers]

        missing_headers = [h for h in expected_headers if h not in actual_headers]
        is_valid = len(missing_headers) == 0

        return is_valid, missing_headers

    @staticmethod
    def normalize_field_names(data_dict: Dict[str, Any], field_mapping: Dict[str, str]) -> Dict[str, Any]:
        """
        Normalize field names berdasarkan mapping
        """
        normalized = {}
        for csv_field, model_field in field_mapping.items():
            if csv_field in data_dict:
                normalized[model_field] = data_dict[csv_field]

        return normalized

    @staticmethod
    def clean_csv_value(value: Optional[Union[str, Any]]) -> str:
        """
        Clean CSV value dari extra whitespace dan unwanted characters
        """
        if value is None:
            return ""

        # Convert to string and strip whitespace
        cleaned = str(value).strip()

        # Remove BOM and other invisible characters
        cleaned = cleaned.replace("\ufeff", "")
        cleaned = cleaned.replace("\u200b", "")

        return cleaned


# Predefined export configurations untuk common use cases
class ExportConfigurations:
    """
    Predefined configurations untuk export scenarios yang umum
    """

    PELANGGAN_EXPORT = {
        "headers": ["ID", "Nama", "Email", "No Telepon", "Alamat", "No KTP", "Tanggal Instalasi", "Brand", "Status"],
        "field_mapping": {
            "ID": "id",
            "Nama": "nama",
            "Email": "email",
            "No Telepon": "no_telp",
            "Alamat": "alamat",
            "No KTP": "no_ktp",
            "Tanggal Instalasi": "tanggal_instalasi",
            "Brand": "id_brand",
            "Status": "status",
        },
        "exclude_fields": ["password", "internal_notes"],
        "transform_functions": {"Tanggal Instalasi": lambda x: str(x) if x else "", "id": lambda x: str(x) if x else ""},
    }

    DATA_TEKNIS_EXPORT = {
        "headers": ["ID Pelanggan", "Nama Pelanggan", "IP Pelanggan", "VLAN", "SN ONT", "Port ODP", "Port OLT", "Status"],
        "field_mapping": {
            "ID Pelanggan": "id_pelanggan",
            "Nama Pelanggan": "pelanggan_nama",
            "IP Pelanggan": "ip_pelanggan",
            "VLAN": "vlan",
            "SN ONT": "sn_ont",
            "Port ODP": "port_odp",
            "Port OLT": "port_olt",
            "Status": "status",
        },
        "exclude_fields": ["internal_config", "secrets"],
    }

    INVOICE_EXPORT = {
        "headers": [
            "Nomor Invoice",
            "Nama Pelanggan",
            "Tanggal Invoice",
            "Jatuh Tempo",
            "Total Harga",
            "Status",
            "Tanggal Bayar",
        ],
        "field_mapping": {
            "Nomor Invoice": "nomor_invoice",
            "Nama Pelanggan": "pelanggan_nama",
            "Tanggal Invoice": "tanggal_invoice",
            "Jatuh Tempo": "tanggal_jatuh_tempo",
            "Total Harga": "total_harga",
            "Status": "status_invoice",
            "Tanggal Bayar": "paid_at",
        },
        "transform_functions": {
            "Total Harga": lambda x: f"Rp {x:,.0f}" if x else "Rp 0",
            "Tanggal Invoice": lambda x: str(x) if x else "",
            "Jatuh Tempo": lambda x: str(x) if x else "",
            "Tanggal Bayar": lambda x: str(x) if x else "",
        },
    }


# Factory functions untuk common export patterns
def create_pelanggan_export_response(data: List[Any]) -> StreamingResponse:
    """Factory function untuk pelanggan export"""
    config = ExportConfigurations.PELANGGAN_EXPORT

    processed_data = CSVExporter.prepare_export_data(
        data,
        field_mapping=config["field_mapping"],
        exclude_fields=config["exclude_fields"],
        transform_functions=config["transform_functions"],
    )

    return CSVExporter.create_csv_response(processed_data, "pelanggan", config["headers"])


def create_data_teknis_export_response(data: List[Any]) -> StreamingResponse:
    """Factory function untuk data teknis export"""
    config = ExportConfigurations.DATA_TEKNIS_EXPORT

    processed_data = CSVExporter.prepare_export_data(
        data,
        field_mapping=config["field_mapping"],
        exclude_fields=config["exclude_fields"]
    )

    return CSVExporter.create_csv_response(processed_data, "data_teknis", config["headers"])


def create_invoice_export_response(data: List[Any]) -> StreamingResponse:
    """Factory function untuk invoice export"""
    config = ExportConfigurations.INVOICE_EXPORT

    processed_data = CSVExporter.prepare_export_data(
        data,
        field_mapping=config["field_mapping"],
        transform_functions=config["transform_functions"]
    )

    return CSVExporter.create_csv_response(processed_data, "invoice", config["headers"])
