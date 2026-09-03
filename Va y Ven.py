import random
import simpy
from colorama import Fore, Style, init

init(autoreset=True)

# 1. ENTRADA DE DATOS (Ingresados de manera interactiva por el usuario)
def capturar_datos_entrada():
    print(
        f"{Style.BRIGHT}{Fore.CYAN}=================================================="
    )
    print(
        f"{Style.BRIGHT}{Fore.WHITE} INGRESO DE DATOS RECABADOS DE LA OBSERVACIÓN"
    )
    print(
        f"{Style.BRIGHT}{Fore.CYAN}=================================================="
    )

    datos = {}

    print(f"{Fore.YELLOW}1. Configuración general:")
    datos["tiempo_simulacion"] = float(
        input("   • Duración de la simulación en minutos: ")
    )
    datos["capacidad_bus"] = int(
        input(
            "   • Capacidad total de la unidad: "
        )
    )

    print(f"\n{Fore.YELLOW}2. Lapsos de llegada de pasajeros (en minutos):")
    datos["llegada_pasajero_min"] = float(
        input("   • Tiempo mínimo entre llegada de pasajeros (En minutos): ")
    )
    datos["llegada_pasajero_max"] = float(
        input("   • Tiempo máximo entre llegada de pasajeros (En minutos): ")
    )

    print(f"\n{Fore.YELLOW}3. Frecuencia de paso de autobuses (En minutos):")
    datos["frecuencia_bus_min"] = float(
        input("   • Intervalo mínimo de llegada de autobuses: (En minutos) ")
    )
    datos["frecuencia_bus_max"] = float(
        input("   • Intervalo máximo de llegada de autobuses (En minutos): ")
    )

    print(f"\n{Fore.YELLOW}4. Tiempos de operación (en segundos):")
    datos["pago_tarjeta_min"] = float(
        input("   • Tiempo mínimo de validación de tarjeta inteligente (En segundos): ")
    )
    datos["pago_tarjeta_max"] = float(
        input("   • Tiempo máximo de validación de tarjeta inteligente (En segundos): ")
    )
    datos["descenso_min"] = float(
        input("   • Tiempo mínimo de descenso por pasajero, puerta trasera (En segundos): ")
    )
    datos["descenso_max"] = float(
        input("   • Tiempo máximo de descenso por pasajero, puerta trasera (En segundos): ")
    )

    print(
        f"\n{Style.BRIGHT}{Fore.GREEN}¡Datos cargados correctamente! Iniciando simulación...\n"
    )
    return datos


# ==============================================================================
# 2. PROCESO DE SIMULACIÓN (Lógica con SimPy)
# ==============================================================================
tiempos_espera = []
tiempos_servicio = []
pasajeros_atendidos = 0


def llegada_pasajeros(env, fila, datos):
    i = 1
    while True:
        intervalo = random.uniform(
            datos["llegada_pasajero_min"], datos["llegada_pasajero_max"]
        )
        yield env.timeout(intervalo)
        nombre = f"Pasajero {i}"
        fila.append((nombre, env.now))
        print(
            f"{Fore.CYAN}{env.now:05.2f} min - {nombre} llega al paradero. (Fila: {len(fila)})"
        )
        i += 1


def autobus(env, id_bus, fila, validador, datos):
    global pasajeros_atendidos
    inicio_parada = env.now
    print(
        f"\n{Fore.YELLOW}=================================================="
    )
    print(
        f"{Fore.YELLOW}{env.now:05.2f} min - Autobús Va y Ven U-{id_bus} llega al paradero"
    )
    print(
        f"{Fore.YELLOW}=================================================="
    )

    # 1. Descenso de pasajeros por la puerta trasera
    pasajeros_bajan = random.randint(5, 15)
    tiempo_descenso = (
        sum(
            random.uniform(datos["descenso_min"], datos["descenso_max"])
            for _ in range(pasajeros_bajan)
        )
        / 60
    )
    yield env.timeout(tiempo_descenso)
    print(
        f"{Fore.MAGENTA}{env.now:05.2f} min - U-{id_bus}: Descendieron {pasajeros_bajan} pasajeros por puerta trasera."
    )

    # 2. Abordaje y validación por la puerta delantera
    asientos_ocupados = random.randint(10, 45)
    asientos_disponibles = datos["capacidad_bus"] - asientos_ocupados
    atendidos_unidad = 0

    print(
        f"{Fore.WHITE}{env.now:05.2f} min - U-{id_bus}: Espacio disponible: {asientos_disponibles} lugares."
    )

    while fila and atendidos_unidad < asientos_disponibles:
        nombre, tiempo_llegada = fila.pop(0)

        with validador.request() as solicitud:
            yield solicitud

            tiempo_pago_seg = random.uniform(
                datos["pago_tarjeta_min"], datos["pago_tarjeta_max"]
            )
            yield env.timeout(tiempo_pago_seg / 60)

            espera = env.now - tiempo_llegada
            tiempos_espera.append(espera)
            atendidos_unidad += 1
            pasajeros_atendidos += 1

            print(
                f"{Fore.GREEN}{env.now:05.2f} min - {nombre} valida tarjeta ({tiempo_pago_seg:.1f}s) y aborda U-{id_bus} (Esperó {espera:.2f} min)"
            )

    tiempo_total_servicio = env.now - inicio_parada
    tiempos_servicio.append(tiempo_total_servicio)

    print(
        f"{Fore.YELLOW}{env.now:05.2f} min - U-{id_bus} finaliza abordaje ({atendidos_unidad} subieron) y sale del paradero. Tiempo en parada: {tiempo_total_servicio:.2f} min"
    )
    print(
        f"{Fore.YELLOW}==================================================\n"
    )


def generador_autobuses(env, fila, validador, datos):
    i = 1
    while True:
        intervalo = random.uniform(
            datos["frecuencia_bus_min"], datos["frecuencia_bus_max"]
        )
        yield env.timeout(intervalo)
        env.process(autobus(env, i, fila, validador, datos))
        i += 1


# ==============================================================================
# 3. EJECUCIÓN Y EMISIÓN DE SALIDA DE RESULTADOS
# ==============================================================================
def ejecutar_simulacion():
    # Paso 1: Pedir los datos al usuario
    datos_entrada = capturar_datos_entrada()

    # Paso 2: Crea el entorno de SimPy con los datos ingresados
    env = simpy.Environment()
    validador = simpy.Resource(env, capacity=1)
    fila_espera = []

    env.process(llegada_pasajeros(env, fila_espera, datos_entrada))
    env.process(generador_autobuses(env, fila_espera, validador, datos_entrada))

    # Corre la simulación durante el tiempo especificado
    env.run(until=datos_entrada["tiempo_simulacion"])

    # Paso 3: Salida del sistema
    print(
        f"{Style.BRIGHT}{Fore.WHITE}=================================================="
    )
    print(
        f"{Style.BRIGHT}{Fore.WHITE} SALIDA DE RESULTADOS Y MÉTRICAS DE LA SIMULACIÓN"
    )
    print(
        f"{Style.BRIGHT}{Fore.WHITE}=================================================="
    )
    print(f"• Total de pasajeros atendidos: {pasajeros_atendidos}")

    if tiempos_espera:
        prom_espera = sum(tiempos_espera) / len(tiempos_espera)
        print(
            f"• Tiempo promedio de espera en fila: {prom_espera:.2f} minutos"
        )

    if tiempos_servicio:
        prom_servicio = sum(tiempos_servicio) / len(tiempos_servicio)
        print(
            f"• Tiempo promedio de servicio por autobús: {prom_servicio:.2f} minutos"
        )

    print(
        f"• Pasajeros remanentes en la fila al finalizar: {len(fila_espera)} personas"
    )
    print(
        f"{Style.BRIGHT}{Fore.WHITE}=================================================="
    )


if __name__ == "__main__":
    ejecutar_simulacion()