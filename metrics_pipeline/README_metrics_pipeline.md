# Pipeline de extracción de métricas de PLN

Este directorio contiene el código utilizado para transformar transcripciones infantiles en un dataframe de métricas de Procesamiento de Lenguaje Natural (PLN). El objetivo es obtener una fila por archivo de texto y una columna por métrica lingüística, para comparar grupos como `control` y `experimental`.

## Entrada esperada

El pipeline espera una carpeta con esta estructura:

```text
Data/1.1/
├─ control/
│  ├─ archivo_001.txt
│  ├─ archivo_002.txt
│  └─ ...
└─ experimental/
   ├─ archivo_001.txt
   ├─ archivo_002.txt
   └─ ...
```

Cada archivo `.txt` debe contener el discurso del niño ya preprocesado. En este proyecto, los archivos provienen de transcripciones `.cha` de CHILDES que fueron filtradas previamente para conservar solamente el habla infantil y remover partes del diálogo que no corresponden al niño.

## Salida generada

El pipeline genera dos archivos en la carpeta `outputs`:

```text
outputs/metrics_by_file.csv
outputs/metrics_by_file.xlsx
```

Cada fila representa una transcripción/archivo. Cada columna representa una métrica o variable derivada del texto.

## Ejecución

Desde la raíz del proyecto:

```powershell
conda run -n escuela python src/build_dataset.py --data-dir "Data\1.1" --output-dir outputs
```

Para una prueba rápida con pocos archivos:

```powershell
conda run -n escuela python src/build_dataset.py --data-dir "Data\1.1" --output-dir outputs --limit 50
```

Si se quiere usar la carpeta configurada por defecto en `config.py`, se puede ejecutar:

```powershell
conda run -n escuela python src/build_dataset.py
```

## Dependencias principales

El pipeline usa:

- `pandas`: construcción y exportación del dataframe.
- `numpy`: operaciones numéricas.
- `openpyxl`: exportación a Excel.
- `spaCy`: tokenización lingüística, POS tagging y dependencias sintácticas.
- `scikit-learn`: cálculo de TF-IDF para métricas semánticas ligeras.

Modelo de spaCy utilizado:

```text
en_core_web_sm
```

Este modelo es ligero y adecuado para correr en laptop. No usa embeddings transformer.

## Estructura de módulos

### `config.py`

Define rutas, parámetros globales y configuraciones del pipeline:

- Carpeta base del proyecto.
- Carpeta de datos por defecto.
- Carpeta de salida.
- Códigos clínicos conocidos.
- Modelo de spaCy.
- Tamaño de ventana para MATTR.
- Umbrales para definir palabras comunes dentro del corpus.
- Lista de etiquetas POS que se contabilizan.

### `io_utils.py`

Se encarga de leer los archivos de texto y construir registros internos.

Funciones principales:

- Recorre carpetas `control` y `experimental`.
- Lee cada archivo `.txt`.
- Extrae el grupo desde la carpeta.
- Intenta extraer códigos clínicos desde el nombre del archivo, si existen.
- Devuelve una estructura con ruta, nombre, grupo, texto y emisiones.

Los códigos clínicos reconocidos actualmente son:

```text
TD  = typically developed
DS  = down syndrome
LT  = late talker
HL  = hearing limited
SLI = specific language impairment
```

Si el nombre del archivo no contiene un código confiable, se marca como:

```text
disorder_label = unspecified
```

### `preprocessing.py`

Realiza limpieza básica del texto antes de calcular métricas.

Procesos principales:

- Elimina marcas entre `< >`.
- Elimina marcas entre `[ ]`.
- Normaliza espacios.
- Tokeniza palabras en minúsculas.
- Conserva solo tokens alfabéticos y contracciones simples.

Ejemplo:

```text
<up> [/?] hi hi .
```

se convierte en tokens como:

```text
hi, hi
```

### `lexical_metrics.py`

Calcula métricas de diversidad y riqueza léxica.

Métricas principales:

- `n_tokens`: número total de palabras.
- `n_types`: número de palabras distintas.
- `type_token_ratio`: diversidad léxica simple.
- `moving_average_ttr`: TTR promedio con ventanas móviles.
- `mtld`: Measure of Textual Lexical Diversity.
- `unique_words`: palabras únicas/distintas.
- `hapax_legomena`: palabras que aparecen una sola vez.
- `hapax_ratio`: proporción de hapax sobre palabras distintas.
- `common_word_token_count`: número de tokens considerados comunes dentro del corpus.
- `common_word_ratio`: proporción de palabras comunes.
- `lexical_density_sqrt`: riqueza léxica ajustada por longitud.

Las palabras comunes se definen dentro del propio corpus, no mediante una lista externa.

### `syntactic_metrics.py`

Calcula métricas sintácticas con ayuda de spaCy.

Métricas principales:

- `n_utterances`: número de emisiones.
- `n_nonempty_utterances`: emisiones con al menos una palabra válida.
- `mean_utterance_length`: longitud media de emisión.
- `sd_utterance_length`: variabilidad de longitud de emisión.
- `min_utterance_length`: emisión más corta.
- `max_utterance_length`: emisión más larga.
- `one_word_utterance_ratio`: proporción de emisiones de una palabra.
- `short_utterance_ratio_1_to_3`: proporción de emisiones de una a tres palabras.
- `pos_*_ratio`: proporción de cada categoría gramatical.
- `syntactic_tree_depth_mean`: profundidad sintáctica promedio.
- `syntactic_tree_depth_max`: profundidad sintáctica máxima.
- `spacy_parsed_utterances`: número de emisiones analizadas por spaCy.

Las categorías POS incluyen sustantivos, verbos, pronombres, auxiliares, adjetivos, adverbios, determinantes, interjecciones, partículas y otras clases gramaticales.

### `semantic_metrics.py`

Calcula métricas semánticas ligeras.

Se utilizan dos aproximaciones:

1. TF-IDF por emisión.
2. Vectores ligeros de spaCy cuando están disponibles.

Métricas TF-IDF:

- `tfidf_adjacent_coherence`: similitud coseno entre emisiones consecutivas.
- `tfidf_centroid_distance`: distancia promedio de cada emisión al centroide del archivo.
- `tfidf_utterances`: número de emisiones usadas en el cálculo.

Métricas de spaCy:

- `spacy_vector_adjacent_coherence`
- `spacy_vector_centroid_distance`
- `spacy_vector_norm_mean`
- `spacy_docs_with_vectors`

Importante: `en_core_web_sm` no contiene embeddings semánticos ricos como un modelo transformer. Por eso las métricas TF-IDF son la señal semántica principal en esta versión.

### `sentiment_metrics.py`

Calcula métricas simples de sentimiento usando un léxico interno pequeño.

Métricas:

- `positive_word_count`: conteo de palabras positivas.
- `negative_word_count`: conteo de palabras negativas.
- `sentiment_polarity_lexicon`: polaridad simple.
- `emotional_word_ratio`: proporción de palabras con carga emocional.

La polaridad se calcula como:

```text
(positive_word_count - negative_word_count) / (positive_word_count + negative_word_count)
```

Estas métricas deben interpretarse con cautela, porque en discurso infantil palabras como `no` pueden tener función pragmática y no necesariamente emocional.

### `discourse_metrics.py`

Calcula métricas de repetición y organización del discurso.

Métricas:

- `unique_utterance_count`: número de emisiones distintas.
- `unique_utterance_ratio`: proporción de emisiones únicas.
- `repeated_utterance_count`: número de emisiones repetidas.
- `repeated_utterance_ratio`: proporción de emisiones repetidas.
- `repeated_token_ratio`: proporción de tokens repetidos.
- `bigram_diversity`: diversidad de bigramas.
- `mean_adjacent_length_change`: cambio promedio en longitud entre emisiones consecutivas.

Estas métricas ayudan a describir variabilidad, repetición, perseveración y organización básica del discurso.

### `build_dataset.py`

Es el script principal del pipeline.

Pasos generales:

1. Carga transcripciones desde `control` y `experimental`.
2. Limpia emisiones.
3. Tokeniza texto.
4. Calcula palabras comunes del corpus.
5. Carga el modelo de spaCy.
6. Calcula métricas léxicas, sintácticas, semánticas, de sentimiento y discurso.
7. Construye un dataframe final.
8. Exporta resultados a CSV y XLSX.

Argumentos disponibles:

```text
--data-dir     Carpeta que contiene control/ y experimental/
--output-dir   Carpeta donde se guardan CSV y XLSX
--limit        Número máximo de archivos para pruebas rápidas
--no-spacy     Ejecuta sin métricas de spaCy
```

## Familias de métricas

### Métricas léxicas

Miden variedad, riqueza y repetición del vocabulario.

Ejemplos:

- TTR
- MATTR
- MTLD
- Hapax
- Palabras comunes

### Métricas sintácticas

Miden complejidad estructural y composición gramatical del discurso.

Ejemplos:

- Longitud media de emisión
- Proporciones POS
- Profundidad del árbol sintáctico

### Métricas semánticas

Miden continuidad y dispersión del contenido.

Ejemplos:

- Coherencia entre emisiones consecutivas
- Distancia al centroide temático del archivo

### Métricas de sentimiento

Miden carga emocional simple con base en un léxico positivo/negativo.

### Métricas de discurso

Miden repetición, variabilidad y diversidad secuencial.

Ejemplos:

- Repetición de emisiones
- Repetición de tokens
- Diversidad de bigramas

## Consideraciones metodológicas

- Cada archivo se trata como una unidad de análisis.
- Cada fila del dataframe representa una transcripción.
- Las métricas no son diagnósticas por sí mismas.
- El análisis es exploratorio y descriptivo.
- Las emisiones infantiles son cortas, por lo que algunas métricas sintácticas pueden ser inestables.
- Las métricas semánticas actuales son ligeras; una mejora futura sería usar embeddings transformer.

## Próximas mejoras posibles

- Incorporar embeddings con `sentence-transformers`.
- Añadir modelos de sentimiento entrenados para inglés.
- Mejorar extracción de metadatos clínicos si los nombres de archivo contienen códigos confiables.
- Generar reportes automáticos por grupo.
- Añadir validaciones de calidad para archivos vacíos o demasiado cortos.
