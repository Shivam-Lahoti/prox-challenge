import os
import logging
import pickle
import hashlib
from pathlib import Path
from typing import List, Dict, Tuple
import fitz
from PIL import Image
import io

logger = logging.getLogger(__name__)


class PDFProcessor:
    """Processes PDF manuals to extract text chunks and images with caching"""
    
    def __init__(self, manuals_dir: str = "../files", cache_dir: str = "cache"):
        self.manuals_dir = Path(manuals_dir)
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        self.image_output_dir = Path("static/images")
        self.image_output_dir.mkdir(parents=True, exist_ok=True)
        
        self.cache_file = self.cache_dir / "processed_documents.pkl"
        self.hash_file = self.cache_dir / "pdf_hashes.txt"
        
    def process_all(self) -> Tuple[List[Dict], Dict[str, str]]:
        """
        Process all PDFs in the manuals directory with caching
        
        Returns:
            Tuple of (documents, images)
            - documents: List of text chunks with metadata
            - images: Dict mapping image_id -> filepath
        """
        # Check if cache is valid
        if self._is_cache_valid():
            logger.info("Loading from cache...")
            return self._load_from_cache()
        
        logger.info("Processing PDFs (first run or cache invalidated)...")
        documents = []
        images = {}
        
        pdf_files = list(self.manuals_dir.glob("*.pdf"))
        logger.info(f"Found {len(pdf_files)} PDF files")
        
        for pdf_path in pdf_files:
            logger.info(f"Processing {pdf_path.name}...")
            
            # Extract text chunks
            text_chunks = self._extract_text(pdf_path)
            documents.extend(text_chunks)
            
            # Extract images
            pdf_images = self._extract_images(pdf_path)
            images.update(pdf_images)
        
        # Save to cache
        self._save_to_cache(documents, images)
        
        return documents, images
    
    def _is_cache_valid(self) -> bool:
        """Check if cached data is still valid"""
        if not self.cache_file.exists() or not self.hash_file.exists():
            return False
        
        # Calculate current hash of all PDFs
        current_hash = self._calculate_pdf_hash()
        
        # Compare with cached hash
        try:
            with open(self.hash_file, 'r') as f:
                cached_hash = f.read().strip()
            return current_hash == cached_hash
        except:
            return False
    
    def _calculate_pdf_hash(self) -> str:
        """Calculate combined hash of all PDF files"""
        hasher = hashlib.md5()
        
        pdf_files = sorted(self.manuals_dir.glob("*.pdf"))
        for pdf_path in pdf_files:
            # Hash filename and file size (fast)
            hasher.update(pdf_path.name.encode())
            hasher.update(str(pdf_path.stat().st_size).encode())
        
        return hasher.hexdigest()
    
    def _load_from_cache(self) -> Tuple[List[Dict], Dict[str, str]]:
        """Load processed documents from cache"""
        try:
            with open(self.cache_file, 'rb') as f:
                data = pickle.load(f)
            
            documents = data['documents']
            images = data['images']
            
            logger.info(f"Loaded {len(documents)} documents and {len(images)} images from cache")
            return documents, images
        
        except Exception as e:
            logger.warning(f"Cache load failed: {e}, will reprocess")
            return self.process_all()
    
    def _save_to_cache(self, documents: List[Dict], images: Dict[str, str]):
        """Save processed documents to cache"""
        try:
            # Save processed data
            with open(self.cache_file, 'wb') as f:
                pickle.dump({
                    'documents': documents,
                    'images': images
                }, f)
            
            # Save hash
            current_hash = self._calculate_pdf_hash()
            with open(self.hash_file, 'w') as f:
                f.write(current_hash)
            
            logger.info(f"Saved cache: {len(documents)} documents, {len(images)} images")
        
        except Exception as e:
            logger.warning(f"Could not save cache: {e}")
    
    def clear_cache(self):
        """Clear cached data (useful for forcing reprocessing)"""
        if self.cache_file.exists():
            self.cache_file.unlink()
        if self.hash_file.exists():
            self.hash_file.unlink()
        logger.info("Cache cleared")
    
    def _extract_text(self, pdf_path: Path) -> List[Dict]:
        """Extract text from PDF, chunked by page and section"""
        documents = []
        
        try:
            doc = fitz.open(pdf_path)
            
            for page_num in range(len(doc)):
                page = doc[page_num]
                text = page.get_text()
                
                if text.strip():
                    # Chunk by page for now (can refine later)
                    documents.append({
                        "content": text,
                        "metadata": {
                            "source": pdf_path.name,
                            "page": page_num + 1,
                            "total_pages": len(doc)
                        }
                    })
            
            doc.close()
            logger.info(f"  → {len(documents)} text chunks")
            
        except Exception as e:
            logger.error(f"Error processing {pdf_path.name}: {e}")
        
        return documents
    
    def _extract_images(self, pdf_path: Path) -> Dict[str, str]:
        """Extract images from PDF and save them"""
        images = {}
        
        try:
            doc = fitz.open(pdf_path)
            image_count = 0
            
            for page_num in range(len(doc)):
                page = doc[page_num]
                image_list = page.get_images()
                
                for img_index, img in enumerate(image_list):
                    try:
                        xref = img[0]
                        base_image = doc.extract_image(xref)
                        image_bytes = base_image["image"]
                        image_ext = base_image["ext"]
                        
                        # Create unique filename
                        filename = f"{pdf_path.stem}_p{page_num + 1}_img{img_index + 1}.{image_ext}"
                        filepath = self.image_output_dir / filename
                        
                        # Save image
                        with open(filepath, "wb") as f:
                            f.write(image_bytes)
                        
                        # Store reference
                        image_id = f"{pdf_path.stem}_page{page_num + 1}_img{img_index + 1}"
                        images[image_id] = str(filepath)
                        image_count += 1
                        
                    except Exception as e:
                        logger.warning(f"Could not extract image {img_index} from page {page_num + 1}: {e}")
            
            doc.close()
            logger.info(f"  → {image_count} images")
            
        except Exception as e:
            logger.error(f"Error extracting images from {pdf_path.name}: {e}")
        
        return images