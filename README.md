# Transcriptor de Video a JSON para Workana

¡Hola equipo de Workana! 👋

He desarrollado esta herramienta con la intención de facilitarles una tarea que imagino puede ser recurrente y de gran valor: la transcripción de contenido audiovisual a formato de texto estructurado.

Mi inspiración surge pensando en la utilidad que podría tener para transcribir las valiosas mentorías que se realizan, similar a cómo se podría hacer en programas como "The Accelerator", permitiendo así un fácil acceso y análisis posterior del contenido impartido. ¡Espero que les sea de mucha utilidad!

## 🚀 Propósito de la Herramienta

Este proyecto consiste en un script de Python y una API Flask diseñada para procesar archivos de video, extraer su audio, transcribirlo utilizando el modelo Whisper de OpenAI (ejecutado localmente) y finalmente, guardar la transcripción segmentada por párrafos con sus respectivos tiempos en un archivo JSON.

## ✨ Características Principales

*   **Extracción de Audio:** Utiliza `moviepy` para extraer la pista de audio de diversos formatos de video.
*   **Transcripción Local con Whisper:** Emplea la biblioteca `whisper` de OpenAI para realizar la transcripción de audio a texto. Soporta la ejecución en CPU y GPU (si está disponible CUDA y PyTorch configurado).
*   **Segmentación de Transcripción:** El resultado de la transcripción se organiza en segmentos (párrafos) con marcas de tiempo de inicio y fin.
*   **Salida en JSON:** La transcripción final se guarda en un archivo JSON estructurado, facilitando su posterior procesamiento o integración.
*   **API Flask:** Incluye un endpoint `/procesar-video` que permite iniciar el proceso de transcripción enviando las rutas del video y del archivo JSON de salida mediante una solicitud POST.
*   **Configuración de Idioma:** Permite especificar el idioma del audio para mejorar la precisión de la transcripción (por defecto configurado para español "es", pero puede ser auto-detectado).
*   **Logging Detallado:** Tanto el script principal como la API Flask cuentan con logging para seguir el proceso y diagnosticar problemas.

## 🛠️ Cómo Funciona

La herramienta se compone de dos partes principales:

1.  **`workana_video_transcriber.py`**: Es el script núcleo que contiene toda la lógica para:
    *   Extraer el audio del video.
    *   Cargar el modelo Whisper.
    *   Transcribir el audio.
    *   Formatear y guardar la transcripción en JSON.
    *   Este script puede ejecutarse de forma independiente para pruebas o procesos batch.

2.  **`app.py`**: Es una aplicación Flask que expone un endpoint API:
    *   **Endpoint:** `POST /procesar-video`
    *   **Body (JSON):**
        ```json
        {
            "ruta_video_entrada": "C:\\ruta\\completa\\al\\video.mp4",
            "ruta_json_salida": "C:\\ruta\\completa\\al\\json_final.json"
        }
        ```
    *   Este endpoint llama a la función `procesar_video_a_json` del script `workana_video_transcriber.py` para realizar la transcripción.

## 💡 Casos de Uso Potenciales para Workana

*   **Transcripción de Mentorías:** Facilitar la documentación y el análisis del contenido de las sesiones de mentoría, como las de "The Accelerator".
*   **Creación de Subtítulos:** Utilizar la transcripción como base para generar subtítulos para videos.
*   **Análisis de Contenido:** Permitir búsquedas y análisis de palabras clave dentro del contenido de los videos.
*   **Documentación Interna:** Convertir webinars, reuniones o presentaciones grabadas en texto para fácil consulta.

## ⚙️ Configuración y Puesta en Marcha

1.  **Clonar el Repositorio (si aplica):**
    ```bash
    git clone https://github.com/EnmOvi/workana.git
    cd workana
    ```
2.  **Instalar Dependencias:**
    Asegúrate de tener Python 3.x instalado. Luego, instala las bibliotecas necesarias. Se recomienda usar un entorno virtual:
    ```bash
    python -m venv venv
    source venv/bin/activate  # En Windows: venv\Scripts\activate
    pip install Flask moviepy openai-whisper torch torchvision torchaudio
    ```
    *Nota sobre Whisper y PyTorch:* Si tienes una GPU NVIDIA compatible, PyTorch intentará usarla, lo que acelera significativamente la transcripción. Asegúrate de tener los drivers CUDA instalados. Si no, Whisper se ejecutará en CPU (más lento).

3.  **FFmpeg:** `moviepy` (y por ende Whisper para la extracción de audio) requiere FFmpeg. Asegúrate de que esté instalado en tu sistema y accesible en el PATH. Puedes descargarlo desde ffmpeg.org.

## ▶️ Uso

### Ejecutar la API Flask:

Desde el directorio del proyecto, ejecuta:
```bash
python app.py
