"""Resolve DOI identifiers into prepared, evidence-bearing source text.

The resolver uses only the Python standard library. It retrieves bibliographic
metadata from Crossref and attempts open-access full text from Europe PMC.
When full text is unavailable it falls back to the abstract, and always records
that limitation in the prepared source metadata.
"""

from __future__ import annotations

import json
import re
import ssl
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

from .extraction import (
    DownloadError,
    SourceDocument,
    _first_descendant,
    _node_text,
    _normalize_newlines,
    read_text_and_chunk,
)

CROSSREF_API = "https://api.crossref.org/works/"
EUROPE_PMC_SEARCH = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"
EUROPE_PMC_FULLTEXT = "https://www.ebi.ac.uk/europepmc/webservices/rest/{source}/{identifier}/fullTextXML"
NCBI_ESEARCH = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
NCBI_EFETCH = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
PMC_BIOC = "https://www.ncbi.nlm.nih.gov/research/bionlp/RESTful/pmcoa.cgi/BioC_xml/{pmcid}/unicode"
USER_AGENT = "bio-variable-extractor/0.2 (mailto:research@example.org)"
_DOI_PATTERN = re.compile(r"^10\.\d{4,9}/\S+$", re.IGNORECASE)
_TIMEOUT_SECONDS = 45


def looks_like_doi(value: str) -> bool:
    """Return True when the string is a DOI identifier rather than a file path."""
    candidate = normalize_doi(value)
    return bool(candidate and _DOI_PATTERN.match(candidate))


def normalize_doi(value: str) -> str:
    """Strip common DOI URL prefixes and whitespace."""
    candidate = value.strip()
    candidate = re.sub(r"^(?:https?://)?(?:dx\.)?doi\.org/", "", candidate, flags=re.IGNORECASE)
    candidate = re.sub(r"^doi:\s*", "", candidate, flags=re.IGNORECASE)
    candidate = candidate.rstrip(" .;,)")
    return candidate


def resolve_doi(
    doi: str,
    *,
    target_words: int = 170,
    max_words: int = 260,
    timeout: int = _TIMEOUT_SECONDS,
) -> tuple[dict[str, object], list[dict[str, object]], SourceDocument]:
    """Fetch a DOI and return a prepared source, chunks, and the raw document."""
    identifier = normalize_doi(doi)
    if not looks_like_doi(identifier):
        raise DownloadError(f"Invalid DOI identifier: {doi!r}")

    crossref = _fetch_crossref(identifier, timeout=timeout)
    metadata = _crossref_metadata(identifier, crossref)
    document = _fetch_full_text(identifier, metadata, timeout=timeout)

    if document is None:
        abstract = str(metadata.get("abstract") or "").strip()
        if not abstract:
            raise DownloadError(
                f"DOI {identifier} could not be resolved to open full text, and no abstract was available."
            )
        metadata["access"] = "abstract_only"
        metadata["full_text_available"] = False
        metadata["warning"] = (
            "Open-access full text was not retrieved; only the Crossref abstract is available."
        )
        document = SourceDocument(
            text=f"# abstract\n\n{abstract}",
            pages=[],
            metadata=metadata,
        )

    source, chunks = read_text_and_chunk(
        document.text,
        source_path=f"doi:{identifier}",
        source_name=f"{identifier}.doi",
        metadata=document.metadata,
        source_bytes=document.text.encode("utf-8"),
        pages=document.pages,
        target_words=target_words,
        max_words=max_words,
    )
    return source, chunks, document


def _fetch_crossref(doi: str, *, timeout: int) -> dict[str, Any]:
    url = CROSSREF_API + urllib.parse.quote(doi, safe="")
    payload = _request_json(url, timeout=timeout)
    message = payload.get("message")
    if not isinstance(message, dict):
        raise DownloadError(f"Crossref returned no work metadata for DOI {doi}.")
    return message


def _crossref_metadata(doi: str, message: dict[str, Any]) -> dict[str, object]:
    title = _first_string(message.get("title"))
    authors: list[str] = []
    for author in message.get("author", []) if isinstance(message.get("author"), list) else []:
        if not isinstance(author, dict):
            continue
        given = str(author.get("given") or "").strip()
        family = str(author.get("family") or "").strip()
        name = " ".join(part for part in (given, family) if part).strip()
        if name:
            authors.append(name)

    year = ""
    for key in ("published-print", "published-online", "issued", "created"):
        block = message.get(key)
        if not isinstance(block, dict):
            continue
        parts = block.get("date-parts")
        if isinstance(parts, list) and parts and isinstance(parts[0], list) and parts[0]:
            year = str(parts[0][0])
            break

    abstract = _clean_crossref_abstract(message.get("abstract"))
    container = _first_string(message.get("container-title"))
    return {
        "title": title,
        "authors": authors,
        "year": year,
        "doi": doi,
        "journal": container,
        "abstract": abstract,
        "source_url": message.get("URL", ""),
        "format": "doi",
        "access": "metadata_only",
        "full_text_available": False,
    }


def _fetch_full_text(
    doi: str,
    metadata: dict[str, object],
    *,
    timeout: int,
) -> SourceDocument | None:
    candidates: list[tuple[str, str]] = []
    europe_record = _fetch_europe_pmc_record(doi, timeout=timeout)
    if europe_record:
        source = str(europe_record.get("source") or "")
        identifier = str(europe_record.get("id") or "")
        pmcid = str(europe_record.get("pmcid") or "")
        if source and identifier:
            candidates.append((source, identifier))
        if pmcid and (source != "PMC" or identifier != pmcid):
            candidates.append(("PMC", pmcid))
        if not metadata.get("abstract"):
            metadata["abstract"] = _clean_crossref_abstract(europe_record.get("abstractText"))

    for source, identifier in candidates:
        document = _download_europe_pmc_full_text(source, identifier, metadata, timeout=timeout)
        if document is not None:
            return document

    # PubMed/PMC fallback keeps DOI resolution working when Europe PMC is unavailable.
    pubmed_record = _fetch_pubmed_record(doi, timeout=timeout)
    if pubmed_record:
        pmcid = pubmed_record.get("pmcid", "")
        if pmcid:
            metadata["pmcid"] = pmcid
            document = _download_europe_pmc_full_text("PMC", str(pmcid), metadata, timeout=timeout)
            if document is not None:
                return document
            document = _download_pmc_bioc_full_text(str(pmcid), metadata, timeout=timeout)
            if document is not None:
                return document
        # Prefer the richer PubMed abstract when Crossref provided none or truncated text.
        pubmed_abstract = str(pubmed_record.get("abstract") or "").strip()
        if pubmed_abstract and len(pubmed_abstract) > len(str(metadata.get("abstract") or "")):
            metadata["abstract"] = pubmed_abstract
        if not metadata.get("title"):
            metadata["title"] = pubmed_record.get("title", "")
        metadata["pubmed_id"] = pubmed_record.get("pmid", "")
    return None


def _download_europe_pmc_full_text(
    source: str,
    identifier: str,
    metadata: dict[str, object],
    *,
    timeout: int,
) -> SourceDocument | None:
    try:
        xml_text = _request_text(
            EUROPE_PMC_FULLTEXT.format(source=source, identifier=identifier),
            timeout=timeout,
        )
    except DownloadError:
        return None
    document = _parse_jats_text(xml_text, metadata)
    if document is None:
        return None
    document.metadata["access"] = "open_full_text"
    document.metadata["full_text_available"] = True
    document.metadata["europe_pmc_source"] = source
    document.metadata["europe_pmc_id"] = identifier
    return document


def _download_pmc_bioc_full_text(
    pmcid: str,
    metadata: dict[str, object],
    *,
    timeout: int,
) -> SourceDocument | None:
    """Download the PMC open-access full text through the NCBI BioC API."""
    try:
        xml_text = _request_text(PMC_BIOC.format(pmcid=pmcid), timeout=timeout)
    except DownloadError:
        return None
    document = _parse_bioc_text(xml_text, metadata)
    if document is None:
        return None
    document.metadata["access"] = "open_full_text"
    document.metadata["full_text_available"] = True
    document.metadata["full_text_source"] = "ncbi_bioc"
    document.metadata["pmcid"] = pmcid
    return document


def bioc_figure_captions(xml_text: str) -> list[str]:
    """Return figure captions embedded in a BioC document."""
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError:
        return []
    captions: list[str] = []
    for passage in root.iter():
        if _local_name(passage.tag) != "passage":
            continue
        infons = {
            str(infon.attrib.get("key", "")): _node_text(infon)
            for infon in passage
            if _local_name(infon.tag) == "infon"
        }
        if infons.get("type") not in {"fig_caption", "fig_title_caption"}:
            continue
        text = _node_text(next((child for child in passage if _local_name(child.tag) == "text"), None))
        if text and text not in captions:
            captions.append(text)
    return captions


def _parse_bioc_text(xml_text: str, metadata: dict[str, object]) -> SourceDocument | None:
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError:
        return None

    passages: list[str] = []
    for passage in root.iter():
        if _local_name(passage.tag) != "passage":
            continue
        infons = {
            str(infon.attrib.get("key", "")): _node_text(infon)
            for infon in passage
            if _local_name(infon.tag) == "infon"
        }
        text = _node_text(next((child for child in passage if _local_name(child.tag) == "text"), None))
        if not text:
            continue
        section = infons.get("section_type", "") or infons.get("type", "")
        if section.upper() in {"REF", "ACK_FUND", "SUPPL"}:
            continue
        passages.append((section, text))

    if not passages:
        return None

    lines: list[str] = []
    current_section = ""
    for section, text in passages:
        normalized = section.lower().replace("_", " ") if section else "body"
        if normalized != current_section:
            lines.extend(["", f"# {normalized}", ""])
            current_section = normalized
        lines.append(text)

    merged = "\n".join(line for line in lines if line is not None).strip()
    merged_metadata = dict(metadata)
    merged_metadata["format"] = "bioc_xml"
    captions = bioc_figure_captions(xml_text)
    if captions:
        merged_metadata["figure_captions"] = captions
    return SourceDocument(text=merged, pages=[None] * len(merged.split("\n")), metadata=merged_metadata)


def _fetch_pubmed_record(doi: str, *, timeout: int) -> dict[str, str]:
    """Resolve a DOI through NCBI E-utilities as a secondary metadata channel."""
    # ESearch uses the DOI expression; ESummary is not needed because EFetch
    # returns the title, abstract, PMCID and PMID in a single XML document.
    search_url = "{}?{}".format(
        NCBI_ESEARCH,
        urllib.parse.urlencode({"db": "pubmed", "term": f"{doi}[DOI]", "retmode": "json"}),
    )
    try:
        payload = _request_json(search_url, timeout=timeout)
    except DownloadError:
        return {}
    ids = payload.get("esearchresult", {}).get("idlist", [])
    if not isinstance(ids, list) or not ids:
        return {}
    pmid = str(ids[0])
    fetch_url = "{}?{}".format(
        NCBI_EFETCH,
        urllib.parse.urlencode(
            {"db": "pubmed", "id": ",".join(str(item) for item in ids[:1]), "retmode": "xml"}
        ),
    )
    try:
        xml_text = _request_text(fetch_url, timeout=timeout)
    except DownloadError:
        return {}
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError:
        return {}
    return {
        "pmid": pmid,
        "title": _node_text(next((item for item in root.iter() if _local_name(item.tag) == "ArticleTitle"), None)),
        "abstract": " ".join(
            _node_text(item)
            for item in root.iter()
            if _local_name(item.tag) == "AbstractText" and _node_text(item)
        ),
        "pmcid": _find_pubmed_pmcid(root),
    }


def _find_pubmed_pmcid(root: ET.Element) -> str:
    for element in root.iter():
        if _local_name(element.tag) == "ArticleId" and element.attrib.get("IdType") == "pmc":
            text = _node_text(element)
            if text:
                return text if text.upper().startswith("PMC") else f"PMC{text}"
    return ""


def _fetch_europe_pmc_record(doi: str, *, timeout: int) -> dict[str, Any]:
    query = urllib.parse.urlencode(
        {
            "query": f'DOI:"{doi}"',
            "format": "json",
            "pageSize": 5,
            "resultType": "core",
        }
    )
    try:
        payload = _request_json(f"{EUROPE_PMC_SEARCH}?{query}", timeout=timeout)
    except DownloadError:
        return {}
    results = payload.get("resultList", {}).get("result", [])
    if not isinstance(results, list):
        return {}
    return next((item for item in results if isinstance(item, dict)), {})


def _parse_jats_text(xml_text: str, metadata: dict[str, object]) -> SourceDocument | None:
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError:
        return None
    body = _first_descendant(root, "body")
    if body is None:
        return None

    lines: list[str] = []
    abstract = _first_descendant(root, "abstract")
    if abstract is not None:
        text = _node_text(abstract)
        if text:
            lines.extend(["# abstract", "", text])
    for element in body.iter():
        if _local_name(element.tag) not in {"sec", "title", "p", "table-wrap", "caption"}:
            continue
        if _local_name(element.tag) == "sec":
            continue
        text = _node_text(element)
        if not text:
            continue
        if _local_name(element.tag) == "title":
            lines.extend(["", f"# {text}", ""])
        elif text not in lines:
            lines.append(text)

    merged = "\n".join(lines).strip()
    if not merged:
        return None

    merged_metadata = dict(metadata)
    article_title = _node_text(_first_descendant(root, "article-title"))
    if article_title:
        merged_metadata["title"] = article_title
    doi = _find_article_id(root, "doi")
    if doi:
        merged_metadata["doi"] = doi
    pmcid = _find_article_id(root, "pmcid")
    if pmcid:
        merged_metadata["pmcid"] = pmcid
    merged_metadata["format"] = "jats_xml"
    return SourceDocument(text=merged, pages=[None] * len(merged.split("\n")), metadata=merged_metadata)


def _find_article_id(root: ET.Element, pub_id_type: str) -> str:
    for element in root.iter():
        if _local_name(element.tag) == "article-id" and element.attrib.get("pub-id-type") == pub_id_type:
            return _node_text(element)
    return ""


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _clean_crossref_abstract(value: Any) -> str:
    if not isinstance(value, str):
        return ""
    text = re.sub(r"<[^>]+>", " ", value)
    text = text.replace("&lt;", "<").replace("&gt;", ">").replace("&amp;", "&")
    return _normalize_newlines(re.sub(r"\s+", " ", text)).strip()


def _first_string(value: Any) -> str:
    if isinstance(value, list) and value:
        return str(value[0]).strip()
    if isinstance(value, str):
        return value.strip()
    return ""


def _request_json(url: str, *, timeout: int) -> dict[str, Any]:
    text = _request_text(url, timeout=timeout, accept="application/json")
    try:
        payload = json.loads(text)
    except json.JSONDecodeError as exc:
        raise DownloadError(f"Invalid JSON returned by {url}: {exc}") from exc
    if not isinstance(payload, dict):
        raise DownloadError(f"Unexpected JSON payload returned by {url}.")
    return payload


def _request_text(url: str, *, timeout: int, accept: str = "application/xml, text/xml, */*") -> str:
    request = urllib.request.Request(
        url,
        headers={"User-Agent": USER_AGENT, "Accept": accept},
    )
    context = ssl.create_default_context()
    try:
        with urllib.request.urlopen(request, timeout=timeout, context=context) as response:
            charset = response.headers.get_content_charset() or "utf-8"
            return response.read().decode(charset, errors="replace")
    except urllib.error.HTTPError as exc:
        raise DownloadError(f"HTTP {exc.code} while fetching {url}.") from exc
    except urllib.error.URLError as exc:
        raise DownloadError(f"Network error while fetching {url}: {exc.reason}") from exc
    except TimeoutError as exc:
        raise DownloadError(f"Timed out while fetching {url}.") from exc
