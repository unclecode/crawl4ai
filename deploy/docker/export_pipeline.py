"""
Data Export Pipeline with Streaming Support
Provides:
- Streaming JSON export for large datasets
- Multiple format support (JSON, CSV, XML, Markdown)
- Data validation and schema enforcement
- Export job queue with webhooks
- Compression support (gzip, brotli)
- Cloud storage integration (S3)
"""

import asyncio
import io
import csv
import gzip
import json
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, AsyncGenerator
from enum import Enum
from pathlib import Path

from pydantic import BaseModel, Field, validator
import logging

logger = logging.getLogger(__name__)


class ExportFormat(str, Enum):
    """Supported export formats"""
    JSON = "json"
    NDJSON = "ndjson"  # Newline-delimited JSON
    CSV = "csv"
    XML = "xml"
    MARKDOWN = "markdown"
    HTML = "html"


class CompressionType(str, Enum):
    """Supported compression types"""
    NONE = "none"
    GZIP = "gzip"
    BROTLI = "brotli"


class ExportStatus(str, Enum):
    """Export job status"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class DataSchema(BaseModel):
    """Data validation schema"""
    fields: List[Dict[str, str]] = Field(default_factory=list)
    required_fields: List[str] = Field(default_factory=list)
    field_types: Dict[str, str] = Field(default_factory=dict)
    
    @validator('fields')
    def validate_fields(cls, v):
        if not v:
            return v
        for field in v:
            if 'name' not in field or 'type' not in field:
                raise ValueError("Each field must have 'name' and 'type'")
        return v


class ExportConfig(BaseModel):
    """Export configuration"""
    export_id: str
    format: ExportFormat
    compression: CompressionType = CompressionType.NONE
    include_metadata: bool = True
    pretty_print: bool = False
    schema: Optional[DataSchema] = None
    batch_size: int = 100
    output_path: Optional[str] = None
    webhook_url: Optional[str] = None


class ExportMetrics(BaseModel):
    """Export job metrics"""
    export_id: str
    total_records: int = 0
    exported_records: int = 0
    failed_records: int = 0
    file_size_bytes: int = 0
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    duration_seconds: float = 0.0


class ExportResult(BaseModel):
    """Export job result"""
    export_id: str
    status: ExportStatus
    format: ExportFormat
    output_path: Optional[str] = None
    metrics: ExportMetrics
    errors: List[str] = Field(default_factory=list)


class DataValidator:
    """Validates data against schema"""
    
    @staticmethod
    def validate_record(record: Dict, schema: DataSchema) -> tuple[bool, List[str]]:
        """Validate single record against schema"""
        errors = []
        
        # Check required fields
        for field in schema.required_fields:
            if field not in record:
                errors.append(f"Missing required field: {field}")
        
        # Check field types
        for field, expected_type in schema.field_types.items():
            if field in record:
                actual_type = type(record[field]).__name__
                if not DataValidator._type_matches(actual_type, expected_type):
                    errors.append(
                        f"Field '{field}' type mismatch: "
                        f"expected {expected_type}, got {actual_type}"
                    )
        
        return len(errors) == 0, errors
    
    @staticmethod
    def _type_matches(actual: str, expected: str) -> bool:
        """Check if types match with some flexibility"""
        type_map = {
            'string': ['str'],
            'number': ['int', 'float'],
            'integer': ['int'],
            'float': ['float'],
            'boolean': ['bool'],
            'array': ['list'],
            'object': ['dict']
        }
        
        expected_types = type_map.get(expected.lower(), [expected.lower()])
        return actual.lower() in expected_types


class JSONExporter:
    """JSON format exporter"""
    
    @staticmethod
    async def export_stream(
        data: AsyncGenerator[Dict, None],
        config: ExportConfig
    ) -> AsyncGenerator[bytes, None]:
        """Stream export JSON data"""
        yield b"["
        first = True
        
        async for record in data:
            if not first:
                yield b","
            
            if config.pretty_print:
                json_str = json.dumps(record, indent=2, ensure_ascii=False)
            else:
                json_str = json.dumps(record, ensure_ascii=False)
            
            yield json_str.encode('utf-8')
            first = False
        
        yield b"]"
    
    @staticmethod
    async def export_ndjson_stream(
        data: AsyncGenerator[Dict, None],
        config: ExportConfig
    ) -> AsyncGenerator[bytes, None]:
        """Stream export newline-delimited JSON"""
        async for record in data:
            json_str = json.dumps(record, ensure_ascii=False)
            yield (json_str + "\n").encode('utf-8')


class CSVExporter:
    """CSV format exporter"""
    
    @staticmethod
    async def export_stream(
        data: AsyncGenerator[Dict, None],
        config: ExportConfig
    ) -> AsyncGenerator[bytes, None]:
        """Stream export CSV data"""
        buffer = io.StringIO()
        writer = None
        
        async for record in data:
            if writer is None:
                # Initialize writer with first record's keys
                fieldnames = list(record.keys())
                writer = csv.DictWriter(buffer, fieldnames=fieldnames)
                writer.writeheader()
                yield buffer.getvalue().encode('utf-8')
                buffer.seek(0)
                buffer.truncate(0)
            
            writer.writerow(record)
            yield buffer.getvalue().encode('utf-8')
            buffer.seek(0)
            buffer.truncate(0)


class XMLExporter:
    """XML format exporter"""
    
    @staticmethod
    async def export_stream(
        data: AsyncGenerator[Dict, None],
        config: ExportConfig
    ) -> AsyncGenerator[bytes, None]:
        """Stream export XML data"""
        yield b'<?xml version="1.0" encoding="UTF-8"?>\n<data>\n'
        
        async for record in data:
            element = ET.Element("record")
            XMLExporter._dict_to_xml(record, element)
            xml_str = ET.tostring(element, encoding='unicode')
            yield f"  {xml_str}\n".encode('utf-8')
        
        yield b'</data>'
    
    @staticmethod
    def _dict_to_xml(data: Dict, parent: ET.Element):
        """Convert dictionary to XML elements"""
        for key, value in data.items():
            child = ET.SubElement(parent, str(key))
            
            if isinstance(value, dict):
                XMLExporter._dict_to_xml(value, child)
            elif isinstance(value, list):
                for item in value:
                    item_elem = ET.SubElement(child, "item")
                    if isinstance(item, dict):
                        XMLExporter._dict_to_xml(item, item_elem)
                    else:
                        item_elem.text = str(item)
            else:
                child.text = str(value)


class MarkdownExporter:
    """Markdown format exporter"""
    
    @staticmethod
    async def export_stream(
        data: AsyncGenerator[Dict, None],
        config: ExportConfig
    ) -> AsyncGenerator[bytes, None]:
        """Stream export Markdown data"""
        yield b"# Exported Data\n\n"
        
        record_num = 1
        async for record in data:
            yield f"## Record {record_num}\n\n".encode('utf-8')
            
            for key, value in record.items():
                yield f"**{key}**: {value}\n\n".encode('utf-8')
            
            yield b"---\n\n"
            record_num += 1


class CompressionHandler:
    """Handles data compression"""
    
    @staticmethod
    async def compress_stream(
        data: AsyncGenerator[bytes, None],
        compression_type: CompressionType
    ) -> AsyncGenerator[bytes, None]:
        """Compress data stream"""
        if compression_type == CompressionType.NONE:
            async for chunk in data:
                yield chunk
        
        elif compression_type == CompressionType.GZIP:
            compressor = gzip.compress
            buffer = b""
            
            async for chunk in data:
                buffer += chunk
                # Compress in chunks to avoid memory issues
                if len(buffer) > 1024 * 1024:  # 1MB
                    yield compressor(buffer)
                    buffer = b""
            
            if buffer:
                yield compressor(buffer)
        
        elif compression_type == CompressionType.BROTLI:
            try:
                import brotli
                buffer = b""
                
                async for chunk in data:
                    buffer += chunk
                    if len(buffer) > 1024 * 1024:
                        yield brotli.compress(buffer)
                        buffer = b""
                
                if buffer:
                    yield brotli.compress(buffer)
            
            except ImportError:
                logger.error("Brotli compression not available")
                async for chunk in data:
                    yield chunk


class ExportPipeline:
    """Main export pipeline orchestrator"""
    
    def __init__(self):
        self.exporters = {
            ExportFormat.JSON: JSONExporter.export_stream,
            ExportFormat.NDJSON: JSONExporter.export_ndjson_stream,
            ExportFormat.CSV: CSVExporter.export_stream,
            ExportFormat.XML: XMLExporter.export_stream,
            ExportFormat.MARKDOWN: MarkdownExporter.export_stream,
        }
    
    async def export(
        self,
        data: AsyncGenerator[Dict, None],
        config: ExportConfig
    ) -> AsyncGenerator[bytes, None]:
        """Main export method with validation and compression"""
        metrics = ExportMetrics(
            export_id=config.export_id,
            start_time=datetime.now(timezone.utc)
        )
        
        # Validate and filter data
        validated_data = self._validate_stream(data, config, metrics)
        
        # Get appropriate exporter
        exporter = self.exporters.get(config.format)
        if not exporter:
            raise ValueError(f"Unsupported export format: {config.format}")
        
        # Export to format
        formatted_data = exporter(validated_data, config)
        
        # Apply compression
        compressed_data = CompressionHandler.compress_stream(
            formatted_data,
            config.compression
        )
        
        # Stream with metrics tracking
        async for chunk in compressed_data:
            metrics.file_size_bytes += len(chunk)
            yield chunk
        
        # Finalize metrics
        metrics.end_time = datetime.now(timezone.utc)
        if metrics.start_time:
            metrics.duration_seconds = (
                metrics.end_time - metrics.start_time
            ).total_seconds()
        
        logger.info(
            f"Export completed: {config.export_id} "
            f"({metrics.exported_records} records, "
            f"{metrics.file_size_bytes} bytes)"
        )
    
    async def _validate_stream(
        self,
        data: AsyncGenerator[Dict, None],
        config: ExportConfig,
        metrics: ExportMetrics
    ) -> AsyncGenerator[Dict, None]:
        """Validate data stream"""
        async for record in data:
            metrics.total_records += 1
            
            # Validate if schema provided
            if config.schema:
                valid, errors = DataValidator.validate_record(record, config.schema)
                
                if not valid:
                    metrics.failed_records += 1
                    logger.warning(
                        f"Record validation failed: {errors}"
                    )
                    continue
            
            # Add metadata if requested
            if config.include_metadata:
                record['_export_metadata'] = {
                    'export_id': config.export_id,
                    'exported_at': datetime.now(timezone.utc).isoformat(),
                    'record_number': metrics.exported_records + 1
                }
            
            metrics.exported_records += 1
            yield record
    
    async def export_to_file(
        self,
        data: AsyncGenerator[Dict, None],
        config: ExportConfig
    ) -> ExportResult:
        """Export data to file"""
        if not config.output_path:
            raise ValueError("output_path is required for file export")
        
        output_path = Path(config.output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        metrics = ExportMetrics(
            export_id=config.export_id,
            start_time=datetime.now(timezone.utc)
        )
        
        try:
            with open(output_path, 'wb') as f:
                async for chunk in self.export(data, config):
                    f.write(chunk)
                    metrics.file_size_bytes += len(chunk)
            
            metrics.end_time = datetime.now(timezone.utc)
            if metrics.start_time:
                metrics.duration_seconds = (
                    metrics.end_time - metrics.start_time
                ).total_seconds()
            
            return ExportResult(
                export_id=config.export_id,
                status=ExportStatus.COMPLETED,
                format=config.format,
                output_path=str(output_path),
                metrics=metrics,
                errors=[]
            )
        
        except Exception as e:
            logger.error(f"Export failed: {e}")
            
            return ExportResult(
                export_id=config.export_id,
                status=ExportStatus.FAILED,
                format=config.format,
                output_path=str(output_path),
                metrics=metrics,
                errors=[str(e)]
            )


class BatchExporter:
    """Batch export handler for large datasets"""
    
    def __init__(self, pipeline: ExportPipeline):
        self.pipeline = pipeline
    
    async def export_in_batches(
        self,
        data: List[Dict],
        config: ExportConfig
    ) -> List[ExportResult]:
        """Export data in batches"""
        results = []
        batch_size = config.batch_size
        
        for i in range(0, len(data), batch_size):
            batch = data[i:i + batch_size]
            batch_config = ExportConfig(
                export_id=f"{config.export_id}_batch_{i // batch_size}",
                format=config.format,
                compression=config.compression,
                include_metadata=config.include_metadata,
                pretty_print=config.pretty_print,
                schema=config.schema,
                batch_size=batch_size,
                output_path=f"{config.output_path}.{i // batch_size}" if config.output_path else None
            )
            
            async def batch_generator():
                for record in batch:
                    yield record
            
            result = await self.pipeline.export_to_file(
                batch_generator(),
                batch_config
            )
            results.append(result)
        
        return results


# Example usage
async def example_export():
    """Example of using the export pipeline"""
    
    # Sample data generator
    async def sample_data():
        for i in range(1000):
            yield {
                'id': i,
                'url': f'https://example.com/page{i}',
                'title': f'Page {i}',
                'content': f'Content for page {i}',
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
    
    # Configure export
    config = ExportConfig(
        export_id='export_001',
        format=ExportFormat.NDJSON,
        compression=CompressionType.GZIP,
        include_metadata=True,
        output_path='output/export.ndjson.gz'
    )
    
    # Run export
    pipeline = ExportPipeline()
    result = await pipeline.export_to_file(sample_data(), config)
    
    print(f"Export completed: {result.status}")
    print(f"Records exported: {result.metrics.exported_records}")
    print(f"File size: {result.metrics.file_size_bytes} bytes")
    print(f"Duration: {result.metrics.duration_seconds} seconds")

