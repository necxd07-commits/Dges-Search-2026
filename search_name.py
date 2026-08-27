import requests
from bs4 import BeautifulSoup
import re

BASE = "https://dges.gov.pt/coloc/2026/"
INDEX = BASE + "col1listas.asp?CodR=11&action=2"

session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0"
})


# ------------------------------------------------------------
# GET ESTABLISHMENTS
# ------------------------------------------------------------

def get_establishments():

    print("Getting 2026 establishment list from DGES...")

    r = session.get(INDEX)
    r.encoding = "iso-8859-1"

    soup = BeautifulSoup(r.text, "html.parser")

    select = soup.find("select", {"name": "CodEstab"})

    if not select:
        print("❌ Could not find establishments.")
        return []

    establishments = []

    for option in select.find_all("option"):

        code = option.get("value")
        name = option.get_text(" ", strip=True)

        if code and name:
            establishments.append((code, name))

    print(f"Found {len(establishments)} establishments.")

    return establishments


# ------------------------------------------------------------
# GET COURSES FOR AN ESTABLISHMENT
# ------------------------------------------------------------

def get_courses(estab_code):

    url = BASE + "col1listaredir.asp"

    data = {
        "CodEstab": estab_code,
        "CodR": "11",
        "listagem": "Lista Ordenada de Candidatos"
    }

    r = session.post(url, data=data)
    r.encoding = "iso-8859-1"

    soup = BeautifulSoup(r.text, "html.parser")

    select = soup.find("select", {"name": "CodCurso"})

    if not select:
        return []

    courses = []

    for option in select.find_all("option"):

        code = option.get("value")
        name = option.get_text(" ", strip=True)

        if code and name:
            courses.append((code, name))

    return courses


# ------------------------------------------------------------
# GET CANDIDATES FOR COURSE
# ------------------------------------------------------------

def get_candidates(estab_code, course_code):

    url = BASE + "col1listaser.asp"

    data = {
        "CodEstab": estab_code,
        "CodCurso": course_code,
        "CodR": "11",
        "search": "Continuar"
    }

    # IMPORTANT:
    # DGES needs POST here
    r = session.post(url, data=data)
    r.encoding = "iso-8859-1"

    candidates = []

    while True:

        soup = BeautifulSoup(r.text, "html.parser")

        # ----------------------------------------------------
        # FIND CANDIDATE ROWS
        # ----------------------------------------------------

        for row in soup.find_all("tr"):

            cells = row.find_all("td")

            if len(cells) < 8:
                continue

            values = [
                c.get_text(" ", strip=True)
                for c in cells
            ]

            # Candidate rows begin with a numeric order
            if not values[0].isdigit():
                continue

            try:
                ordem = int(values[0])
            except:
                continue

            candidate = {
                "ordem": ordem,
                "id": values[1],
                "nome": values[2],
                "nota": values[3],
                "opcao": values[4],
                "PI": values[5],
                "12": values[6],
                "10/11": values[7]
            }

            candidates.append(candidate)

        # ----------------------------------------------------
        # FIND NEXT PAGE
        # ----------------------------------------------------

        next_link = None

        for a in soup.find_all("a"):

            text = a.get_text(" ", strip=True)

            if "Seguinte" in text:

                href = a.get("href")

                if href:
                    next_link = href

                break

        if not next_link:
            break

        # href is relative to the 2026 directory
        if next_link.startswith("http"):
            next_url = next_link
        else:
            next_url = BASE + next_link

        r = session.get(next_url)
        r.encoding = "iso-8859-1"

    return candidates


# ------------------------------------------------------------
# SEARCH
# ------------------------------------------------------------

def search_name(name):

    search = name.lower().strip()

    establishments = get_establishments()

    if not establishments:
        return

    print()
    print("=" * 70)
    print(f"SEARCHING FOR: {name}")
    print("=" * 70)

    found = []

    for i, (estab_code, estab_name) in enumerate(establishments, 1):

        print()
        print(f"[{i}/{len(establishments)}] {estab_name}")

        courses = get_courses(estab_code)

        print(f"  → {len(courses)} courses")

        for j, (course_code, course_name) in enumerate(courses, 1):

            print(
                f"     [{j}/{len(courses)}] "
                f"{course_code} - {course_name}"
            )

            try:
                candidates = get_candidates(
                    estab_code,
                    course_code
                )

            except Exception as e:

                print(f"        ⚠ Error: {e}")
                continue

            for candidate in candidates:

                if search in candidate["nome"].lower():

                    found.append({
                        "estab": estab_name,
                        "course": course_name,
                        "course_code": course_code,
                        **candidate
                    })

                    print(
                        f"        🎯 FOUND: {candidate['nome']}"
                    )

    # --------------------------------------------------------
    # RESULTS
    # --------------------------------------------------------

    print()
    print("=" * 70)
    print("RESULTS")
    print("=" * 70)

    if not found:

        print()
        print("❌ No candidates found.")
        return

    print()
    print(f"✅ Found {len(found)} result(s):")
    print()

    for result in found:

        print("-" * 70)

        print(f"Nome:        {result['nome']}")
        print(f"Instituição: {result['estab']}")
        print(f"Curso:       {result['course']}")
        print(f"Código:      {result['course_code']}")
        print(f"Ordem:       {result['ordem']}")
        print(f"Nota:        {result['nota']}")
        print(f"Opção:       {result['opcao']}")
        print(f"Ident.:      {result['id']}")

    print("-" * 70)


# ------------------------------------------------------------
# MAIN
# ------------------------------------------------------------

def main():

    print("=" * 70)
    print("DGES 2026 NAME SEARCH")
    print("=" * 70)
    print()

    while True:

        name = input("Enter name to search (or 'exit'): ").strip()

        if name.lower() == "exit":
            break

        if not name:
            continue

        search_name(name)


if __name__ == "__main__":
    main()