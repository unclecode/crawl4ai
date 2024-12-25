"""Utility functions for exporting SSL certificates in various formats."""

import json
import base64
from typing import Dict, Any, Optional
from pathlib import Path
import OpenSSL.crypto
from datetime import datetime

class CertificateExporter:
    """
    Handles exporting SSL certificates in various formats:
    1. JSON - Human-readable format with all certificate details
    2. PEM - Standard text format for certificates
    3. DER - Binary format
    """

    @staticmethod
    def _decode_cert_data(data: Any) -> Any:
        """Helper method to decode bytes in certificate data."""
        if isinstance(data, bytes):
            return data.decode('utf-8')
        elif isinstance(data, dict):
            return {
                (k.decode('utf-8') if isinstance(k, bytes) else k): CertificateExporter._decode_cert_data(v)
                for k, v in data.items()
            }
        elif isinstance(data, list):
            return [CertificateExporter._decode_cert_data(item) for item in data]
        return data

    @staticmethod
    def to_json(cert_info: Dict[str, Any], filepath: Optional[str] = None) -> Optional[str]:
        """
        Export certificate information to JSON format.
        
        Args:
            cert_info: Dictionary containing certificate information
            filepath: Optional path to save the JSON file
            
        Returns:
            str: JSON string if filepath is None, otherwise None
        """
        if not cert_info:
            return None
            
        # Decode any bytes in the certificate data
        cert_data = CertificateExporter._decode_cert_data(cert_info)
        
        # Convert datetime objects to ISO format strings
        for key, value in cert_data.items():
            if isinstance(value, datetime):
                cert_data[key] = value.isoformat()
                
        json_str = json.dumps(cert_data, indent=2, ensure_ascii=False)
        
        if filepath:
            Path(filepath).write_text(json_str, encoding='utf-8')
            return None
        return json_str

    @staticmethod
    def to_pem(cert_info: Dict[str, Any], filepath: Optional[str] = None) -> Optional[str]:
        """
        Export certificate to PEM format.
        This is the most common format, used for Apache/Nginx configs.
        
        Args:
            cert_info: Dictionary containing certificate information
            filepath: Optional path to save the PEM file
            
        Returns:
            str: PEM string if filepath is None, otherwise None
        """
        if not cert_info or 'raw_cert' not in cert_info:
            return None
            
        try:
            x509 = OpenSSL.crypto.load_certificate(
                OpenSSL.crypto.FILETYPE_ASN1, 
                base64.b64decode(cert_info['raw_cert'])
            )
            pem_data = OpenSSL.crypto.dump_certificate(
                OpenSSL.crypto.FILETYPE_PEM, 
                x509
            ).decode('utf-8')
            
            if filepath:
                Path(filepath).write_text(pem_data, encoding='utf-8')
                return None
            return pem_data
            
        except Exception as e:
            return f"Error converting to PEM: {str(e)}"

    @staticmethod
    def to_der(cert_info: Dict[str, Any], filepath: Optional[str] = None) -> Optional[bytes]:
        """
        Export certificate to DER format (binary).
        This format is commonly used in Java environments.
        
        Args:
            cert_info: Dictionary containing certificate information
            filepath: Optional path to save the DER file
            
        Returns:
            bytes: DER bytes if filepath is None, otherwise None
        """
        if not cert_info or 'raw_cert' not in cert_info:
            return None
            
        try:
            der_data = base64.b64decode(cert_info['raw_cert'])
            
            if filepath:
                Path(filepath).write_bytes(der_data)
                return None
            return der_data
            
        except Exception as e:
            return None

    @staticmethod
    def export_all(cert_info: Dict[str, Any], base_path: str, filename: str) -> Dict[str, str]:
        """
        Export certificate in all supported formats.
        
        Args:
            cert_info: Dictionary containing certificate information
            base_path: Base directory to save the files
            filename: Base filename without extension
            
        Returns:
            Dict[str, str]: Dictionary mapping format to filepath
        """
        base_path = Path(base_path)
        base_path.mkdir(parents=True, exist_ok=True)
        
        paths = {}
        
        # Export JSON
        json_path = base_path / f"{filename}.json"
        CertificateExporter.to_json(cert_info, str(json_path))
        paths['json'] = str(json_path)
        
        # Export PEM
        pem_path = base_path / f"{filename}.pem"
        CertificateExporter.to_pem(cert_info, str(pem_path))
        paths['pem'] = str(pem_path)
        
        # Export DER
        der_path = base_path / f"{filename}.der"
        CertificateExporter.to_der(cert_info, str(der_path))
        paths['der'] = str(der_path)
        
        return paths
