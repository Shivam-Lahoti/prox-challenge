import logging
from typing import Dict, List, Optional
import re

logger = logging.getLogger(__name__)


class AgentTools:
    """Tools that leverage both structured data and RAG"""
    
    def __init__(
        self, 
        vector_store, 
        images: Dict[str, str],
        structured_data: Dict
    ):
        """
        Initialize tools with structured data
        
        Args:
            vector_store: Vector store for RAG searches
            images: Dict mapping image_id -> filepath
            structured_data: Pre-extracted tables/configs
        """
        self.vector_store = vector_store
        self.images = images
        self.structured_data = structured_data
        
        # Extract specific datasets
        self.duty_cycles = structured_data.get("duty_cycles", {})
        self.polarity_configs = structured_data.get("polarity", {})
        self.troubleshooting = structured_data.get("troubleshooting", {})
        self.weld_diagnosis = structured_data.get("weld_diagnosis", {})
    
    def generate_duty_cycle_calculator(self, query: str) -> Optional[Dict]:
        """
        Generate duty cycle calculator artifact
        Uses structured data for accuracy
        """
        # Extract parameters from query
        process = self._extract_process(query)
        voltage = self._extract_voltage(query)
        amperage = self._extract_amperage(query)
        
        if not self.duty_cycles:
            logger.warning("No duty cycle data available")
            return None
        
        # Return artifact data structure
        return {
            "type": "duty_cycle_calculator",
            "data": {
                "duty_cycles": self.duty_cycles,
                "initial_values": {
                    "process": process or "MIG",
                    "voltage": voltage or "240",
                    "amperage": amperage or "200"
                }
            }
        }
    
    def generate_polarity_diagram(self, query: str) -> Optional[Dict]:
        """
        Generate polarity setup diagram
        Uses structured polarity configurations
        """
        process = self._extract_process(query)
        
        if not process or not self.polarity_configs:
            return None
        
        # Handle "Flux" vs "Flux-Cored" naming
        if process == "Flux" and "Flux" not in self.polarity_configs:
            # Try alternative names
            for key in ["Flux-Cored", "FluxCored", "FCAW"]:
                if key in self.polarity_configs:
                    process = key
                    break
        
        config = self.polarity_configs.get(process)
        
        if not config:
            logger.warning(f"No polarity config found for {process}")
            return None
        
        return {
            "type": "polarity_diagram",
            "data": {
                "process": process,
                "config": config
            }
        }
    
    def get_troubleshooting_guide(self, query: str) -> Optional[Dict]:
        """
        Get relevant troubleshooting info
        Uses structured troubleshooting matrix
        """
        query_lower = query.lower()
        
        # Match query to troubleshooting category
        relevant_issues = []
        
        for category, issues in self.troubleshooting.items():
            for issue in issues:
                problem = issue.get('problem', '').lower()
                causes = ' '.join(issue.get('causes', [])).lower()
                
                # Check if query matches this issue
                if any(word in problem or word in causes for word in query_lower.split()):
                    relevant_issues.append({
                        "category": category,
                        **issue
                    })
        
        if not relevant_issues:
            return None
        
        return {
            "type": "troubleshooting",
            "issues": relevant_issues[:3]  # Top 3 matches
        }
    
    def find_relevant_images(
        self, 
        query: str, 
        relevant_docs: List[Dict]
    ) -> List[str]:
        """Find relevant images based on query and retrieved docs"""
        query_lower = query.lower()
        image_urls = []
        
        # Get pages from relevant docs
        relevant_pages = set()
        for doc in relevant_docs[:5]:
            relevant_pages.add(doc['metadata']['page'])
        
        logger.info(f"🔍 Looking for images from pages: {relevant_pages}")
        
        # Find images from those pages
        for image_id, filepath in self.images.items():
            # Check if image is from a relevant page
            for page in relevant_pages:
                if f"_p{page}_" in image_id or f"page{page}" in image_id.lower():
                    # Extract just the filename (handle Windows paths)
                    filename = filepath.replace('\\', '/').split('/')[-1]
                    url = f"/images/{filename}"
                    
                    if url not in image_urls:
                        image_urls.append(url)
                        logger.info(f"   ✓ Added image: {url}")
                    break
        
        logger.info(f"🖼️ Returning {len(image_urls)} image URLs")
        return image_urls[:5]
    
    def calculate_duty_cycle(
        self, 
        process: str, 
        voltage: str, 
        amperage: str
    ) -> Optional[Dict]:
        """
        Calculate exact duty cycle from structured data
        
        Returns:
            Dict with duty_cycle, weld_minutes, rest_minutes, continuous_amperage
        """
        voltage_key = f"{voltage}V"
        amperage_key = f"{amperage}A"
        
        process_data = self.duty_cycles.get(process, {})
        voltage_data = process_data.get(voltage_key, {})
        amperage_data = voltage_data.get(amperage_key)
        
        if not amperage_data:
            # Try to find closest match
            available = list(voltage_data.keys())
            logger.info(f"No exact match for {amperage}A, available: {available}")
            return None
        
        duty_cycle = amperage_data.get('duty_cycle')
        continuous = amperage_data.get('continuous')
        
        if duty_cycle is None:
            return None
        
        weld_minutes = (duty_cycle / 100) * 10
        rest_minutes = 10 - weld_minutes
        
        return {
            "duty_cycle": duty_cycle,
            "weld_minutes": round(weld_minutes, 1),
            "rest_minutes": round(rest_minutes, 1),
            "continuous_amperage": continuous
        }
    
    def _extract_process(self, query: str) -> Optional[str]:
        """Extract welding process from query"""
        query_lower = query.lower()
        
        # Check for specific process mentions
        if 'flux' in query_lower and ('core' in query_lower or 'gasless' in query_lower):
            return 'Flux'
        elif 'mig' in query_lower or ('wire' in query_lower and 'gas' in query_lower):
            return 'MIG'
        elif 'tig' in query_lower or 'tungsten' in query_lower:
            return 'TIG'
        elif 'stick' in query_lower or 'smaw' in query_lower:
            return 'Stick'
        
        return None
    
    def _extract_voltage(self, query: str) -> Optional[str]:
        """Extract voltage from query"""
        if '120' in query or '120v' in query.lower():
            return '120'
        elif '240' in query or '240v' in query.lower():
            return '240'
        
        return None
    
    def _extract_amperage(self, query: str) -> Optional[str]:
        """Extract amperage from query"""
        # Match patterns like "200A", "200 amps", "200 amp"
        match = re.search(r'(\d+)\s*a(?:mp(?:s|erage)?)?', query.lower())
        if match:
            return match.group(1)
        
        return None