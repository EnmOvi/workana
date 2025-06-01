import logging
import os
from flask import Flask, request, jsonify

# Importar la función principal del script de transcripción
# Asumimos que workana_video_transcriber.py está en el mismo directorio o en el PYTHONPATH
try:
    from workana_video_transcriber import procesar_video_a_json
except ImportError:
    logging.error("Error: No se pudo importar 'procesar_video_a_json' desde 'workana_video_transcriber.py'.")
    logging.error("Asegúrate de que 'workana_video_transcriber.py' esté en el mismo directorio que 'app.py' o en el PYTHONPATH.")
    # Salir si no se puede importar la función esencial
    import sys
    sys.exit(1)


app = Flask(__name__)

# Configuración básica de logging para la app Flask.
# La configuración de logging en workana_video_transcriber.py también se aplicará
# cuando se llame a sus funciones.
if not app.debug: # No configurar logging si Flask está en modo debug, ya que lo maneja diferente.
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

@app.route('/procesar-video', methods=['POST'])
def endpoint_procesar_video():
    """
    Endpoint para procesar un video.
    Espera un JSON en el body con:
    {
        "ruta_video_entrada": "ruta/al/video.mp4",
        "ruta_json_salida": "ruta/donde/guardar/transcripcion.json"
    }
    """
    app.logger.info("Solicitud recibida en /procesar-video")

    if not request.is_json:
        app.logger.error("La solicitud no contenía datos JSON.")
        return jsonify({"error": "La solicitud debe ser de tipo JSON"}), 400

    data = request.get_json()
    ruta_video_entrada = data.get('ruta_video_entrada')
    ruta_json_salida = data.get('ruta_json_salida')

    if not ruta_video_entrada or not ruta_json_salida:
        app.logger.error("Parámetros 'ruta_video_entrada' o 'ruta_json_salida' faltantes en el JSON.")
        return jsonify({"error": "Faltan los parámetros 'ruta_video_entrada' y/o 'ruta_json_salida'"}), 400

    app.logger.info(f"Video a procesar: {ruta_video_entrada}")
    app.logger.info(f"JSON de salida se guardará en: {ruta_json_salida}")

    # Validar que el video de entrada exista antes de procesar
    if not os.path.exists(ruta_video_entrada):
        app.logger.error(f"El archivo de video '{ruta_video_entrada}' no fue encontrado.")
        return jsonify({"error": f"El archivo de video '{ruta_video_entrada}' no fue encontrado."}), 404
    
    # Validar que el directorio para el JSON de salida exista (opcional, pero buena práctica)
    directorio_salida_json = os.path.dirname(ruta_json_salida)
    if directorio_salida_json and not os.path.exists(directorio_salida_json):
        try:
            os.makedirs(directorio_salida_json, exist_ok=True)
            app.logger.info(f"Directorio de salida '{directorio_salida_json}' creado.")
        except OSError as e:
            app.logger.error(f"No se pudo crear el directorio de salida '{directorio_salida_json}': {e}")
            return jsonify({"error": f"No se pudo crear el directorio de salida para el JSON: {e}"}), 500


    try:
        # Llamar a la función de procesamiento del script importado
        # Esta función ya maneja su propio logging detallado.
        exito = procesar_video_a_json(ruta_video_entrada, ruta_json_salida)

        if exito:
            app.logger.info(f"Procesamiento completado exitosamente para {ruta_video_entrada}.")
            return jsonify({
                "mensaje": "Video procesado exitosamente.",
                "ruta_video_entrada": ruta_video_entrada,
                "ruta_json_salida": ruta_json_salida
            }), 200
        else:
            app.logger.error(f"El procesamiento del video {ruta_video_entrada} falló.")
            return jsonify({
                "error": "El procesamiento del video falló. Revisa los logs del servidor para más detalles.",
                "ruta_video_entrada": ruta_video_entrada
            }), 500

    except Exception as e:
        app.logger.error(f"Ocurrió un error inesperado en el endpoint /procesar-video: {e}", exc_info=True)
        return jsonify({"error": f"Ocurrió un error inesperado en el servidor: {str(e)}"}), 500

if __name__ == '__main__':
    # Es importante configurar el host a '0.0.0.0' para que sea accesible
    # externamente si ejecutas esto en un servidor o Docker.
    # El modo debug NO debe usarse en producción.
    app.run(host='0.0.0.0', port=5000, debug=True)