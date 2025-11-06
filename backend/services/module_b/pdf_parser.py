"""
Module B - PDF Parser with LangChain
Parse regulatory PDFs (UDC, DOTD) to extract structured data
"""
import PyPDF2
import pdfplumber
from pathlib import Path
from typing import List, Dict, Optional, Any
import logging
import re

# LangChain imports (optional - only if OPENAI_API_KEY is set)
try:
    from langchain.text_splitter import RecursiveCharacterTextSplitter
    from langchain_openai import ChatOpenAI
    from langchain.chains import create_extraction_chain
    from langchain.prompts import PromptTemplate
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False

logger = logging.getLogger(__name__)


class PDFParser:
    """
    Parse PDF documents and extract text content.

    Supports two modes:
    1. Basic text extraction (PyPDF2 + pdfplumber)
    2. AI-powered extraction with LangChain (requires OpenAI API key)
    """

    def __init__(self, pdf_path: str, use_langchain: bool = False, openai_api_key: Optional[str] = None):
        """
        Initialize PDF parser.

        Args:
            pdf_path: Path to PDF file
            use_langchain: Use LangChain for intelligent extraction
            openai_api_key: OpenAI API key for LangChain (optional)
        """
        self.pdf_path = Path(pdf_path)
        self.use_langchain = use_langchain and LANGCHAIN_AVAILABLE
        self.openai_api_key = openai_api_key
        self.pages: List[Dict] = []

        if not self.pdf_path.exists():
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")

        if use_langchain and not LANGCHAIN_AVAILABLE:
            logger.warning("LangChain not available. Falling back to basic extraction.")
            self.use_langchain = False

    def extract_text(self) -> List[Dict[str, Any]]:
        """
        Extract text from all pages.

        Returns:
            List of dictionaries with page number and text
        """
        try:
            with pdfplumber.open(self.pdf_path) as pdf:
                self.pages = []

                for page_num, page in enumerate(pdf.pages, start=1):
                    text = page.extract_text() or ""
                    tables = page.extract_tables()

                    self.pages.append({
                        "page_number": page_num,
                        "text": text,
                        "tables": tables,
                        "width": page.width,
                        "height": page.height,
                    })

            logger.info(f"Extracted text from {len(self.pages)} pages: {self.pdf_path.name}")
            return self.pages

        except Exception as e:
            logger.error(f"Error extracting text from PDF: {e}")
            raise

    def search_text(self, pattern: str, case_sensitive: bool = False) -> List[Dict]:
        """
        Search for text pattern across all pages.

        Args:
            pattern: Regex pattern to search for
            case_sensitive: Case-sensitive search

        Returns:
            List of matches with page number and context
        """
        if not self.pages:
            self.extract_text()

        flags = 0 if case_sensitive else re.IGNORECASE
        matches = []

        for page in self.pages:
            text = page["text"]
            for match in re.finditer(pattern, text, flags):
                # Get context (50 chars before and after)
                start = max(0, match.start() - 50)
                end = min(len(text), match.end() + 50)
                context = text[start:end]

                matches.append({
                    "page_number": page["page_number"],
                    "matched_text": match.group(),
                    "context": context,
                    "start_pos": match.start(),
                })

        logger.debug(f"Found {len(matches)} matches for pattern: {pattern}")
        return matches

    def extract_tables(self) -> List[Dict]:
        """
        Extract all tables from PDF.

        Returns:
            List of tables with page number
        """
        if not self.pages:
            self.extract_text()

        all_tables = []

        for page in self.pages:
            if page["tables"]:
                for table_idx, table in enumerate(page["tables"]):
                    all_tables.append({
                        "page_number": page["page_number"],
                        "table_index": table_idx,
                        "data": table,
                        "rows": len(table),
                        "columns": len(table[0]) if table else 0,
                    })

        logger.info(f"Extracted {len(all_tables)} tables from PDF")
        return all_tables

    def get_page_text(self, page_number: int) -> str:
        """
        Get text from a specific page.

        Args:
            page_number: Page number (1-indexed)

        Returns:
            Text content of the page
        """
        if not self.pages:
            self.extract_text()

        for page in self.pages:
            if page["page_number"] == page_number:
                return page["text"]

        raise ValueError(f"Page {page_number} not found (total pages: {len(self.pages)})")

    def extract_with_langchain(
        self,
        schema: Dict,
        chunk_size: int = 2000,
        chunk_overlap: int = 200
    ) -> List[Dict]:
        """
        Extract structured data using LangChain.

        Args:
            schema: JSON schema defining the structure to extract
            chunk_size: Size of text chunks for processing
            chunk_overlap: Overlap between chunks

        Returns:
            List of extracted structured data

        Example schema:
            {
                "properties": {
                    "land_use": {"type": "string"},
                    "c_value": {"type": "number"},
                    "description": {"type": "string"}
                },
                "required": ["land_use", "c_value"]
            }
        """
        if not self.use_langchain:
            raise RuntimeError("LangChain not enabled. Set use_langchain=True and provide OpenAI API key.")

        if not self.pages:
            self.extract_text()

        # Combine all text
        full_text = "\n\n".join(page["text"] for page in self.pages)

        # Split into chunks
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        )
        chunks = text_splitter.split_text(full_text)

        # Initialize LangChain model
        llm = ChatOpenAI(
            model="gpt-3.5-turbo",
            temperature=0,
            openai_api_key=self.openai_api_key
        )

        # Create extraction chain
        chain = create_extraction_chain(schema, llm)

        # Extract from each chunk
        all_extractions = []

        for chunk_idx, chunk in enumerate(chunks):
            try:
                result = chain.run(chunk)
                if result:
                    all_extractions.extend(result)
                logger.debug(f"Processed chunk {chunk_idx + 1}/{len(chunks)}")
            except Exception as e:
                logger.warning(f"Error processing chunk {chunk_idx}: {e}")
                continue

        logger.info(f"Extracted {len(all_extractions)} items using LangChain")
        return all_extractions

    def get_metadata(self) -> Dict:
        """
        Get PDF metadata.

        Returns:
            Dictionary with PDF metadata
        """
        try:
            with open(self.pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                metadata = pdf_reader.metadata

                return {
                    "title": metadata.get("/Title", ""),
                    "author": metadata.get("/Author", ""),
                    "subject": metadata.get("/Subject", ""),
                    "creator": metadata.get("/Creator", ""),
                    "producer": metadata.get("/Producer", ""),
                    "total_pages": len(pdf_reader.pages),
                    "file_size_bytes": self.pdf_path.stat().st_size,
                }
        except Exception as e:
            logger.error(f"Error reading PDF metadata: {e}")
            return {"error": str(e)}

    def to_text_file(self, output_path: str):
        """
        Export extracted text to a plain text file.

        Args:
            output_path: Path for output text file
        """
        if not self.pages:
            self.extract_text()

        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            for page in self.pages:
                f.write(f"\n{'='*80}\n")
                f.write(f"PAGE {page['page_number']}\n")
                f.write(f"{'='*80}\n\n")
                f.write(page['text'])
                f.write('\n\n')

        logger.info(f"Exported text to: {output_path}")
