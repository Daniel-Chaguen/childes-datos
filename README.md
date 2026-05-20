# Proyecto final análisis de datos 2026

### Título:
Diferencias léxicas, semánticas y sintácticas en el lenguaje producido por niños con desarrollo del lenguaje típico y niños con alteraciones del lenguaje asociadas a trastornos del neurodesarrollo.

#### Descripción:
Este proyecto implementa distintas herramientas de la materia de análisis de dato 2026-1 para cuplir el ciclo de vida de los datos y resolver la pregunta central: ¿Existe alguna diferencia significativa en la producción del lenguaje entre niños con desarrollo de lenguaje típico y niños con trastornos del neurodesarrollo o alteraciones en la adquisición del lenguaje? 

Se utilizan archivos de textos de lenguaje infantil producidos en entrevistas con investigadores y terapeutas mientras se realizan diversas tareas. Los datos fueron obtenidos de la subdivisión de CHILDES de la base de datos pública TalkBank https://talkbank.org/childes/. 


#### Uso:
El preprocesamiento está basado en el repositorio de: https://github.com/Mars-tin/PyChildes.git

---Preprocesamiento---
- Paso 1:
Identificar las colecciones de interés dentro del CHILDES talkbank y descargar las carpetas con los archivos .cha correspondientes.

- Paso 2:
Crear una carpeta "raw" donde se guardarán todas las carpetas originales. En este proyecto se utilizaron las colecciones de Clinical-Eng, ENG-UK y Eng-NA. En estas colecciones se encuentran conversaciones en inglés con niños de múltiples grupos (Habla normal, síndrome de down, hablante tardío, etc...). *** En caso de buscar otra población, modificar el set de categorías en categorize_cha.py y en split_binary.py para que vaya acorde con el proyecto.

- Paso 3:
Una vez realizadas las carpetas, modificar los paths de entrada y salida para los siguientes 3 scripts: categorize_cha.py, split_binary.py, run_prepare_childes.py.

- Paso 4:
Correr los scripts con el siguiente orden:
categorize_cha.py  ->  split_binary.py  ->  run_prepare_childes.py
Si desea mantener la división en categorías puede no usar el script split_binary.py.

---¿Qué hace el preprocesamiento?---
Los archivos .cha por parte del talkbank llevan un proceso de estandarización, el cual involucra agregar caracteres específicos que enriquecen la información disponible en los transcritos. Cada línea pertenece a uno de los siguientes tipos:
- @  — Encabezados (metadata, fecha, idioma, etc.)
- (*)  — Utterances (Instancias de la conversación)
- %  — Anotaciones del investigador: morfología (%mor), gramática (%gra), acción (%act)

Este tipo de anotaciones nos permite empezar la separación por categorías para el análisis propuesto. El script categorize_cha.py reliza esto. Investiga en 3 niveles jerárquicos para delimitar el grupo al que entra cada archivo de texto. 
Niveles: 
1. Nombre de la carpeta
2. Identificar si existe algún match en el encabezado @Type
3. Identificar si existe algún match en el encabezado @ID

Esto culmina en una separación en carpetas de los archivos de la siguiente forma:
| Group | Files |
|---|---|
| TD — Typically Developing | 12,508 |
| SLI — Specific Language Impairment | 882 |
| LT — Late Talker | 515 |
| HL — Hearing Loss | 162 |
| DS — Down Syndrome | 134 |
| unsure | 329 |

*** Unsure representa esos archivos que el código no fue capaz de separar.

Limpieza de los utterance:
El script run_prepare_childes.py orquesta el preprocesado de los archivos. Este script genera el loop que va a iterar por cada archivo y llama a las funciones en prepare_childe.py. Estas funciones están diseñadas para seguir las instrucciones el el yaml disponible (PyChildes/configs/classifier.yaml). Es posible generar un yaml distinto. El preprocesamiento según las instrucciones utilizadas hace lo siguiente:
- Quita la metadata almacenada en el archivo.
- Quita las anotaciones con símbolos específicos del investigador.
- Limpia las utterances.

La limpieza de las utterances conlleva los siguientes pasos:

  **Paso 1 — Marcadores prosódicos** (`process_basic`)
  Se eliminan: dirección de tono ↑↓, alargamiento  `:`, marcas de énfasis ˈˌ, bloqueo ≠, pausas
  `(...)`.

  **Paso 2 — Linkers de utterance** (`process_linker`)
  Los terminadores especiales se normalizan: `+...` voz que se apaga → `...`, `+/.` interrumpido → `...`, `+.`
   corte de transcripción → `.`
  
  **Paso 3 — Palabras incompletas** (`process_incomplete`)
  Se restaura el material omitido entre paréntesis: `(a)n(d)` → `and`.

  **Paso 4 — Marcadores de scope** (`process_paralinguistic`)
  
  | Marcador | Comportamiento por defecto | Nuestro comportamiento |
  |---|---|---|
  | `[:]` reemplazo | Guarda la corrección (`gonna` → `going to`) | **Guarda el original** (`gonna`) |
  | `[/]` repetición | Elimina el material repetido | **Mantiene** (`I I want`) |
  | `[=]` explicación | Envuelve en tag `<exp>` | **Elimina** |
  | `[^]` paralingüístico | Envuelve en tag `<EVT>` | **Elimina** |
  | `[*]` error | Descarta la utterance | **Mantiene la utterance** |
  
  **Paso 5 — Formas especiales** (`process_special_form`)
  
  | Marcador | Significado | Tratamiento |
  |---|---|---|
  | `@b` | Babbling — vocalización pre-lingüística | → `<unk>` |
  | `@c` | Child-invented — palabra inventada | → `<unk>` |
  | `@f` | Family-specific — palabra familiar | → `<unk>` |
  | `@wp` | Word play — no-palabra lúdica | → `<unk>` |
  | `@fp` | Filled pause — uh/um anotado | Eliminado |
  | `@d` | Dialect — forma dialectal | Se mantiene |
  | `@i` | Interjection — oh, ah, wow | Se mantiene |
  | `@o` | Onomatopoeia — moo, woof | Se mantiene |
  | `@l` | Letter — letra suelta | Mayúscula |
  | `@k` | Multi-letter — cadena de letras | Mayúsculas separadas por espacio |

  **Paso 6 — Marcador no verbal**
  `0` (acción sin habla) → token `<0>`.

  **Paso 7 — Eventos locales**
  `&=laugh`, `&=coughs`, etc. → `<0>`.
  
  **Paso 8 — Disfluencias** (`process_disfluencies`)

  | Marcador | Significado | Tratamiento |
  |---|---|---|
  | `&+` | Fragmento fonológico | Eliminado |
  | `&-` | Filler (uh, um, er) | **Mantenido** |
  | `&~` | No-palabra | → `<unk>` |

  **Paso 9 — Habla no identificable** (`process_unidentifiable`)
  `xxx` (ininteligible), `yyy` (codificado fonológicamente), `www` (no transcrito) → todos → `<unk>`.


Ya realizada la limpieza de los utterance, se pasa por un último procesamiento, donde el código elige solo las utterance de los niños <CHI> y quita el <CHI>. Además elimina archivos vacíos, solo con puntuación o archivos con menos de 10 filas. 


