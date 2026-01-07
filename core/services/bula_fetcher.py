import re
import time

import httpx
from decouple import config
from openai import OpenAI
from django.core.cache import cache

from core.models import BulaAccessLog, BulaCache


class BulaFetcherError(Exception):
    pass


MD_SAUDE_BASE = "https://www.mdsaude.com/bulas/"
ANVISA_SEARCH = "https://consultas.anvisa.gov.br/#/bulario/q/"


def _rate_limit(key, ttl=2):
    if cache.get(key):
        time.sleep(ttl)
    cache.set(key, True, ttl)


def _extract_links(html, base_url):
    return re.findall(r'href="([^"]+)"', html)


def _find_mdsaude_bula(term):
    with httpx.Client(timeout=10.0) as client:
        response = client.get(f"{MD_SAUDE_BASE}?s={term}")
        response.raise_for_status()
        links = _extract_links(response.text, MD_SAUDE_BASE)
        for link in links:
            if "/bulas/" in link:
                return link if link.startswith("http") else f"{MD_SAUDE_BASE.rstrip('/')}/{link.lstrip('/')}"
    return None


def _find_anvisa_bula(term):
    return f"{ANVISA_SEARCH}{term}"


def fetch_bula(term, hospital):
    cache_key = f"bula:{term}"
    cached = cache.get(cache_key)
    if cached:
        BulaAccessLog.objects.create(hospital=hospital, url=cached["url"], titulo=cached.get("titulo", ""))
        return cached

    _rate_limit("bula_fetcher")
    url = _find_mdsaude_bula(term)
    if not url:
        url = _find_anvisa_bula(term)

    if not url:
        raise BulaFetcherError("Bula não encontrada.")

    with httpx.Client(timeout=10.0) as client:
        response = client.get(url)
        response.raise_for_status()
        titulo_match = re.search(r"<title>(.*?)</title>", response.text, re.IGNORECASE | re.DOTALL)
        titulo = titulo_match.group(1).strip() if titulo_match else term
        conteudo = re.sub(r"<[^>]+>", "", response.text)

    cache_data = {"url": url, "titulo": titulo, "conteudo": conteudo, "url_pdf": None}
    cache.set(cache_key, cache_data, 60 * 60 * 24)

    BulaCache.objects.create(
        hospital=hospital,
        titulo=titulo,
        url=url,
        conteudo=conteudo[:10000],
    )
    BulaAccessLog.objects.create(hospital=hospital, url=url, titulo=titulo)
    return cache_data


def summarize_bula(conteudo):
    prompt = (
        "Resuma a bula em seções: "
        "Indicações/Para que serve, Como usar/Posologia, Efeitos colaterais, "
        "Contraindicações, Advertências e interações, Orientações ao Paciente."
    )
    try:
        client = OpenAI(api_key=config("OPENAI_API_KEY"))
        response = client.responses.create(
            model="gpt-4o-mini",
            input=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": conteudo[:6000]},
            ],
        )
        return response.output_text
    except Exception as exc:
        raise BulaFetcherError("Falha ao resumir bula.") from exc
