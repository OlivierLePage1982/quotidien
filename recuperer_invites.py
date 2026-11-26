import json
import re
from datetime import date, datetime
from pathlib import Path
from zoneinfo import ZoneInfo
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup


BASE_URL = "https://www.coulisses-tv.fr"
TIME_ZONE = ZoneInfo("Europe/Paris")
DATA_FILE = Path(__file__).resolve().parent / "quotidien.json"


def get_today():
    return datetime.now(TIME_ZONE).date()


def find_articles():
    urls = [
        BASE_URL,
        BASE_URL + "/index.php/magazines",
    ]

    articles = []

    for url in urls:
        try:
            response = requests.get(
                url,
                timeout=20,
                headers={"User-Agent": "Mozilla/5.0"}
            )
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")

            for link in soup.find_all("a", href=True):
                href = urljoin(url, link["href"])

                if "quotidien" not in href.lower():
                    continue

                if href.startswith(BASE_URL):
                    articles.append(href.split("#")[0])

        except requests.RequestException as error:
            print(f"Erreur lors de la lecture de {url}: {error}")

    return list(dict.fromkeys(articles))


def extract_publication_date(soup):
    # On cherche explicitement la mention « Publié » pour ne pas confondre
    # la date de publication avec une éventuelle date de modification.
    page_text = soup.get_text(" ", strip=True)

    months = {
        "janvier": 1,
        "février": 2,
        "fevrier": 2,
        "mars": 3,
        "avril": 4,
        "mai": 5,
        "juin": 6,
        "juillet": 7,
        "août": 8,
        "aout": 8,
        "septembre": 9,
        "octobre": 10,
        "novembre": 11,
        "décembre": 12,
        "decembre": 12,
    }

    match = re.search(
        r"Publié\s+(?:le\s+)?"
        r"(?:(?:lundi|mardi|mercredi|jeudi|vendredi|samedi|dimanche)\s+)?"
        r"(\d{1,2})\s+"
        r"(janvier|février|fevrier|mars|avril|mai|juin|juillet|août|aout|"
        r"septembre|octobre|novembre|décembre|decembre)\s+"
        r"(\d{4})",
        page_text,
        re.IGNORECASE
    )

    if not match:
        return None

    day = int(match.group(1))
    month = months[match.group(2).lower()]
    year = int(match.group(3))

    try:
        return date(year, month, day)
    except ValueError:
        return None


def extract_guests(article_url):
    response = requests.get(
        article_url,
        timeout=20,
        headers={"User-Agent": "Mozilla/5.0"}
    )
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    title = soup.title.get_text(" ", strip=True) if soup.title else ""

    if "quotidien" not in title.lower():
        return None

    publication_date = extract_publication_date(soup)

    if publication_date is None:
        print("Date de publication introuvable :", article_url)
        return None

    if publication_date != get_today():
        print(
            f"Article ignoré (publié le {publication_date.isoformat()}) : "
            f"{article_url}"
        )
        return None

    heading = None

    for element in soup.find_all(["h2", "h3", "h4"]):
        text = element.get_text(" ", strip=True)

        if re.match(r"^Les invités reçus\b", text, re.IGNORECASE):
            heading = element
            break

    if heading is None:
        print("Intertitre des invités introuvable.")
        return None

    guests = []

    for element in heading.find_all_next(["p", "h2", "h3", "h4"]):
        if element.name in ["h2", "h3", "h4"]:
            break

        text = element.get_text(" ", strip=True)
        text = re.sub(r"\s+", " ", text).strip()

        if not text:
            continue

        lower_text = text.lower()

        if lower_text == "magazines":
            continue
        if "newsletter" in lower_text:
            continue
        if "pour ne rien louper" in lower_text:
            continue
        if "recevez en avant-première" in lower_text:
            continue

        guests.append(text)

    if not guests:
        print("Aucun invité trouvé dans la section.")
        return None

    return {
        "date": get_today().isoformat(),
        "url": article_url,
        "updated_at": datetime.now(TIME_ZONE).isoformat(),
        "guests": guests,
    }


def save_data(data):
    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)

    with DATA_FILE.open("w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=2)


def main():
    today = get_today()
    result = None

    for article_url in find_articles():
        try:
            result = extract_guests(article_url)
        except requests.RequestException as error:
            print(f"Erreur de lecture de l'article {article_url}: {error}")
            continue

        if result:
            break

    if result is None:
        print("Aucune liste d'invités publiée pour aujourd'hui.")
        result = {
            "date": today.isoformat(),
            "url": "",
            "updated_at": "",
            "guests": []
        }

    save_data(result)
    print(f"Fichier actualisé : {DATA_FILE}")


if __name__ == "__main__":
    main()
