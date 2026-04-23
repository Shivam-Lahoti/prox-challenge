import logging
from typing import Dict, Optional
import fitz
from anthropic import Anthropic
import os
import base64
import json
from pathlib import Path

logger = logging.getLogger(__name__)


class StructuredExtractor:
    """Extract structured data from PDF manuals using Claude Vision"""
    
    def __init__(self, api_key: str):
        self.client = Anthropic(api_key=api_key)
        self.cache_dir = Path("cache")
        self.cache_dir.mkdir(exist_ok=True)
        self.model = os.getenv("CLAUDE_MODEL", "claude-sonnet-4-20250514")
    
    def extract_all_structured_data(self, pdf_path: str) -> Dict:
        """
        Extract all structured data from manual
        
        Returns:
            Dict with duty_cycles, polarity, troubleshooting, weld_diagnosis
        """
        cache_file = self.cache_dir / "structured_data.json"
        
        # Check cache first
        if cache_file.exists():
            logger.info("Loading all structured data from cache")
            with open(cache_file, 'r') as f:
                return json.load(f)
        
        logger.info("Extracting structured data from PDF using Vision API...")
        
        structured_data = {
            "duty_cycles": self._extract_duty_cycles(pdf_path),
            "polarity": self._extract_polarity_configs(pdf_path),
            "troubleshooting": self._extract_troubleshooting(pdf_path),
            "weld_diagnosis": self._extract_weld_diagnosis(pdf_path)
        }
        
        # Cache everything
        with open(cache_file, 'w') as f:
            json.dump(structured_data, f, indent=2)
        
        logger.info(f"All structured data extracted and cached")
        
        return structured_data
    
    def _render_page_to_base64(self, pdf_path: str, page_num: int) -> str:
        """Render a PDF page as base64 PNG"""
        doc = fitz.open(pdf_path)
        page = doc[page_num]
        pix = page.get_pixmap(dpi=300)
        img_data = pix.tobytes("png")
        img_base64 = base64.b64encode(img_data).decode('utf-8')
        doc.close()
        return img_base64
    
    def _extract_duty_cycles(self, pdf_path: str) -> Dict:
        """Extract duty cycle specifications from page 7"""
        logger.info("  → Extracting duty cycles from page 7...")
        
        # Render page 7 (specifications)
        img_base64 = self._render_page_to_base64(pdf_path, 6)  # Page 7 (0-indexed)
        
        response = self.client.messages.create(
            model=self.model,
            max_tokens=2048,
            messages=[{
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/png",
                            "data": img_base64
                        }
                    },
                    {
                        "type": "text",
                        "text": """Extract ALL duty cycle specifications from this specifications page.

                            Look for tables showing:
                            - MIG duty cycles (120V and 240V)
                            - TIG duty cycles (120V and 240V)  
                            - Stick duty cycles (120V and 240V)

                            For each, extract the duty cycle percentage and continuous use amperage.

                            Return ONLY valid JSON with this EXACT structure:
                            {
                            "MIG": {
                                "120V": {
                                "100A": {"duty_cycle": 40, "continuous": 75},
                                "75A": {"duty_cycle": 100, "continuous": 75}
                                },
                                "240V": {
                                "200A": {"duty_cycle": 25, "continuous": 115},
                                "115A": {"duty_cycle": 100, "continuous": 115}
                                }
                            },
                            "TIG": {
                                "120V": {...},
                                "240V": {...}
                            },
                            "Stick": {
                                "120V": {...},
                                "240V": {...}
                            }
                            }

                            Be extremely accurate with the numbers. Double-check each value."""
                    }
                ]
            }]
        )
        
        text = response.content[0].text
        text = text.replace('```json', '').replace('```', '').strip()
        duty_cycles = json.loads(text)
        
        logger.info(f"    ✓ Extracted duty cycles for {len(duty_cycles)} processes")
        return duty_cycles
    
    def _extract_polarity_configs(self, pdf_path: str) -> Dict:
        """Extract polarity configurations from setup pages"""
        logger.info("  → Extracting polarity configs from pages 13-14, 24, 27...")
        
        # Get relevant pages with polarity diagrams
        pages = [12, 13, 23, 26]  # Pages 13, 14, 24, 27 (0-indexed)
        images = []
        
        for page_num in pages:
            img_base64 = self._render_page_to_base64(pdf_path, page_num)
            images.append({
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": "image/png",
                    "data": img_base64
                }
            })
        
        response = self.client.messages.create(
            model=self.model,
            max_tokens=2048,
            messages=[{
                "role": "user",
                "content": [
                    *images,
                    {
                        "type": "text",
                        "text": """Extract polarity setup configurations for all welding processes from these pages.

                        Look for information about which socket (Positive + or Negative -) each cable goes into:
                        - MIG (gas shielded solid wire)
                        - Flux-Cored (gasless)
                        - TIG 
                        - Stick

                        Return ONLY valid JSON with this EXACT structure:
                        {
                        "MIG": {
                            "type": "DCEP",
                            "description": "Direct Current Electrode Positive (Gas Shielded)",
                            "ground_clamp_socket": "negative",
                            "power_cable_socket": "positive",
                            "gas_required": true
                        },
                        "Flux": {
                            "type": "DCEN",
                            "description": "Direct Current Electrode Negative (Gasless)",
                            "ground_clamp_socket": "positive",
                            "power_cable_socket": "negative",
                            "gas_required": false
                        },
                        "TIG": {...},
                        "Stick": {...}
                        }

                        Be precise about which socket each cable connects to."""
                    }
                ]
            }]
        )
        
        text = response.content[0].text
        text = text.replace('```json', '').replace('```', '').strip()
        polarity_configs = json.loads(text)
        
        logger.info(f"Extracted polarity configs for {len(polarity_configs)} processes")
        return polarity_configs
    
    def _extract_troubleshooting(self, pdf_path: str) -> Dict:
        """Extract troubleshooting matrices from pages 42-44"""
        logger.info("  → Extracting troubleshooting guides from pages 42-44...")
        
        # Troubleshooting pages
        pages = [41, 42, 43]  # Pages 42-44 (0-indexed)
        images = []
        
        for page_num in pages:
            img_base64 = self._render_page_to_base64(pdf_path, page_num)
            images.append({
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": "image/png",
                    "data": img_base64
                }
            })
        
        response = self.client.messages.create(
            model=self.model,
            max_tokens=4096,
            messages=[{
                "role": "user",
                "content": [
                    *images,
                    {
                        "type": "text",
                        "text": """Extract troubleshooting information from these pages.

                        Create a structured troubleshooting guide with:
                        - Problem/symptom
                        - Possible causes
                        - Solutions

                        Return ONLY valid JSON with this structure:
                        {
                        "wire_feed_issues": [
                            {
                            "problem": "Wire does not feed properly",
                            "causes": ["Insufficient wire feed pressure", "Incorrect roller size"],
                            "solutions": ["Increase feed pressure", "Check roller size"]
                            }
                        ],
                        "welding_issues": [
                            {
                            "problem": "Porosity in weld",
                            "causes": [...],
                            "solutions": [...]
                            }
                        ],
                        "electrical_issues": [...]
                        }

                        Be comprehensive and extract all troubleshooting information."""
                    }
                ]
            }]
        )
        
        text = response.content[0].text
        text = text.replace('```json', '').replace('```', '').strip()
        troubleshooting = json.loads(text)
        
        logger.info(f"    ✓ Extracted troubleshooting for {len(troubleshooting)} categories")
        return troubleshooting
    
    def _extract_weld_diagnosis(self, pdf_path: str) -> Dict:
        """Extract weld diagnosis images and descriptions from pages 35-38"""
        logger.info("  → Extracting weld diagnosis from pages 35-38...")
        
        # Weld diagnosis pages
        pages = [34, 35, 36, 37]  # Pages 35-38 (0-indexed)
        images = []
        
        for page_num in pages:
            img_base64 = self._render_page_to_base64(pdf_path, page_num)
            images.append({
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": "image/png",
                    "data": img_base64
                }
            })
        
        response = self.client.messages.create(
            model=self.model,
            max_tokens=4096,
            messages=[{
                "role": "user",
                "content": [
                    *images,
                    {
                        "type": "text",
                        "text": """Extract weld quality diagnosis information from these pages.

                        For each weld defect shown (porosity, spatter, burn-through, etc.), extract:
                        - Defect name
                        - Visual characteristics
                        - Causes
                        - Solutions

                        Return ONLY valid JSON with this structure:
                        {
                        "defects": [
                            {
                            "name": "Porosity",
                            "description": "Small cavities or holes in the bead",
                            "visual_signs": ["Small holes", "Pitted surface"],
                            "causes": ["Dirty workpiece", "Insufficient gas", "Wrong polarity"],
                            "solutions": ["Clean to bare metal", "Increase gas flow", "Check polarity"],
                            "page": 37
                            }
                        ]
                        }

                        Extract all defect types shown."""
                    }
                ]
            }]
        )
        
        text = response.content[0].text
        text = text.replace('```json', '').replace('```', '').strip()
        weld_diagnosis = json.loads(text)
        
        logger.info(f"    ✓ Extracted diagnosis for {len(weld_diagnosis.get('defects', []))} defect types")
        return weld_diagnosis