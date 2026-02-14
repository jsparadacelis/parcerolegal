# PRD: Parcerolegal.co (Versión Colombia)

## 1. Visión y Propósito
**Parcerolegal.co** es un archivero de legislación colombiano, **gratuito, abierto y para todos**, diseñado para simplificar el acceso, consulta y comprensión de las leyes [1, 2]. Siguiendo el modelo de Justicio.es, busca eliminar las barreras entre el ciudadano y el derecho mediante una **comunicación sencilla, afable y accesible** basada en Inteligencia Artificial [1, 3].

## 2. Requisitos de Usuario y UX
*   **Interfaz "Tipo Google":** Una caja de búsqueda central única donde el usuario puede preguntar lo que quiera en lenguaje natural [4, 5].
*   **Eliminación del Prompting:** El sistema transforma internamente la pregunta del usuario para buscar en las bases de datos legales, evitando que el usuario deba aprender a hablarle a la máquina [6, 7].
*   **Sin Registro:** El acceso debe ser inmediato, **sin necesidad de registros**, correos electrónicos o suscripciones [5, 8].
*   **Rapidez:** Respuestas generadas idealmente en **menos de 15 segundos**, con un límite de 30 segundos [9].
*   **Multidispositivo:** Optimizado para escritorio, tabletas y móviles (iOS/Android/Windows/Mac) [10, 11].

## 3. Características Funcionales (Core)

### 3.1. Motor de Inteligencia Artificial (RAG)
*   **Arquitectura RAG:** Implementación de *Retrieval Augmented Generation* [12]. Los documentos se fragmentan en bloques de aproximadamente **1200 caracteres**, se convierten en vectores (embeddings) y se almacenan en una base de datos vectorial [13, 14].
*   **Cero Alucinaciones:** La **temperatura (creatividad)** del modelo se configura en **cero** para asegurar que la IA no invente conceptos y se ciña estrictamente a los datos [15-17].
*   **Filtro de Seguridad:** Si la consulta está fuera del ámbito entrenado, el sistema declara: **"A mí lo de alucinar no me va"**, explicando por qué no puede responder de forma fundamentada [18, 19].

### 3.2. Transparencia y Confianza
*   **Referencias Directas:** Inclusión de enlaces clicables al **PDF o HTML original** de la norma o sentencia [20, 21].
*   **Descarga de Archivos:** Facilidad para descargar las referencias directamente, permitiendo a los abogados realizar sus propias anotaciones sobre el documento [22].

### 3.3. Funciones de Comprensión Avanzada
*   **Selector de Jerga:** Adapta la respuesta en volumen, estructura y tono según el perfil: **Abogado, Adulto, Adolescente o Niño** (usando metáforas como "juguetes" para explicar la propiedad) [23-25].
*   **Glosario Contextual:** Los términos técnicos muestran una **definición clara y sencilla** al pasar el cursor sobre ellos [26].
*   **Ejemplos Prácticos:** Generación de casos hipotéticos para ilustrar la aplicación práctica de la norma [26, 27].

## 4. Especificaciones Técnicas
*   **Stack Sugerido:** Python (lenguaje principal), FastAPI (backend), Qdrant (base de datos vectorial) y BeautifulSoup (extracción de datos) [28, 29].
*   **Licencia:** Código abierto bajo **licencia MIT** para permitir la auditoría de "las tripas" del sistema [1, 12, 30].

## 5. Gestión de Datos (ETL)
*   **Indexación Diaria:** Un proceso ETL diario debe descargar las nuevas normas, transformarlas en embeddings y actualizar la base de datos [31, 32].
*   **Fuentes Prioritarias (Colombia):** Aunque Justicio usa el BOE y DOUE [8], Parcerolegal.co debe enfocarse en la Constitución, leyes nacionales y jurisprudencia de altas cortes (Corte Constitucional, etc.) [33, 34].

## 6. Aviso Legal
El sistema debe incluir un descargo de responsabilidad indicando que las respuestas son fundamentadas pero deben ser **complementadas por un profesional legal calificado** [35, 36].

---

## Fuentes
1.  **Transcripción de Video:** "Analizamos Justicio, la IA gratuita y abierta que simplifica la consulta de legislación" - Canal *Derecho Práctico*.
2.  **Transcripción de Video:** "Conocemos las nuevas funcionalidades de Justicio, archivero de legislación gratuito y abierto" - Canal *Derecho Práctico*.
3.  **Artículo:** "Descubre Justicio: Tu Puerta Abierta a la Legislación con IA Gratuita" - *TicDoc* (Enric Mestre Ribera).
4.  **Repositorio GitHub:** "bukosabino/justicio: Building an assistant for Boletin Oficial del Estado (BOE) using Retrieval Augmented Generation (RAG)".
5.  **Ficha Técnica / Guía Legaltech:** "Justicio | Derecho Práctico" (Little John, S.L.).
6.  **Landing Page:** "Justicio, el archivero de la legislación estatal, autonómica y europea...".