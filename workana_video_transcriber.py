import json
import os
from moviepy.video.io.VideoFileClip import VideoFileClip
import sys
import whisper
import logging
import torch

# --- Configuración ---
MODELO_WHISPER_LOCAL = "turbo"
# Opcional: especifica el idioma si se conoce de antemano (ej. "es" para español). Dejar como None para autodetección.
IDIOMA_AUDIO = "es"
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Funciones Auxiliares ---
def formatear_tiempo(segundos_totales):
    """Convierte segundos totales a formato MM:SS."""
    minutos = int(segundos_totales // 60)
    segundos = int(segundos_totales % 60)
    return f"{minutos:02d}:{segundos:02d}"

def extraer_audio_de_video(ruta_video, ruta_audio_salida="audio_temporal.mp3"):
    """Extrae el audio de un archivo de video y lo guarda como MP3."""
    logging.info(f"Extrayendo audio de: {ruta_video}...")
    try:
        clip_video = VideoFileClip(ruta_video)
        clip_audio = clip_video.audio
        # logger=None para reducir la verbosidad de moviepy en la consola
        clip_audio.write_audiofile(ruta_audio_salida, codec='mp3', logger=None)
        clip_audio.close()
        clip_video.close()
        logging.info(f"Audio extraído y guardado en: {ruta_audio_salida}")
        return ruta_audio_salida
    except Exception as e:
        logging.error(f"Error al extraer el audio: {e}")
        logging.error("Asegúrate de que FFmpeg esté instalado y en el PATH del sistema si el error persiste.")
        logging.error("Puedes descargarlo desde: https://ffmpeg.org/download.html")
        return None

def transcribir_audio_con_segmentos_local(ruta_audio, modelo_nombre=MODELO_WHISPER_LOCAL, idioma=IDIOMA_AUDIO):
    """
    Transcribe el audio usando un modelo de Whisper local.
    Devuelve una lista de segmentos, donde cada segmento se trata como un párrafo.
    """
    logging.info(f"Cargando modelo de Whisper local: {modelo_nombre}...")
    
    # Determinar el dispositivo (GPU o CPU)
    device = "cpu"
    if torch.cuda.is_available():
        logging.info("CUDA (GPU) detectada. Intentando usar GPU.")
        device = "cuda"
    else:
        logging.info("CUDA (GPU) no detectada o no disponible. Usando CPU.")
        logging.warning("La transcripción en CPU puede ser significativamente más lenta para modelos grandes.")

    try:
        # Cargar el modelo. La primera vez, se descargará.
        model = whisper.load_model(modelo_nombre, device=device)
        logging.info(f"Modelo '{modelo_nombre}' cargado en el dispositivo: {device}.")
        logging.info(f"Transcribiendo audio ({os.path.basename(ruta_audio)})... Esto puede tardar, especialmente con modelos grandes o en CPU.")
        
        # Transcribir el audio
        # Opciones adicionales que podrías considerar:
        # prompt="Workana, ..." # Para guiar al modelo con nombres propios o jerga
        # fp16=False # Si usas CPU y tienes problemas, aunque True es más rápido en GPU
        opciones_transcripcion = {"language": idioma} if idioma else {}

        resultado_transcripcion = model.transcribe(ruta_audio, **opciones_transcripcion)
        
        logging.info("Transcripción completada localmente.")
        return resultado_transcripcion.get('segments', [])

    except FileNotFoundError:
        logging.error(f"Error: El archivo de audio '{ruta_audio}' no fue encontrado.")
        return None
    except Exception as e:
        logging.error(f"Ocurrió un error inesperado durante la carga del modelo o la transcripción local: {e}", exc_info=True)
        logging.error("Asegúrate de tener suficiente RAM y, si usas GPU, que los drivers y PyTorch estén configurados correctamente.")
        return None

def procesar_video_a_json(ruta_video_entrada, ruta_json_salida):
    """
    Función principal para procesar un video:
    1. Extrae audio.
    2. Transcribe el audio obteniendo segmentos (párrafos) con tiempos.
    3. Formatea la transcripción al JSON deseado.
    4. Guarda el JSON.
    """
    logging.info(f"Iniciando procesamiento para el video: {ruta_video_entrada}")
    
    # 1. Extraer audio
    nombre_base_video = os.path.splitext(os.path.basename(ruta_video_entrada))[0]
    # Crear un nombre de archivo temporal único para el audio
    ruta_audio_temporal = f"audio_temporal_para_{nombre_base_video}_{os.getpid()}.mp3"
    
    ruta_audio_extraido = extraer_audio_de_video(ruta_video_entrada, ruta_audio_temporal)
    
    if not ruta_audio_extraido:
        logging.error("Falló la extracción de audio. Abortando proceso.")
        return False # Indicar fallo

    # 2. Transcribir audio
    segmentos_transcritos = transcribir_audio_con_segmentos_local(ruta_audio_extraido, modelo_nombre=MODELO_WHISPER_LOCAL, idioma=IDIOMA_AUDIO)
    
    # Limpiar el archivo de audio temporal después de la transcripción
    if os.path.exists(ruta_audio_extraido):
        try:
            os.remove(ruta_audio_extraido)
            logging.info(f"Archivo de audio temporal '{ruta_audio_extraido}' eliminado.")
        except OSError as e:
            logging.warning(f"No se pudo eliminar el archivo de audio temporal '{ruta_audio_extraido}': {e}")
    
    if segmentos_transcritos is None:
        logging.error("Falló la transcripción. Abortando proceso.")
        return False # Indicar fallo
        
    if not segmentos_transcritos:
        logging.warning("La transcripción no devolvió segmentos. El audio podría estar vacío o no contener voz.")
        try:
            with open(ruta_json_salida, 'w', encoding='utf-8') as f:
                json.dump({"mensaje": "No se encontraron segmentos de voz en el audio.", "parrafos": []}, f, ensure_ascii=False, indent=4)
            logging.info(f"JSON de salida guardado con mensaje de no segmentos en: {ruta_json_salida}")
        except IOError as e:
            logging.error(f"Error al escribir el archivo JSON vacío: {e}", exc_info=True)
        return True # Proceso completado, aunque sin datos de transcripción

    logging.info(f"Transcripción exitosa. Se encontraron {len(segmentos_transcritos)} segmentos (párrafos).")
    
    # 3. Formatear al JSON deseado
    datos_json_salida = []
    for i, segmento in enumerate(segmentos_transcritos):
        texto_parrafo = segmento['text'].strip()
        tiempo_inicio_seg = segmento['start']
        tiempo_fin_seg = segmento['end']
        
        datos_json_salida.append({
            "id_parrafo": i + 1, 
            "parrafo_texto": texto_parrafo,
            "tiempo_inicio_segundos": round(tiempo_inicio_seg, 3), 
            "tiempo_fin_segundos": round(tiempo_fin_seg, 3),
            "tiempo_inicio_formato_MMSS": formatear_tiempo(tiempo_inicio_seg),
            "tiempo_fin_formato_MMSS": formatear_tiempo(tiempo_fin_seg)
        })
        
    # 4. Guardar JSON
    try:
        with open(ruta_json_salida, 'w', encoding='utf-8') as f:
            json.dump(datos_json_salida, f, ensure_ascii=False, indent=4)
        logging.info(f"Transcripción formateada y guardada en: {ruta_json_salida}")
        return True # Indicar éxito
    except IOError as e:
        logging.error(f"Error al escribir el archivo JSON de salida: {e}", exc_info=True)
        return False # Indicar fallo

# --- Ejecución Principal ---
if __name__ == "__main__":
    logging.info("Automatización de Transcripción de Video a JSON para Workana")
    if IDIOMA_AUDIO:
        logging.info(f"Idioma especificado para la transcripción: {IDIOMA_AUDIO}")
    else:
        logging.info("Idioma para la transcripción: Autodetección")
    logging.info("------------------------------------------------------------")

    # Configuración de archivos de entrada y salida
    ruta_del_video_a_procesar = "C:\\Users\\ovied\\Downloads\\Video\\Sesión de Mentoría_ Upskilling & Reskilling Potencia tu Valor y Domina tu Estrategia de Pricing.mp4.mp4"
    nombre_archivo_json_salida = "transcripcion_video_workana.json" 
    if ruta_del_video_a_procesar == "ruta/al/video/ejemplo.mp4":
        logging.error("\n¡ACCIÓN REQUERIDA!")
        logging.error("***********************************************************************************")
        logging.error("POR FAVOR: Edita este script (workana_video_transcriber.py) y actualiza la")
        logging.error("           variable 'ruta_del_video_a_procesar' (línea 160 aprox.) con la ruta")
        logging.error("           completa a tu archivo de video.")
        logging.error(f"Ejemplo Linux/Mac: ruta_del_video_a_procesar = '/usuarios/tu_usuario/videos/mi_video.mp4'")
        logging.error(f"Ejemplo Windows: ruta_del_video_a_procesar = r'C:\\ruta\\completa\\a\\mi_video.mp4'")
        logging.error("***********************************************************************************")
        sys.exit(1)
    elif not os.path.exists(ruta_del_video_a_procesar):
        logging.error(f"\nError: El archivo de video '{ruta_del_video_a_procesar}' no fue encontrado.")
        logging.error("Por favor, verifica la ruta y asegúrate de que el archivo exista.")
        sys.exit(1)
    else:
        # Construir ruta de salida completa para el JSON en el directorio del script
        directorio_script = os.path.dirname(os.path.abspath(__file__))
        ruta_json_final = os.path.join(directorio_script, nombre_archivo_json_salida)
        
        logging.info(f"El video a procesar es: {ruta_del_video_a_procesar}")
        logging.info(f"El JSON de salida se guardará como: {ruta_json_final}")
        
        logging.warning("\nADVERTENCIA:")
        logging.warning(f"El modelo '{MODELO_WHISPER_LOCAL}' puede requerir una cantidad significativa de tiempo y recursos (RAM/CPU).")
        logging.warning("La primera ejecución también descargará el modelo si aún no está presente localmente.")
        
        confirmacion = input("¿Deseas continuar con el procesamiento? (s/N): ").strip().lower()
        if confirmacion == 's':
            exito = procesar_video_a_json(ruta_del_video_a_procesar, ruta_json_final)
            if exito:
                logging.info("------------------------------------------------------------")
                logging.info("Proceso completado exitosamente.")
            else:
                logging.error("------------------------------------------------------------")
                logging.error("El proceso finalizó con errores.")
        else:
            logging.info("Proceso cancelado por el usuario.")

    logging.info("Script finalizado.")