#!/usr/bin/env python3
"""
LonkoDev · Rota las frases del texto tipeado del README.

Elige 4 frases al azar del pool y reescribe el bloque entre
<!-- typing:start --> y <!-- typing:end --> en README.md.
Para agregar o quitar frases, edita la lista FRASES.
"""

import random
import re
from pathlib import Path
from urllib.parse import quote_plus

README = Path(__file__).resolve().parent.parent / "README.md"
CANTIDAD = 4

FRASES = [
    "> git commit -m 'arreglado (creo)'",
    "> Funciona en mi máquina 🤷",
    "> Si se repite 3 veces, se automatiza",
    "> Primero que funcione, después que sea bonito",
    "> El mejor código es el que no escribes",
    "> Leer la documentación también es programar",
    "> Un deploy un viernes es valentía",
    "> Docker: ahora funciona en todas las máquinas",
    "> La nube es el computador de otro",
    "> Los bugs no se arreglan, se migran",
    "> SQL > Excel con 40 pestañas",
    "> Nombra bien tus variables, tu yo del futuro te lo agradece",
    "> Un patrón de diseño a tiempo ahorra cien parches",
    "> Git no muerde, el merge sí",
    "> Hoy enseño lo que ayer rompí",
    "> Menos reuniones, más commits",
    "> 404: motivación no encontrada (pero igual pusheo)",
    "> Automatizo cosas para no hacerlas dos veces",
    "> Las APIs también tienen sentimientos",
    "> El café es una dependencia de producción ☕",
    "> Clean code > clever code",
    "> Refactor: el arte de cambiar todo sin cambiar nada",
    "> Si no hay backup, no existe",
    "> console.log() sigue siendo mi debugger favorito",
    "> Escalar empieza por un buen índice",
    "> La seguridad no es un feature, es la base",
    "> Tests: porque la fe no es una estrategia",
    "> Del aula a producción 🇨🇱",
    "> Código sin humo",
    "> Cada error en rojo es una clase gratis",
    "> 99 bugs en el código... arreglas uno... 127 bugs",
    "> La IA escribe, tú entiendes. Esa es la pega.",
    "> rm -rf node_modules && npm install. Fe.",
    "> Un README bueno vale más que mil reuniones",
    "> Cloud, contenedores y cero miedo",
    "> Programar es resolver problemas, no escribir código",
    "> Ctrl+Z: el mejor amigo del dev",
    "> Mientras compila, hago contenido",
]


def url(frases: list[str]) -> str:
    lines = ";".join(quote_plus(f) for f in frases)
    return (
        "https://readme-typing-svg.demolab.com?font=JetBrains+Mono&weight=600&size=22"
        "&duration=2800&pause=900&color=F1882D&center=true&vCenter=true&width=720"
        f"&lines={lines}"
    )


def main() -> None:
    elegidas = random.sample(FRASES, CANTIDAD)
    bloque = (
        "<!-- typing:start -->\n"
        '<p align="center">\n'
        '  <a href="https://lonkodev.cl">\n'
        f'    <img src="{url(elegidas)}" alt="Frases tech de LonkoDev" />\n'
        "  </a>\n"
        "</p>\n"
        "<!-- typing:end -->"
    )
    texto = README.read_text(encoding="utf-8")
    nuevo, n = re.subn(r"<!-- typing:start -->.*?<!-- typing:end -->", bloque, texto, flags=re.S)
    if n == 0:
        raise SystemExit("No encontré los marcadores typing:start / typing:end en README.md")
    README.write_text(nuevo, encoding="utf-8")
    print("Frases actualizadas")


if __name__ == "__main__":
    main()
