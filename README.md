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
- *  — Utterances. Ejemplo: *CHI:\t I wanna go. Instancias de la conversación.
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

